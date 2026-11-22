from flask import Flask, render_template, send_from_directory, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import os, hashlib, datetime, shutil

app = Flask(__name__)

# ==========================================
# 16. AUTO-HEALING ENGINE (சுய-பழுதுபார்ப்பு)
# ==========================================
def auto_heal_system():
    os.makedirs('templates', exist_ok=True)
    # index.html காணாமல் போனாலோ அல்லது காலியாக இருந்தாலோ தானாகவே மீட்டெடுக்கும்
    if not os.path.exists('templates/index.html') or os.path.getsize('templates/index.html') == 0:
        if os.path.exists('index.html') and os.path.getsize('index.html') > 0:
            shutil.copy('index.html', 'templates/index.html')
        else:
            with open('templates/index.html', 'w') as f:
                f.write("<html><body style='background:#090d16;color:#00f5d4;text-align:center;padding:50px;'><h1>🚀 Panam Auto-Healed Cloud Active</h1><p>System recovered automatically!</p></body></html>")
        log_event("AUTO-HEAL: Restored missing index.html automatically.")

def log_event(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("system_events.log", "a") as f:
        f.write(f"[{timestamp}] {message}\n")

# ==========================================
# 18. CLOUD CRON SCHEDULER (தானியங்கி டைமர்)
# ==========================================
def scheduled_background_task():
    auto_heal_system()
    log_event("CRON-JOB: Automated 10-minute health check & cleanup completed.")

scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_background_task, trigger="interval", minutes=10)
scheduler.start()

# சர்வர் தொடங்கும் போதே ஒருமுறை சரிபார்க்கும்
auto_heal_system()

# ==========================================
# MAIN ROUTES & ERROR HANDLER
# ==========================================
@app.route('/')
def home():
    auto_heal_system()
    return render_template('index.html')

# எந்தவொரு 500 சர்வர் பிழை வந்தாலும் முடங்காமல் சமாளிக்கும்
@app.errorhandler(500)
def internal_error(error):
    auto_heal_system()
    log_event(f"ERROR-RECOVERED: {str(error)}")
    return jsonify({"status": "Auto-Healed", "message": "Server recovered from an error. Refresh page."}), 200

# ==========================================
# 17. CUSTOM MICRO-APIs (API மார்க்கெட்பிளேஸ்)
# ==========================================
@app.route('/api/ip')
def api_get_ip():
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    return jsonify({
        "service": "Panam IP Checker API",
        "your_ip": user_ip,
        "user_agent": request.headers.get('User-Agent')
    })

@app.route('/api/hash')
def api_generate_hash():
    text = request.args.get('text', 'panam')
    hashed = hashlib.sha256(text.encode()).hexdigest()
    return jsonify({
        "service": "Panam Crypto Hash API",
        "input": text,
        "sha256": hashed
    })

# Cron மற்றும் Auto-Heal லாக்குகளைப் பார்க்கும் பக்கம்
@app.route('/api/logs')
def view_logs():
    if os.path.exists("system_events.log"):
        with open("system_events.log", "r") as f:
            logs = f.readlines()[-20:] # கடைசி 20 நிகழ்வுகள்
        return jsonify({"recent_events": logs})
    return jsonify({"recent_events": ["No events yet"]})

@app.route('/<path:filename>')
def serve_files(filename):
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
