import os
import glob
from google import genai
from google.genai import types

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "raw_stocks")
OUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "outlines_stocks")
os.makedirs(OUT_DIR, exist_ok=True)

# Load API key
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(SCRIPT_DIR, "..", "..", ".env"))
except ImportError:
    pass

def generate_outline(raw_filepath):
    filename = os.path.basename(raw_filepath)
    base_name = os.path.splitext(filename)[0]
    out_filepath = os.path.join(OUT_DIR, f"{base_name}_outline.md")
    
    print(f"✍️ Drafting Outline for: {filename}")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set.")
        return False
        
    with open(raw_filepath, 'r', encoding='utf-8') as f:
        raw_text = f.read()
        
    client = genai.Client(api_key=api_key)
    
    system_prompt = """你现在是喜马拉雅/蜻蜓FM等音频平台最顶级的“财经悬疑故事”金牌编剧。
我们需要为一档叫《妖股传说与游资复盘》的20分钟音频节目撰写剧本大纲。

要求：
1. 你的任务是把这份原始且枯燥的生平简历，提炼成一份跌宕起伏的、适合用说书口吻讲述的【20分钟广播剧大纲】。
2. 采用经典的四幕剧结构：起（超级钩子与微末出身）、承（初露锋芒与悟道期）、转（巅峰极客战役/千金散尽还复来）、合（神话落幕或隐退江湖的时代反思）。
3. 必须精准包含真实的股票代码、资金体量、连板天数等硬核数据，这是财经受众最在意的“爽点”。
4. 输出格式为 Markdown，务必排版清晰（比如标注出每一幕的核心冲突和情绪基调）。
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Flash is fast and cheap enough for outlining
            contents=[system_prompt, f"Raw Source Material:\n{raw_text}"],
            config=types.GenerateContentConfig(
                temperature=0.6 # Balance creativity with factual structure
            ),
        )
        
        with open(out_filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        print(f"✅ Saved Outline to {out_filepath} ({len(response.text)} chars)")
        return True
    except Exception as e:
        print(f"❌ Failed to generate outline for {filename}: {e}")
        return False

if __name__ == "__main__":
    print(f"🎬 Starting Phase 10: Step 2 - LLM Outline Generator")
    print(f"📂 Reading from: {RAW_DIR}")
    print(f"📂 Output to: {OUT_DIR}\n")
    
    raw_files = glob.glob(os.path.join(RAW_DIR, "*.txt"))
    if not raw_files:
        print("❌ No raw text files found in data/raw_stocks/")
        sys.exit(1)
        
    for rf in raw_files:
        generate_outline(rf)
