from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import os
import json
import pandas as pd
from ml_model.predict import get_prediction_and_tip
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DB_FILE = 'users.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        gmail TEXT UNIQUE,
                        username TEXT,
                        password TEXT,
                        profile_icon TEXT
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS appliances (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        appliance TEXT,
                        count INTEGER,
                        toggle TEXT DEFAULT 'off'
                    )''')
        conn.commit()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        gmail = request.form.get('gmail')
        password = request.form.get('password')

        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT id, username, profile_icon FROM users WHERE gmail=? AND password=?", (gmail, password))
            row = c.fetchone()
            if row:
                session['user_id'] = row[0]
                session['username'] = row[1]
                session['profile_icon'] = row[2]
                return redirect('/dashboard')
            else:
                flash('Invalid credentials', 'error')
                return redirect('/login')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        gmail = request.form.get('gmail')
        username = request.form.get('username')
        password = request.form.get('password')
        profile_icon = request.form.get('profile_icon', 'icon1.png')

        if not gmail or not username or not password:
            flash('Please fill all required fields', 'error')
            return redirect('/register')

        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE gmail=?", (gmail,))
            if c.fetchone():
                flash('Email already registered', 'error')
                return redirect('/register')

            c.execute("INSERT INTO users (gmail, username, password, profile_icon) VALUES (?, ?, ?, ?)",
                      (gmail, username, password, profile_icon))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect('/login')

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    username = session.get('username', 'User')
    profile_icon = session.get('profile_icon', 'default.png')

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT appliance, toggle FROM appliances WHERE user_id=?", (user_id,))
        appliance_rows = c.fetchall()
        appliance_states = {row[0]: row[1] for row in appliance_rows}

    # ML Prediction
    overuse_alert = ""
    energy_tip = ""
    try:
        # Prepare user_data dict for prediction
        user_data = {}
        for appliance, state in appliance_states.items():
            # Assuming 'on' means usage of 5 hours, 'off' means 0 hours (example logic)
            user_data[appliance] = 5 if state == 'on' else 0

        pred, tip = get_prediction_and_tip(user_data)
        if pred == "⚠️ Overuse Detected":
            overuse_alert = "Overuse Detected! Please reduce usage."
        energy_tip = tip
    except Exception as e:
        energy_tip = "Keep up the good work!"

    # Weather Alert
    weather_alert = ""
    try:
        api_key = "9bf46d04e890b1c1f39d7100cf2cbdf3"
        city = "Hyderabad"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
        response = requests.get(url)
        weather_data = response.json()
        weather = weather_data['weather'][0]['main']
        if weather in ['Rain', 'Thunderstorm']:
            weather_alert = f"⚠️ Bad weather detected: {weather}. Consider turning off unused appliances."
    except:
        pass

    return render_template(
        "dashboard.html",
        username=username,
        profile_icon=profile_icon,
        appliance_states=appliance_states,
        overuse_alert=overuse_alert,
        energy_tip=energy_tip,
        weather_alert=weather_alert
    )

@app.route('/update_toggle', methods=['POST'])
def update_toggle():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    appliance = data.get('appliance')
    state = data.get('state')

    if not appliance or not state:
        return jsonify({'error': 'Invalid data'}), 400

    user_id = session['user_id']
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("UPDATE appliances SET toggle=? WHERE user_id=? AND appliance=?", (state, user_id, appliance))
        conn.commit()

    return jsonify({'status': 'success'})

if __name__ == "__main__":
    try:
        init_db()
    except Exception as e:
        print("Database initialization error:", e)

    app.run(debug=True)
