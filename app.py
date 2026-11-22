from flask import Flask, render_template, send_from_directory, request, jsonify, send_file
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from fpdf import FPDF
import yt_dlp
import os, hashlib, datetime, shutil, io, uuid, json, requests, qrcode, psutil

app = Flask(__name__)

# தரவு சேமிப்பகங்கள்
SECRET_VAULT = {}
DB_FILE = 'panam_cloud_db.json'
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") # Render Environment-ல் உங்கள் Key-ஐ சேர்க்கலாம்

# ==========================================
# 16 & 18. AUTO-HEALING & CRON SCHEDULER (OLD)
# ==========================================
def auto_heal_system():
    os.makedirs('templates', exist_ok=True)
    if not os.path.exists('templates/index.html') or os.path.getsize('templates/index.html') == 0:
        if os.path.exists('index.html') and os.path.getsize('index.html') > 0:
            shutil.copy('index.html', 'templates/index.html')

def log_event(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("system_events.log", "a") as f:
        f.write(f"[{timestamp}] {message}\n")

scheduler = BackgroundScheduler()
scheduler.add_job(func=lambda: log_event("CRON: v5.0 Super Server Health OK"), trigger="interval", minutes=10)
scheduler.start()
auto_heal_system()

@app.route('/')
def home():
    auto_heal_system()
    return render_template('index.html')

# ==========================================
# 17, 20, 21, 22, 23, 24. OLD CORE APIs
# ==========================================
@app.route('/api/ip')
def api_get_ip():
    return jsonify({"your_ip": request.headers.get('X-Forwarded-For', request.remote_addr)})

@app.route('/api/hash')
def api_generate_hash():
    text = request.args.get('text', 'panam')
    return jsonify({"input": text, "sha256": hashlib.sha256(text.encode()).hexdigest()})

@app.route('/api/logs')
def view_logs():
    if os.path.exists("system_events.log"):
        with open("system_events.log", "r") as f:
            return jsonify({"recent_events": f.readlines()[-15:]})
    return jsonify({"recent_events": ["System Active"]})

@app.route('/api/proxy')
def cloud_proxy():
    target_url = request.args.get('url')
    if not target_url: return jsonify({"error": "URL required"}), 400
    try:
        resp = requests.get(target_url, timeout=8, headers={"User-Agent": "PanamProxy/5.0"})
        return jsonify({"status": resp.status_code, "preview": resp.text[:1000]})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/qr')
def generate_qr():
    data = request.args.get('data', 'https://onrender.com')
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/api/secret/create', methods=['POST'])
def create_secret():
    secret_text = (request.json or {}).get('text', '')
    if not secret_text: return jsonify({"error": "Text required"}), 400
    secret_id = str(uuid.uuid4())[:8]
    SECRET_VAULT[secret_id] = secret_text
    return jsonify({"one_time_link": f"https://onrender.com/api/secret/read/{secret_id}"})

@app.route('/api/secret/read/<secret_id>')
def read_secret(secret_id):
    if secret_id in SECRET_VAULT:
        return jsonify({"status": "DESTROYED", "secret": SECRET_VAULT.pop(secret_id)})
    return jsonify({"error": "Already destroyed or invalid!"}), 404

@app.route('/api/sysinfo')
def system_monitor():
    mem = psutil.virtual_memory()
    return jsonify({
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "ram_used_mb": round(mem.used / (1024 * 1024), 2),
        "ram_percent": mem.percent
    })

@app.route('/api/scrape')
def smart_scraper():
    target_url = request.args.get('url', 'https://ycombinator.com')
    try:
        soup = BeautifulSoup(requests.get(target_url, timeout=8).text, 'html.parser')
        headings = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])[:8]]
        return jsonify({"title": soup.title.string.strip() if soup.title else "No Title", "headings": headings})
    except Exception as e: return jsonify({"error": str(e)}), 500

# ==========================================
# 25. GEMINI AI ASSISTANT API (NEW)
# ==========================================
@app.route('/api/ai', methods=['POST'])
def ai_assistant():
    data = request.json or {}
    prompt = data.get('prompt', '')
    user_key = data.get('api_key') or GEMINI_API_KEY
    if not prompt: return jsonify({"error": "கேள்வியை உள்ளிடவும் (Prompt required)"}), 400
    if not user_key:
        return jsonify({"error": "Gemini API Key தேவை! Render Environment அல்லது கீழே உள்ள பெட்டியில் Key கொடுக்கவும்."}), 400
    try:
        url = f"https://googleapis.com{user_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, timeout=15).json()
        reply = res['candidates'][0]['content']['parts'][0]['text']
        return jsonify({"ai_response": reply})
    except Exception as e:
        return jsonify({"error": "AI Connection Error", "details": str(e)}), 500

# ==========================================
# 26. VIDEO / AUDIO STREAM EXTRACTOR API (NEW)
# ==========================================
@app.route('/api/media')
def media_extractor():
    video_url = request.args.get('url')
    if not video_url: return jsonify({"error": "Video URL required"}), 400
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'format': 'best'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return jsonify({
                "title": info.get('title'),
                "duration_sec": info.get('duration'),
                "direct_stream_url": info.get('url'),
                "thumbnail": info.get('thumbnail')
            })
    except Exception as e:
        return jsonify({"error": "Media extraction failed", "details": str(e)}), 500

# ==========================================
# 27. INSTANT PDF DOCUMENT GENERATOR API (NEW)
# ==========================================
@app.route('/api/pdf')
def create_pdf():
    title = request.args.get('title', 'Panam Cloud Document')
    content = request.args.get('text', 'Generated from Panam Ultimate Cloud v5.0')
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title.encode('latin-1', 'replace').decode('latin-1'), ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=content.encode('latin-1', 'replace').decode('latin-1'))
    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="panam_doc.pdf", mimetype='application/pdf')

# ==========================================
# 28. LIVE CRYPTO & CURRENCY MARKET API (NEW)
# ==========================================
@app.route('/api/market')
def live_market():
    try:
        crypto = requests.get("https://coingecko.com", timeout=6).json()
        forex = requests.get("https://er-api.com", timeout=6).json()
        return jsonify({
            "usd_to_inr": forex.get("rates", {}).get("INR"),
            "bitcoin_inr": crypto.get("bitcoin", {}).get("inr"),
            "ethereum_inr": crypto.get("ethereum", {}).get("inr"),
            "timestamp": str(datetime.datetime.now())
        })
    except Exception as e:
        return jsonify({"error": "Market API error", "details": str(e)}), 500

# ==========================================
# 30. MINI CLOUD KEY-VALUE DATABASE API (NEW)
# ==========================================
def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, 'r') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f, indent=2)

@app.route('/api/db', methods=['GET', 'POST'])
def cloud_database():
    db = load_db()
    if request.method == 'POST':
        data = request.json or {}
        key, val = data.get('key'), data.get('value')
        if not key: return jsonify({"error": "Key required"}), 400
        db[key] = val
        save_db(db)
        return jsonify({"status": "Saved to Cloud DB", "key": key, "value": val})
    key = request.args.get('key')
    if key: return jsonify({key: db.get(key, "Not Found")})
    return jsonify({"all_stored_data": db})

@app.route('/<path:filename>')
def serve_files(filename):
    if os.path.exists(filename): return send_from_directory('.', filename)
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
