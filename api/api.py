import eventlet
eventlet.monkey_patch()

from datetime import datetime, timezone
import uuid
import logging
import os
import sys
import random
import time
import threading
import traceback

def configure_local_dev_environment():
    """
    Sets up environment variables for local development if not already set.
    This function should NOT be called in a deployed environment.
    """
    if not os.environ.get('ENVIRONMENT'):
        print("Local development environment detected. Setting local variables.")
        os.environ['ENVIRONMENT'] = 'local'
        os.environ['USERS_TABLE'] = 'gregs-games-users-local'
        os.environ['GAME_HISTORY_TABLE'] = 'gregs-games-history-local'
        os.environ['AWS_ACCESS_KEY_ID'] = 'dummy'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'dummy'
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        os.environ['DYNAMODB_ENDPOINT'] = 'http://localhost:8000'
        os.environ['COGNITO_USER_POOL_ID'] = 'us-east-1_esUPZHWY4'
        os.environ['COGNITO_APP_CLIENT_ID'] = '2rr03i7clo2f8lmu1qp1d1jtto'
        os.environ['COGNITO_IDENTITY_POOL_ID'] = 'us-east-1:dcbc5711-2abf-4bc8-9298-0c2d4e135e11'
        os.environ['COGNITO_REGION'] = 'us-east-1'
    else:
        print(f"Running in deployed environment: {os.environ.get('ENVIRONMENT')}")

# AWS Cognito Configuration
COGNITO_REGION = os.environ.get('COGNITO_REGION')
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
COGNITO_APP_CLIENT_ID = os.environ.get('COGNITO_APP_CLIENT_ID')
COGNITO_IDENTITY_POOL_ID = os.environ.get('COGNITO_IDENTITY_POOL_ID')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

# Database Configuration
DYNAMODB_REGION = os.environ.get('DYNAMODB_REGION')
DYNAMODB_TABLE_PREFIX = os.environ.get('DYNAMODB_TABLE_PREFIX')

# Table names
USERS_TABLE = os.environ.get('USERS_TABLE')
GAME_HISTORY_TABLE = os.environ.get('GAME_HISTORY_TABLE')

print("Starting imports...")
print(f"Environment: {os.environ.get('ENVIRONMENT', 'not set')}")

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

print("Flask imports successful...")

from database.dynamodb_client import db_client
from database.user_service import user_service
from database.game_history_service import game_history_service

print("Database imports successful...")

from api.auth_utils import require_auth, get_current_user, verify_cognito_token

print("Auth imports successful...")

from game_engine.player import Player
from game_engine.game_loop import GameLoop
from game_engine.games.asshole import AssholeGame
from game_engine.card import Card

print("Game engine imports successful...")
print("All imports completed successfully!")

# --- START Logging Configuration ---
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logging.getLogger('boto3').setLevel(logging.DEBUG)
logging.getLogger('botocore').setLevel(logging.DEBUG)
logging.getLogger('urllib3').setLevel(logging.DEBUG)
# --- END Logging Configuration ---

app = Flask(__name__)
print("Flask app created...")
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'my_dev_key')

if os.environ.get('ENVIRONMENT') == 'local':
    try:
        db_client.create_tables()
    except Exception as e:
        print(f"Warning: Could not initialize database tables: {e}")

frontend_origins = [
    "http://localhost:3000",
    "https://main.dt7s5ohdz6dup.amplifyapp.com",
    "https://dev.dt7s5ohdz6dup.amplifyapp.com",
    "https://play.gregsgames.social",
]
frontend_origins = [origin for origin in frontend_origins if origin is not None]

CORS(app, resources={r"/*": {"origins": frontend_origins}}, supports_credentials=True)

socketio = SocketIO(app, cors_allowed_origins=frontend_origins, async_mode='eventlet', logger=True, engineio_logger=True)

active_games = {}
logger.debug(f"DEBUG_GLOBAL_ACTIVE_GAMES_ID_AT_START: {id(active_games)}")
try:
    logger.debug("Attempting the first critical operation after active_games ID debug.")
    logger.debug("Just before potential problematic call 1...")
    logger.debug("Just after potential problematic call 1.")
    logger.debug("Just before potential problematic call 2...")
    logger.debug("Just after potential problematic call 2.")
    logger.debug("All initial setup after active_games ID debug completed successfully.")
except Exception as e:
    logger.critical(f"CRITICAL ERROR: Application crashed during startup after active_games ID debug!", exc_info=True)
    raise
player_id_map = {}
player_to_room_map = {}

# --- Helper functions ---
def generate_unique_room_code(length=4):
    characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        if code not in active_games:
            return code

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

    interrupt_bids_data = []
    if game.interrupt_bids:
        for bid_entry in game.interrupt_bids:
            bid_player_id = bid_entry['player_id']
            bid_cards_data = [card.to_dict() for card in bid_entry['cards']]

            frontend_bid_entry = {
                'player_id': bid_player_id,
                'cards': bid_cards_data,
                'bid_time': bid_entry['bid_time'],
                'cards_played_in_bomb': bid_entry.get('cards_played_in_bomb')
            }

            interrupt_bids_data.append(frontend_bid_entry)

    return {
        'room_code': game.room_code,
        'game_type': game.game_type,
        'host_id': game.host_id,
        'current_player_name': current_player_name,
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
        'game_status': game.status,
        'game_message': game.game_message,
        'current_play_rank': game.current_play_rank,
        'current_play_count': game.current_play_count,
        'interrupt_active': game.interrupt_active,
        'interrupt_type': game.interrupt_type,
        'interrupt_initiator_player_id': game.interrupt_initiator_player_id,
        'interrupt_rank': game.interrupt_rank,
        'interrupt_bids': interrupt_bids_data,
        'interrupt_active_until': game.interrupt_active_until,
        'players_responded_to_interrupt': list(game.players_responded_to_interrupt),
    }

