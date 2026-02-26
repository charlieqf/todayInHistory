import os
import requests
import sys
import io

# Force utf-8 for terminal output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

URL = "http://101.227.82.130:13002/tts"
RATE = 32000

# Some good potential combinations for a finance/story podcast
COMBINATIONS = [
    # Combo 1: Serious Host + Lively Guest
    {"name": "Combo1", "host": "xuanyijiangjie", "guest": "zhishuaiyingzi"},
    # Combo 2: Calm Host + Sweet Guest
    {"name": "Combo2", "host": "lzr", "guest": "zsy"},
    # Combo 3: Narrative Host + Normal Female
    {"name": "Combo3", "host": "yunzedashu", "guest": "nv1"},
    # Combo 4: Young Host + Young Guest (more casual)
    {"name": "Combo4", "host": "zhoukai", "guest": "wf"}
]

# A standard 2-line test script
TEST_DIALOGUE = [
    {"role": "host", "text": "如果现在给你十万块钱，让你去炒股，给你八年时间，你觉得你能赚多少钱？"},
    {"role": "guest", "text": "哎呀，股市风险那么大，要是运气好翻个倍，变成二三十万吧？"}
]

out_dir = r"c:\work\code\todayInHistory\podcast_engine\voice_tests"
os.makedirs(out_dir, exist_ok=True)

def generate_voice(voice_id, text, output_path):
    payload = {
        "text": text,
        "text_lang": "zh",
        "ref_audio_path": "voice/张舒怡.wav", # default from user script
        "prompt_lang": "zh",
        "aux_ref_audio_paths": [],
        "top_k": 30,
        "top_p": 1,
        "temperature": 1,
        "text_split_method": "cut5",
        "batch_size": 32,
        "batch_threshold": 0.75,
        "split_bucket": True,
        "speed_factor": 1.0,
        "media_type": "wav", # The user script reads PCM streams, but standard wav is much easier to review
        "streaming_mode": False, # Set to False to just get the full file back immediately
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
    
    print(f"  -> Requesting [Voice: {voice_id}]...", end="", flush=True)
    try:
        resp = requests.post(URL, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            print(" ✅ OK")
            return True
        else:
            print(f" ❌ Error {resp.status_code}: {resp.text[:50]}")
            return False
    except Exception as e:
        print(f" ❌ Exception: {e}")
        return False

# Try generating standard wav files first for easy concatenation
for combo in COMBINATIONS:
    combo_name = combo["name"]
    host_voice = combo["host"]
    guest_voice = combo["guest"]
    
    print(f"\n[Test] Generating Audio for: {combo_name} (Host: {host_voice}, Guest: {guest_voice})")
    
    # Generate Host
    host_out = os.path.join(out_dir, f"{combo_name}_01_Host_{host_voice}.wav")
    generate_voice(host_voice, TEST_DIALOGUE[0]["text"], host_out)
    
    # Generate Guest
    guest_out = os.path.join(out_dir, f"{combo_name}_02_Guest_{guest_voice}.wav")
    generate_voice(guest_voice, TEST_DIALOGUE[1]["text"], guest_out)

print(f"\n✅ All tests finished! Audio saved to: {out_dir}")
