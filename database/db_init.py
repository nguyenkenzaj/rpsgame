import sqlite3
import os

def init_db():
    # Đảm bảo thư mục rps_game tồn tại
    os.makedirs('rps_game', exist_ok=True)
    # Sử dụng đường dẫn tương đối chính xác
    db_path = os.path.join('rps_game', 'rps.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (
                 user_id INTEGER PRIMARY KEY,
                 username TEXT,
                 turns INTEGER,
                 coins INTEGER,
                 energy INTEGER,
                 last_reset TEXT
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                 user_id INTEGER,
                 task_id TEXT,
                 completed INTEGER,
                 FOREIGN KEY(user_id) REFERENCES players(user_id)
                 )''')
    conn.commit()
    conn.close()
