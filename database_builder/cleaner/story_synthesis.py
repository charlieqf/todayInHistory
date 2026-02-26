import os
import glob
import sqlite3
from google import genai
from google.genai import types

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTLINES_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "outlines_stocks")
DB_PATH = os.path.join(SCRIPT_DIR, "..", "..", "data", "history_events.db")

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(SCRIPT_DIR, "..", "..", ".env"))
except ImportError:
    pass

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def synthesize_and_ingest():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set.")
        return
        
    client = genai.Client(api_key=api_key)
    
    conn = get_db_connection()
    # Find the stock_replay channel id
    channel = conn.execute("SELECT id FROM channels WHERE slug = 'stock_replay'").fetchone()
    if not channel:
        print("❌ Could not find channel with slug 'stock_replay'. Please ensure Seed Data was inserted.")
        return
    channel_id = channel['id']

    outline_files = glob.glob(os.path.join(OUTLINES_DIR, "*_outline.md"))
    if not outline_files:
        print("❌ No outline files found.")
        return

    for filepath in outline_files:
        filename = os.path.basename(filepath)
        print(f"🎙️ Synthesizing clean broadcast script from: {filename}...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            outline_text = f.read()

        system_prompt = """你是一个顶级的财经悬疑电台主笔。
用户提供了一份剧本大纲以及相关的硬核数据。

你的核心任务是：
1. **极限扩写（字数要求极高）**：这份大纲目前只有 3000 字。请你发挥极为出色的说书人天赋，对每一段博弈、每一次交易的情绪、当时市场的宏观环境，进行**疯狂且细腻的扩写**。必须要写出跌宕起伏的临场感！请以 5000 - 8000 字的篇幅展开，确保播讲时长能达到 25 分钟。
2. **纯粹的TTS口播格式（极其重要）**：
   - 彻底删除大纲中所有的【旁白】、【音效】、（背景音乐：xxx）等提示词！
   - 彻底删除所有的 Markdown 格式符（如 `**`、`#`）。
   - 你输出的**必须且只能是**纯粹的一连串中文口播句子，因为这段文本将直接送给 AI 主播朗读。如果出现括号里的动作提示，AI 念出来会非常滑稽可笑！
3. 在文本最开头，以 `### TITLE: [提取的标题]` 的格式输出标题。
4. 在文本第二行，以 `### SUMMARY: [一句话核心总结]` 的格式输出摘要。
5. 第三行开始输出正文。
"""

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[system_prompt, f"Draft Outline:\n{outline_text}"],
                config=types.GenerateContentConfig(temperature=0.3), # Low temp for formatting
            )
            
            final_text = response.text
            
            # Parse title, summary, and rich context
            title = "未知游资传说"
            summary = "游资风云谱"
            rich_context = ""
            
            lines = final_text.splitlines()
            body_start = 0
            for i, line in enumerate(lines):
                if line.startswith("### TITLE:"):
                    title = line.replace("### TITLE:", "").strip()
                elif line.startswith("### SUMMARY:"):
                    summary = line.replace("### SUMMARY:", "").strip()
                elif line.strip() == "" and i < 3:
                     continue
                else:
                    if not line.startswith("### TITLE:") and not line.startswith("### SUMMARY:"):
                        body_start = i
                        break
            
            rich_context = "\n".join(lines[body_start:]).strip()
            
            print(f"   📌 Title: {title}")
            # Insert or replace into database to overwrite the old shorter version
            try:
                # We use the title as a unique constraint. Since it's unique, we might need to delete old first if we want to bypass IntegrityError without REPLACE.
                # The schema for historical_events doesn't have UNIQUE(title), it has UNIQUE(channel_id, month, day, year, title) where dates are NULL.
                # So let's just delete the old one based on the exact same title first, then insert.
                conn.execute('DELETE FROM historical_events WHERE title = ?', (title,))
                
                conn.execute('''
                    INSERT INTO historical_events (channel_id, title, summary, category, importance_score, rich_context)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (channel_id, title, summary, '游资传说', 10, rich_context))
                conn.commit()
                print(f"   ✅ Upserted expanded script into DB cleanly!")
            except sqlite3.IntegrityError as e:
                print(f"   ⚠️ DB Error during Upsert: {e}")
                
        except Exception as e:
            print(f"❌ Failed to synthesize {filename}: {e}")

if __name__ == "__main__":
    print(f"🎬 Starting Phase 10: Steps 4 & 5 - Final Story Synthesis & DB Ingestion\n")
    synthesize_and_ingest()
