import json
import os
import subprocess
import sys
import io

# Force utf-8 for terminal output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

VOICE_HOST = "zh-CN-YunjianNeural"
VOICE_GUEST = "zh-CN-XiaoxiaoNeural"

def generate_podcast_audio(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        dialogues = json.load(f)

    out_dir = r"c:\work\code\todayInHistory\podcast_engine\audio_clips"
    os.makedirs(out_dir, exist_ok=True)
    
    playlist_path = os.path.join(out_dir, "00_PLAYLIST.m3u")
    with open(playlist_path, 'w', encoding='utf-8') as m3u:
        m3u.write("#EXTM3U\n")

        print(f"=== Synthesizing {len(dialogues)} clips ===")
        for i, line in enumerate(dialogues):
            role = line["role"]
            text = line["text"]
            emotion = line["emotion"]
            
            idx = f"{i+1:03d}"
            
            if role == "host":
                voice = VOICE_HOST
            elif role == "guest":
                voice = VOICE_GUEST
            elif role.startswith("sys_inject_"):
                voice = "zh-CN-YunxiNeural"
                text = f"【系统提示：此处接入外挂模块。{text}】"
            else:
                continue

            file_name = f"{idx}_{role}_{emotion}.mp3"
            file_path = os.path.join(out_dir, file_name)
            
            print(f"[{idx}/{len(dialogues)}] Generating {role}: {text[:30]}...")
            
            cmd = [
                "python", "-m", "edge_tts",
                "--voice", voice,
                "--text", text,
                "--write-media", file_path
            ]
            
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                m3u.write(f"{file_name}\n")
            except Exception as e:
                print(f"Failed edge-tts on clip {idx}: {e}")

    print(f"\nAll Audio Clips Synthesized in {out_dir}")
    print(f"You can double-click {os.path.abspath(playlist_path)} in VLC/Windows Media Player to hear the full conversation flow!")

if __name__ == "__main__":
    draft_file = r"c:\work\code\todayInHistory\podcast_engine\podcast_draft.json"
    if os.path.exists(draft_file):
        generate_podcast_audio(draft_file)
    else:
        print("podcast_draft.json not found!")
