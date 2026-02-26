import sys
import os
import json
import sqlite3
import math
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Setup relative imports for the DB storage
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "..", "db")
sys.path.append(DB_DIR)
from storage import get_db_connection

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(SCRIPT_DIR, "..", "..", ".env"))
except ImportError:
    pass

class VisualScene(BaseModel):
    text: str = Field(description="The exact text chunk corresponding to this scene.")
    imagePrompt: str = Field(description="Highly detailed English prompt for an AI Image Generator capturing the emotion/action of this chunk.")

class VisualScript(BaseModel):
    scenes: list[VisualScene] = Field(description="List of scenes with their corresponding image prompts.")

def run_visual_mapping(job_id: int, words_per_chunk: int = 500):
    """
    Node 2.5: For long-form text (like 5000-word stock replays), we don't have a structured scene JSON yet.
    This step grabs the rich_context, chunks it, and asks Gemini to assign ONE image prompt per chunk.
    It then saves this structured JSON to `video_jobs.script_json`, bridging it to the legacy `node_assets_gen`.
    """
    print(f"🖼️ [Node 2.5 - Visual Mapper] Starting for Job #{job_id}...")
    
    conn = get_db_connection()
    try:
        job = conn.execute('''
            SELECT vj.*, e.rich_context, e.title
            FROM video_jobs vj 
            JOIN historical_events e ON vj.event_id = e.id 
            WHERE vj.id = ?
        ''', (job_id,)).fetchone()
        
        if not job or not job['rich_context']:
            print(f"❌ Job {job_id} not found or lacks rich_context.")
            return False

        full_text = job['rich_context']
        
        # 1. Simple heuristic chunking by paragraph/length
        paragraphs = [p.strip() for p in full_text.split('\n') if p.strip()]
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            if len(current_chunk) + len(p) > words_per_chunk and current_chunk:
                chunks.append(current_chunk)
                current_chunk = p
            else:
                current_chunk += "\n" + p if current_chunk else p
        
        if current_chunk:
            chunks.append(current_chunk)
            
        print(f"🧩 Split {len(full_text)} chars into {len(chunks)} visual scenes.")
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY not set.")
            return False
            
        client = genai.Client(api_key=api_key)
        
        # Process each chunk iteratively or as a batch to prevent Gemini token explosion
        # For ~10 chunks, we can do it in one shot if we format the prompt carefully.
        
        system_prompt = f"""You are the Art Director for a 20-minute financial documentary podcast.
The script has been divided into {len(chunks)} distinct scenes.
For each scene, I will give you the narrator's text.
You must return a valid JSON array matching the provided Schema, where you map the exact text I gave you to a highly evocative, cinematic English image prompt suitable for Replicate/Flux.
"""
        user_prompt = "Here are the text chunks to map:\n"
        for i, chunk in enumerate(chunks):
            user_prompt += f"--- CHUNK {i+1} ---\n{chunk}\n\n"
            
        print("🧠 Asking Gemini to dream up visuals for the entire timeline...")
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[system_prompt, user_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VisualScript,
                temperature=0.4,
            ),
        )
        
        script_obj = json.loads(response.text)
        
        # Bridge to legacy format (inject durationInFrames stub, it gets recalculated in node_assets_gen later anyway)
        legacy_scenes = []
        for s in script_obj.get("scenes", []):
            legacy_scenes.append({
                "durationInFrames": 150, # Dummy, overwritten later by audio sync
                "text": s.get("text", ""),
                "imagePrompt": s.get("imagePrompt", "")
            })
            
        final_script = {"audioUrl": "", "scenes": legacy_scenes}
        
        conn.execute("UPDATE video_jobs SET script_json = ?, status = 'SCRIPT_MAPPED' WHERE id = ?", (json.dumps(final_script, ensure_ascii=False), job_id))
        conn.commit()
        print(f"✅ Successfully mapped {len(legacy_scenes)} visual scenes to DB!")
        return True
        
    except Exception as e:
        print(f"❌ Error in visual mapper: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        run_visual_mapping(int(sys.argv[1]))
    else:
        print("Usage: python node_visual_mapper.py <job_id>")
