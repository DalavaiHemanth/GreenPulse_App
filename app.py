from flask import Flask
import sqlite3

app = Flask(__name__)
app.secret_key = 'greenpulse-secret-key'  # Required for session management

def init_db():
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()

        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gmail TEXT UNIQUE,
                username TEXT,
                password TEXT,
                profile_icon TEXT
            )
        ''')

        # Create appliances table
        c.execute('''
            CREATE TABLE IF NOT EXISTS appliances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                appliance_name TEXT,
                count INTEGER,
                usage_hours REAL DEFAULT 0,
                is_on INTEGER DEFAULT 0
            )
        ''')

        conn.commit()

# ✅ Run this function once to initialize the DB
init_db()

# Simple route to confirm the app is running
@app.route('/')
def home():
    return "✅ GreenPulse Server Running!"

if __name__ == '__main__':
    app.run(debug=True)
