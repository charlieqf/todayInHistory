import os
import sys
import json
import asyncio
import urllib.request
from typing import Dict, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "..", "db")
sys.path.append(DB_DIR)
from storage import get_db_connection

# Add root folder to sys path to import our existing Edge-TTS wrapper
ROOT_DIR = os.path.join(SCRIPT_DIR, "..", "..")
sys.path.append(ROOT_DIR)
try:
    from generate_audio import generate_audio
except ImportError:
    generate_audio = None

# Where to save the physical media files for Remotion
ASSET_OUT_DIR = os.path.join(ROOT_DIR, "video-generator", "public", "assets")
os.makedirs(ASSET_OUT_DIR, exist_ok=True)

async def generate_scene_image(prompt: str, scene_index: int, output_path: str):
    """
    Generate a scene image using Gemini's native AI image generation.
    Falls back to LoremFlickr themed stock photos if AI generation fails.
    """
    print(f"   [Vision] Sketching Scene {scene_index + 1}...")
    
    # Try Gemini AI Image Generation first
    try:
        from google import genai
        from google.genai import types
        
        # Load API key
        try:
            from dotenv import load_dotenv
            load_dotenv(os.path.join(SCRIPT_DIR, "..", "..", ".env"))
        except ImportError:
            pass
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            client = genai.Client(api_key=api_key)
            
            # Use Gemini's native image generation model
            response = client.models.generate_content(
                model='gemini-2.5-flash-image',
                contents=f"Generate a high-quality, cinematic image for a short video scene. The image should be portrait orientation (9:16 aspect ratio for mobile). Prompt: {prompt}",
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'],
                ),
            )
            
            # Extract image from response parts
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    img_data = part.inline_data.data
                    with open(output_path, 'wb') as f:
                        f.write(img_data)
                    print(f"   [Vision] ✅ Scene {scene_index + 1} AI Image saved ({len(img_data)} bytes)")
                    return True
            
            print(f"   [Vision] ⚠️ No image in Gemini response, falling back to stock photo...")
    except Exception as e:
        print(f"   [Vision] ⚠️ Gemini image gen failed ({e}), falling back to stock photo...")
    
    # Fallback: LoremFlickr themed stock photos
    try:
        url = f"https://loremflickr.com/1080/1920/computer,technology,history?lock={hash(prompt) % 10000}"
        urllib.request.urlretrieve(url, output_path)
        print(f"   [Vision] ✅ Scene {scene_index + 1} Fallback image saved to {output_path}")
        return True
    except Exception as e:
        print(f"   [Vision] ❌ Failed to generate image for scene {scene_index + 1}: {e}")
        return False

