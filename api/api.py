import sys
import os

# Get the absolute path to the project root directory (one level up from 'api')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the project root to sys.path if it's not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from flask import Flask, request, jsonify
from game_engine.player import Player
from game_engine.game_loop import GameLoop
from game_engine.games.asshole import AssholeGame

app = Flask(__name__)

# Dictionary to store the current game state (for a single game for now)
game_state = {}
game_loop = {}

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

@app.route('/game_state', methods=['GET'])
def get_current_game_state():
    if 'game' not in game_state:
        return jsonify({'error': 'No game in progress'}), 400
    
    game = game_state['game']
    current_state = {
        'current_player': game.get_current_player().name if game.get_current_player() else None,
        'pile': [card.to_string() for card in game.pile],
        'hands': {p.name: [card.to_string() for card in p.get_hand().cards] for p in game.players},
        'is_game_over': game.is_game_over(),
        'rankings': {p.name: p.rank for p in sorted(game.players, key=lambda x: x.rank if x.rank is not None else float('inf'))}
    }
    return jsonify(current_state), 200

if __name__ == '__main__':
    app.run(debug=True)