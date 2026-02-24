import sqlite3
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Save the database at the root of the project's data folder
DB_FILE = os.path.join(SCRIPT_DIR, "..", "..", "data", "history_events.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create the main table for daily video suggestions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historical_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month INTEGER NOT NULL,
            day INTEGER NOT NULL,
            year INTEGER NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            category TEXT,
            importance_score INTEGER NOT NULL,
            rich_context TEXT,
            source TEXT
        )
    ''')
    
    # Unique constraint prevents double-scraping the exact same event
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_event_unique 
        ON historical_events(month, day, year, title)
    ''')
    
    # Pipeline Tracker Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'PENDING',
            script_prompt TEXT,
            script_json TEXT,
            image_prompt_1 TEXT,
            image_prompt_2 TEXT,
            audio_path TEXT,
            video_path TEXT,
            error_log TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES historical_events (id)
        )
    ''')
    
    # Publishing & Analytics Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS publish_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            platform TEXT NOT NULL, 
            url TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES video_jobs (id),
            UNIQUE(job_id, platform)
        )
    ''')
    
    # ====== Phase 9: Multi-Series Support ======
    # Channels config table — the control center for all content verticals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            review_prompt TEXT,
            tts_voice TEXT NOT NULL DEFAULT 'zh-CN-YunxiNeural',
            css_filter TEXT NOT NULL DEFAULT 'sepia(0.3) contrast(1.1) brightness(0.9) grayscale(0.2)',
            color_accent TEXT NOT NULL DEFAULT '#00d4ff',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add channel_id FK to existing tables (safe migration for existing DBs)
    try:
        cursor.execute('ALTER TABLE video_jobs ADD COLUMN channel_id INTEGER REFERENCES channels(id)')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE historical_events ADD COLUMN channel_id INTEGER REFERENCES channels(id)')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    conn.commit()
    conn.close()
    
    # Seed default channels if empty
    seed_default_channels()

