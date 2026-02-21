import json
import asyncio
import edge_tts

async def main():
    # Read script
    with open('day1_script_xerox_alto.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    text = data['audio_script']
    
    # Use top tier Chinese voice from Edge TTS (Azure Cloud)
    # zh-CN-YunxiNeural is a very natural and energetic male voice, perfect for storytelling/tech
    voice = 'zh-CN-YunxiNeural' 
    output_file = 'assets/audio_track.mp3'
    
    print(f"Generating cloud TTS audio for '{voice}'...")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    print(f"Successfully saved to {output_file}")

if __name__ == '__main__':
    asyncio.run(main())
