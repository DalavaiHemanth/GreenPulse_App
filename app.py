from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import sqlite3
import os
import json

app = Flask(__name__)
app.secret_key = 'greenpulse_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DATABASE = 'users.db'

class User(UserMixin):
    def __init__(self, id_, email, username, profile_icon):
        self.id = id_
        self.email = email
        self.username = username
        self.profile_icon = profile_icon

def get_user_by_email(email):
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT id, email, username, password, profile_icon FROM users WHERE email = ?", (email,))
        row = c.fetchone()
        if row:
            return User(row[0], row[1], row[2], row[4]), row[3]
    return None, None

@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT id, email, username, profile_icon FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        if row:
            return User(row[0], row[1], row[2], row[3])
    return None

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        profile_icon = request.form['profile_icon']

        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE email = ?", (email,))
            if c.fetchone():
                flash("Email already exists")
                return render_template('register.html')

            c.execute("INSERT INTO users (email, username, password, profile_icon) VALUES (?, ?, ?, ?)",
                      (email, username, password, profile_icon))
            conn.commit()

        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        user, db_password = get_user_by_email(email)
        if user and db_password == password_input:
            login_user(user)

            with sqlite3.connect(DATABASE) as conn:
                c = conn.cursor()
                c.execute("SELECT appliances FROM appliances WHERE user_id = ?", (user.id,))
                row = c.fetchone()

                if not row or not row[0] or row[0] == '{}':
                    return redirect(url_for('appliance_selection'))

                session['appliances'] = json.loads(row[0])

            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password")
    return render_template('login.html')

@app.route('/appliance_selection', methods=['GET', 'POST'])
@login_required
def appliance_selection():
    appliance_list = ['Fan', 'Light', 'TV', 'AC', 'Fridge', 'Heater', 'Washer', 'Dryer', 'Microwave', 'Computer']

    if request.method == 'POST':
        appliance_dict = {
            appliance: 'off'
            for appliance in appliance_list
            if request.form.get(appliance) and request.form.get(appliance).isdigit() and int(request.form.get(appliance)) > 0
        }

        session['appliances'] = appliance_dict

        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("REPLACE INTO appliances (user_id, appliances) VALUES (?, ?)",
                      (current_user.id, json.dumps(appliance_dict)))
            conn.commit()

        return redirect(url_for('dashboard'))

    return render_template('appliance_selection.html', appliances=appliance_list)

@app.route('/dashboard')
@login_required
def dashboard():
    appliances = session.get('appliances')
    if not appliances:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT appliances FROM appliances WHERE user_id = ?", (current_user.id,))
            row = c.fetchone()
            if row and row[0]:
                appliances = json.loads(row[0])
                session['appliances'] = appliances
            else:
                return redirect(url_for('appliance_selection'))

    return render_template('dashboard.html',
                           appliances=appliances,
                           username=current_user.username,
                           profile_icon=current_user.profile_icon)

@app.route('/update_toggle', methods=['POST'])
@login_required
def update_toggle():
    data = request.json
    appliance = data.get('appliance')
    state = data.get('state')

    if not appliance or state not in ['on', 'off']:
        return jsonify({'error': 'Invalid data'}), 400

    appliances = session.get('appliances', {})
    appliances[appliance] = state
    session['appliances'] = appliances

    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("REPLACE INTO appliances (user_id, appliances) VALUES (?, ?)",
                  (current_user.id, json.dumps(appliances)))
        conn.commit()

    return jsonify({'success': True}), 200

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('login'))

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL,
                        profile_icon TEXT NOT NULL
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS appliances (
                        user_id INTEGER PRIMARY KEY,
                        appliances TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
        conn.commit()

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    else:
        init_db()

    port = int(os.environ.get("PORT", 5000))  # <== 🔧 Use dynamic port for Render
    app.run(host='0.0.0.0', port=port, debug=True)
