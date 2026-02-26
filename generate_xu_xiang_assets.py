import sqlite3
import os
import sys

# Add pipeline directory to path so we can import the nodes
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_DIR = os.path.join(SCRIPT_DIR, "database_builder", "pipeline")
sys.path.append(PIPELINE_DIR)

from node_visual_mapper import run_visual_mapping
from node_assets_gen import run_asset_generation

def generate_assets_only():
    print("🚀 Starting Asset-Only Generation for: 徐翔_从“私募一哥”到“妖股缔造者”的沉浮录")
    
    # 1. Read the text file
    txt_path = os.path.join(SCRIPT_DIR, "data", "final_scripts_stocks", "徐翔_从“私募一哥”到“妖股缔造者”的沉浮录.txt")
    with open(txt_path, 'r', encoding='utf-8') as f:
        rich_context = f.read()
        
    # 2. Setup SQLite DB connection
    db_path = os.path.join(SCRIPT_DIR, "data", "history_events.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the Xu Xiang event already exists in DB to avoid dupes
    cursor.execute("SELECT id FROM historical_events WHERE title LIKE '%徐翔%'")
    event_row = cursor.fetchone()
    
    if event_row:
        event_id = event_row[0]
        print(f"✅ Found existing Event ID {event_id} for Xu Xiang.")
    else:
        # Create a new event just for this job
        cursor.execute('''
            INSERT INTO historical_events (title, event_date, rich_context, category, tags, channel_id)
            VALUES (?, ?, ?, ?, ?, (SELECT id FROM channels WHERE slug = 'stock_replay'))
        ''', ("徐翔：从私募一哥到妖股缔造者", "2015-11-01", rich_context, "Financial History", "徐翔, 涨停板敢死队, 泽熙投资"))
        conn.commit()
        event_id = cursor.lastrowid
        print(f"🆕 Created new Event ID {event_id} for Xu Xiang.")
        
    # 3. Create a new video_job
    cursor.execute('''
        INSERT INTO video_jobs (event_id, channel_id, status) 
        VALUES (?, (SELECT id FROM channels WHERE slug = 'stock_replay'), 'PENDING')
    ''', (event_id,))
    conn.commit()
    job_id = cursor.lastrowid
    print(f"✨ Created new Job ID {job_id} for Asset Generation.")
    conn.close()
    
    # 4. Run Node 2.5: Visual Mapper (Chunk text and get Gemini prompts)
    print("\n>>> STEP 1: AI Visual Mapping (Chunking & Prompting)")
    if not run_visual_mapping(job_id, words_per_chunk=400):
        print(f"❌ Visual Mapping Failed for Job {job_id}")
        return False
        
    # 5. Run Node 3: Asset Synthesis (TTS + Replicate Flux Images)
    print("\n>>> STEP 2: Asset Synthesis (Audio TTS & Flux Images)")
    if not run_asset_generation(job_id):
        print(f"❌ Asset Synthesis Failed for Job {job_id}")
        return False
        
    print(f"\n🎉 SUCCESS! All assets generated for Job #{job_id}. Skipping Remotion Video Render.")
    print(f"You can find the assets in: c:\\work\\code\\todayInHistory\\video-generator\\public\\assets\\")
    print(f"- MP3 Audio: job_{job_id}_narration.mp3")
    print(f"- PNG Images: job_{job_id}_scene_*.png")
    
if __name__ == "__main__":
    generate_assets_only()
