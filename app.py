import os
import sqlite3
from datetime import datetime
from urllib.parse import quote
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

# --- உங்கள் விவரங்களை இங்கே மாற்றிக்கொள்ளலாம் ---
SHOP_NAME = "சென்னை ஆன்லைன் ஸ்டோர்"
UPI_ID = "yourname@okicici"
ADMIN_PASSWORD = "admin123"
# ---------------------------------------------

def get_db():
    conn = sqlite3.connect('store.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, price INTEGER, 
                  customer_name TEXT, phone TEXT, address TEXT, time TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price INTEGER, desc TEXT)''')
    
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO products (name, price, desc) VALUES (?, ?, ?)", 
                  ("பாதாம் அல்வா (250g)", 150, "சுத்தமான நெய்யில் செய்தது"))
        c.execute("INSERT INTO products (name, price, desc) VALUES (?, ?, ?)", 
                  ("சிக்கன் பிரியாணி", 220, "சீரக சம்பா தம் பிரியாணி"))
    conn.commit()
    conn.close()

init_db()

HOME_HTML = """
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ shop_name }}</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; margin: 0; padding: 15px; }
        .header { background: linear-gradient(135deg, #1a73e8, #0d47a1); color: white; padding: 20px; text-align: center; border-radius: 12px; }
        .card { background: white; padding: 16px; margin-top: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .price { color: #d93025; font-weight: bold; font-size: 19px; margin: 8px 0; }
        input, textarea { width: 94%; padding: 10px; margin: 6px 0; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; }
        .upi-btn { display: block; text-align: center; background: #28a745; color: white; text-decoration: none; padding: 11px; border-radius: 6px; font-weight: bold; margin: 10px 0; }
        .order-btn { background: #1a73e8; color: white; border: none; padding: 12px; border-radius: 6px; font-weight: bold; width: 100%; font-size: 15px; cursor: pointer; }
        .footer { text-align: center; margin-top: 25px; font-size: 13px; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin:0;">🛍️ {{ shop_name }}</h2>
        <p style="margin:5px 0 0 0; opacity:0.9;">நேரடி ஆன்லைன் ஆர்டர் தளம்</p>
    </div>

    {% if success %}
    <div class="card" style="background: #d4edda; color: #155724; text-align: center; border: 1px solid #c3e6cb;">
        <h3 style="margin:0;">🎉 ஆர்டர் வெற்றிகரமாகப் பதிவு செய்யப்பட்டது!</h3>
        <p style="margin:5px 0 0 0;">உங்கள் பொருள் விரைவில் டெலிவரி செய்யப்படும்.</p>
    </div>
    {% endif %}

    {% for item in products %}
    <div class="card">
        <h3 style="margin:0;">{{ item['name'] }}</h3>
        <p style="color:#555; margin:5px 0;">{{ item['desc'] }}</p>
        <p class="price">விலை: ₹{{ item['price'] }}</p>
        
        <a class="upi-btn" href="upi://pay?pa={{ upi_id }}&pn={{ encoded_shop }}&am={{ item['price'] }}&cu=INR&tn={{ item['name'] }}">
            📲 GPay / PhonePe-ல் ₹{{ item['price'] }} செலுத்து
        </a>

        <form action="/order" method="POST">
            <input type="hidden" name="item" value="{{ item['name'] }}">
            <input type="hidden" name="price" value="{{ item['price'] }}">
            <input type="text" name="name" placeholder="உங்கள் பெயர்" required>
            <input type="tel" name="phone" placeholder="மொபைல் எண்" required>
            <textarea name="address" placeholder="முழு டெலிவரி முகவரி" rows="2" required></textarea>
            <button type="submit" class="order-btn">✅ பணம் செலுத்திவிட்டேன் - ஆர்டர் செய்</button>
        </form>
    </div>
    {% endfor %}

    <div class="footer">
        <a href="/admin" style="color:#555; text-decoration:none; font-weight:bold;">🔒 Admin Login</a>
    </div>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - {{ shop_name }}</title>
    <style>
        body { font-family: sans-serif; padding: 15px; background: #f4f6f9; margin: 0; }
        .box { background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); }
        input { width: 93%; padding: 9px; margin: 5px 0; border: 1px solid #ccc; border-radius: 5px; }
        .add-btn { background: #28a745; color: white; border: none; padding: 10px; width: 100%; border-radius: 5px; font-weight: bold; }
        .del-btn { background: #dc3545; color: white; text-decoration: none; padding: 4px 8px; border-radius: 4px; font-size: 12px; float: right; }
        .order-card { border-left: 4px solid #1a73e8; padding: 10px; background: #f8f9fa; margin-bottom: 10px; border-radius: 4px; }
        .prod-item { padding: 10px 0; border-bottom: 1px solid #eee; }
    </style>
</head>
<body>
    <h2>⚙️ {{ shop_name }} - நிர்வாகப் பக்கம்</h2>
    <p><a href="/">← வாடிக்கையாளர் பக்கத்திற்குச் செல்</a></p>

    <div class="box">
        <h3 style="margin-top:0;">➕ புதிய பொருள் சேர்க்க</h3>
        <form action="/add_product?pass={{ pwd }}" method="POST">
            <input type="text" name="name" placeholder="பொருளின் பெயர் (எ.கா: மைசூர் பாக் 250g)" required>
            <input type="number" name="price" placeholder="விலை (எ.கா: 180)" required>
            <input type="text" name="desc" placeholder="சிறிய விளக்கம் (எ.கா: நெய் மைசூர் பாக்)" required>
            <button type="submit" class="add-btn">பொருளைச் சேர்</button>
        </form>
    </div>

    <div class="box">
        <h3 style="margin-top:0;">📦 கடையில் உள்ள பொருட்கள் ({{ products|length }})</h3>
        {% for p in products %}
        <div class="prod-item">
            <b>{{ p['name'] }}</b> - ₹{{ p['price'] }}
            <a class="del-btn" href="/delete_product/{{ p['id'] }}?pass={{ pwd }}">நீக்கு</a>
        </div>
        {% endfor %}
    </div>

    <div class="box">
        <h3 style="margin-top:0;">📋 வந்திருக்கும் ஆர்டர்கள் ({{ orders|length }})</h3>
        {% for o in orders %}
        <div class="order-card">
            <b>ஆர்டர் #{{ o['id'] }}</b> ({{ o['time'] }})<br>
            <b>பொருள்:</b> {{ o['item'] }} (₹{{ o['price'] }})<br>
            <b>பெயர்:</b> {{ o['customer_name'] }} | <b>போன்:</b> {{ o['phone'] }}<br>
            <b>முகவரி:</b> {{ o['address'] }}
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    success = request.args.get('success')
    conn = get_db()
    products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(HOME_HTML, shop_name=SHOP_NAME, products=products, 
                                  upi_id=UPI_ID, encoded_shop=quote(SHOP_NAME), success=success)

@app.route('/order', methods=['POST'])
def place_order():
    item = request.form['item']
    price = request.form['price']
    name = request.form['name']
    phone = request.form['phone']
    address = request.form['address']
    now = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    conn = get_db()
    conn.execute("INSERT INTO orders (item, price, customer_name, phone, address, time) VALUES (?, ?, ?, ?, ?, ?)",
                 (item, price, name, phone, address, now))
    conn.commit()
    conn.close()
    return redirect('/?success=1')

@app.route('/admin')
def admin():
    pwd = request.args.get('pass')
    if pwd != ADMIN_PASSWORD:
        return '''
        <form action="/admin" method="GET" style="padding:30px; font-family:sans-serif; text-align:center;">
            <h3>🔒 Admin Login</h3>
            <input type="password" name="pass" placeholder="பாஸ்வேர்டு உள்ளிடவும்" style="padding:10px; border-radius:5px; border:1px solid #ccc;"><br><br>
            <button type="submit" style="padding:10px 20px; background:#1a73e8; color:white; border:none; border-radius:5px;">உள்நுழை</button>
        </form>
        '''
    conn = get_db()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, shop_name=SHOP_NAME, orders=orders, products=products, pwd=pwd)

@app.route('/add_product', methods=['POST'])
def add_product():
    pwd = request.args.get('pass')
    if pwd == ADMIN_PASSWORD:
        name = request.form['name']
        price = request.form['price']
        desc = request.form['desc']
        conn = get_db()
        conn.execute("INSERT INTO products (name, price, desc) VALUES (?, ?, ?)", (name, price, desc))
        conn.commit()
        conn.close()
    return redirect(f'/admin?pass={pwd}')

@app.route('/delete_product/<int:prod_id>')
def delete_product(prod_id):
    pwd = request.args.get('pass')
    if pwd == ADMIN_PASSWORD:
        conn = get_db()
        conn.execute("DELETE FROM products WHERE id=?", (prod_id,))
        conn.commit()
        conn.close()
    return redirect(f'/admin?pass={pwd}')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