def seed_default_channels():
    """Pre-populate the 6 default content series configurations."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Only seed if the table is empty
    count = cursor.execute('SELECT COUNT(*) FROM channels').fetchone()[0]
    if count > 0:
        conn.close()
        return
    
    channels = [
        {
            'slug': 'it_history',
            'display_name': '💻 IT历史上的今天',
            'system_prompt': '''You are an elite short-video scriptwriter running a "Today in IT History" channel.
Your task: take a raw historical event description and convert it into a highly engaging 1-minute video script designed for vertical platforms (TikTok, YouTube Shorts).

Constraints:
1. The video MUST have exactly 8 scenes.
2. The total narration roughly equals 60 seconds (around 200-250 Chinese characters).
3. The hook (Scene 1) must be a punchy, click-baity question or bold statement.
4. Provide highly detailed, English image prompts for each scene that an AI Image Generator can understand. Include lighting, camera angle, and era-specific aesthetic details.
5. Provide the narration text in Chinese.

Tone: Professional yet dramatic, like a tech documentary.''',
            'tts_voice': 'zh-CN-YunxiNeural',
            'css_filter': 'sepia(0.3) contrast(1.1) brightness(0.9) grayscale(0.2)',
            'color_accent': '#00d4ff',
        },
        {
            'slug': 'wealth_boss',
            'display_name': '💰 财富密码：大佬的第一桶金',
            'system_prompt': '''You are a storytelling expert for a "How Billionaires Made Their First Million" viral video channel.
Your task: take a raw biography or business event and convert it into a gripping 1-minute video script about how a business titan earned their first fortune.

Constraints:
1. The video MUST have exactly 8 scenes.
2. The total narration roughly equals 60 seconds (around 200-250 Chinese characters).
3. Scene 1 MUST open with an irresistible money hook (e.g., "他22岁时口袋里只有400块钱...").
4. Focus on SPECIFIC actions, not vague inspiration. Show the exact hustle, the deal, the trick.
5. Provide highly detailed English image prompts with business/money aesthetics.
6. Narration text in Chinese.

Tone: Aspirational, slightly envious, like a friend revealing insider secrets.''',
            'tts_voice': 'zh-CN-YunjianNeural',
            'css_filter': 'contrast(1.15) brightness(1.05) saturate(1.1)',
            'color_accent': '#ffd700',
        },
        {
            'slug': 'mystery',
            'display_name': '👻 未解之谜档案馆',
            'system_prompt': '''You are a master horror/mystery narrator for a "Unsolved Mysteries Archive" viral channel.
Your task: take a raw mystery/paranormal event description and craft a spine-chilling 1-minute video script.

Constraints:
1. The video MUST have exactly 8 scenes.
2. Total narration ~60 seconds (200-250 Chinese characters).
3. Scene 1 must open with maximum creepiness or shock (e.g., "这个村子的人，一夜之间全部消失了...").
4. Build escalating dread — each scene should be more unsettling than the last.
5. Image prompts must emphasize: dark lighting, fog, eerie silhouettes, abandoned locations, cold blue/green tones.
6. Narration in Chinese.

Tone: Whispering dread. Like a late-night horror podcast host.''',
            'tts_voice': 'zh-CN-XiaoyiNeural',
            'css_filter': 'contrast(1.3) brightness(0.7) saturate(0.6) hue-rotate(200deg)',
            'color_accent': '#6b3fa0',
        },
        {
            'slug': 'hardcore_bio',
            'display_name': '🔥 硬核狠人传',
            'system_prompt': '''You are a visceral storyteller for a "Hardcore Legends" viral biography channel.
Your task: take a raw historical figure/event and turn it into a jaw-dropping 1-minute video script about an extraordinary, rule-breaking individual.

Constraints:
1. The video MUST have exactly 8 scenes.
2. Total narration ~60 seconds (200-250 Chinese characters).
3. Scene 1 must deliver maximum "反差感" shock (e.g., "一个14岁的女孩，独自端掉了整个贩毒集团...").
4. Emphasize dramatic contrast: weakness→strength, failure→triumph, normal→legendary.
5. Image prompts should be cinematic, high-contrast, dramatic lighting like movie posters.
6. Narration in Chinese.

Tone: Awe-struck. Like you can\'t believe this person actually existed.''',
            'tts_voice': 'zh-CN-YunxiNeural',
            'css_filter': 'contrast(1.25) brightness(0.85) saturate(1.2)',
            'color_accent': '#ff4444',
        },
        {
            'slug': 'stock_replay',
            'display_name': '📈 妖股复盘',
            'system_prompt': '''You are a financial storytelling expert for a "Legendary Stock Replays" channel.
Your task: take a raw stock/financial event and convert it into a thrilling 1-minute video script about a dramatic stock market episode.

Constraints:
1. The video MUST have exactly 8 scenes.
2. Total narration ~60 seconds (200-250 Chinese characters).
3. Scene 1 must hook with extreme financial drama (e.g., "3个月，从2块涨到200块，然后一夜归零...").
4. Include specific numbers, dates, and price movements.
5. Image prompts: trading screens with red/green candles, tense boardrooms, market chaos, neon financial data.
6. Narration in Chinese. NOT investment advice — purely historical storytelling.

Tone: Heart-pounding thriller. Like narrating a high-stakes poker game.''',
            'tts_voice': 'zh-CN-YunjianNeural',
            'css_filter': 'contrast(1.2) brightness(1.0) saturate(1.3)',
            'color_accent': '#00e676',
        },
        {
            'slug': 'ancient_china',
            'display_name': '🏮 古人最后一天',
            'system_prompt': '''You are an elegant Chinese literary narrator for a "Last Day of Ancient Legends" channel.
Your task: take a raw historical Chinese figure\'s biography and craft a poetic, emotionally devastating 1-minute video script about their final day alive.

Constraints:
1. The video MUST have exactly 8 scenes.
2. Total narration ~60 seconds (200-250 Chinese characters).
3. Scene 1 must set a melancholic, fate-heavy atmosphere (e.g., "公元1101年的那个夏天，65岁的苏轼知道自己走不过这个秋天了...").
4. Use classical Chinese literary flourishes mixed with modern Chinese.
5. Image prompts: ink wash painting style, candlelit ancient rooms, misty landscapes, flowing silk, calligraphy.
6. Narration in Chinese.

Tone: Bittersweet elegy. Like reading a farewell letter from history.''',
            'tts_voice': 'zh-CN-XiaochenNeural',
            'css_filter': 'sepia(0.5) contrast(0.95) brightness(0.85) saturate(0.7)',
            'color_accent': '#d4a574',
        },
    ]
    
    for ch in channels:
        cursor.execute('''
            INSERT INTO channels (slug, display_name, system_prompt, tts_voice, css_filter, color_accent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (ch['slug'], ch['display_name'], ch['system_prompt'], ch['tts_voice'], ch['css_filter'], ch['color_accent']))
    
    # Set existing events and jobs to channel 1 (it_history) by default
    cursor.execute('UPDATE historical_events SET channel_id = 1 WHERE channel_id IS NULL')
    cursor.execute('UPDATE video_jobs SET channel_id = 1 WHERE channel_id IS NULL')
    
    conn.commit()
    conn.close()
    print(f"🌱 Seeded {len(channels)} default channels.")

def insert_events(events, source="wikipedia", channel_id=1):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    inserted_count = 0
    duplicate_count = 0
    
    for event in events:
        try:
            cursor.execute('''
                INSERT INTO historical_events 
                (month, day, year, title, summary, category, importance_score, source, channel_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event['month'], event['day'], event['year'], 
                event['title'][:100], event['summary'], event['category'], 
                event['importance_score'], source, channel_id
            ))
            inserted_count += 1
        except sqlite3.IntegrityError:
            duplicate_count += 1
            
    conn.commit()
    conn.close()
    return inserted_count, duplicate_count

if __name__ == "__main__":
    init_db()
    print(f"✅ SQLite Database initialized at {DB_FILE}")
