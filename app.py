from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import os
from ml_model.predict import predict_overuse
from datetime import datetime
import csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ----------- DATABASE INIT -----------
def init_db():
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL,
                        profile_icon TEXT NOT NULL
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS appliances (
                        user_id INTEGER,
                        appliance TEXT,
                        count INTEGER,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS usage (
                        user_id INTEGER,
                        appliance TEXT,
                        hours REAL,
                        date TEXT,
                        PRIMARY KEY (user_id, appliance, date),
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS appliance_states (
                        email TEXT,
                        appliance TEXT,
                        state TEXT,
                        PRIMARY KEY (email, appliance)
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS toggle_states (
                        user_id INTEGER,
                        appliance_name TEXT,
                        state INTEGER,
                        PRIMARY KEY (user_id, appliance_name)
                    )''')
        conn.commit()

init_db()

# ----------- LOG USAGE TO CSV -----------
def log_usage_to_csv(gmail, usage_hours):
    file_path = 'data/usage_data.csv'
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    fieldnames = ['Gmail', 'TV', 'Fan', 'AC', 'Heater', 'Fridge', 'Washing Machine',
                  'Iron', 'Computer', 'Light', 'Microwave', 'Others']

    row = {appliance: 0 for appliance in fieldnames}
    row['Gmail'] = gmail
    for appliance, hours in usage_hours.items():
        if appliance in row and hours > 0:
            row[appliance] = hours

    file_exists = os.path.isfile(file_path)
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# ----------- ROUTES -----------

@app.route('/')
def index():
    return redirect('/login')

# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        profile_icon = request.form['profile_icon']

        with sqlite3.connect('users.db') as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (email, username, password, profile_icon) VALUES (?, ?, ?, ?)",
                          (email, username, password, profile_icon))
                conn.commit()
                flash("Registration successful! Please select your appliances.", "success")

                session['email'] = email
                user_id = c.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()[0]
                session['user_id'] = user_id
                session['username'] = username

                return redirect('/appliance_selection')
            except sqlite3.IntegrityError:
                flash("Email already registered. Try logging in.", "danger")

    return render_template('register.html')

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect('users.db') as conn:
            c = conn.cursor()
            c.execute("SELECT id, username, password FROM users WHERE email=?", (email,))
            result = c.fetchone()

            if result and result[2] == password:
                session['email'] = email
                session['user_id'] = result[0]
                session['username'] = result[1]
                return redirect('/dashboard')
            else:
                flash("Invalid email or password.", "danger")

    return render_template('login.html')

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect('/login')

# ---------- APPLIANCE SELECTION ----------
@app.route('/appliance_selection', methods=['GET', 'POST'])
def appliance_selection():
    appliances_list = [
        "Fan", "TV", "Light", "AC", "Fridge", "Washing Machine", "Heater",
        "Microwave", "Computer", "Mobile Charger", "Cooler", "Geyser", "Oven", "Vacuum Cleaner", "Printer"
    ]

    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        user_id = session['user_id']

        with sqlite3.connect('users.db') as conn:
            c = conn.cursor()
            c.execute("DELETE FROM appliances WHERE user_id=?", (user_id,))
            for appliance in appliances_list:
                count = request.form.get(appliance)
                if count and int(count) > 0:
                    c.execute("INSERT INTO appliances (user_id, appliance, count) VALUES (?, ?, ?)",
                              (user_id, appliance, int(count)))
            conn.commit()

        flash("Appliances saved successfully!", "success")
        return redirect('/dashboard')

    return render_template('appliance_selection.html', appliances=appliances_list)

# ---------- DASHBOARD ----------
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    username = session['username']
    email = session['email']
    today = datetime.today().strftime('%Y-%m-%d')
    alerts = []
    tips = []

    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()

        c.execute("SELECT appliance, count FROM appliances WHERE user_id=?", (user_id,))
        appliance_data = c.fetchall()
        appliance_counts = {app: count for app, count in appliance_data}

        c.execute("SELECT appliance, state FROM appliance_states WHERE email=?", (email,))
        state_data = dict(c.fetchall())

        usage_today = {}

        if request.method == 'POST':
            for appliance in appliance_counts.keys():
                hours_str = request.form.get(appliance)
                if hours_str:
                    try:
                        hours = float(hours_str)
                        usage_today[appliance] = hours
                        c.execute('''
                            INSERT INTO usage (user_id, appliance, hours, date)
                            VALUES (?, ?, ?, ?)
                            ON CONFLICT(user_id, appliance, date) DO UPDATE SET hours=excluded.hours
                        ''', (user_id, appliance, hours, today))
                    except ValueError:
                        continue
            conn.commit()

        c.execute("SELECT appliance, hours FROM usage WHERE user_id=? AND date=?", (user_id, today))
        usage_today = dict(c.fetchall())

        if usage_today:
            log_usage_to_csv(email, usage_today)

        try:
            overuse_flag, tips = predict_overuse(usage_today)
            if overuse_flag:
                alerts.append("⚠️ High energy usage detected today!")
        except Exception as e:
            alerts.append(f"Prediction error: {str(e)}")

    return render_template('dashboard.html',
                           username=username,
                           appliance_counts=appliance_counts,
                           appliance_states=state_data,
                           overuse_prediction=alerts[0] if alerts else "No overuse detected.",
                           energy_tip=tips[0] if tips else "Keep up the good work!")

# ---------- UPDATE TOGGLE STATE ----------
@app.route('/update_toggle', methods=['POST'])
def update_toggle():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    data = request.get_json()
    appliance = data['appliance']
    state = 1 if data['state'] else 0
    user_id = session['user_id']

    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO toggle_states (user_id, appliance_name, state)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, appliance_name) DO UPDATE SET state=excluded.state
        ''', (user_id, appliance, state))
        conn.commit()

    # Log usage to CSV only if turned on
    if state == 1:
        now = datetime.now()
        os.makedirs('data', exist_ok=True)
        with open('data/usage_data.csv', 'a') as f:
            f.write(f"{user_id},{appliance},{now.date()},{now.hour},{now.minute}\n")

    return jsonify(success=True)

# ---------- RUN ----------
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
