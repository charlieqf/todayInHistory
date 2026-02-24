import sqlite3
import os
import sys
from flask import Flask, render_template, request, jsonify
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Set up paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.join(SCRIPT_DIR, "..")
sys.path.append(PARENT_DIR)  # Allow importing pipeline module

DB_FILE = os.path.join(SCRIPT_DIR, "..", "..", "data", "history_events.db")
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)

def get_db_connection():
    if not os.path.exists(DB_FILE):
        raise FileNotFoundError(f"Database not found at {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/channels')
def channels_page():
    return render_template('channels.html')

# ====== Channel CRUD API ======
@app.route('/api/channels', methods=['GET'])
def get_channels():
    try:
        conn = get_db_connection()
        channels = conn.execute('''
            SELECT c.*, 
                   (SELECT COUNT(*) FROM historical_events e WHERE e.channel_id = c.id) as event_count,
                   (SELECT COUNT(*) FROM video_jobs vj WHERE vj.channel_id = c.id) as job_count
            FROM channels c ORDER BY c.id
        ''').fetchall()
        conn.close()
        return jsonify([dict(c) for c in channels])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/channels', methods=['POST'])
def create_channel():
    data = request.json
    required = ['slug', 'display_name', 'system_prompt']
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Missing required field: {field}"}), 400
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO channels (slug, display_name, system_prompt, review_prompt, tts_voice, css_filter, color_accent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['slug'], data['display_name'], data['system_prompt'],
            data.get('review_prompt', ''),
            data.get('tts_voice', 'zh-CN-YunxiNeural'),
            data.get('css_filter', 'sepia(0.3) contrast(1.1) brightness(0.9) grayscale(0.2)'),
            data.get('color_accent', '#00d4ff'),
        ))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Channel created"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/channels/<int:channel_id>', methods=['PUT'])
def update_channel(channel_id):
    data = request.json
    try:
        conn = get_db_connection()
        conn.execute('''
            UPDATE channels SET 
                display_name = COALESCE(?, display_name),
                system_prompt = COALESCE(?, system_prompt),
                review_prompt = ?,
                tts_voice = COALESCE(?, tts_voice),
                css_filter = COALESCE(?, css_filter),
                color_accent = COALESCE(?, color_accent)
            WHERE id = ?
        ''', (
            data.get('display_name'), data.get('system_prompt'),
            data.get('review_prompt', ''),
            data.get('tts_voice'), data.get('css_filter'),
            data.get('color_accent'), channel_id
        ))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Channel updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/create_job', methods=['POST'])
def create_job():
    data = request.json
    event_id = data.get('event_id')
    channel_id = data.get('channel_id', 1)  # Default to channel 1 (it_history)
    
    if not event_id:
        return jsonify({"error": "No event_id provided"}), 400
        
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO video_jobs (event_id, channel_id, status) VALUES (?, ?, 'PENDING')",
            (event_id, channel_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Job already exists for this event"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
        
    return jsonify({"success": True, "message": "Pipeline initialized"})

@app.route('/pipeline/<int:job_id>')
def pipeline_view(job_id):
    conn = get_db_connection()
    job = conn.execute('''
        SELECT vj.*, e.title, e.summary, e.month, e.day, e.year, e.rich_context 
        FROM video_jobs vj 
        JOIN historical_events e ON vj.event_id = e.id 
        WHERE vj.id = ?
    ''', (job_id,)).fetchone()
    
    metrics = conn.execute('SELECT * FROM publish_metrics WHERE job_id = ?', (job_id,)).fetchall()
    conn.close()
    
    if not job:
        return "Job not found", 404
        
    return render_template('pipeline.html', job=dict(job), metrics=[dict(m) for m in metrics])

@app.route('/api/jobs/<int:job_id>/enrich', methods=['POST'])
def enrich_node(job_id):
    prompt = request.json.get('prompt', '')
    
    try:
        conn = get_db_connection()
        # Get the event_id and existing info for this job
        job = conn.execute('''
            SELECT vj.event_id, e.title, e.summary, e.month, e.day, e.year 
            FROM video_jobs vj 
            JOIN historical_events e ON vj.event_id = e.id 
            WHERE vj.id = ?
        ''', (job_id,)).fetchone()
        
        if not job:
            return jsonify({"error": "Job not found"}), 404
            
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return jsonify({"error": "GEMINI_API_KEY not configured"}), 500
            
        client = genai.Client(api_key=api_key)
        
        base_context = f"Event: {job['title']} ({job['year']}-{job['month']}-{job['day']})\nSummary: {job['summary']}"
        full_prompt = f"Based on this historical event:\n{base_context}\n\nPlease fulfill this enrichment request to deepen the story context:\n{prompt}"
        
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=full_prompt,
        )
        
        enriched_text = response.text
        
        conn.execute("UPDATE historical_events SET rich_context = ? WHERE id = ?", (enriched_text, job['event_id']))
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
        
    return jsonify({"success": True, "message": "Enrichment completed via Gemini"})

