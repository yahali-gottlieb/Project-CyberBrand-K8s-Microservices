from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from pydantic import BaseModel, Field, ValidationError
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
import time
from prometheus_client import Counter, Histogram, Info, generate_latest, CONTENT_TYPE_LATEST

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', filename='logs/api.log', filemode='a')

app = Flask(__name__)
CORS(app)

# ==========================================
# PROMETHEUS METRICS DEFINITIONS
# ==========================================

# 1. App Info (Version)
APP_INFO = Info('app_info', 'Application information')
APP_INFO.info({'version': '1.0.0', 'environment': 'production'})

# 2. HTTP Requests Counter (RPS, Errors)
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'http_status']
)

# 3. HTTP Request Latency Histogram (p95/p99)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 
    'HTTP request latency', 
    ['method', 'endpoint']
)

# 4. Business Metric (Total Scores Provisioned)
SCORES_PROVISIONED = Counter(
    'app_quiz_scores_saved_total', 
    'Total successful game scores saved to the database'
)

# ==========================================
# PROMETHEUS MIDDLEWARE
# ==========================================

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    # Do not track the /metrics endpoint itself to avoid noise
    if request.path != '/metrics':
        latency = time.time() - getattr(request, 'start_time', time.time())
        REQUEST_LATENCY.labels(request.method, request.path).observe(latency)
        REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
    return response

# ==========================================
# PROMETHEUS ENDPOINT
# ==========================================

@app.route('/metrics', methods=['GET'])
def metrics():
    """Endpoint for Prometheus to scrape metrics."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# ==========================================
# ORIGINAL APPLICATION LOGIC
# ==========================================

@app.route('/')
def health_check():
    return {"status": "healthy"}, 200

# Database connection settings from environment variables
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER", "dbadmin")
DB_PASS = os.environ.get("DB_PASS")

if not DB_PASS:
    raise ValueError("CRITICAL: DB_PASS environment variable is missing. Refusing to start.")

DB_NAME = os.environ.get("DB_NAME", "appdb")

def get_db_connection():
    host = DB_HOST.split(':')[0] if DB_HOST else 'localhost'
    conn = psycopg2.connect(
        host=host,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

def init_db():
    try:
        if not DB_HOST:
            logging.warning("DB_HOST is not set. Running in local/test mode without DB.")
            return
            
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS quiz_scores (
                id SERIAL PRIMARY KEY,
                player_name VARCHAR(100) NOT NULL,
                game_stats VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()
        cur.close()
        conn.close()
        logging.info("Database initialized successfully with quiz_scores table.")
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")

init_db()

class GamePayload(BaseModel):
    name: str = Field(..., min_length=2)
    os: str = Field(...) 
    cpu: int 
    ram: int 
    provision: bool = False 

@app.route('/api/provision', methods=['POST'])
def save_score():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400
        
        config = GamePayload(**data)
        auth_id = f"auth-{str(uuid.uuid4())[:8]}"
        
        if DB_HOST:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO quiz_scores (player_name, game_stats)
                VALUES (%s, %s)
            ''', (config.name, config.os))
            conn.commit()
            cur.close()
            conn.close()
            logging.info(f"Score for player '{config.name}' saved to RDS database.")
            
            # Increment the business metric when a score is successfully saved
            SCORES_PROVISIONED.inc()
            
        else:
            logging.warning("DB_HOST missing, skipping DB insertion.")

        return jsonify({
            "status": "success",
            "message": f"Score for '{config.name}' saved to DB successfully!",
            "data": {
                "instance_id": auth_id,
                "name": config.name
            }
        }), 201

    except ValidationError as e:
        errors = [{"field": err["loc"][0], "message": err["msg"]} for err in e.errors()]
        logging.error(f"[API] Validation Error: {errors}")
        return jsonify({"status": "error", "message": "Invalid input", "details": errors}), 400
        
    except Exception as e:
        logging.error(f"[API] Internal Server Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/machines', methods=['GET'])
def get_scores():
    try:
        if not DB_HOST:
            return jsonify({"status": "error", "message": "Database not configured"}), 500
            
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM quiz_scores ORDER BY created_at DESC LIMIT 50;')
        scores = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({"status": "success", "data": scores}), 200
        
    except Exception as e:
        logging.error(f"[API] Error fetching scores: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("Starting CyberBrand API on http://0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)