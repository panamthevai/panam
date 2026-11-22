from flask import Flask, render_template, send_from_directory, jsonify, request
import os, json, datetime

app = Flask(__name__)
STATS_FILE = 'stats.json'

# விசிட்டர் மற்றும் டவுன்லோட் டேட்டாவைச் சேமிக்கும் அமைப்பு
def get_stats():
    if not os.path.exists(STATS_FILE):
        return {"visitors": 0, "downloads": 0, "last_updated": "Never"}
    with open(STATS_FILE, 'r') as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/')
def home():
    stats = get_stats()
    stats["visitors"] += 1
    save_stats(stats)
    return render_template('index.html', stats=stats)

# Termux APT Repository & Direct File Server
@app.route('/install.sh')
def install_script():
    stats = get_stats()
    stats["downloads"] += 1
    save_stats(stats)
    return send_from_directory('.', 'install.sh', mimetype='text/plain')

@app.route('/<path:filename>')
def serve_repo_files(filename):
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    return jsonify({"error": "File not found in Panam Cloud"}), 404

# Live API Status (Termux-ல் இருந்து நிலையை அறிய)
@app.route('/api/status')
def api_status():
    stats = get_stats()
    return jsonify({
        "status": "ONLINE",
        "server": "Panam Render Cloud v3.0",
        "total_visitors": stats["visitors"],
        "script_installs": stats["downloads"],
        "server_time": str(datetime.datetime.now())
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
