import sqlite3
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "data", "history_events.db")

def migrate_db():
    print(f"Starting V3 Multi-Series Database Migration on {DB_FILE}...")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # 1. Begin Transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # 2. Create Channels Table
        print("Creating channels table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                system_prompt TEXT NOT NULL,
                review_prompt TEXT,
                tts_voice TEXT NOT NULL DEFAULT 'zh-CN-YunxiNeural',
                css_filter TEXT NOT NULL DEFAULT 'sepia(0.3) contrast(1.1) brightness(0.9) grayscale(0.2)',
                color_accent TEXT NOT NULL DEFAULT '#00d4ff',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert Default Channels (as per seed data phase 9 plan)
        print("Seeding default channels...")
        cursor.executemany('''
            INSERT OR IGNORE INTO channels (id, slug, display_name, system_prompt, tts_voice, css_filter)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [
            (1, 'it_history', '💻 IT历史上的今天', 'Please explain this IT history event.', 'zh-CN-YunxiNeural', 'sepia(0.3) contrast(1.1) brightness(0.9) grayscale(0.2)'),
            (2, 'wealth_boss', '💰 财富密码', 'Explain this business success.', 'zh-CN-YunjianNeural', 'contrast(1.2) brightness(1.1)'),
            (3, 'mystery', '👻 未解之谜档案馆', 'Tell this spooky story.', 'zh-CN-XiaoyiNeural', 'invert(0.1) hue-rotate(180deg)'),
            (4, 'hardcore_bio', '🔥 硬核狠人传', 'Narrate this intense biography.', 'zh-CN-YunxiNeural', 'contrast(1.3) grayscale(0.3)'),
            (5, 'stock_replay', '📈 妖股复盘', 'Act as an intense financial storyteller recapping a wild stock market run.', 'zh-CN-YunjianNeural', 'contrast(1.4) saturate(1.5)'),
            (6, 'ancient_china', '🏮 古人最后一天', 'Tell a tragic historical story.', 'zh-CN-XiaochenNeural', 'sepia(0.5) blur(1px)')
        ])
        
        # 3. Handle video_jobs table
        print("Adding channel_id to video_jobs...")
        try:
            cursor.execute("ALTER TABLE video_jobs ADD COLUMN channel_id INTEGER REFERENCES channels(id)")
        except sqlite3.OperationalError:
            print("  Column channel_id already exists in video_jobs, skipping.")
        
        print("Assigning existing jobs to channel 1...")
        cursor.execute("UPDATE video_jobs SET channel_id = 1 WHERE channel_id IS NULL")
        
        # 4. Handle historical_events table migration
        print("Creating new_historical_events table allowing NULL dates...")
        cursor.execute('''
            CREATE TABLE new_historical_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER REFERENCES channels(id),
                month INTEGER,
                day INTEGER,
                year INTEGER,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                category TEXT,
                importance_score INTEGER DEFAULT 0,
                rich_context TEXT,
                source TEXT
            )
        ''')
        
        # Get count to verify later
        cursor.execute("SELECT COUNT(*) FROM historical_events")
        old_count = cursor.fetchone()[0]
        
        print(f"Migrating {old_count} existing events to new schema (assigning to channel 1)...")
        # Ensure 'month' and 'day' are set, avoiding null logic hiding per user request
        # Since these all came from the IT history calendar scraper, they MUST have dates.
        cursor.execute('''
            INSERT INTO new_historical_events (id, channel_id, month, day, year, title, summary, category, importance_score, rich_context, source)
            SELECT id, 1, month, day, year, title, summary, category, importance_score, rich_context, source 
            FROM historical_events
        ''')
        
        # Swap tables
        print("Swapping old table for new table...")
        cursor.execute("DROP TABLE historical_events")
        cursor.execute("ALTER TABLE new_historical_events RENAME TO historical_events")
        
        print("Recreating unique index on (channel_id, month, day, year, title)...")
        cursor.execute("CREATE UNIQUE INDEX idx_event_unique ON historical_events(channel_id, month, day, year, title)")
        
        # Commit the transaction
        cursor.execute("COMMIT")
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"❌ Error during migration. Rolling back changes. Error: {e}")
        raise e
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_db()
