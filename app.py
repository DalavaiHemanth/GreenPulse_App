from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Ensure DB exists
def init_db():
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                location TEXT,
                profile_icon TEXT
            )
        ''')
        conn.commit()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        location = request.form['location']
        password = request.form['password']
        profile_icon = request.form['profile_icon']

        with sqlite3.connect('users.db') as conn:
            c = conn.cursor()
            try:
                c.execute('INSERT INTO users (email, username, password, location, profile_icon) VALUES (?, ?, ?, ?, ?)',
                          (email, username, password, location, profile_icon))
                conn.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect('/login')
            except sqlite3.IntegrityError:
                flash('Email already exists.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect('users.db') as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
            user = c.fetchone()
            if user:
                session['user_id'] = user[0]
                session['username'] = user[2]
                session['profile_icon'] = user[5]
                flash('Login successful!', 'success')
                return redirect('/dashboard')
            else:
                flash('Invalid email or password.', 'danger')
                return redirect('/login')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'danger')
        return redirect('/login')
    return f"Welcome {session['username']} to your dashboard!"

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect('/login')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
