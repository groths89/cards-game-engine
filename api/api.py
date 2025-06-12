import sys
import os
import uuid
import random
import traceback

# Get the absolute path to the project root directory (one level up from 'api')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the project root to sys.path if it's not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from flask import Flask, request, jsonify, session
from flask_cors import CORS
from game_engine.player import Player
from game_engine.game_loop import GameLoop
from game_engine.games.asshole import AssholeGame

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'my_dev_key')

frontend_origins = [
    "http://localhost:3000",
    "https://main.dt7s5ohdz6dup.amplifyapp.com",
    "https://play.gregsgames.social",
]
frontend_origins = [origin for origin in frontend_origins if origin is not None]

CORS(app, resources={r"/*": {"origins": frontend_origins}})

# Dictionary to store the current game state (for a single game for now)
active_games = {}
print(f"DEBUG_GLOBAL_ACTIVE_GAMES_ID_AT_START: {id(active_games)}") # Unique ID of the dictionary object
player_id_map = {}
player_to_room_map = {}

def generate_unique_room_code(length=4):
    characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        if code not in active_games:
            return code

@app.route("/")
def home():
    return jsonify({"message": "Hello from Greg's Games Social Backend!"})

@app.route('/create_room', methods=['POST'])
def create_room():
    player_id = session.get('player_id')
    if not player_id:
        player_id = str(uuid.uuid4())
        session['player_id'] = player_id # Store new ID in session

    data = request.get_json()
    player_name = data.get('player_name', '').strip()
    game_type = data.get('game_type', '').lower()

    if not player_name:
        return jsonify({"success": False, "message": "Player name is required to create a room."}), 400

    room_code = generate_unique_room_code()
    host_id = player_id

    GameClass = None
    if game_type == 'asshole':
        GameClass = AssholeGame
    else:
        return jsonify({'error': 'Invalid game type specified.'}), 400

    try:
        new_game = GameClass(room_code=room_code, host_id=host_id, game_type=game_type)
        host_player_obj = Player(player_id=host_id, name=player_name)
        new_game.add_player(host_player_obj)
        new_game.status = "WAITING_FOR_PLAYERS"
        active_games[room_code] = new_game
        print(f"DEBUG_CREATE_ROOM_ACTIVE_GAMES_ID: {id(active_games)}") # Unique ID of the dictionary object
        print(f"DEBUG_CREATE_ROOM_AFTER_ADD_KEYS: {list(active_games.keys())}") # Confirms content after addition
        player_to_room_map[player_id] = room_code
        game_state_payload = _get_game_state_for_player(new_game, host_id)
        if not game_state_payload:
            raise Exception("Failed to get initial game state for host.")

        return jsonify({
            'message': f'Successfully created room {room_code} as {player_name}',
            'room_code': room_code,
            'player_id': player_id,
            'player_name': player_name,
            'game_state': game_state_payload # Return initial game state
        }), 201
    except Exception as e:
        print(f"Error creating room: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to create room: {str(e)}'}), 500

@app.route('/join_room', methods=['POST'])
def join_room():
    player_id = session.get('player_id')
    if not player_id:
        player_id = str(uuid.uuid4())
        session['player_id'] = player_id

    data = request.get_json()
    room_code = data.get('room_code', '').upper()
    player_name = data.get('player_name', '').strip()

    print(f"Join Lobby Request: Player ID from session: {player_id}, Room: {room_code}, Name: {player_name}")

    if not room_code or len(room_code) != 4:
        return jsonify({'error': 'Room code must be 4 characters.'}), 400
    if not player_name:
        return jsonify({'error': 'Player name cannot be empty'}), 400

    game = active_games.get(room_code)

    if not game:
        return jsonify({'error': f'Room "{room_code}" does not exist.'}), 404

    if game.status not in ["WAITING_FOR_PLAYERS", "WAITING", "LOBBY"]:
        return jsonify({'error': 'Game has already started or is not joinable.'}), 403

    if len(game.players) >= game.MAX_PLAYERS:
        return jsonify({'error': 'This room is full.'}), 400

    existing_player_in_game = next((p for p in game.players if p.player_id == player_id), None)
    if existing_player_in_game:
        if existing_player_in_game.name != player_name:
            existing_player_in_game.name = player_name
            print(f"Player {player_id} rejoining with updated name to {player_name} in room {room_code}.")
        else:
            print(f"Player {player_name} ({player_id}) rejoining room {room_code}.")
        
        player_to_room_map[player_id] = room_code # Ensure map is updated
        game_state_payload = _get_game_state_for_player(game, player_id)
        return jsonify({
            'message': f'Successfully re-joined room {room_code} as {player_name}',
            'room_code': room_code,
            'player_id': player_id,
            'player_name': player_name,
            'game_state': game_state_payload
        }), 200

    if player_id in player_to_room_map and player_to_room_map[player_id] != room_code:
        return jsonify({"error": "Player already in another game. Please leave existing game first."}), 400

    new_player = Player(player_name, player_id=player_id)
    game.add_player(new_player)
    player_to_room_map[player_id] = room_code

    print(f"Player {player_name} ({player_id}) joined room {room_code}. Current players: {game.get_num_players()}")

    game_state_payload = _get_game_state_for_player(game, player_id)
    if not game_state_payload:
        raise Exception("Failed to get initial game state for joining player.")

    return jsonify({
        'message': f'Successfully joined room {room_code} as {player_name}',
        'room_code': room_code,
        'player_id': player_id,
        'player_name': player_name,
        'game_state': game_state_payload
    }), 200

@app.route('/rooms', methods=['GET'])
def get_room():
    lobbies_data = []
    for room_code, game in active_games.items():
        lobbies_data.append({
            "room_code": room_code,
            "game_type": game.game_type,
            "host_name": game.get_player_by_id(game.host_id).name if game.host_id else "Unknown",
            "current_players": game.get_num_players(),
            "max_players": game.MAX_PLAYERS,
            "status": game.status,
            "game_started": game.is_game_started
        })
    return jsonify({
        "success": True,
        "rooms": lobbies_data
    }), 200

# /leave_room endpoint
@app.route('/leave_room', methods=['POST'])
def leave_room():
    data = request.json
    room_code = data.get('room_code', '').upper()
    player_id = data.get('player_id')

    game = active_games.get(room_code)

    if not game:
        return jsonify({'error': 'Game room not found.'}), 404

    player_to_remove = game.get_player_by_id(player_id)
    if not player_to_remove:
        return jsonify({'error': 'Player not found in this room.'}), 404
    
    game.remove_player(player_id) # Assuming you add this method to your Game class
    if player_id in player_to_room_map:
        del player_to_room_map[player_id] # Remove player from map

    # Check if the host left. If the host leaves, delete the room immediately.
    # OR, if the room is now empty, delete it.
    if game.host_id == player_id or game.get_num_players() == 0:
        del active_games[room_code]
        print(f"Room {room_code} deleted because host ({player_id}) left or room is empty.")
        return jsonify({'message': 'You left the room. Room deleted (host left or room empty).'}), 200
    
    # If the host didn't leave and room is not empty, update state
    # If the game is already started, you might want to handle player leaving differently (e.g., mark as inactive)
    if game.is_game_started:
        # Here you might want to check if the current player left, and advance turn
        # Or mark player as 'inactive'
        # For simplicity, we just remove them from game.players list.
        pass # The filtering above already handles removal
    
    print(f"Player {player_id} left room {room_code}. Current players: {[p.name for p in game.players]}")
    return jsonify({'message': 'Successfully left the room.'}), 200

# /delete_room endpoint (only for host)
@app.route('/delete_room', methods=['POST'])
def delete_room():
    data = request.json
    room_code = data.get('room_code', '').upper()
    player_id = data.get('player_id')

    game = active_games.get(room_code)

    if not game:
        return jsonify({'error': 'Game room not found.'}), 404

    # Authorization: Only the host can delete the room
    if game.host_id != player_id:
        return jsonify({'error': 'Only the host can delete the room.'}), 403

    # Delete the room from active_games
    del active_games[room_code]
    players_in_room = [p.player_id for p in game.players]
    for p_id in players_in_room:
        if p_id in player_to_room_map:
            del player_to_room_map[p_id]
    print(f"Host ({player_id}) explicitly deleted room {room_code}.")
    return jsonify({'message': f'Room {room_code} has been successfully deleted.'}), 200

@app.route('/start_game_round', methods=['POST'])
def start_game_round():
    data = request.json
    room_code = data.get('room_code', '').upper()
    player_id = data.get('player_id')

    game = active_games.get(room_code)

    print("\n--- Backend Start Game Round Debug ---")
    print(f"Request for Room: {room_code}")
    print(f"Player ID from Frontend (sent in POST body): {player_id}")
    print(f"Stored Game Host ID (from active_games[{room_code}]): {game.host_id if game else 'N/A'}")
    print(f"Comparison: {game.host_id == player_id if game else 'N/A'}")
    print("--- End Backend Start Game Round Debug ---\n")

    if not game:
        return jsonify({'error': 'Game room not found.'}), 404 # Not Found
    
    if game.host_id != player_id:
        return jsonify({'error': 'Only the host can start the game.'}), 403

    try:
        if len(game.players) < game.MIN_PLAYERS:
            return jsonify({'error': f'Need at least {game.MIN_PLAYERS} players to start. Current: {len(game.players)}'}), 400
        if len(game.players) > game.MAX_PLAYERS:
            return jsonify({'error': f'Cannot exceed {game.MAX_PLAYERS} players. Current: {len(game.players)}'}), 400
        if game.is_game_started:
            return jsonify({'error': 'Game has already started in this room.'}), 400
        
        game.start_game()

        game_state_payload = _get_game_state_for_player(game, player_id)
        if not game_state_payload:
            raise Exception("Failed to get game state after starting game.")

        return jsonify({
            'message': 'Game round started!',
            'room_code': room_code,
            'current_player': game.get_current_player().name if game.get_current_player() else None,
            'game_state': game_state_payload,
            'player_hands_dealt': True
        }), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred while starting the game: {str(e)}'}), 500

@app.route('/play_cards', methods=['POST'])
def play_cards():
    data = request.get_json()
    room_code = data.get('room_code', '').upper()
    player_id = data.get('player_id')
    cards_to_play_data = data.get('cards', [])
    game = active_games.get(room_code)

    if not game:
        return jsonify({'error': 'Game room not found.'}), 404
    
    if game.status != "IN_PROGRESS":
        return jsonify({'error': 'Game is not in progress.'}), 400

    try:
        game.play_cards(player_id, cards_to_play_data)

        game_state_payload = _get_game_state_for_player(game, player_id)
        if not game_state_payload:
            raise Exception("Failed to get game state after playing cards.")

        return jsonify({'message': 'Card(s) played', 'game_state': game_state_payload}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error playing cards: {e}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    
@app.route('/pass_turn', methods=['POST'])
def pass_turn():
    data = request.get_json()
    room_code = data.get('room_code', '').upper()
    player_id = data.get('player_id')

    game = active_games.get(room_code)

    if not game:
        return jsonify({'error': 'Game room not found.'}), 404

    if game.status != "IN_PROGRESS":
        return jsonify({'error': 'Game is not in progress.'}), 400

    try:
        game.pass_turn(player_id)    

        game_state_payload = _get_game_state_for_player(game, player_id)
        if not game_state_payload:
            raise Exception("Failed to get game state after passing turn.")
        return jsonify({'message': 'Turn passed', 'game_state': game_state}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error passing turn: {e}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

# Helper to get the current game state for a specific player
def _get_game_state_for_player(game, player_id):
    player = next((p for p in game.players if str(p.player_id) == player_id), None)
    if not player:
        return None
    all_players_data = [
        {'name': p.name, 'id': p.player_id, 'is_active': p.is_active, 'hand_size': len(p.get_hand().cards), 'rank': p.rank}
        for p in game.players
    ]

    player_hand_cards_data = [card.to_dict() for card in player.get_hand().cards]

    pile_cards_data = [card.to_dict() for card in game.pile]

    current_player_name = game.get_current_player().name if game.get_current_player() else None
    current_turn_player_id = game.get_current_player().player_id if game.get_current_player() else None

    final_rankings = sorted(game.players, key=lambda p: p.rank if p.rank is not None else float('inf'))
    rankings_data = {
        p.name: game.get_rank_name(p.rank, len(game.players))
        for p in final_rankings if p.rank is not None
    }

    last_played_cards_data = [card.to_dict() for card in game.last_played_cards] if hasattr(game, 'last_played_cards') else []

    return {
        'room_code': game.room_code,
        'game_type': game.game_type, #Added
        'host_id': game.host_id,
        'current_player': current_player_name,
        'current_turn_player_id': current_turn_player_id,
        'pile': pile_cards_data,
        'your_hand': player_hand_cards_data,
        'all_players_data': all_players_data,
        'num_active_players': game.get_num_active_players(),
        'is_game_over': game.is_game_over,
        'rankings': rankings_data,
        'game_started': game.is_game_started,
        'MIN_PLAYERS': game.MIN_PLAYERS,
        'MAX_PLAYERS': game.MAX_PLAYERS,
        'last_played_cards': last_played_cards_data,
        'game_status': game.status
    }

@app.route('/game_state', methods=['GET'])
def get_current_game_state():
    room_code = request.args.get('room_code', '').upper()
    player_id = request.args.get('player_id', '')
    game_type = request.args.get('game_type', '').lower()

    game = active_games.get(room_code)

    if not game:
        traceback.print_exc()
        return jsonify({'error': 'Game room not found.'}), 404

    game_state_data = _get_game_state_for_player(game, player_id)

    if not game_state_data:
        return jsonify({'error': 'Player not found in this game or invalid game state.'}), 404
    return jsonify(game_state_data), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 8080))