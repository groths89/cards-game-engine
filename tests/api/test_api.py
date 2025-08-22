import pytest
import unittest.mock as mock
from flask import Flask
from api.api import app, active_games, player_to_room_map, COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID
from game_engine.games.asshole import AssholeGame
from game_engine.player import Player
from game_engine.card import Card
from unittest.mock import MagicMock, patch

class MockGame:
    def __init__(self, room_code, host_id, game_type):
        self.room_code = room_code
        self.host_id = host_id
        self.game_type = game_type
        self.players = []
        self.is_game_started = False
        self.status = "WAITING_FOR_PLAYERS"
        self.MAX_PLAYERS = 6
        self.MIN_PLAYERS = 2
        self.is_game_over = False
        self.interrupt_active = False
        self.last_played_cards = []
        self.pile = []
        self.current_play_rank = None
        self.current_play_count = None
        self.interrupt_bids = []
        self.interrupt_active_until = None
        self.players_responded_to_interrupt = set()
        self.game_message = ""
        self.current_turn_player_id = None
        self.created_at = None
        self.interrupt_type = None
        self.interrupt_initiator_player_id = None
        self.interrupt_rank = None

    def add_player(self, player):
        self.players.append(player)

    def get_num_players(self):
        return len(self.players)

    def get_player_by_id(self, player_id):
        return next((p for p in self.players if p.player_id == player_id), None)
        
    def remove_player(self, player_id):
        self.players = [p for p in self.players if p.player_id != player_id]

    def start_game(self):
        self.is_game_started = True
        self.status = "IN_PROGRESS"
        self.current_turn_player_id = self.players[0].player_id

    def get_current_player(self):
        return self.get_player_by_id(self.current_turn_player_id)

    def play_cards(self, player_id, cards_to_play):
        pass # Mocked out

    def pass_turn(self, player_id):
        pass # Mocked out

    def get_num_active_players(self):
        return len(self.players)

    def get_rank_name(self, rank, total_players):
        return "Rank"
        
    def resolve_interrupt(self):
        self.interrupt_active = False

    def submit_interrupt_bid(self, player_id, cards_data):
        pass

@pytest.fixture
def client():
    # Use the test client for the Flask app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def mock_dependencies():
    with patch('api.api.AssholeGame', new=MagicMock(side_effect=MockGame)) as mock_game_class, \
         patch('api.api.socketio', new=MagicMock()) as mock_socketio, \
         patch('api.api.db_client', new=MagicMock()) as mock_db_client, \
         patch('api.api.user_service', new=MagicMock()) as mock_user_service, \
         patch('api.api.game_history_service', new=MagicMock()) as mock_game_history_service:
        
        active_games.clear()
        player_to_room_map.clear()
        
        yield {
            "game_class": mock_game_class,
            "socketio": mock_socketio,
            "db_client": mock_db_client,
            "user_service": mock_user_service,
            "game_history_service": mock_game_history_service
        }

# Helper to create a game and add a player for testing
def create_test_game(room_code='ABCD', host_id='player1'):
    mock_game = MockGame(room_code=room_code, host_id=host_id, game_type='asshole')
    mock_game.add_player(Player(name='Host', player_id=host_id))
    active_games[room_code] = mock_game
    player_to_room_map[host_id] = room_code
    return mock_game

