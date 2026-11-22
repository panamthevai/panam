import os
import sqlite3
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super_secret_key_123")

# --- 1. DATABASE CONNECTION (Cloud PostgreSQL அல்லது Local SQLite) ---
DATABASE_URL = os.environ.get("DATABASE_URL") # Render/Supabase Postgres URL

def get_db_connection():
    if DATABASE_URL:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn, True
    else:
        conn = sqlite3.connect('ecommerce.db')
        conn.row_factory = sqlite3.Row
        return conn, False

def init_db():
    conn, is_pg = get_db_connection()
    cur = conn.cursor()
    id_type = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    # Orders அட்டவணை (Table) உருவாக்குதல்
    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS orders (
            id {id_type},
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            items TEXT NOT NULL,
            total_amount REAL NOT NULL,
            utr_number TEXT NOT NULL,
            status TEXT DEFAULT 'Order Placed'
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

# --- 2. BACKGROUND EMAIL NOTIFICATION ---
def send_email_task(customer_name, customer_email, order_id, total_amount, items):
    sender_email = os.environ.get("SENDER_EMAIL")
    app_password = os.environ.get("EMAIL_PASSWORD")
    
    if not sender_email or not app_password:
        print("Email credentials not set in Environment Variables.")
        return

    recipients = [sender_email]
    if customer_email:
        recipients.append(customer_email)

    subject = f"ஆர்டர் உறுதிப்படுத்தப்பட்டது! - Order #{order_id}"
    body = f"""வணக்கம் {customer_name},

உங்கள் ஆர்டர் வெற்றிகரமாகப் பதிவு செய்யப்பட்டுள்ளது!

ஆர்டர் எண் (Order ID): #{order_id}
பொருட்கள்: {items}
மொத்த தொகை: ₹{total_amount}
தற்போதைய நிலை: Order Placed

உங்கள் ஆர்டர் நிலையை இணையதளத்தில் 'Track Order' மூலம் தெரிந்துகொள்ளலாம்.
நன்றி!
"""
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipients, msg.as_string())
        server.quit()
        print(f"Email sent for Order #{order_id}")
    except Exception as e:
        print(f"Email Error: {e}")

# --- 3. ROUTES (பக்கங்கள்) ---

@app.route('/')
def index():
    return render_template('index.html')

# ஆர்டர் பதிவு செய்தல் (Checkout & Place Order)
@app.route('/place_order', methods=['POST'])
def place_order():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    items = request.form.get('items')
    total_amount = request.form.get('total_amount')
    utr = request.form.get('utr')

    conn, is_pg = get_db_connection()
    cur = conn.cursor()
    placeholder = "%s" if is_pg else "?"

    query = f'''
        INSERT INTO orders (customer_name, customer_email, phone, address, items, total_amount, utr_number)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
    '''
    if is_pg:
        query += " RETURNING id"

    cur.execute(query, (name, email, phone, address, items, total_amount, utr))
    
    if is_pg:
        new_order_id = cur.fetchone()['id']
    else:
        new_order_id = cur.lastrowid

    conn.commit()
    cur.close()
    conn.close()

    # தளம் மெதுவாகாமல் இருக்க பின்னணியில் (Background) மெயில் அனுப்புதல்
    threading.Thread(
        target=send_email_task,
        args=(name, email, new_order_id, total_amount, items)
    ).start()

    return render_template('order_success.html', order_id=new_order_id, name=name)

# வாடிக்கையாளர் ஆர்டர் நிலை அறிதல் (Order Tracking)
@app.route('/track', methods=['GET', 'POST'])
def track_order():
    order = None
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        phone = request.form.get('phone')
        
        conn, is_pg = get_db_connection()
        cur = conn.cursor()
        placeholder = "%s" if is_pg else "?"
        
        cur.execute(f"SELECT * FROM orders WHERE id = {placeholder} AND phone = {placeholder}", (order_id, phone))
        order = cur.fetchone()
        cur.close()
        conn.close()
        
        if not order:
            flash("தவறான Order ID அல்லது மொபைல் எண்!")

    return render_template('track.html', order=order)

# Admin Panel - அனைத்து ஆர்டர்களையும் பார்க்க
@app.route('/admin')
def admin_panel():
    conn, is_pg = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', orders=orders)

# Admin Status Update (Packed / Shipped / Delivered)
@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    new_status = request.form.get('status')
    conn, is_pg = get_db_connection()
    cur = conn.cursor()
    placeholder = "%s" if is_pg else "?"
    
    cur.execute(f"UPDATE orders SET status = {placeholder} WHERE id = {placeholder}", (new_status, order_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)

