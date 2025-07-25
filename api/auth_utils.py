import os
import jwt
import boto3
from botocore.exceptions import ClientError
from functools import wraps
from flask import request, jsonify, session

def create_cognito_user(username, password, email):
    """Create a new user in Cognito."""
    if os.environ.get('ENVIRONMENT') == 'local':
        # Mock for local development
        return {
            'success': True,
            'user_id': f"cognito_{username}",
            'message': 'Mock user created'
        }
    
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=os.getenv('COGNITO_REGION', 'us-east-1')
        )
        
        response = cognito_client.admin_create_user(
            UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
            Username=username,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'}
            ],
            TemporaryPassword=password,
            MessageAction='SUPPRESS'
        )
        
        return {
            'success': True,
            'user_id': response['User']['Username']
        }
        
    except ClientError as e:
        return {
            'success': False,
            'error': str(e)
        }

def authenticate_cognito_user(username, password):
    """Authenticate user with Cognito."""
    if os.environ.get('ENVIRONMENT') == 'local':
        # Mock for local development
        return {
            'success': True,
            'user_id': f"cognito_{username}",
            'access_token': 'mock_access_token',
            'id_token': 'mock_id_token'
        }
    
    try:
        cognito_client = boto3.client(
            'cognito-idp',
            region_name=os.getenv('COGNITO_REGION', 'us-east-1')
        )
        
        response = cognito_client.admin_initiate_auth(
            UserPoolId=os.getenv('COGNITO_USER_POOL_ID'),
            ClientId=os.getenv('COGNITO_APP_CLIENT_ID'),
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        return {
            'success': True,
            'user_id': username,
            'access_token': response['AuthenticationResult']['AccessToken'],
            'id_token': response['AuthenticationResult']['IdToken']
        }
        
    except ClientError as e:
        return {
            'success': False,
            'error': str(e)
        }

def verify_cognito_token(token):
    """Verify Cognito JWT token."""
    if os.environ.get('ENVIRONMENT') == 'local' and token == 'mock_access_token':
        return {'success': True, 'user_id': 'mock_user'}
    
    # In production, implement proper JWT verification
    return {'success': False, 'error': 'Token verification not implemented'}

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            token = auth_header.split(' ')[1]  # Bearer <token>
            verification = verify_cognito_token(token)
            if not verification['success']:
                return jsonify({'error': 'Invalid token'}), 401
            
            request.current_user = verification
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({'error': 'Invalid authorization header'}), 401
    
    return decorated_function

def get_current_user():
    """Get current user from session or token."""
    return session.get('player_id')

