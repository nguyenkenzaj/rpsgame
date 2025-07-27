import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'rps.db')

def get_player(user_id, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
    player = c.fetchone()
    if not player:
        c.execute('INSERT INTO players (user_id, username, turns, points, last_reset) VALUES (?, ?, ?, ?, ?)',
                  (user_id, username, 10, 0, '2025-07-27T14:59:00'))
        conn.commit()
        player = (user_id, username, 10, 0, '2025-07-27T14:59:00')
    conn.close()
    return player

def update_player(user_id, turns, coins):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE players SET turns = ?, points = ? WHERE user_id = ?',
              (turns, coins, user_id))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM players ORDER BY points DESC LIMIT 10')
    players = c.fetchall()
    conn.close()
    return players

def reset_daily_turns(user_id, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE players SET turns = 10, last_reset = ? WHERE user_id = ?',
              ('2025-07-27T14:59:00', user_id))
    conn.commit()
    conn.close()