@mock.patch('api.api.generate_unique_room_code', return_value='ABCD')
@mock.patch('api.api.uuid.uuid4', return_value='test_player_id')
def test_create_room_success(mock_uuid, mock_gen_code, client, mock_dependencies):
    # Configure the mock to return a user profile
    mock_dependencies['user_service'].get_or_create_user.return_value = {         
        'id': 'test_player_id',
        'username': 'TestPlayer',
        'userType': 'anonymous' 
    }

    with client.session_transaction() as sess:
        sess['player_id'] = None

    response = client.post('/create_room', json={'player_name': 'TestPlayer', 'game_type': 'asshole'})
    assert response.status_code == 201
    json_data = response.get_json()

    # Assert the new 'user_profile' key exists in the response
    assert 'user_profile' in json_data
    assert json_data['user_profile']['username'] == 'TestPlayer'

    assert json_data['room_code'] == 'ABCD'
    assert json_data['player_id'] == 'test_player_id'
    assert 'ABCD' in active_games
    assert 'test_player_id' in player_to_room_map
    assert len(active_games['ABCD'].players) == 1
    assert active_games['ABCD'].players[0].name == 'TestPlayer'
    assert active_games['ABCD'].players[0].player_id == 'test_player_id'
    assert active_games['ABCD'].status == "WAITING_FOR_PLAYERS"

def test_create_room_no_player_name(client, mock_dependencies):
    response = client.post('/create_room', json={'player_name': '', 'game_type': 'asshole'})
    assert response.status_code == 400
    assert 'Player name is required' in response.get_json()['message']

def test_create_room_invalid_game_type(client, mock_dependencies):
    response = client.post('/create_room', json={'player_name': 'TestPlayer', 'game_type': 'invalid'})
    assert response.status_code == 400
    assert 'Invalid game type' in response.get_json()['error']

@mock.patch('api.api.Player', side_effect=Exception('Player creation failed'))
def test_create_room_server_error(mock_player, client, mock_dependencies):
    response = client.post('/create_room', json={'player_name': 'TestPlayer', 'game_type': 'asshole'})
    assert response.status_code == 500
    assert 'Failed to create room' in response.get_json()['error']

def test_join_room_http_success(client, mock_dependencies):
    create_test_game()  # Set up a game to join
    with client.session_transaction() as sess:
        sess['player_id'] = None # Ensure new session

    response = client.post('/join_room', json={'room_code': 'ABCD', 'player_name': 'NewPlayer'})
    assert response.status_code == 200
    assert 'Successfully joined room' in response.get_json()['message']
    assert len(active_games['ABCD'].players) == 2

def test_join_room_http_rejoin_success(client, mock_dependencies):
    game = create_test_game()
    player_id = 'rejoin_player'
    game.add_player(Player(name='Rejoiner', player_id=player_id))
    player_to_room_map[player_id] = 'ABCD'

    with client.session_transaction() as sess:
        sess['player_id'] = player_id

    response = client.post('/join_room', json={'room_code': 'ABCD', 'player_name': 'UpdatedName'})
    assert response.status_code == 200
    assert 're-joined room' in response.get_json()['message']
    assert game.get_player_by_id(player_id).name == 'UpdatedName'

def test_join_room_http_not_found(client, mock_dependencies):
    response = client.post('/join_room', json={'room_code': 'WXYZ', 'player_name': 'TestPlayer'})
    assert response.status_code == 404
    assert 'does not exist' in response.get_json()['error']

def test_join_room_http_game_in_progress(client, mock_dependencies):
    game = create_test_game()
    game.status = "IN_PROGRESS"
    response = client.post('/join_room', json={'room_code': 'ABCD', 'player_name': 'TestPlayer'})
    assert response.status_code == 403
    assert 'Game has already started' in response.get_json()['error']

def test_join_room_http_room_full(client, mock_dependencies):
    game = create_test_game()
    game.MAX_PLAYERS = 1
    response = client.post('/join_room', json={'room_code': 'ABCD', 'player_name': 'TestPlayer'})
    assert response.status_code == 400
    assert 'room is full' in response.get_json()['error']

""" def test_join_room_http_player_in_another_room(client, mock_dependencies):
    create_test_game(room_code='ABD2', host_id='player1')
    player_to_room_map['player1'] = 'ABD2'
    response = client.post('/join_room', json={'room_code': 'ABD2', 'player_name': 'TestPlayer'})
    assert response.status_code == 400
    assert 'already in another game' in response.get_json()['error'] """