import sqlite3
import os
from flask import Flask, render_template, request, jsonify

# Set up paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
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

@app.route('/api/create_job', methods=['POST'])
def create_job():
    data = request.json
    event_id = data.get('event_id')
    
    if not event_id:
        return jsonify({"error": "No event_id provided"}), 400
        
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO video_jobs (event_id, status) VALUES (?, 'PENDING')",
            (event_id,)
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
    
    # In a real backend, this would trigger Gemini to fetch the raw Wikipedia text
    # and run the given `prompt` to generate deep context, then write to `rich_context`.
    # For now, we mock the DB write to demonstrate the UI data flow to the user.
    mock_enriched_text = f"[AI Enriched Context via '{prompt}'] \\n\\nThis is a mocked deep dive into the historical event..."
    
    try:
        conn = get_db_connection()
        # Get the event_id for this job
        job = conn.execute("SELECT event_id FROM video_jobs WHERE id = ?", (job_id,)).fetchone()
        if job:
            conn.execute("UPDATE historical_events SET rich_context = ? WHERE id = ?", (mock_enriched_text, job[0]))
            conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
        
    return jsonify({"success": True, "message": "Enrichment completed"})

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
               (SELECT GROUP_CONCAT(pm.platform) FROM publish_metrics pm WHERE pm.job_id = vj.id) as published_platforms
        FROM historical_events e
        LEFT JOIN video_jobs vj ON e.id = vj.event_id
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
    try:
        conn = get_db_connection()
        total = conn.execute("SELECT count(*) FROM historical_events").fetchone()[0]
        categories = conn.execute("SELECT DISTINCT category FROM historical_events WHERE category IS NOT NULL").fetchall()
        
        # Monthly distribution
        monthly_counts = conn.execute("SELECT month, count(*) FROM historical_events GROUP BY month ORDER BY month").fetchall()
        conn.close()
        
        return jsonify({
            "total": total,
            "categories": [c[0] for c in categories if c[0]],
            "monthly": {row[0]: row[1] for row in monthly_counts}
        })
    except Exception:
        return jsonify({"total": 0, "categories": [], "monthly": {}})

if __name__ == '__main__':
    # Run the Flask app on port 8080 and bind to all IP addresses
    print(f"Starting IT History Admin Dashboard...")
    print(f"DB Path: {DB_FILE}")
    print(f"Network Access: http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