async def synthesize_assets_for_job(job_id: int):
    print(f"🎞️ [Node 3 - Asset Synthesis] Started for Job #{job_id}...")
    
    conn = get_db_connection()
    try:
        # JOIN with channels to get TTS voice and CSS filter config
        job = conn.execute('''
            SELECT vj.*, ch.tts_voice, ch.css_filter, ch.display_name as ch_display_name
            FROM video_jobs vj
            LEFT JOIN channels ch ON vj.channel_id = ch.id
            WHERE vj.id = ?
        ''', (job_id,)).fetchone()
        
        if not job or not job['script_json']:
            print(f"❌ Job {job_id} missing or lacks script JSON. Have you run Node 2?")
            return False

        # Load channel-specific config
        tts_voice = job['tts_voice'] or 'zh-CN-YunxiNeural'
        css_filter = job['css_filter'] or 'sepia(0.3) contrast(1.1) brightness(0.9) grayscale(0.2)'
        channel_name = job['ch_display_name'] or 'Default'
        print(f"📺 Channel: {channel_name} | Voice: {tts_voice}")

        script_data: Dict[str, Any] = json.loads(job['script_json'])
        scenes = script_data.get('scenes', [])
        
        if not scenes:
            print("❌ No scenes found in script JSON.")
            return False

        # Inject the channel's CSS filter into the script JSON for Remotion
        script_data['filterStyle'] = css_filter

        # 1. Aggregate Full Audio Script for TTS
        print(f"🎤 [Audio] Aggregating narration for {len(scenes)} scenes...")
        full_narration = " ".join([scene.get('text', '') for scene in scenes])
        
        audio_filename = f"job_{job_id}_narration.mp3"
        audio_filepath = os.path.join(ASSET_OUT_DIR, audio_filename)
        
        if generate_audio:
            success = await generate_audio(full_narration, audio_filepath, voice=tts_voice)
            if not success:
               raise Exception("TTS Generation failed.")
            print(f"🎤 [Audio] ✅ Master audio saved to {audio_filepath}")
        else:
            print(f"🎤 [Audio] ⚠️ Could not import generate_audio. Skipping true TTS.")
            # Leave dummy file
            open(audio_filepath, 'a').close()

        # Update the script JSON to point the React app to this audio file
        script_data['audioUrl'] = f"assets/{audio_filename}"

        # Sync Video Length to Audio Length (Fixes the black/silent screen bug at the end)
        print("⏱️ [Sync] Probing actual Audio Length to normalize Scene Durations...")
        try:
            from mutagen.mp3 import MP3
            import math
            audio_info = MP3(audio_filepath)
            audio_duration_sec = audio_info.info.length
            # Remotion is configured for 30 FPS. We pad +1 second to give the final scene room to breathe.
            total_target_frames = math.ceil((audio_duration_sec + 1.0) * 30)
            
            # Calculate sum of LLM guessed frames
            original_total_frames = sum([int(s.get('durationInFrames', 150)) for s in scenes])
            
            # Distribute the target frames proportionally
            assigned_frames = 0
            for i, scene in enumerate(scenes):
                orig_dur = int(scene.get('durationInFrames', 150))
                if i == len(scenes) - 1:
                    # Give the last scene the exact remaining frames to ensure pixel-perfect length
                    scene['durationInFrames'] = total_target_frames - assigned_frames
                else:
                    new_dur = int((orig_dur / original_total_frames) * total_target_frames)
                    scene['durationInFrames'] = new_dur
                    assigned_frames += new_dur
                    
            print(f"⏱️ [Sync] ✅ Adjusted Total Frames: {original_total_frames} -> {total_target_frames} ({audio_duration_sec:.2f}s)")
        except ImportError:
            print("⚠️ [Sync] `mutagen` module not found, cannot measure audio length. Video may have silent dead space. Run `pip install mutagen`.")
        except Exception as e:
            print(f"⚠️ [Sync] Failed to probe audio: {e}")

        # 2. Concurrently generate Images for every scene
        print(f"🎨 [Vision] Generating {len(scenes)} discrete assets...")
        image_tasks = []
        for idx, scene in enumerate(scenes):
            prompt = scene.get('imagePrompt', f"Tech computer history scene {idx}")
            img_filename = f"job_{job_id}_scene_{idx}.png"
            img_filepath = os.path.join(ASSET_OUT_DIR, img_filename)
            
            # React components will load from the public folder root
            scene['imageUrl'] = f"assets/{img_filename}"
            
            # Push task to asyncio event loop
            image_tasks.append(generate_scene_image(prompt, idx, img_filepath))
            
        # Await all images to finish downloading/generating
        await asyncio.gather(*image_tasks)

        # 3. Save the enriched script JSON (with asset URLs attached) back to the DB
        enriched_json_str = json.dumps(script_data, ensure_ascii=False)
        
        # Advance Pipeline Status
        conn.execute('''
            UPDATE video_jobs 
            SET script_json = ?, audio_path = ?, status = 'AUDIO_GEN', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (enriched_json_str, audio_filepath, job_id))
        conn.commit()
        
        print(f"✅ [Node 3 - Asset Synthesis] Complete! DB status promoted to AUDIO_GEN.")
        return True

    except Exception as e:
        print(f"❌ [Node 3 - Asset Synthesis] Pipeline crashed: {e}")
        conn.execute("UPDATE video_jobs SET error_log = ?, status = 'ERROR' WHERE id = ?", (str(e), job_id))
        conn.commit()
        return False
    finally:
        conn.close()

def run_asset_generation(job_id: int):
    """Synchronous wrapper for Flask API & CLI calling"""
    try:
        # In Python 3.7+, this handles creating/running the loop
        return asyncio.run(synthesize_assets_for_job(job_id))
    except Exception as e:
        print(f"Error in async loop: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        job_id = int(sys.argv[1])
        run_asset_generation(job_id)
    else:
        print("Usage: python node_assets_gen.py <job_id>")
