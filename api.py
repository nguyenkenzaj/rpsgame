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
        return jsonify({
            'turns': player[2],
            'coins': player[3],
            'photo_url': 'https://via.placeholder.com/50'  # Thay bằng URL avatar nếu có
        })
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

@app.route('/random_match', methods=['POST'])
def random_match():
    user_id = request.args.get('user_id')
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT room_code, user_id FROM rooms WHERE opponent_id IS NULL AND user_id != ?', (user_id,))
        room = c.fetchone()
        if room:
            room_code, creator_id = room
            c.execute('UPDATE rooms SET opponent_id = ? WHERE room_code = ?', (user_id, room_code))
            conn.commit()
            c.execute('SELECT points FROM players WHERE user_id = ?', (creator_id,))
            opponent_coins = c.fetchone()[0]
            conn.close()
            return jsonify({
                'roomCode': room_code,
                'opponent_coins': opponent_coins,
                'opponent_photo': 'https://via.placeholder.com/50'
            })
        room_code = str(uuid.uuid4())[:8]
        c.execute('INSERT INTO rooms (room_code, user_id) VALUES (?, ?)', (room_code, user_id))
        conn.commit()
        conn.close()
        return jsonify({
            'roomCode': room_code,
            'opponent_coins': 0,
            'opponent_photo': 'https://via.placeholder.com/50'
        })
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

@app.route('/join_room', methods=['POST'])
def join_room():
    user_id = request.args.get('user_id')
    room_code = request.args.get('room_code')
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT user_id FROM rooms WHERE room_code = ?', (room_code,))
        room = c.fetchone()
        if not room:
            return jsonify({'error': 'Mã phòng không tồn tại!'}), 404
        creator_id = room[0]
        c.execute('UPDATE rooms SET opponent_id = ? WHERE room_code = ?', (user_id, room_code))
        conn.commit()
        c.execute('SELECT points FROM players WHERE user_id = ?', (creator_id,))
        opponent_coins = c.fetchone()[0]
        conn.close()
        return jsonify({
            'roomCode': room_code,
            'opponent_coins': opponent_coins,
            'opponent_photo': 'https://via.placeholder.com/50'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/play_pvp', methods=['POST'])
def play_pvp():
    user_id = request.args.get('user_id')
    choice = request.args.get('choice')
    room_code = request.args.get('room_code')
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT user_id, opponent_id FROM rooms WHERE room_code = ?', (room_code,))
        room = c.fetchone()
        if not room:
            return jsonify({'error': 'Phòng không tồn tại!'}), 404
        creator_id, opponent_id = room
        if user_id != str(creator_id) and user_id != str(opponent_id):
            return jsonify({'error': 'Bạn không ở trong phòng này!'}), 403
        c.execute('SELECT turns, points FROM players WHERE user_id = ?', (user_id,))
        player = c.fetchone()
        if player[0] <= 0:
            return jsonify({
                'error': 'Hết lượt chơi!',
                'turns': player[0],
                'coins': player[1]
            }), 400
        opponent_id = creator_id if user_id != str(creator_id) else opponent_id
        c.execute('SELECT turns, points FROM players WHERE user_id = ?', (opponent_id,))
        opponent = c.fetchone()
        opponent_choice = random.choice(['rock', 'paper', 'scissors'])  # Giả lập lựa chọn đối thủ
        result = determine_winner(choice, opponent_choice)
        turns = player[0] - 1
        coins = player[1]
        opponent_coins = opponent[1]
        if result == 'Thắng':
            coins += 25
            opponent_coins -= 10
        elif result == 'Thua':
            coins -= 10
            opponent_coins += 25
        update_player(int(user_id), turns, coins)
        update_player(int(opponent_id), opponent[0], opponent_coins)
        conn.close()
        return jsonify({
            'user_choice': choice,
            'opponent_choice': opponent_choice,
            'result': result,
            'turns': turns,
            'coins': coins,
            'opponent_coins': opponent_coins
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