def _check_and_resolve_interrupts(game):
    """Checks if an active interrupt has expired and resolves it."""
    if game.interrupt_active and game.interrupt_active_until and time.time() > game.interrupt_active_until:
        print(f"DEBUG: Interrupt for room {game.room_code} expired. Resolving now.")
        try:
            game.resolve_interrupt()
        except Exception as e:
            print(f"ERROR: Failed to resolve expired interrupt for room {game.room_code}: {e}")
            traceback.print_exc()

def _get_all_rooms_state():
    """Enhanced room state with player profiles."""
    try:
        rooms = []
        for room_code, game in active_games.items():
            # Get enhanced player info
            players_info = []
            for player in game.players:
                player_info = {
                    'id': player.player_id,
                    'name': player.name,
                    'isHost': player.player_id == game.host_id
                }
                
                # Add profile info if available
                try:
                    profile = user_service.get_user_profile(player.player_id)
                    if profile:
                        player_info.update({
                            'gamesWon': profile.get('gamesWon', 0),
                            'winRate': profile.get('winRate', 0),
                            'userType': profile.get('userType', 'anonymous')
                        })
                except:
                    pass
                
                players_info.append(player_info)
            
            # Find the host player to get their name
            host_player = next((p for p in game.players if p.player_id == game.host_id), None)
            host_name = host_player.name if host_player else "Unknown"
            
            room_info = {
                'room_code': room_code,
                'game_type': getattr(game, 'game_type', 'asshole'),
                'status': getattr(game, 'status', 'WAITING_FOR_PLAYERS'),
                'player_count': len(game.players),
                'max_players': getattr(game, 'MAX_PLAYERS', 6),
                'host_id': game.host_id,
                'host_name': host_name,
                'players': players_info,
                'created_at': getattr(game, 'created_at', datetime.now(timezone.utc).isoformat()),
                'is_game_started': getattr(game, 'is_game_started', False)
            }
            rooms.append(room_info)
        
        return {'success': True, 'rooms': rooms}
    except Exception as e:
        print(f"Error getting rooms state: {e}")
        return {'success': False, 'rooms': []}

def _send_game_state_update_to_room_players(game):
    """Sends each player in the game their individual game state update."""
    _check_and_resolve_interrupts(game)
    
    # Save game results if game just completed
    if game.is_game_over and not getattr(game, '_results_saved', False):
        try:
            game_history_service.save_game_result(game)
            game._results_saved = True  # Prevent duplicate saves
            print(f"Game results saved for room {game.room_code}")
        except Exception as e:
            print(f"Warning: Could not save game results for room {game.room_code}: {e}")
    
    print(f"DEBUG: Preparing game_state_update for room {game.room_code} (players: {len(game.players)})")
    for p in game.players:
        if player_id_map.get(p.player_id):
            sid = player_id_map[p.player_id]
            game_state_payload = _get_game_state_for_player(game, p.player_id)
            if game_state_payload:
                socketio.emit('game_state_update', game_state_payload, room=sid)
                print(f"DEBUG: Sent game_state_update to player {p.name} ({p.player_id}) at SID: {sid}")
            else:
                print(f"WARNING: Could not get game state for player {p.name} ({p.player_id}) in room {game.room_code}")
        else:
            print(f"DEBUG: Player {p.name} ({p.player_id}) in room {game.room_code} has no active SID in player_id_map. Cannot send direct update.")

def game_timer_monitor():
    """
    Background thread that monitors active game timers (e.g., interrupt timers).
    """
    print("DEBUG: Game timer monitor thread started.")
    while True:
        for room_code, game in list(active_games.items()):
            if game.interrupt_active:
                should_resolve_interrupt = False
                
                active_players_count = sum(1 for p in game.players if p.is_active)

                if game.interrupt_type == 'bomb_opportunity':                    
                    timer_expired = False
                    if game.interrupt_active_until is not None:
                        timer_expired = (time.time() >= game.interrupt_active_until)

                    all_responded = (len(game.players_responded_to_interrupt) >= active_players_count)

                    if timer_expired:
                        print(f"DEBUG: Bomb interrupt timed out for room {room_code}.")
                        should_resolve_interrupt = True
                    elif all_responded:
                        print(f"DEBUG: Bomb interrupt: All active players responded for room {room_code}.")
                        should_resolve_interrupt = True

                elif game.interrupt_type == 'three_play':
                    all_responded = (len(game.players_responded_to_interrupt) >= active_players_count)
                    if all_responded:
                        print(f"DEBUG: Three-play interrupt: All active players passed for room {room_code}.")
                        should_resolve_interrupt = True
                
                if should_resolve_interrupt:
                    if game.interrupt_active: 
                        game.resolve_interrupt()
                        with app.app_context():
                            _send_game_state_update_to_room_players(game)

            time.sleep(0.01) 
        
        time.sleep(1)

