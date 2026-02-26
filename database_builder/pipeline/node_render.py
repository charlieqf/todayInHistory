import os
import sys
import json
import subprocess
from typing import Dict, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "..", "db")
sys.path.append(DB_DIR)
from storage import get_db_connection

ROOT_DIR = os.path.join(SCRIPT_DIR, "..", "..")
REMOTION_DIR = os.path.join(ROOT_DIR, "video-generator")
SCRIPT_JSON_PATH = os.path.join(REMOTION_DIR, "src", "current_script.json")

def render_video_for_job(job_id: int) -> bool:
    print(f"🎬 [Node 4 - Render Engine] Starting for Job #{job_id}...")
    
    conn = get_db_connection()
    try:
        job = conn.execute('SELECT * FROM video_jobs WHERE id = ?', (job_id,)).fetchone()
        
        if not job or not job['script_json'] or job['status'] not in ['AUDIO_GEN', 'RENDER_COMPLETE']:
            print(f"❌ Job {job_id} is missing assets or doesn't exist.")
            return False

        # 1. Inject JSON into the React codebase
        script_data = json.loads(job['script_json'])
        with open(SCRIPT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
            
        print(f"   [Data Injection] ✅ Rewrote current_script.json for React compiler.")

        # 2. Setup output paths
        output_filename = f"job_{job_id}_final.mp4"
        output_filepath = os.path.join(REMOTION_DIR, "out", output_filename)
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

        # 3. Call `npx remotion render` subprocess
        cmd = [
            "npx.cmd" if os.name == "nt" else "npx",
            "remotion",
            "render",
            "src/index.ts",
            "IT-History-Today-Xerox-Alto",
            f"out/{output_filename}"
        ]
        
        print(f"   [FFMpeg] 🚀 Spawning Remotion Bundle & Render command...")
        print(f"   [FFMpeg] Executing: {' '.join(cmd)}")
        
        # This will block until the video is rendered. Capturing output.
        process = subprocess.Popen(
            cmd,
            cwd=REMOTION_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        # Stream logs to the python terminal
        for line in process.stdout:
            sys.stdout.write(f"     [Remotion] {line}")
            
        process.wait()

        if process.returncode != 0:
            raise Exception(f"Remotion Exit Code: {process.returncode}")

        # 4. Save video path and mark complete
        relative_video_path = f"out/{output_filename}" # Use relative to be served by a static server if needed
        conn.execute('''
            UPDATE video_jobs 
            SET video_path = ?, status = 'RENDER_COMPLETE', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (relative_video_path, job_id))
        conn.commit()
        
        print(f"✅ [Node 4 - Render Engine] Production finished! Video at {relative_video_path}")
        return True

    except Exception as e:
        print(f"❌ [Node 4 - Render Engine] Rendering crashed: {e}")
        conn.execute("UPDATE video_jobs SET error_log = ?, status = 'ERROR' WHERE id = ?", (str(e), job_id))
        conn.commit()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        job_id = int(sys.argv[1])
        render_video_for_job(job_id)
    else:
        print("Usage: python node_render.py <job_id>")
