import json
import os
import subprocess
import sys
import re

def install_requirements():
    try:
        import imageio_ffmpeg
    except ImportError:
        print("Installing imageio-ffmpeg to get a local ffmpeg binary...")
        subprocess.run([sys.executable, "-m", "pip", "install", "imageio-ffmpeg"], check=True)
        
install_requirements()
import imageio_ffmpeg

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

draft_file = r"c:\work\code\todayInHistory\podcast_engine\podcast_draft.json"
out_dir = r"c:\work\code\todayInHistory\podcast_engine\sample_clips"
os.makedirs(out_dir, exist_ok=True)

with open(draft_file, 'r', encoding='utf-8') as f:
    dialogues = json.load(f)[:10]

valid_clips = []
for i, line in enumerate(dialogues):
    role = line.get("role")
    text = line.get("text", "")
    voice = line.get("voice_profile", "zh-CN-YunjianNeural")
    rate = line.get("rate", "+0%")
    pitch = line.get("pitch", "+0Hz")
    
    if role not in ["host", "guest"]:
        continue
        
    clean_text = re.sub(r'<[^>]+>', '', text)
    file_path = os.path.join(out_dir, f"{i}.mp3")
    
    cmd = [
        sys.executable, "-m", "edge_tts",
        "--voice", voice,
        "--rate", rate,
        "--pitch", pitch,
        "--text", clean_text,
        "--write-media", file_path
    ]
    print(f"Generating block {i} ({voice}, {rate}): {clean_text[:30]}...")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    valid_clips.append(file_path)

print("Concatenating clips with FFmpeg...")
concat_file = os.path.join(out_dir, "concat.txt")
with open(concat_file, "w", encoding="utf-8") as f:
    for clip in valid_clips:
        # ffmpeg safely expects escaped paths or relative paths. 
        # using absolute paths with single quotes is fine in concat demuxer
        f.write(f"file '{clip.replace(os.sep, '/')}'\n")

output_mp3 = r"c:\work\code\todayInHistory\podcast_engine\podcast_sample.mp3"
os.makedirs(os.path.dirname(output_mp3), exist_ok=True)

concat_cmd = [
    ffmpeg_exe, 
    "-f", "concat", 
    "-safe", "0", 
    "-i", concat_file, 
    "-c", "copy", 
    output_mp3, 
    "-y"
]
subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print(f"✅ Success! 1-minute Sample generated at {output_mp3}")
