from flask import Flask, jsonify, request
from flask_cors import CORS
from database.db_operations import get_player, update_player, get_leaderboard, reset_daily_turns
import sqlite3
import random
import uuid
import os

app = Flask(__name__)
CORS(app)
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'rps.db')

@app.route('/player', methods=['GET'])
def get_player_data():
    user_id = request.args.get('user_id')
    username = 'Unknown'
    try:
        player = get_player(int(user_id), username)
        return jsonify({'turns': player[2], 'coins': player[3]})  # Map points to coins
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/play', methods=['POST'])
def play_game():
    user_id = request.args.get('user_id')
    choice = request.args.get('choice')
    username = 'Unknown'
    try:
        player = get_player(int(user_id), username)
        if player[2] <= 0:
            return jsonify({
                'error': 'Hết lượt chơi!',
                'turns': player[2],
                'coins': player[3]
            }), 400
        bot_choice = random.choice(['rock', 'paper', 'scissors'])
        result = determine_winner(choice, bot_choice)
        coins = player[3]
        turns = player[2] - 1
        if result == 'Thắng':
            coins += 25
        update_player(int(user_id), turns, coins)
        return jsonify({
            'user_choice': choice,
            'bot_choice': bot_choice,
            'result': result,
            'turns': turns,
            'coins': coins
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    try:
        players = get_leaderboard()
        return jsonify([{'name': player[1], 'coins': player[3]} for player in players])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/create_room', methods=['POST'])
def create_room():
    user_id = request.args.get('user_id')
    try:
        room_code = str(uuid.uuid4())[:8]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO rooms (room_code, user_id) VALUES (?, ?)', (room_code, user_id))
        conn.commit()
        conn.close()
        return jsonify({'roomCode': room_code})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def determine_winner(user_choice, bot_choice):
    if user_choice == bot_choice:
        return 'Hòa'
    if (user_choice == 'rock' and bot_choice == 'scissors') or \
       (user_choice == 'paper' and bot_choice == 'rock') or \
       (user_choice == 'scissors' and bot_choice == 'paper'):
        return 'Thắng'
    return 'Thua'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
