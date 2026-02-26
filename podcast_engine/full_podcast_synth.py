"""
Full Podcast Synthesizer
========================
Reads podcast_draft.json (58 lines of dialogue) and calls the custom TTS API
to generate individual WAV clips per line, then uses ffmpeg to concatenate
them into one final podcast MP3 file.

Voice Selection:
  Host  = zhoukai
  Guest = zsy
"""
import json
import os
import re
import requests
import subprocess
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- Config ---
TTS_URL = "http://101.227.82.130:13002/tts"
VOICE_MAP = {
    "host": "zhoukai",
    "guest": "zsy",
}
DRAFT_FILE = r"c:\work\code\todayInHistory\podcast_engine\podcast_draft.json"
CLIPS_DIR = r"c:\work\code\todayInHistory\podcast_engine\full_clips"
OUTPUT_MP3 = r"c:\work\code\todayInHistory\podcast_engine\podcast_final.mp3"

os.makedirs(CLIPS_DIR, exist_ok=True)

def rate_to_speed_factor(rate_str):
    """Convert SSML rate like '+15%' or '-10%' to a speed_factor float."""
    try:
        pct = int(rate_str.replace('%', '').replace('+', ''))
        return round(1.0 + pct / 100.0, 2)
    except:
        return 1.0

def clean_ssml(text):
    """Strip embedded SSML tags from text, keeping only the spoken content."""
    return re.sub(r'<[^>]+>', '', text)

def generate_clip(voice_id, text, speed_factor, output_path):
    """Call the custom TTS API and save the result as a WAV file."""
    payload = {
        "text": text,
        "text_lang": "zh",
        "ref_audio_path": "voice/张舒怡.wav",
        "prompt_lang": "zh",
        "aux_ref_audio_paths": [],
        "top_k": 30,
        "top_p": 1,
        "temperature": 1,
        "text_split_method": "cut5",
        "batch_size": 32,
        "batch_threshold": 0.75,
        "split_bucket": True,
        "speed_factor": speed_factor,
        "media_type": "wav",
        "streaming_mode": False,
        "seed": 100,
        "parallel_infer": True,
        "repetition_penalty": 1.35,
        "sample_steps": 32,
        "super_sampling": False,
        "sample_rate": 32000,
        "fragment_interval": 0.01,
        "voice_id": voice_id,
    }
    headers = {"Content-Type": "application/json"}
    
    resp = requests.post(TTS_URL, headers=headers, json=payload, timeout=60)
    if resp.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(resp.content)
        return True
    else:
        print(f"    ERROR {resp.status_code}: {resp.text[:80]}")
        return False

def main():
    with open(DRAFT_FILE, 'r', encoding='utf-8') as f:
        dialogues = json.load(f)

    total = len(dialogues)
    print(f"=== Full Podcast Synthesis: {total} lines ===")
    print(f"    Host voice:  zhoukai")
    print(f"    Guest voice: zsy")
    print()

    valid_clips = []
    t_start = time.perf_counter()

    for i, line in enumerate(dialogues):
        role = line.get("role", "")
        text = line.get("text", "")
        rate = line.get("rate", "+0%")

        # Determine voice
        if role in VOICE_MAP:
            voice_id = VOICE_MAP[role]
        elif role.startswith("sys_inject_"):
            # Skip system injection placeholders (ads, songs, Q&A)
            # In production these would be replaced by actual audio assets
            print(f"  [{i+1:02d}/{total}] SKIP {role}: {text[:40]}")
            continue
        else:
            print(f"  [{i+1:02d}/{total}] SKIP unknown role: {role}")
            continue

        clean_text = clean_ssml(text)
        speed = rate_to_speed_factor(rate)
        clip_path = os.path.join(CLIPS_DIR, f"{i+1:03d}_{role}.wav")

        print(f"  [{i+1:02d}/{total}] {role} (speed={speed}): {clean_text[:35]}...", end="", flush=True)
        
        if generate_clip(voice_id, clean_text, speed, clip_path):
            print(" OK")
            valid_clips.append(clip_path)
        else:
            print(" FAILED")

    elapsed = time.perf_counter() - t_start
    print(f"\n--- TTS generation complete in {elapsed:.1f}s ---")
    print(f"    {len(valid_clips)} clips generated, {total - len(valid_clips)} skipped/failed")

    # --- Concatenate with ffmpeg ---
    if not valid_clips:
        print("No clips to concatenate!")
        return

    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    concat_file = os.path.join(CLIPS_DIR, "concat_list.txt")
    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in valid_clips:
            f.write(f"file '{clip.replace(os.sep, '/')}'\n")

    print(f"\nConcatenating {len(valid_clips)} clips into final MP3...")
    cmd = [
        ffmpeg_exe,
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-ac", "1",
        "-ar", "32000",
        "-b:a", "192k",
        OUTPUT_MP3,
        "-y"
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    file_size_mb = os.path.getsize(OUTPUT_MP3) / (1024 * 1024)
    print(f"\n=== DONE! ===")
    print(f"    Final podcast: {OUTPUT_MP3}")
    print(f"    File size: {file_size_mb:.1f} MB")

if __name__ == "__main__":
    main()
