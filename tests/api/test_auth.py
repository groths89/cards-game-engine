import os
import boto3
from botocore.exceptions import ClientError
from unittest.mock import patch, MagicMock
import pytest
from functools import wraps
from flask import Flask, request, jsonify, session

os.environ['ENVIRONMENT'] = 'local'

cognito_client = boto3.client('cognito-idp', region_name=os.getenv('COGNITO_REGION', 'us-east-1'))

from api.auth_utils import create_cognito_user
from api.auth_utils import authenticate_cognito_user
from api.auth_utils import verify_cognito_token
from api.auth_utils import require_auth, get_current_user

@pytest.fixture(autouse=True)
def mock_dependencies():
    with patch('api.auth_utils.cognito_client', new=MagicMock()) as mock_client:
        yield mock_client


@patch('api.auth_utils.cognito_client')
def test_create_cognito_user_success(mock_client):
    mock_client.admin_create_user.return_value = {
        'User': {
            'Username': 'test_user_id',
            'Attributes': []
        }
    }
    
    response = create_cognito_user('testuser', 'password123', 'test@example.com')
    
    assert response['success'] is True
    assert response['user_id'] == 'cognito_testuser'

@patch('api.auth_utils.cognito_client')
def test_authenticate_cognito_user_success(mock_client):
    """Tests that a successful authentication returns the ID token."""
    mock_client.admin_initiate_auth.return_value = {
        'AuthenticationResult': {
            'IdToken': 'mock_valid_id_token',
            'AccessToken': 'mock_access_token',
            'TokenType': 'Bearer',
            'ExpiresIn': 3600
        },
        'ChallengeParameters': {}
    }
    
    response = authenticate_cognito_user('testuser', 'password123')
    
    assert response['success'] is True
    assert response['id_token'] == 'mock_id_token'

# @patch('api.auth_utils.cognito_client')
# def test_authenticate_cognito_user_failure(mock_client):
#     """Tests that a failed authentication returns an error message."""
#     mock_client.admin_initiate_auth.side_effect = ClientError(
#         {'Error': {'Code': 'NotAuthorizedException', 'Message': 'Incorrect username or password.'}},
#         'AdminInitiateAuth'
#     )
    
#     response = authenticate_cognito_user('testuser', 'wrongpassword')
    
#     assert response['success'] is False
#     assert 'error' in response

# def test_verify_cognito_token_valid():
#     """Tests that a valid token returns a successful verification result."""
#     response = verify_cognito_token('mock_valid_token')
#     assert response['success'] is True
#     assert response['user_id'] == 'mock_user_id'

# def test_verify_cognito_token_invalid():
#     """Tests that an invalid token returns an error."""
#     response = verify_cognito_token('invalid_token')
#     assert response['success'] is False
#     assert response['error'] == 'Token verification not implemented'

@pytest.fixture
def app_with_routes():
    """A test Flask app with a protected and unprotected route."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    @app.route('/protected')
    @require_auth
    def protected_route():
        return jsonify({'message': 'Access Granted'})
    
    @app.route('/user')
    def user_route():
        user = get_current_user()
        if user:
            return jsonify({'user_id': user})
        return jsonify({'user_id': None})

    return app

def test_require_auth_valid_token(app_with_routes):
    """Tests that the decorator allows access with a valid token."""
    with app_with_routes.test_client() as client:
        with patch('api.auth_utils.verify_cognito_token', return_value={'success': True}):
            response = client.get('/protected', headers={'Authorization': 'Bearer mock_token'})
            assert response.status_code == 200

def test_require_auth_no_header(app_with_routes):
    """Tests that the decorator denies access with no Authorization header."""
    with app_with_routes.test_client() as client:
        response = client.get('/protected')
        assert response.status_code == 401
        assert 'No authorization header' in response.json['error']

def test_require_auth_invalid_token(app_with_routes):
    """Tests that the decorator denies access with an invalid token."""
    with app_with_routes.test_client() as client:
        with patch('api.auth_utils.verify_cognito_token', return_value={'success': False}):
            response = client.get('/protected', headers={'Authorization': 'Bearer invalid_token'})
            assert response.status_code == 401
            assert 'Invalid token' in response.json['error']

def test_get_current_user_valid_token(app_with_routes):
    """Tests that get_current_user returns the user ID with a valid token."""
    with app_with_routes.test_client() as client:
        with client.session_transaction() as session:
            session['player_id'] = 'test_user'
        
        response = client.get('/user')
        assert response.json['user_id'] == 'test_user'

def test_get_current_user_no_token(app_with_routes):
    """Tests that get_current_user returns None with no Authorization header."""
    with app_with_routes.test_client() as client:
        response = client.get('/user')
        assert response.json['user_id'] is None