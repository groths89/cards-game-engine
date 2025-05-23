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
            if isinstance(game, GameClass) and not game.is_game_started:
                pass
            else:
                return jsonify({'error': f'Room "{room_code}" already exists and is in use.'}), 409 # Conflict
        else:
            print(f"Creating new {game_type} game for room: {room_code}")
            game = GameClass(players=[])
            active_games[room_code] = game
            game.room_code = room_code

    # --- Handle 'Join' Action ---
    elif action == 'join':
        if not game:
            return jsonify({'error': f'Room "{room_code}" does not exist.'}), 404 # Not Found
        if not isinstance(game, GameClass):
            return jsonify({'error': f'Room "{room_code}" is hosting a different game type ({game.__class__.__name__}).'}), 409 # Conflict
        if game.is_game_started:
            return jsonify({'error': 'Game has already started in this room. Cannot join.'}), 403 # Forbidden
        
    # -- Common Player Joining Logic (for both create and join) ---
    if any(p.name == player_name for p in game.players):
        return jsonify({'error': f'Name "{player_name}" is already taken in this room.'}), 400
    if len(game.players) >= 10:
        return jsonify({'error': 'This room is full.'}), 400
    
    player_id = str(uuid.uuid4())
    new_player = Player(player_name, player_id=player_id)
    game.players.append(new_player)
    player_id_map[player_id] = player_name

    print(f"Player {player_name} ({player_id}) {action}ed room {room_code}. Current players: {[p.name for p in game.players]}")

    return jsonify({
        'message': f'Successfully {action}ed room {room_code} as {player_name}',
        'game_id': room_code,
        'player_id': player_id,
        'player_name': player_name
    }), 200

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
    data.request.get_json()
    room_code = data.get('room_code', '').upper()

    game = active_games.get(room_code)
    if not game:
        return jsonify({'error': 'Game room not found.'}), 404 # Not Found
    
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
        'current_player': current_player_name,
        'pile': pile_cards_str,
        'your_hand': player_hand_cards_str,
        'all_player_names': [p.name for p in game.players],
        'num_active_players': game.get_num_active_players(),
        'is_game_over': game.is_game_over(),
        'rankings': rankings_data,
        'game_started': game.is_game_started
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