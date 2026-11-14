import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

# --- உங்கள் விவரங்களை இங்கே மாற்றவும் ---
SHOP_NAME = "சென்னை ஆன்லைன் ஸ்டோர்"
UPI_ID = "yourname@okicici"
ADMIN_PASSWORD = "admin123"  # ஆர்டர்களைப் பார்க்கும் ரகசியப் பாஸ்வேர்ட்
# ---------------------------------------

PRODUCTS = [
    {"id": 1, "name": "பாதாம் அல்வா (250g)", "price": 150, "desc": "சுத்தமான நெய்யில் செய்தது"},
    {"id": 2, "name": "சிக்கன் பிரியாணி", "price": 220, "desc": "சீரக சம்பா தம் பிரியாணி"},
    {"id": 3, "name": "சாக்லேட் கேக் (500g)", "price": 350, "desc": "ஃப்ரெஷ் கிரீம் கேக்"},
    {"id": 4, "name": "பாதாம் பால்", "price": 60, "desc": "குளிர்ச்சியான சுவை"}
]

# டேட்டாபேஸ் உருவாக்குதல்
def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, price INTEGER, 
                  customer_name TEXT, phone TEXT, address TEXT, time TEXT)''')
    conn.commit()
    conn.close()

init_db()

# 1. வாடிக்கையாளர்களுக்கான முகப்புப் பக்கம்
HOME_HTML = """
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ shop_name }}</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding: 15px; }
        .header { background: #1a73e8; color: white; padding: 15px; text-align: center; border-radius: 10px; }
        .card { background: white; padding: 15px; margin-top: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .price { color: #d93025; font-weight: bold; font-size: 18px; }
        input, textarea { width: 95%; padding: 8px; margin: 5px 0; border: 1px solid #ccc; border-radius: 5px; }
        .btn { background: #1a73e8; color: white; border: none; padding: 10px 15px; border-radius: 5px; font-weight: bold; width: 100%; cursor: pointer; }
        .upi-box { background: #e8f0fe; padding: 10px; border-radius: 5px; margin: 10px 0; font-size: 14px; }
    </style>
</head>
<body>
    <div class="header">
        <h2>🛍️ {{ shop_name }}</h2>
        <p>நேரடி ஆன்லைன் ஆர்டர் தளம்</p>
    </div>

    {% if success %}
    <div class="card" style="background: #d4edda; color: #155724; text-align: center;">
        <h3>🎉 உங்கள் ஆர்டர் வெற்றிகரமாகப் பதிவு செய்யப்பட்டது!</h3>
        <p>விரைவில் டெலிவரி செய்யப்படும்.</p>
    </div>
    {% endif %}

    {% for item in products %}
    <div class="card">
        <h3>{{ item.name }}</h3>
        <p>{{ item.desc }}</p>
        <p class="price">விலை: ₹{{ item.price }}</p>
        <form action="/order" method="POST">
            <input type="hidden" name="item" value="{{ item.name }}">
            <input type="hidden" name="price" value="{{ item.price }}">
            <input type="text" name="name" placeholder="உங்கள் பெயர்" required>
            <input type="tel" name="phone" placeholder="மொபைல் எண்" required>
            <textarea name="address" placeholder="முழு முகவரி" required></textarea>
            <div class="upi-box">
                💳 பணம் செலுத்த UPI ID: <b>{{ upi_id }}</b><br>
                (பணம் செலுத்திய பிறகு கீழே உள்ள பொத்தானை அழுத்தவும்)
            </div>
            <button type="submit" class="btn">✅ ஆர்டரை உறுதி செய்</button>
        </form>
    </div>
    {% endfor %}
</body>
</html>
"""

# 2. கடை உரிமையாளருக்கான Admin பக்கம்
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - ஆர்டர் பட்டியல்</title>
    <style>
        body { font-family: sans-serif; padding: 15px; background: #f8f9fa; }
        .order-card { background: white; padding: 15px; margin-bottom: 10px; border-left: 5px solid #28a745; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <h2>📋 வந்திருக்கும் ஆர்டர்கள் ({{ orders|length }})</h2>
    {% for o in orders %}
    <div class="order-card">
        <b>ஆர்டர் #{{ o[0] }}</b> - {{ o[6] }}<br>
        <b>பொருள்:</b> {{ o[1] }} (₹{{ o[2] }})<br>
        <b>பெயர்:</b> {{ o[3] }} | <b>போன்:</b> {{ o[4] }}<br>
        <b>முகவரி:</b> {{ o[5] }}
    </div>
    {% endfor %}
</body>
</html>
"""

@app.route('/')
def home():
    success = request.args.get('success')
    return render_template_string(HOME_HTML, shop_name=SHOP_NAME, products=PRODUCTS, upi_id=UPI_ID, success=success)

@app.route('/order', methods=['POST'])
def place_order():
    item = request.form['item']
    price = request.form['price']
    name = request.form['name']
    phone = request.form['phone']
    address = request.form['address']
    now = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("INSERT INTO orders (item, price, customer_name, phone, address, time) VALUES (?, ?, ?, ?, ?, ?)",
              (item, price, name, phone, address, now))
    conn.commit()
    conn.close()
    return redirect('/?success=1')

@app.route('/admin')
def admin():
    pwd = request.args.get('pass')
    if pwd != ADMIN_PASSWORD:
        return "<h3>அணுகல் மறுக்கப்பட்டது! சரியான பாஸ்வேர்டுடன் வரவும். (உதாரணம்: /admin?pass=admin123)</h3>"
    
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = c.fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, orders=orders)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
