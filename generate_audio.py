import json
import asyncio
import edge_tts

async def generate_audio(text: str, output_file: str, voice: str = 'zh-CN-YunxiNeural') -> bool:
    try:
        print(f"Generating cloud TTS audio for '{voice}'...")
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        print(f"Successfully saved to {output_file}")
        return True
    except Exception as e:
        print(f"Edge TTS failed: {e}")
        return False