def _ensure_user_profile(player_id, player_name):
    """Ensure user has a profile in the database (optional, non-blocking)"""
    try:
        user_service.get_or_create_user(player_id, player_name, "anonymous")
    except Exception as e:
        print(f"Warning: Could not create/update user profile for {player_id}: {e}")

def _handle_game_completion(game, winner_id):
    """Handle game completion and update user stats."""
    try:
        for player in game.players:
            games_played_delta = 1
            games_won_delta = 1 if player.player_id == winner_id else 0
            
            user_service.update_user_stats(
                player.player_id, 
                games_played_delta, 
                games_won_delta
            )
        
        print(f"Updated stats for game completion. Winner: {winner_id}")
    except Exception as e:
        print(f"Error updating game stats: {e}")

voice_chat_participants = {}
def broadcast_voice_users_update(room_code):
    """Helper function to get and broadcast the current list of voice users."""
    users_in_room = []
    if room_code in voice_chat_participants:
        for player_id, user_data in voice_chat_participants[room_code].items():
            users_in_room.append({
                'id': player_id,
                'name': user_data['name'],
                'isMuted': user_data.get('is_muted', False),
                'isSpeaking': user_data.get('is_speaking', False)
            })
    
    print(f"Broadcasting voice_users_update for room {room_code}: {users_in_room}")
    emit('voice_users_update', users_in_room, room=f"voice_{room_code}")

# --- HTTP API Endpoints ---
@app.route("/")
def home():
    return jsonify({"message": "Hello from Greg's Games Social Backend!"})

