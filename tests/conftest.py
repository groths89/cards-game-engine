import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch

from api.api import app, socketio, active_games, player_id_map, player_to_room_map, voice_chat_participants

@pytest.fixture
def client():
    """A test client for the Flask application."""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        with app.app_context():
            # Clear global state before each test
            active_games.clear()
            player_id_map.clear()
            player_to_room_map.clear()
            voice_chat_participants.clear()
        yield client

@pytest.fixture
def socketio_client(client):
    """A test client for the SocketIO server."""
    return socketio.test_client(app, flask_test_client=client)