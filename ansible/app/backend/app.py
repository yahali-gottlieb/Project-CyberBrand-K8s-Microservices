from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel, Field, ValidationError
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', filename='logs/api.log', filemode='a')

app = Flask(__name__)
@app.route('/')
def health_check():
    return {"status": "healthy"}, 200
CORS(app) 

# Database connection settings from environment variables
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER", "dbadmin")

# STRICT SECURITY: No hardcoded fallback password! Fail fast if missing.
DB_PASS = os.environ.get("DB_PASS")
if not DB_PASS:
    raise ValueError("CRITICAL: DB_PASS environment variable is missing. Refusing to start.")

DB_NAME = os.environ.get("DB_NAME", "appdb")

def get_db_connection():
    # Terraform AWS RDS endpoint formatting
    host = DB_HOST.split(':')[0] if DB_HOST else 'localhost'
    conn = psycopg2.connect(
        host=host,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

def init_db():
    """Create the quiz_scores table if it doesn't exist."""
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

# Pydantic Model matches the payload sent by the Cyber Brand Quiz frontend
class GamePayload(BaseModel):
    name: str = Field(..., min_length=2)
    os: str = Field(...) # Contains the score and accuracy string
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
        
        # Fake instance ID to satisfy the frontend's expected response
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
    # STRICT SECURITY: Disable Flask debug mode in production
    app.run(host='0.0.0.0', port=5001, debug=False)