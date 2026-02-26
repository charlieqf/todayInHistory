import sys
import os
import json
import logging

# Ensure modules in pipeline can be imported
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

# Import the nodes sequentially
from node_script_gen import run_script_generation
from node_assets_gen import run_asset_generation
from node_render import render_video_for_job

def run_full_pipeline(job_id: int):
    """
    Orchestrates the entire video generation pipeline for a given job.
    Executes Node 2 -> Node 3 -> Node 4 sequentially.
    """
    print(f"\n=======================================================")
    print(f"🚀 [Orchestrator] Launching Full Pipeline for Job #{job_id}")
    print(f"=======================================================\n")
    
    # 0. Check Job Channel to determine branching
    import sqlite3
    DB_PATH = os.path.join(SCRIPT_DIR, "..", "..", "data", "history_events.db")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    job_info = conn.execute('''
        SELECT ch.slug 
        FROM video_jobs vj 
        LEFT JOIN channels ch ON vj.channel_id = ch.id 
        WHERE vj.id = ?
    ''', (job_id,)).fetchone()
    conn.close()
    
    channel_slug = job_info['slug'] if job_info else ''
    
    # Node 2: Script Generation (or Visual Mapping for long-form content)
    print(f">>> STEP 1: AI Script/Visual Generation (Channel: {channel_slug})")
    
    if channel_slug == 'stock_replay':
        from node_visual_mapper import run_visual_mapping
        if not run_visual_mapping(job_id, words_per_chunk=400):
            print(f"❌ [Orchestrator] Pipeline Halted: Visual Mapping Failed for Job {job_id}")
            return False
    else:
        if not run_script_generation(job_id):
            print(f"❌ [Orchestrator] Pipeline Halted: Script Generation Failed for Job {job_id}")
            return False
        
    print("\n>>> STEP 2: Asset Synthesis (Audio & Vision)")
    # Node 3: Audio (TTS) & Image Generation
    if not run_asset_generation(job_id):
        print(f"❌ [Orchestrator] Pipeline Halted: Asset Synthesis Failed for Job {job_id}")
        return False
        
    print("\n>>> STEP 3: React Remotion Rendering")
    # Node 4: React Remotion Rendering
    if not render_video_for_job(job_id):
        print(f"❌ [Orchestrator] Pipeline Halted: Video Rendering Failed for Job {job_id}")
        return False
        
    print(f"\n🎉 [Orchestrator] SUCCESS! Full Pipeline completed for Job #{job_id}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        job_id = int(sys.argv[1])
        run_full_pipeline(job_id)
    else:
        print("Usage: python automation_orchestrator.py <job_id>")