@app.route('/api/jobs/<int:job_id>/run_script', methods=['POST'])
def run_script_node(job_id):
    from pipeline.node_script_gen import run_script_generation
    try:
        success = run_script_generation(job_id)
        if success:
            return jsonify({"success": True, "message": "Script generated successfully"})
        else:
            return jsonify({"error": "Failed to generate script"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/generate_assets', methods=['POST'])
def generate_assets_node(job_id):
    from pipeline.node_assets_gen import run_asset_generation
    try:
        success = run_asset_generation(job_id)
        if success:
            return jsonify({"success": True, "message": "Audio & Visual Assets generated successfully"})
        else:
            return jsonify({"error": "Asset generation failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/render', methods=['POST'])
def render_video_node(job_id):
    from pipeline.node_render import render_video_for_job
    try:
        success = render_video_for_job(job_id)
        if success:
            return jsonify({"success": True, "message": "Video rendered and saved successfully"})
        else:
            return jsonify({"error": "Video rendering failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/run_all', methods=['POST'])
def run_all_nodes(job_id):
    from pipeline.automation_orchestrator import run_full_pipeline
    try:
        success = run_full_pipeline(job_id)
        if success:
            return jsonify({"success": True, "message": "全自动流水线执行完毕！视频已生成。"})
        else:
            return jsonify({"error": "流水线执行失败，请检查报错日志"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/publish', methods=['POST'])
def add_publish_metric(job_id):
    data = request.json
    platform = data.get('platform')
    url = data.get('url', '')
    
    if not platform:
        return jsonify({"error": "Missing platform"}), 400
        
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO publish_metrics (job_id, platform, url) 
            VALUES (?, ?, ?) 
            ON CONFLICT(job_id, platform) DO UPDATE SET url=excluded.url, last_updated=CURRENT_TIMESTAMP
        ''', (job_id, platform, url))
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"success": True, "message": f"Published to {platform}"})

@app.route('/api/events')
def get_events():
    search = request.args.get('search', '').strip()
    month = request.args.get('month', '').strip()
    category = request.args.get('category', '').strip()
    channel = request.args.get('channel', '').strip()
    sort_by = request.args.get('sort', 'importance_score')
    
    # Secure sort column mapping
    allowed_sorts = {
        'importance_score': 'importance_score DESC',
        'date_asc': 'month ASC, day ASC',
        'date_desc': 'month DESC, day DESC',
        'year_desc': 'year DESC'
    }
    order_by_clause = allowed_sorts.get(sort_by, 'importance_score DESC')
    
    try:
        conn = get_db_connection()
    except FileNotFoundError:
        return jsonify([])

    query = """
        SELECT e.*, 
               COALESCE(vj.status, 'UNSTARTED') as pipeline_status,
               vj.id as job_id,
               ch.display_name as channel_name,
               ch.color_accent as channel_color,
               (SELECT GROUP_CONCAT(pm.platform) FROM publish_metrics pm WHERE pm.job_id = vj.id) as published_platforms
        FROM historical_events e
        LEFT JOIN video_jobs vj ON e.id = vj.event_id
        LEFT JOIN channels ch ON e.channel_id = ch.id
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (e.title LIKE ? OR e.summary LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if month:
        query += " AND e.month = ?"
        params.append(month)
    if category:
        query += " AND e.category = ?"
        params.append(category)
    if channel:
        query += " AND e.channel_id = ?"
        params.append(channel)
        
    query += f" ORDER BY e.{order_by_clause} LIMIT 1000"
    
    try:
        events = conn.execute(query, params).fetchall()
    except Exception as e:
        print(f"DB Error: {e}")
        events = []
    finally:
        conn.close()
    
    return jsonify([dict(ix) for ix in events])

@app.route('/api/stats')
def get_stats():
    channel = request.args.get('channel', '').strip()
    
    try:
        conn = get_db_connection()
        params = []
        base_query = "FROM historical_events WHERE 1=1"
        if channel:
            base_query += " AND channel_id = ?"
            params.append(channel)
            
        total = conn.execute(f"SELECT count(*) {base_query}", params).fetchone()[0]
        categories = conn.execute(f"SELECT DISTINCT category {base_query} AND category IS NOT NULL", params).fetchall()
        
        # Monthly distribution
        monthly_counts = conn.execute(f"SELECT month, count(*) {base_query} GROUP BY month ORDER BY month", params).fetchall()
        conn.close()
        
        return jsonify({
            "total": total,
            "categories": [c[0] for c in categories if c[0]],
            "monthly": {row[0]: row[1] for row in monthly_counts}
        })
    except Exception as e:
        print(f"Stats Error: {e}")
        return jsonify({"total": 0, "categories": [], "monthly": {}})

if __name__ == '__main__':
    # Run the Flask app on port 8080 and bind to all IP addresses
    print(f"Starting IT History Admin Dashboard...")
    print(f"DB Path: {DB_FILE}")
    print(f"Network Access: http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
