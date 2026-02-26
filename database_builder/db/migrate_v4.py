import sqlite3
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "..", "..", "data", "history_events.db")

def migrate():
    print("⏳ Starting V4 Database Migration...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if the column exists first
        cursor.execute("PRAGMA table_info(channels)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "audio_bgm" not in columns:
            print("   -> Adding 'audio_bgm' column to channels table...")
            cursor.execute("ALTER TABLE channels ADD COLUMN audio_bgm TEXT")
            print("   ✅ Schema updated successfully.")
            
            # Optionally populate stock_replay with a placeholder BGM for testing
            cursor.execute("""
                UPDATE channels 
                SET audio_bgm = 'assets/bgm/suspense_loop_1.mp3' 
                WHERE slug = 'stock_replay'
            """)
            print("   ✅ Seeded default BGM path for 'stock_replay'.")
            
            conn.commit()
        else:
            print("   ✅ Column 'audio_bgm' already exists. No migration needed.")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()
        
if __name__ == "__main__":
    migrate()
