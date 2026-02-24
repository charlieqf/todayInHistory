import sqlite3
import os

def test_db():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "data", "history_events.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Grab the second event
    cursor.execute("SELECT id, title FROM historical_events LIMIT 1 OFFSET 1")
    event = cursor.fetchone()
    print(f"Found event: {event}")
    
    # Check jobs
    cursor.execute("SELECT id, status FROM video_jobs")
    jobs = cursor.fetchall()
    print(f"Current Video Jobs: {jobs}")

if __name__ == "__main__":
    test_db()
