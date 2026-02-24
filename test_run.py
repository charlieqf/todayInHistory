import sqlite3
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "data", "history_events.db")
sys.path.append(os.path.join(SCRIPT_DIR, "database_builder"))

from pipeline.automation_orchestrator import run_full_pipeline

def spawn_and_run():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Event 66
    cursor.execute('INSERT OR IGNORE INTO video_jobs (event_id, status) VALUES (?, ?)', (66, 'PENDING'))
    conn.commit()
    
    cursor.execute('SELECT id FROM video_jobs WHERE event_id = ?', (66,))
    job_id = cursor.fetchone()[0]
    conn.close()
    
    print(f"Created/Found Job ID: {job_id}. Triggering Orchestrator...")
    run_full_pipeline(job_id)

if __name__ == "__main__":
    spawn_and_run()
