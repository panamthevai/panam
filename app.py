from flask import Flask, render_template, send_from_directory, request, jsonify, send_file
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
import os, hashlib, datetime, shutil, io, uuid, requests, qrcode, psutil

app = Flask(__name__)

# தற்காலிக சீக்ரெட் மெசேஜ்களைச் சேமிக்கும் இடம் (Feature 22)
SECRET_VAULT = {}

# ==========================================
# 16 & 18. AUTO-HEALING & CRON SCHEDULER
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
scheduler.add_job(func=lambda: log_event("CRON: 10-min health check OK"), trigger="interval", minutes=10)
scheduler.start()
auto_heal_system()

@app.route('/')
def home():
    auto_heal_system()
    return render_template('index.html')

# ==========================================
# 17. IP & HASH APIs
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

# ==========================================
# 20. CLOUD WEB PROXY API (தளங்களைப் படிக்க)
# ==========================================
@app.route('/api/proxy')
def cloud_proxy():
    target_url = request.args.get('url')
    if not target_url:
        return jsonify({"error": "URL parameter required. Ex: /api/proxy?url=https://example.com"}), 400
    try:
        resp = requests.get(target_url, timeout=8, headers={"User-Agent": "PanamCloudProxy/4.0"})
        return jsonify({
            "status_code": resp.status_code,
            "target": target_url,
            "content_preview": resp.text[:1000] # முதல் 1000 எழுத்துக்கள்
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 21. INSTANT QR CODE GENERATOR API
# ==========================================
@app.route('/api/qr')
def generate_qr():
    data = request.args.get('data', 'https://onrender.com')
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# ==========================================
# 22. BURN-AFTER-READING SECRET SHARE
# ==========================================
@app.route('/api/secret/create', methods=['POST'])
def create_secret():
    data = request.json or {}
    secret_text = data.get('text', '')
    if not secret_text:
        return jsonify({"error": "No secret text provided"}), 400
    secret_id = str(uuid.uuid4())[:8]
    SECRET_VAULT[secret_id] = secret_text
    return jsonify({
        "status": "Created",
        "secret_id": secret_id,
        "one_time_link": f"https://onrender.com/api/secret/read/{secret_id}"
    })

@app.route('/api/secret/read/<secret_id>')
def read_secret(secret_id):
    if secret_id in SECRET_VAULT:
        msg = SECRET_VAULT.pop(secret_id) # படித்தவுடன் அழித்துவிடும்!
        return jsonify({"status": "DESTROYED_AFTER_READING", "secret_message": msg})
    return jsonify({"error": "Secret already destroyed or invalid ID!"}), 404

# ==========================================
# 23. SERVER CPU & RAM MONITOR API
# ==========================================
@app.route('/api/sysinfo')
def system_monitor():
    mem = psutil.virtual_memory()
    return jsonify({
        "cpu_usage_percent": psutil.cpu_percent(interval=0.5),
        "ram_total_mb": round(mem.total / (1024 * 1024), 2),
        "ram_used_mb": round(mem.used / (1024 * 1024), 2),
        "ram_percent": mem.percent,
        "active_secrets_in_vault": len(SECRET_VAULT)
    })

# ==========================================
# 24. SMART WEB SCRAPER API (தலைப்புச் செய்திகள் / லிங்க் எடுக்க)
# ==========================================
@app.route('/api/scrape')
def smart_scraper():
    target_url = request.args.get('url', 'https://ycombinator.com')
    try:
        resp = requests.get(target_url, timeout=8)
        soup = BeautifulSoup(resp.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else "No Title"
        headings = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])[:10]]
        return jsonify({
            "source_url": target_url,
            "page_title": title,
            "extracted_headings": headings
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/<path:filename>')
def serve_files(filename):
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
