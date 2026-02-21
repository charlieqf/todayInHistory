import sqlite3
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Save the database at the root of the project's data folder
DB_FILE = os.path.join(SCRIPT_DIR, "..", "..", "data", "history_events.db")

def init_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create the main table for daily video suggestions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month INTEGER NOT NULL,
            day INTEGER NOT NULL,
            year INTEGER NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            category TEXT,
            importance_score INTEGER NOT NULL,
            rich_context TEXT,
            source TEXT
        )
    ''')
    
    # Unique constraint prevents double-scraping the exact same event
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_event_unique 
        ON historical_events(month, day, year, title)
    ''')
    
    # Pipeline Tracker Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'PENDING',
            script_prompt TEXT,
            script_json TEXT,
            image_prompt_1 TEXT,
            image_prompt_2 TEXT,
            audio_path TEXT,
            video_path TEXT,
            error_log TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES historical_events (id)
        )
    ''')
    
    # Publishing & Analytics Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS publish_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            platform TEXT NOT NULL, 
            url TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES video_jobs (id),
            UNIQUE(job_id, platform)
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_events(events, source="wikipedia"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    inserted_count = 0
    duplicate_count = 0
    
    for event in events:
        try:
            cursor.execute('''
                INSERT INTO historical_events 
                (month, day, year, title, summary, category, importance_score, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event['month'], event['day'], event['year'], 
                event['title'][:100], event['summary'], event['category'], 
                event['importance_score'], source
            ))
            inserted_count += 1
        except sqlite3.IntegrityError:
            # If the exact same date and title exist, it's a silent duplicate skip
            duplicate_count += 1
            
    conn.commit()
    conn.close()
    return inserted_count, duplicate_count

if __name__ == "__main__":
    init_db()
    print(f"✅ SQLite Database initialized at {DB_FILE}")
