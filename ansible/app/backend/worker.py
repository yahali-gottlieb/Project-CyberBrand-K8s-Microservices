import os
import csv
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import boto3

os.makedirs('logs', exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', filename='logs/worker.log', filemode='a')

# AWS Configurations
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "devops-project-bucket-yahali-v2")
SNS_TOPIC_NAME = os.environ.get("SNS_TOPIC_NAME", "devops-app-alerts")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Database Configuration
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER", "dbadmin")

# STRICT SECURITY: No hardcoded fallback password! Fail fast if missing.
DB_PASS = os.environ.get("DB_PASS")
if not DB_PASS:
    raise ValueError("CRITICAL: DB_PASS environment variable is missing. Refusing to start.")

DB_NAME = os.environ.get("DB_NAME", "appdb")

def get_db_connection():
    host = DB_HOST.split(':')[0] if DB_HOST else 'localhost'
    return psycopg2.connect(host=host, database=DB_NAME, user=DB_USER, password=DB_PASS)

def generate_report():
    logging.info("Starting daily game scores report generation...")
    if not DB_HOST:
        logging.error("No DB_HOST configured. Cannot generate report.")
        return None
    
    filename = f"/tmp/quiz_leaderboard_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM quiz_scores ORDER BY created_at DESC;')
        scores = cur.fetchall()
        
        with open(filename, 'w', newline='') as f:
            if scores:
                writer = csv.DictWriter(f, fieldnames=scores[0].keys())
                writer.writeheader()
                writer.writerows(scores)
            else:
                f.write("No game scores recorded yet.\n")
                
        cur.close()
        conn.close()
        logging.info(f"Report generated successfully: {filename}")
        return filename
    except Exception as e:
        logging.error(f"Error generating report: {e}")
        return None

def upload_to_s3(filename):
    s3 = boto3.client('s3', region_name=AWS_REGION)
    object_name = f"reports/{os.path.basename(filename)}"
    try:
        s3.upload_file(filename, S3_BUCKET_NAME, object_name)
        logging.info(f"Uploaded {object_name} to S3 bucket {S3_BUCKET_NAME}")
        return True
    except Exception as e:
        logging.error(f"Failed to upload to S3: {e}")
        return False

def get_sns_topic_arn(sns_client, topic_name):
    topics = sns_client.list_topics()['Topics']
    for topic in topics:
        if topic['TopicArn'].endswith(f":{topic_name}"):
            return topic['TopicArn']
    return None

def send_sns_notification(message):
    sns = boto3.client('sns', region_name=AWS_REGION)
    topic_arn = get_sns_topic_arn(sns, SNS_TOPIC_NAME)
    
    if not topic_arn:
        logging.error(f"SNS Topic '{SNS_TOPIC_NAME}' not found.")
        return
        
    try:
        sns.publish(
            TopicArn=topic_arn,
            Subject="CyberBrand Quiz - Daily Leaderboard Report",
            Message=message
        )
        logging.info("SNS notification sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send SNS notification: {e}")

if __name__ == "__main__":
    print("Running worker job to generate and upload leaderboard...")
    report_file = generate_report()
    if report_file:
        success = upload_to_s3(report_file)
        if success:
            msg = f"The daily CyberBrand Quiz leaderboard has been generated and uploaded to S3.\nFile: {os.path.basename(report_file)}"
            send_sns_notification(msg)
            print("Done! Check your S3 bucket and email for the SNS alert.")
        else:
            send_sns_notification("Failed to upload the leaderboard report to S3.")
    print("Worker job completed.")