@app.route('/create_room', methods=['POST'])
def create_room():
    player_id = session.get('player_id')
    if not player_id:
        player_id = str(uuid.uuid4())
        session['player_id'] = player_id

    data = request.get_json()
    player_name = data.get('player_name', '').strip()
    game_type = data.get('game_type', '').lower()

    if not player_name:
        return jsonify({"success": False, "message": "Player name is required to create a room."}), 400

    # Create/update user profile
    try:
        user_profile = user_service.get_or_create_user(player_id, player_name, "anonymous")
        print(f"User profile created/updated for {player_name}")
    except Exception as e:
        print(f"Warning: Could not create/update user profile for {player_id}: {e}")

    room_code = generate_unique_room_code()
    host_id = player_id

    GameClass = None
    if game_type == 'asshole':
        GameClass = AssholeGame
    else:
        return jsonify({'error': 'Invalid game type specified.'}), 400

    try:
        new_game = GameClass(room_code=room_code, host_id=host_id, game_type=game_type)
        new_game.created_at = datetime.utcnow().isoformat()  # Add timestamp
        
        host_player_obj = Player(player_id=host_id, name=player_name)
        new_game.add_player(host_player_obj)
        new_game.status = "WAITING_FOR_PLAYERS"
        active_games[room_code] = new_game
        player_to_room_map[player_id] = room_code
        
        # Broadcast enhanced room update
        socketio.emit('room_update', _get_all_rooms_state())
        socketio.emit('room_created', {
            'room_code': room_code,
            'host_name': player_name,
            'game_type': game_type
        })
        
        _send_game_state_update_to_room_players(new_game)

        game_state_payload = _get_game_state_for_player(new_game, host_id)
        if not game_state_payload:
            raise Exception("Failed to get initial game state for host.")

        return jsonify({
            'message': f'Successfully created room {room_code} as {player_name}',
            'room_code': room_code,
            'player_id': player_id,
            'player_name': player_name,
            'game_state': game_state_payload,
            'user_profile': user_profile
        }), 201
    except Exception as e:
        print(f"Error creating room: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to create room: {str(e)}'}), 500

@app.route('/join_room', methods=['POST'])
def join_room_http():
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

    # Create/update user profile (optional, non-blocking)
    _ensure_user_profile(player_id, player_name)

    game = active_games.get(room_code)

    if not game:
        return jsonify({'error': f'Room "{room_code}" does not exist.'}), 404

    if game.status == "IN_PROGRESS" or game.status == "GAME_OVER":
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

        player_to_room_map[player_id] = room_code

        _send_game_state_update_to_room_players(game)
        socketio.emit('room_update', _get_all_rooms_state())
        print(f"DEBUG: Emitted room_update globally after re-join for room {room_code}")

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

    _send_game_state_update_to_room_players(game)
    socketio.emit('room_update', _get_all_rooms_state())
    print(f"DEBUG: Emitted room_update globally after new player joined room {room_code}")

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
def get_room_list():
    return jsonify(_get_all_rooms_state()), 200

@app.route('/leave_room', methods=['POST'])
def leave_room_http():
    data = request.json
    room_code = data.get('room_code', '').upper()
    player_id = data.get('player_id')

    game = active_games.get(room_code)

    if not game:
        return jsonify({'error': 'Game room not found.'}), 404

    player_to_remove = game.get_player_by_id(player_id)
    if not player_to_remove:
        return jsonify({'error': 'Player not found in this room.'}), 404
    
    game.remove_player(player_id)
    if player_id in player_to_room_map:
        del player_to_room_map[player_id]

    if game.host_id == player_id or game.get_num_players() == 0:
        del active_games[room_code]
        print(f"Room {room_code} deleted because host ({player_id}) left or room is empty.")
        socketio.emit('room_deleted', {'room_code': room_code, 'message': 'Room has been disbanded'})
        socketio.emit('room_update', _get_all_rooms_state())
        return jsonify({'message': 'You left the room. Room deleted (host left or room empty).'}), 200
    
    if game.is_game_started:
        pass
    
    print(f"Player {player_id} left room {room_code}. Current players: {[p.name for p in game.players]}")
    _send_game_state_update_to_room_players(game)
    socketio.emit('room_update', _get_all_rooms_state())
    return jsonify({'message': 'Successfully left the room.'}), 200

@app.route('/delete_room', methods=['POST'])
def delete_room_http():
    data = request.json
    room_code = data.get('room_code', '').upper()
    player_id = data.get('player_id')

    game = active_games.get(room_code)

    if not game:
        return jsonify({'error': 'Game room not found.'}), 404

    if game.host_id != player_id:
        return jsonify({'error': 'Only the host can delete the room.'}), 403

    del active_games[room_code]
    players_in_room = [p.player_id for p in game.players]
    for p_id in players_in_room:
        if p_id in player_to_room_map:
            del player_to_room_map[p_id]
    print(f"Host ({player_id}) explicitly deleted room {room_code}.")
    
    socketio.emit('room_deleted', {'room_code': room_code, 'message': 'Room has been disbanded by the host.'})
    socketio.emit('room_update', _get_all_rooms_state())

    return jsonify({'message': f'Room {room_code} has been successfully deleted.'}), 200

@app.route('/start_game_round', methods=['POST'])
def start_game_round():
    data = request.json
    room_code = data.get('room_code', '').upper()
    player_id = data.get('player_id')

    game = active_games.get(room_code)

    if not game:
        return jsonify({'error': 'Game room not found.'}), 404
    
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

        _send_game_state_update_to_room_players(game)
        socketio.emit('room_update', _get_all_rooms_state())

        game_state_payload = _get_game_state_for_player(game, player_id)
        if not game_state_payload:
            raise Exception("Failed to get game state after starting game.")

        return jsonify({
            'message': 'Game round started!',
            'room_code': room_code,
            'current_player_name': game_state_payload['current_player_name'],
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
        return jsonify({'success': False, 'error': 'Game room not found.'}), 404
    
    if game.status != "IN_PROGRESS":
        return jsonify({'success': False, 'error': 'Game is not in progress.'}), 400

    _check_and_resolve_interrupts(game)

    if game.interrupt_active and game.get_current_player().player_id == player_id:
        print(f"DEBUG: Implicitly resolving interrupt of type {game.interrupt_type} initiated by {game.interrupt_initiator_player_id}.")
        try:
            game.resolve_interrupt()
            print(f"DEBUG: Interrupt resolved before normal play.")
        except Exception as e:
            print(f"ERROR: Failed to resolve interrupt implicitly: {e}")
            traceback.print_exc()
            return jsonify({'success': False, 'error': f"Failed to resolve interrupt: {str(e)}"}), 500
    try:
        game.play_cards(player_id, cards_to_play_data)

        _send_game_state_update_to_room_players(game)

        game_state_payload = _get_game_state_for_player(game, player_id)
        if not game_state_payload:
            raise Exception("Failed to get game state after playing cards.")

        return jsonify({'message': 'Card(s) played', 'game_state': game_state_payload}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error playing cards: {e}")
        traceback.print_exc()
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    
@app.route('/pass_turn', methods=['POST'])
def pass_turn():
    data = request.get_json()
    room_code = data.get('room_code', '').upper()
    player_id = data.get('player_id')

    game = active_games.get(room_code)

    if not game:
        return jsonify({'success': False, 'error': 'Game room not found.'}), 404

    if game.status != "IN_PROGRESS":
        return jsonify({'success': False, 'error': 'Game is not in progress.'}), 400

    _check_and_resolve_interrupts(game)

    if game.interrupt_active and game.get_current_player().player_id == player_id:
        print(f"DEBUG: Implicitly resolving interrupt of type {game.interrupt_type} initiated by {game.interrupt_initiator_player_id}.")
        try:
            game.resolve_interrupt()
            print(f"DEBUG: Interrupt resolved before normal pass.")
        except Exception as e:
            print(f"ERROR: Failed to resolve interrupt implicitly during pass: {e}")
            traceback.print_exc()
            return jsonify({'success': False, 'error': f"Failed to resolve interrupt: {str(e)}"}), 500

    try:
        game.pass_turn(player_id)    

        _send_game_state_update_to_room_players(game)

        game_state = _get_game_state_for_player(game, player_id)
        if not game_state:
            raise Exception("Failed to get game state after passing turn.")
        return jsonify({'message': 'Turn passed', 'game_state': game_state}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error passing turn: {e}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/submit_interrupt_bid', methods=['POST'])
def submit_interrupt_bid_route():
    data = request.get_json()
    room_code = data.get('room_code', '').upper()
    player_id = data.get('player_id')
    cards_data = data.get('cards')

    game = active_games.get(room_code)

    if not game:
        return jsonify({'success': False, 'error': 'Game room not found.'}), 404

    try:
        game.submit_interrupt_bid(player_id, cards_data)
        _send_game_state_update_to_room_players(game)
        return jsonify({'success': True, 'message': 'Interrupt bid/pass submitted.'}), 200
    except ValueError as e:
        print(f"Interrupt bid validation error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        print(f"An unexpected error occurred during interrupt bid: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'An unexpected server error occurred.'}), 500

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

@app.route('/user_profile', methods=['GET'])
def get_user_profile():
    """Get user profile information."""
    player_id = request.args.get('player_id')
    
    print(f"Getting user profile for player_id: {player_id}")
    
    if not player_id:
        return jsonify({'error': 'Player ID required'}), 400
    
    try:
        profile = user_service.get_user_profile(player_id)
        print(f"Profile found: {profile}")
        
        if not profile:
            print(f"No profile found for player_id: {player_id}")
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(profile), 200
    except Exception as e:
        print(f"Error getting user profile: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get user profile'}), 500

@app.route('/update_profile', methods=['POST'])
def update_user_profile():
    """Update user profile."""
    data = request.get_json()
    player_id = data.get('player_id')
    
    if not player_id:
        return jsonify({'error': 'Player ID required'}), 400
    
    try:
        # Update user preferences
        preferences = data.get('preferences', {})
        if preferences:
            user = user_service.get_user(player_id)
            if user:
                current_prefs = user.get('userPreferences', {})
                current_prefs.update(preferences)
                
                success = user_service.db.update_item('users', {'userId': player_id}, {
                    'userPreferences': current_prefs
                })
                
                if success:
                    return jsonify({'message': 'Profile updated successfully'}), 200
        
        return jsonify({'error': 'Failed to update profile'}), 500
    except Exception as e:
        print(f"Error updating profile: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

@app.route('/auth/register', methods=['POST'])
def auth_register():
    """Register a new user with Cognito and create profile."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not all([username, password, email]):
        return jsonify({'error': 'Username, password, and email required'}), 400
    
    try:
        # Create Cognito user
        from api.auth_utils import create_cognito_user
        cognito_result = create_cognito_user(username, password, email)
        
        if cognito_result and cognito_result.get('success'):
            # Create user profile in our database
            user_id = cognito_result['user_id']
            user_profile = user_service.create_user(user_id, username, "authenticated", email)
            
            if user_profile:
                return jsonify({
                    'success': True,
                    'message': 'User registered successfully',
                    'user_id': user_id,
                    'username': username
                }), 201
        
        return jsonify({
            'success': False, 
            'error': cognito_result.get('error', 'Failed to register user')
        }), 400
        
    except Exception as e:
        print(f"Error registering user: {e}")
        return jsonify({'success': False, 'error': 'Registration failed'}), 500

@app.route('/auth/login', methods=['POST'])
def auth_login():
    """Authenticate user with Cognito."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return jsonify({'error': 'Username and password required'}), 400
    
    try:
        from api.auth_utils import authenticate_cognito_user
        auth_result = authenticate_cognito_user(username, password)
        
        if auth_result and auth_result.get('success'):
            # Get user profile
            user_profile = user_service.get_user_profile(auth_result['user_id'])

            # Add this for session management
            session['player_id'] = auth_result['user_id']
            # If you also want to store username in session:
            # session['username'] = username # (Assuming Cognito username is consistent with your profile username)

            return jsonify({
                'success': True,
                'access_token': auth_result['access_token'],
                'id_token': auth_result['id_token'],
                'user_id': auth_result['user_id'],
                'profile': user_profile
            }), 200
        
        return jsonify({
            'success': False,
            'error': auth_result.get('error', 'Authentication failed')
        }), 401
        
    except Exception as e:
        print(f"Error during login: {e}")
        return jsonify({'success': False, 'error': 'Login failed'}), 500

@app.route('/auth/mock_login', methods=['POST'])
def mock_login():
    """Mock login for local testing without Cognito.
    Generates a consistent UUID for mock users based on their username.
    """
    data = request.get_json()
    username = data.get('username', 'testuser') # e.g., 'test@example.com'

    # Generate a predictable UUID based on the username.
    # This ensures that 'test@example.com' always maps to the same UUID,
    # making your mock users consistent across restarts and allowing profile retrieval.
    # We use NAMESPACE_DNS and the username to create a UUIDv5, which is deterministic.
    mock_user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, username))

    try:
        print(f"Mock login attempt for username: {username}")
        print(f"Generated mock_user_id (UUID format): {mock_user_uuid}")

        # Try to get existing user profile using the generated UUID
        profile_response = user_service.get_user_profile(mock_user_uuid)
        profile = profile_response.get('profile') # Extract the profile dictionary if success is True

        if not profile:
            # If no profile found with this UUID, create a new mock user profile
            print(f"No profile found for user_id: {mock_user_uuid}. Creating new mock user profile.")
            # Call create_user with the generated UUID, consistent with your DB schema
            create_result = user_service.create_user(mock_user_uuid, username, "mock", f"{username}@test.com")

            if create_result.get('success'):
                profile = create_result['profile']
                print(f"Created profile: {profile}")
            else:
                # Handle error if profile creation fails
                print(f"Error creating mock user profile: {create_result.get('error')}")
                return jsonify({'success': False, 'error': create_result.get('error', 'Failed to create mock user profile')}), 500
        else:
            print(f"Existing profile found for user_id: {mock_user_uuid}: {profile}")

        # Set the session with the correct UUID
        session['player_id'] = mock_user_uuid
        session['username'] = username # Keep username in session for display if needed

        return jsonify({
            'success': True,
            'access_token': 'mock_token', # Mock token for local testing
            'user_id': mock_user_uuid, # IMPORTANT: Send the UUID to the frontend
            'username': username,
            'profile': profile # Include the profile data
        }), 200

    except Exception as e:
        print(f"Error in mock login: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Mock login failed due to server error'}), 500

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get top players leaderboard."""
    try:
        # This would need a more sophisticated query in production
        # For now, return a simple response
        return jsonify({
            'leaderboard': [
                {'username': 'Player1', 'gamesWon': 15, 'winRate': 75.0},
                {'username': 'Player2', 'gamesWon': 12, 'winRate': 60.0},
                {'username': 'Player3', 'gamesWon': 8, 'winRate': 53.3}
            ]
        }), 200
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        return jsonify({'error': 'Failed to get leaderboard'}), 500

@app.route('/user_game_history', methods=['GET'])
def get_user_game_history():
    """Get user's recent game history"""
    player_id = request.args.get('player_id')
    limit = int(request.args.get('limit', 10))
    
    if not player_id:
        player_id = session.get('player_id')
    
    if not player_id:
        return jsonify({'error': 'Player ID required'}), 400
    
    try:
        history = game_history_service.get_user_game_history(player_id, limit)
        return jsonify({'games': history}), 200
    except Exception as e:
        print(f"Error getting user game history: {e}")
        return jsonify({'error': 'Failed to get game history'}), 500

# --- SocketIO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    current_sid = request.sid
    player_id_from_session = session.get('player_id')
    
    print(f'Client {current_sid} attempting to connect. Session player_id: {player_id_from_session}')
    
    if player_id_from_session:
        player_id_map[player_id_from_session] = current_sid
        join_room(current_sid)
        print(f'Client {current_sid} (Player ID: {player_id_from_session}) connected.')
        emit('status', {'msg': f'Connected to server! Your SID: {current_sid}. Player ID: {player_id_from_session}'})

        if player_id_from_session in player_to_room_map:
            room_code = player_to_room_map[player_id_from_session]
            join_room(room_code)
            print(f'Client {current_sid} (Player ID: {player_id_from_session}) also joined game room: {room_code}')
            emit('status', {'msg': f'Re-joined game room {room_code} via WebSocket.'}, room=current_sid)
            
            # Send initial game state
            game = active_games.get(room_code)
            if game:
                socketio.emit('game_state_update', _get_game_state_for_player(game, player_id_from_session), room=current_sid)
    else:
        print(f'Client {current_sid} connected (no player ID in session).')
        emit('status', {'msg': f'Connected to server! Your SID: {current_sid}'})

    socketio.emit('room_update', _get_all_rooms_state())

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handles a client WebSocket disconnection.
    Removes the player's SID mapping and logs the disconnection.
    """
    current_sid = request.sid
    disconnected_player_id = None

    for p_id, sid_in_map in list(player_id_map.items()):
        if sid_in_map == current_sid:
            disconnected_player_id = p_id
            del player_id_map[p_id]
            print(f"Mapped Player ID {disconnected_player_id} removed from player_id_map.")
            break

    if disconnected_player_id:
        rooms_voice_chat_updated = set()

        for room_code, participants in list(voice_chat_participants.items()):
            if disconnected_player_id in participants:
                del participants[disconnected_player_id]
                print(f"Player {disconnected_player_id} removed from voice chat in room {room_code}.")

                if not participants:
                    del voice_chat_participants[room_code]
                    print(f"Voice chat room {room_code} is now empty and removed.")
                
                rooms_voice_chat_updated.add(room_code)

        for room_code_to_update in rooms_voice_chat_updated:
            broadcast_voice_users_update(room_code_to_update)
            
    else:
        print(f"No player ID found for disconnected SID {current_sid} in player_id_map.")
    
    if disconnected_player_id and disconnected_player_id in player_to_room_map:
        room_code = player_to_room_map[disconnected_player_id]
        print(f"Player {disconnected_player_id} was in game room {room_code}.")
        
        del player_to_room_map[disconnected_player_id]
        
        game = active_games.get(room_code)
        if game:
            print(f"Triggering game state update for room {room_code}.")
            _send_game_state_update_to_room_players(game)
        else:
            print(f"DEBUG: Disconnected player {disconnected_player_id} was in room {room_code}, but game no longer exists in active_games.")
    else:
        print(f"Disconnected player {disconnected_player_id} not found in player_to_room_map or player_id was not found.")

    socketio.emit('room_update', _get_all_rooms_state())
    print("Emitted global room_update.")

@socketio.on('send_chat_message')
def handle_chat_message(data):
    """Enhanced chat message handler with user info."""
    message = data.get('message', '').strip()
    room_code = data.get('room_code')
    sender_id = session.get('player_id')
    
    if not message:
        return
    
    # Get sender info
    sender_name = "Anonymous"
    sender_profile = None
    
    if sender_id:
        # Try to get from game first
        if sender_id in player_to_room_map:
            game = active_games.get(player_to_room_map[sender_id])
            if game:
                player_obj = game.get_player_by_id(sender_id)
                if player_obj:
                    sender_name = player_obj.name
        
        # Get user profile for additional info
        try:
            sender_profile = user_service.get_user_profile(sender_id)
        except:
            pass
    
    # Create enhanced message payload
    message_payload = {
        'sender': sender_name,
        'senderId': sender_id,
        'message': message,
        'timestamp': datetime.utcnow().isoformat(),
        'senderProfile': {
            'gamesWon': sender_profile.get('gamesWon', 0) if sender_profile else 0,
            'userType': sender_profile.get('userType', 'anonymous') if sender_profile else 'anonymous'
        }
    }
    
    if room_code and room_code in active_games:
        emit('receive_chat_message', message_payload, room=room_code)
        print(f"Chat message to room {room_code} from {sender_name}: {message}")
    else:
        emit('receive_chat_message', message_payload, broadcast=True)
        print(f"Broadcast chat message from {sender_name}: {message}")

@socketio.on('typing_indicator')
def handle_typing_indicator(data):
    """Handle typing indicators for chat."""
    room_code = data.get('room_code')
    sender_id = session.get('player_id')
    is_typing = data.get('is_typing', False)
    
    if sender_id and room_code and room_code in active_games:
        # Get sender name
        sender_name = "Anonymous"
        if sender_id in player_to_room_map:
            game = active_games.get(player_to_room_map[sender_id])
            if game:
                player_obj = game.get_player_by_id(sender_id)
                if player_obj:
                    sender_name = player_obj.name
        
        # Broadcast typing indicator to room (except sender)
        emit('typing_indicator', {
            'sender': sender_name,
            'senderId': sender_id,
            'is_typing': is_typing
        }, room=room_code, include_self=False)

@socketio.on('join_game_room_socket')
def handle_join_game_room_socket(data):
    room_code = data.get('room_code')
    player_id = data.get('player_id') or session.get('player_id')
    
    if not player_id:
        emit('status', {'msg': 'Error: No player ID provided or in session.'}, room=request.sid)
        return
    
    # Ensure session has the player_id
    session['player_id'] = player_id
    
    if room_code and room_code in active_games:
        player_id_map[player_id] = request.sid
        join_room(room_code)
        player_to_room_map[player_id] = room_code
        print(f'Client {request.sid} (Player ID: {player_id}) joined SocketIO room: {room_code}')
        emit('status', {'msg': f'Successfully joined game WebSocket room {room_code}.'}, room=request.sid)

        game = active_games.get(room_code)
        if game:
            socketio.emit('game_state_update', _get_game_state_for_player(game, player_id), room=request.sid)
            print(f"Emitted initial game_state_update to {player_id} upon joining socket room {room_code}")
    else:
        emit('status', {'msg': f'Error: Room {room_code} not found or invalid.'}, room=request.sid)

@socketio.on('leave_game_room_socket')
def on_leave_game_room_socket(data):
    """
    Handles a client's request to leave a specific SocketIO room.
    Typically called when a player leaves a game or navigates away.
    """
    room_code = data.get('room_code')
    player_id = data.get('player_id')

    if not player_id:
        emit('status', {'msg': 'Error: Player ID not found in session.'}, room=request.sid)
        return
    
    if room_code and room_code in active_games:
        leave_room(room_code)
        if player_id in player_to_room_map and player_to_room_map[player_id] == room_code:
            del player_to_room_map[player_id]
        print(f'Client {request.sid} (Player ID: {player_id}) left SocketIO room: {room_code}')
        emit('status', {'msg': f'Successfully left game WebSocket room {room_code}.'}, room=request.sid)

        game = active_games.get(room_code)
        if game:
            _send_game_state_update_to_room_players(game)
        else:
           print(f"DEBUG: Player {player_id} left room {room_code}, but game no longer exists (might have been deleted by host/last player).") 
    else:
        emit('status', {'msg': f'Warning: Room {room_code} not found or invalid on leave.'}, room=request.sid)

@socketio.on('submit_interrupt_bid')
def on_submit_interrupt_bid(data):
    """
    Handles a player's attempt to submit an interrupt bid (e.g., playing 3s out of turn).
    """
    room_code = data.get('room_code')
    player_id = data.get('player_id')
    cards_data = data.get('cards', [])

    print(f"DEBUG: Received 'submit_interrupt_bid' from Player ID: {player_id} in Room: {room_code} with cards: {cards_data}")

    game = active_games.get(room_code)
    if not game:
        emit('status', {'msg': 'Error: Game room not found for interrupt bid.'}, room=request.sid)
        return

    # Convert incoming card data (dict) to Card objects
    cards_to_play_objects = [Card(c['suit'], c['rank']) for c in cards_data]

    try:
        game.submit_interrupt_bid(player_id, cards_to_play_objects)
        print(f"DEBUG: Player {player_id} successfully submitted interrupt bid.")
        _send_game_state_update_to_room_players(game)
        emit('status', {'msg': 'Interrupt bid submitted.'}, room=request.sid)
    except ValueError as e:
        print(f"ERROR: ValueError on interrupt bid: {e}")
        emit('status', {'msg': f'Error submitting interrupt bid: {str(e)}'}, room=request.sid)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred on interrupt bid: {e}")
        traceback.print_exc()
        emit('status', {'msg': f'An unexpected error occurred during interrupt bid: {str(e)}'}, room=request.sid)    

@socketio.on('game_finished')
def handle_game_finished(data):
    """Handle when a game finishes."""
    room_code = data.get('room_code')
    winner_id = data.get('winner_id')
    
    if room_code in active_games:
        game = active_games[room_code]
        
        _handle_game_completion(game, winner_id)
        
        socketio.emit('game_completed', {
            'winner_id': winner_id,
            'final_rankings': data.get('final_rankings', [])
        }, room=room_code)

@socketio.on('join_voice_chat')
def handle_join_voice_chat(data):
    """Handle user joining voice chat."""
    room_code = data.get('room_code')
    user_name = data.get('user_name', 'Unknown')
    player_id = session.get('player_id')
    
    if not player_id or not room_code:
        emit('voice_error', {'error': 'Missing player ID or room code'})
        return
    
    if room_code not in voice_chat_participants:
        voice_chat_participants[room_code] = {}
    
    voice_chat_participants[room_code][player_id] = {
        'name': user_name,
        'sid': request.sid,
        'is_muted': False
    }

    join_room(f"voice_{room_code}")
    
    emit('user_joined_voice', {
        'userId': player_id,
        'userName': user_name,
        'roomCode': room_code
    }, room=f"voice_{room_code}", include_self=False)
    
    print(f"Player {user_name} ({player_id}) joined voice chat in room {room_code}")

    broadcast_voice_users_update(room_code)

@socketio.on('leave_voice_chat')
def handle_leave_voice_chat(data):
    """Handle user leaving voice chat."""
    room_code = data.get('room_code')
    player_id = session.get('player_id')
    
    if not player_id or not room_code:
        return
    
    if room_code in voice_chat_participants and player_id in voice_chat_participants[room_code]:
        del voice_chat_participants[room_code][player_id]
        print(f"Player {player_id} removed from voice_chat_participants in room {room_code}")

    leave_room(f"voice_{room_code}")
    
    emit('user_left_voice', {
        'userId': player_id,
        'roomCode': room_code
    }, room=f"voice_{room_code}")
    
    print(f"Player {player_id} left voice chat in room {room_code}")

    broadcast_voice_users_update(room_code)

@socketio.on('voice_offer')
def handle_voice_offer(data):
    """Handle WebRTC offer for voice chat."""
    target_user = data.get('target')
    offer = data.get('offer')
    room_code = data.get('room_code')
    sender_id = session.get('player_id')
    
    if not all([target_user, offer, room_code, sender_id]):
        return
    
    target_sid = player_id_map.get(target_user)
    if target_sid:
        emit('voice_offer', {
            'offer': offer,
            'sender': sender_id,
            'room_code': room_code
        }, room=target_sid)

@socketio.on('voice_answer')
def handle_voice_answer(data):
    """Handle WebRTC answer for voice chat."""
    target_user = data.get('target')
    answer = data.get('answer')
    room_code = data.get('room_code')
    sender_id = session.get('player_id')
    
    if not all([target_user, answer, room_code, sender_id]):
        return
    
    target_sid = player_id_map.get(target_user)
    if target_sid:
        emit('voice_answer', {
            'answer': answer,
            'sender': sender_id,
            'room_code': room_code
        }, room=target_sid)

@socketio.on('voice_ice_candidate')
def handle_voice_ice_candidate(data):
    """Handle WebRTC ICE candidate for voice chat."""
    target_user = data.get('target')
    candidate = data.get('candidate')
    room_code = data.get('room_code')
    sender_id = session.get('player_id')
    
    if not all([target_user, candidate, room_code, sender_id]):
        return
    
    target_sid = player_id_map.get(target_user)
    if target_sid:
        emit('voice_ice_candidate', {
            'candidate': candidate,
            'sender': sender_id,
            'room_code': room_code
        }, room=target_sid)

@socketio.on('user_speaking')
def handle_user_speaking(data):
    """Handle speaking status updates."""
    room_code = data.get('room_code')
    is_speaking = data.get('is_speaking', False)
    player_id = session.get('player_id')
    
    if not player_id or not room_code:
        print(f"User speaking update failed: Missing player_id ({player_id}) or room_code ({room_code}).")
        return
    
    if room_code in voice_chat_participants and player_id in voice_chat_participants[room_code]:
        voice_chat_participants[room_code][player_id]['is_speaking'] = is_speaking
        print(f"Player {player_id} in room {room_code} speaking status set to: {is_speaking}")
        
        broadcast_voice_users_update(room_code)
    else:
        print(f"User {player_id} not found in voice chat for room {room_code} for speaking update.")

@socketio.on('toggle_mute_voice')
def handle_toggle_mute_voice(data):
    room_code = data.get('room_code')
    sender_id = session.get('player_id')
    
    if not room_code or not sender_id:
        return
        
    if room_code in voice_chat_participants and sender_id in voice_chat_participants[room_code]:
        current_mute_status = voice_chat_participants[room_code][sender_id].get('is_muted', False)
        voice_chat_participants[room_code][sender_id]['is_muted'] = not current_mute_status
        broadcast_voice_users_update(room_code)
        print(f"Player {sender_id} mute status toggled to {not current_mute_status} in room {room_code}")

if __name__ == '__main__':
    print("Starting Flask-SocketIO server...")
    print(f"Environment: {os.environ.get('ENVIRONMENT', 'not set')}")
    print(f"Port: {os.environ.get('PORT', 8080)}")
    print(f"Debug mode: True")
    
    timer_thread = threading.Thread(target=game_timer_monitor, daemon=True)
    timer_thread.start()
    print("Game timer monitor thread started.")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
