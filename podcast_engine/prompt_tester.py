import os
import io
import sys
import json
import google.generativeai as genai
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv(r'c:\work\code\todayInHistory\.env')
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def generate_podcast_script(raw_text_path):
    with open(raw_text_path, 'r', encoding='utf-8') as f:
        content = f.read()

    system_prompt = """
    You are an elite podcast producer and scriptwriter.
    Your task is to take a long, dry factual text about a historical stock market legend and adapt it into a highly engaging, interactive, and thrilling TWO-PERSON podcast script.
    
    The format should strictly mirror the dynamic of "老高与小茉" (Lao Gao and Xiao Mo) or a true-crime storytelling podcast:
    - **Host (男)**: The storyteller. He is knowledgeable, creates suspense, pauses for dramatic effect, and guides the narrative. 
    - **Guest (女)**: The active listener. She interrupts with genuine questions, acts surprised, makes relatable everyday comparisons, and represents the audience's point of view.
    
    CRITICAL RULES FOR REALISM:
    1. **Conversational Tone**: Use filler words (哎, 哇, 不是吧, 天哪). Sentences should be short and punchy. Nobody speaks in long paragraphs. They must interrupt each other.
    2. **Show, Don't Tell**: Instead of saying "He bought it and made 10x", the host should set up the risk: "You know what he did next? He went ALL IN." And the guest reacts: "Wait, on a stock that was crashing?!"
    3. **System Injections**: We are a radio show. At natural breakpoints in the story you MUST insert special system roles to allow external assets to play:
       - role: 'sys_inject_ad' (Text should be a placeholder like "[AD_INSERT_1]")
       - role: 'sys_inject_song' (Text should be a placeholder for a song snippet)
       - role: 'sys_inject_qa' (Text should be a placeholder for a listener question)
    
    4. **TTS SSML TAGS INJECTION (CRITICAL)**: To make this text ready for professional TTS, you must insert structural voice tags into the JSON output. 
    Please output ONLY valid JSON in the following format so it can be parsed programmatically:
    [
        {"role": "host", "voice_profile": "zh-CN-YunjianNeural", "pitch": "-5Hz", "rate": "+10%", "text": "大家好，<break time=\\"500ms\\"/>欢迎来到今天的节目。"},
        {"role": "guest", "voice_profile": "zh-CN-XiaoxiaoNeural", "pitch": "+0Hz", "rate": "+25%", "text": "<prosody rate=\\"fast\\">啊？真的吗？</prosody>"}
    ]
    """

    print('Prompting Gemini 3.1 Pro for Podcast Transformation...')
    model = genai.GenerativeModel('gemini-3.1-pro-preview', system_instruction=system_prompt)
    
    response = model.generate_content(
        content,
        generation_config=genai.GenerationConfig(
            temperature=0.8
        )
    )

    out_file = r'c:\work\code\todayInHistory\podcast_engine\podcast_draft.json'
    
    # Clean possible markdown JSON wrappers
    final_text = response.text.strip()
    if final_text.startswith('```json'):
        final_text = final_text[7:]
    if final_text.endswith('```'):
        final_text = final_text[:-3]
        
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(final_text)
    
    print(f'Success! Generated structured podcast script at {os.path.abspath(out_file)}')

if __name__ == "__main__":
    test_file = r'c:\work\code\todayInHistory\data\final_scripts_stocks\赵老哥_八年一万倍的股市传奇.txt'
    if os.path.exists(test_file):
        generate_podcast_script(test_file)
    else:
        print('Test file not found!')
