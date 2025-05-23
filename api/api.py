import sys
import os
import uuid

# Get the absolute path to the project root directory (one level up from 'api')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the project root to sys.path if it's not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from flask import Flask, request, jsonify
from flask_cors import CORS
from game_engine.player import Player
from game_engine.game_loop import GameLoop
from game_engine.games.asshole import AssholeGame

app = Flask(__name__)
CORS(app)

# Dictionary to store the current game state (for a single game for now)
active_games = {}
player_id_map = {}
game_state = {}
game_loop = {}

@app.route('/manage_game_room', methods=['POST'])
def manage_game_room():
    data = request.get_json()
    room_code = data.get('room_code', '').upper()
    player_name = data.get('player_name', '').strip()
    game_type = data.get('game_type', '').lower()
    action = data.get('action')
    player_id = str(uuid.uuid4())
    new_player = Player(player_name, player_id=player_id)

    print("--- Backend Manage Room Debug ---")
    print(f"Action: {action}, Room Code: {room_code}, Player Name: {player_name}, Game Type: {game_type}")
    print(f"Generated Player ID for THIS manage_game_room request: {player_id}")
    print("--- End Backend Manage Room Debug ---")

    # --- Basic Validation ---
    if not room_code or len(room_code) != 4:
        return jsonify({'error': 'Room code must be 4 characters.'}), 400
    if not player_name:
        return jsonify({'error': 'Player name cannot be empty'}), 400
    if action not in ['create', 'join']:
        return jsonify({'error': 'Invalid action specified. Must be "create" or "join".'}), 400
    
    GameClass = None
    if game_type == 'asshole':
        GameClass = AssholeGame
    else:
        return jsonify({'error': 'Invalid game type specified.'})
    
    game = active_games.get(room_code)

    # --- Handle 'Create' Action ---
    if action == 'create':
        if game:
            # If game already exists, it must match the requested type and not be started
            return jsonify({'error': f'Room "{room_code}" already exists and is in use.'}), 409 # Conflict
        else:
            game = GameClass(players=[])
            active_games[room_code] = game
            game.room_code = room_code
            game.host_id = player_id
            print(f"Backend: Host ID set for room {room_code}: {game.host_id}")
            print(f"Creating new {game_type} game for room: {room_code}")

    # --- Handle 'Join' Action ---
    elif action == 'join':
        if not game:
            return jsonify({'error': f'Room "{room_code}" does not exist.'}), 404 # Not Found
        if not isinstance(game, GameClass):
            return jsonify({'error': f'Room "{room_code}" is hosting a different game type ({game.__class__.__name__}).'}), 409 # Conflict
        if game.is_game_started:
            return jsonify({'error': 'Game has already started in this room. Cannot join.'}), 403 # Forbidden
        
    # -- Common Player Joining Logic (for both create and join) ---
    # Check if player name is already taken in the room
    if any(p.name == player_name for p in game.players):
        # If the player ID matches an existing player, it means they're rejoining
        existing_player = next((p for p in game.players if p.player_id == player_id), None)
        if existing_player and existing_player.name == player_name:
            # Player is rejoining with the same ID and name, allow it
            print(f"Player {player_name} ({player_id}) rejoining room {room_code}.")
            # You might want to update their session or simply confirm their presence
            return jsonify({
                'message': f'Successfully re-joined room {room_code} as {player_name}',
                'game_id': room_code,
                'player_id': player_id,
                'player_name': player_name
            }), 200
        else:
            # Name taken by a different player or same ID with different name (unlikely for uuid4)
            return jsonify({'error': f'Name "{player_name}" is already taken in this room.'}), 400

    # Check for room capacity
    if len(game.players) >= game.MAX_PLAYERS: # Use game.MAX_PLAYERS
        return jsonify({'error': 'This room is full.'}), 400
    
    if new_player.player_id in [p.player_id for p in game.players]:
        return jsonify({'error': 'Player with this ID already in room'}), 400
    
    if action == 'create' and game.host_id == new_player.player_id:
        pass    
    

    game.players.append(new_player)
    player_id_map[player_id] = player_name

    print(f"Player {player_name} ({player_id}) {action}ed room {room_code}. Current players: {[p.name for p in game.players]}")

    return jsonify({
        'message': f'Successfully {action}ed room {room_code} as {player_name}',
        'game_id': room_code,
        'player_id': player_id,
        'player_name': player_name
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

    # Remove player from the game's players list
    player_removed = False
    # Filter out the player by ID
    game.players = [p for p in game.players if p.player_id != player_id]
    
    if not player_removed: # This logic needs adjustment based on how game.players is structured
        # Assuming game.players is a list of Player objects directly
        initial_player_count = len(game.players)
        game.players = [p for p in game.players if p.player_id != player_id]
        if len(game.players) < initial_player_count:
            player_removed = True
        else:
            return jsonify({'error': 'Player not found in this room.'}), 404

    # Check if the host left. If the host leaves, delete the room immediately.
    # OR, if the room is now empty, delete it.
    if game.host_id == player_id or not game.players:
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
    print(f"Host ({player_id}) explicitly deleted room {room_code}.")
    return jsonify({'message': f'Room {room_code} has been successfully deleted.'}), 200


@app.route('/start_game', methods=['POST'])
def start_game():
    data = request.get_json()
    player_names = data.get('players', [])
    if not player_names or len(player_names) < 4:
        return jsonify({'error': 'Must have at least 4 players'}), 400
    
    players = [Player(name) for name in player_names]
    game = AssholeGame(players)
    game_state['game'] = game
    game_loop['loop'] = GameLoop(game)
    game_state['current_player'] = game.get_current_player().name if game.get_current_player() else None
    game_state['pile'] = [card.to_string() for card in game.pile]
    game_state['hands'] = {player.name: [card.to_string() for card in player.get_hand().cards] for player in players}
    game_state['is_game_over'] = game.is_game_over()

    return jsonify({'message': 'Game started', 'game_state': game_state}), 200

@app.route('/start_game_round', methods=['POST'])
def start_game_round():
    data = request.json
    room_code = data.get('room_code', '').upper()
    player_id = data.get('player_id')
    player_id_from_frontend = data.get('player_id') 

    game = active_games.get(room_code)

    print("\n--- Backend Start Game Round Debug ---")
    print(f"Request for Room: {room_code}")
    print(f"Player ID from Frontend (sent in POST body): {player_id_from_frontend}")
    print(f"Stored Game Host ID (from active_games[{room_code}]): {game.host_id if game else 'N/A'}")
    print(f"Comparison: {game.host_id == player_id_from_frontend if game else 'N/A'}")
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

        return jsonify({
            'message': 'Game round started!',
            'game_id': room_code,
            'current_player': game.get_current_player().name if game.get_current_player() else None,
            'player_hands_dealt': True
        }), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred while starting the game: {str(e)}'}), 500

@app.route('/play_card', methods=['POST'])
def play_card():
    if 'game' not in game_state:
        return jsonify({'error': 'No game in progress'}), 400
    
    data = request.get_json()
    player_name = data.get('player')
    cards_to_play_str = data.get('cards', [])
    game = game_state['game']
    player = next((p for p in game.players if p.name == player_name), None)

    if not player:
        return jsonify({'error': f'Player {player_name} not found'}), 404
    
    cards_to_play = [game.card.string_to_card(card_str) for card_str in cards_to_play_str]

    try:
        is_valid = game.play_turn(player, cards_to_play)
        if is_valid:
            game.handle_player_out()
            game_state['current_player'] = game.get_current_player().name if game.get_current_player() else None
            game_state['pile'] = [card.to_string() for card in game.pile]
            game_state['hands'] = {p.name: [card.to_string() for card in p.get_hand().cards] for p in game.players}
            game_state['is_game_over'] = game.is_game_over()
            return jsonify({'message': 'Card(s) played', 'game_state': game_state}), 200
        else:
            return jsonify({'error': 'Invalid play'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
@app.route('/pass_turn', methods=['POST'])
def pass_turn():
    if 'game' not in game_state:
        return jsonify({'error': 'No game in progress'}), 400
    
    data = request.get_json()
    player_name = data.get('player')
    game = game_state['game']
    player = next((p for p in game.players if p.name == player_name), None)

    if not player:
        return jsonify({'error': f'Player {player_name} not found'}), 404
    
    game.pass_turn(player)
    game_state['current_player'] = game.get_current_player().name if game.get_current_player() else None
    game_state['pile'] = [card.to_string() for card in game.pile]
    game_state['is_game_over'] = game.is_game_over()
    return jsonify({'message': 'Turn passed', 'game_state': game_state}), 200

# Helper to get the current game state for a specific player
def _get_game_state_for_player(game, player_id):
    player = next((p for p in game.players if p.player_id == player_id), None)
    if not player:
        return None
    
    all_players_data = [
        {'name': p.name, 'id': p.player_id, 'is_active': p.is_active, 'hand_size': len(p.get_hand().cards), 'rank': p.rank}
        for p in game.players
    ]

    player_hand_cards_str = [card.to_string() for card in player.get_hand().cards]

    pile_cards_str = [card.to_string() for card in game.pile]

    current_player_name = game.get_current_player().name if game.get_current_player() else None

    final_rankings = sorted(game.players, key=lambda p: p.rank if p.rank is not None else float('inf'))
    rankings_data = {
        p.name: game.get_rank_name(p.rank, len(game.players))
        for p in final_rankings if p.rank is not None
    }

    return {
        'room_code': game.room_code,
        'host_id': game.host_id,
        'current_player': current_player_name,
        'pile': pile_cards_str,
        'your_hand': player_hand_cards_str,
        'all_players_data': all_players_data,
        'num_active_players': game.get_num_active_players(),
        'is_game_over': game.is_game_over(),
        'rankings': rankings_data,
        'game_started': game.is_game_started,
        'MIN_PLAYERS': game.MIN_PLAYERS,
        'MAX_PLAYERS': game.MAX_PLAYERS,
    }

@app.route('/game_state', methods=['GET'])
def get_current_game_state():
    room_code = request.args.get('room_code', '').upper()
    player_id = request.args.get('player_id', '')
    game_type = request.args.get('game_type', '').lower()

    game = active_games.get(room_code)

    if not game:
        return jsonify({'error': 'Game room not found.'}), 404

    game_state_data = _get_game_state_for_player(game, player_id)

    if not game_state_data:
        return jsonify({'error': 'Player not found in this game or invalid game state.'}), 404
    
    return jsonify(game_state_data), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)