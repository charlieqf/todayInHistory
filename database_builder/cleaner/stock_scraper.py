import os
import sys
from google import genai
from google.genai import types

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "raw_stocks")
os.makedirs(OUT_DIR, exist_ok=True)

# Load API key from .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(SCRIPT_DIR, "..", "..", ".env"))
except ImportError:
    pass

def scrape_with_ai_search(target_name: str, output_filename: str):
    print(f"🔍 AI Scouting: Performing deep web search for '{target_name}'...")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set.")
        return False
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Please perform a comprehensive deep web search for the famous Chinese stock market trader: {target_name}.
    
    I need you to act as a raw data scraper. Gather the following factual information:
    1. Early life and background.
    2. Complete trading history and milestones (e.g., specific dates, capital growth, famous quotes like "8 years 10,000x").
    3. Their most legendary stock battles (which specific stocks did they trade, when, and how did they operate? e.g., China CRRC, Eastern Communications).
    4. Their core trading philosophy and specific techniques (e.g., "打板", "二板定龙头").
    5. Any interesting anecdotes, quotes, or their ultimate outcome/aftermath (e.g., arrests, weddings).
    
    Output this strictly as a highly detailed, factual Wikipedia-style report in Chinese. Do NOT format it as a video script. This is just raw research data. Include as many specific dates, numbers, and stock codes as you can find.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro', # Use Pro for deep research
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{'google_search': {}}],
                temperature=0.2 # Keep it factual
            ),
        )
        
        output_path = os.path.join(OUT_DIR, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"--- Factual Dossier: {target_name} ---\n\n")
            f.write(response.text)
            
        print(f"✅ Saved {len(response.text)} characters of rich factual data to {output_filename}\n")
        return True
    except Exception as e:
        print(f"❌ Failed to scout '{target_name}': {e}\n")
        return False

if __name__ == "__main__":
    print(f"🎬 Starting Phase 10: Step 1 - AI Grounded Web Scraper")
    print(f"📂 Output Directory: {OUT_DIR}\n")
    
    targets = [
        {"name": "徐翔 (泽熙投资, 涨停板敢死队)", "filename": "xu_xiang_raw.txt"},
        {"name": "赵强 (赵老哥, 八年一万倍, 银河证券绍兴营业部)", "filename": "zhao_laoge_raw.txt"}
    ]
    
    for target in targets:
        scrape_with_ai_search(target['name'], target['filename'])
