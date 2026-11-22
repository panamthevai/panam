from flask import Flask, render_template, send_from_directory, request, redirect, url_for, Response
import os

app = Flask(__name__)

# உங்களது ரகசிய பாஸ்வேர்ட் மற்றும் API கீ (இதை மாற்றிக்கொள்ளவும்)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASS", "panam2026")
SECRET_API_KEY = os.environ.get("API_KEY", "PANAM_VIP_999")
UPLOAD_FOLDER = '.'

@app.route('/')
def home():
    files = [f for f in os.listdir('.') if f.endswith(('.deb', '.sh', '.apk'))]
    return render_template('index.html', files=files)

# அம்சம் 4: Secret Key பாதுகாப்புடன் கூடிய Installer
@app.route('/install.sh')
def protected_install():
    user_key = request.args.get('key')
    if user_key != SECRET_API_KEY:
        return Response("echo '❌ தவறான Secret Key! அணுகல் மறுக்கப்பட்டது.'\nexit 1", mimetype='text/plain', status=403)
    return send_from_directory('.', 'install.sh', mimetype='text/plain')

# அம்சம் 2: Web Admin Panel (கோப்புகளை அப்லோட் செய்ய)
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    msg = ""
    if request.method == 'POST':
        password = request.form.get('password')
        if password != ADMIN_PASSWORD:
            msg = "❌ தவறான பாஸ்வேர்ட்!"
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                file.save(os.path.join(UPLOAD_FOLDER, file.filename))
                msg = f"✅ {file.filename} வெற்றிகரமாக அப்லோட் செய்யப்பட்டது!"

    return f'''
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background:#090d16; color:#fff; font-family:sans-serif; text-align:center; padding:40px; }}
        .box {{ background:#111827; padding:30px; border-radius:12px; max-width:400px; margin:auto; border:1px solid #00f5d4; }}
        input, button {{ width:100%; padding:12px; margin:10px 0; border-radius:6px; border:none; }}
        button {{ background:#00f5d4; color:#000; font-weight:bold; cursor:pointer; }}
    </style></head>
    <body>
        <div class="box">
            <h2>🔐 Panam Cloud Admin</h2>
            <p style="color:#00f5d4;">{msg}</p>
            <form method="post" enctype="multipart/form-data">
                <input type="password" name="password" placeholder="Admin Password (panam2026)" required>
                <input type="file" name="file" required>
                <button type="submit">Upload to Cloud 🚀</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/<path:filename>')
def serve_files(filename):
    if os.path.exists(filename):
        return send_from_directory('.', filename)
    return "File not found", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
