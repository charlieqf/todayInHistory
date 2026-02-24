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
    
    # Node 2: Script Generation
    print(">>> STEP 1: AI Script Generation")
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
