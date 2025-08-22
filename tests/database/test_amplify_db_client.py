import pytest
import os
import boto3
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from io import StringIO

# We need to import the class from the file you provided.
# Assuming the file is named `amplify_db_client.py`
from database.amplify_client import AmplifyDynamoDBClient

@pytest.fixture(autouse=True)
def teardown_os_environ():
    """Fixture to ensure a clean slate for each test by resetting os.environ."""
    original_environ = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_environ)

@pytest.fixture
def mock_dynamodb():
    """Mocks the boto3.resource calls and returns a mock object."""
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb = MagicMock()
        mock_resource.return_value = mock_dynamodb
        yield mock_dynamodb

@pytest.fixture
def mock_print():
    """Mocks the built-in print function."""
    with patch('builtins.print') as mock:
        yield mock

# def test_init_local_environment(mock_dynamodb):
#     """Tests the __init__ method in a local environment with default table names."""
#     os.environ['ENVIRONMENT'] = 'local'
#     os.environ.pop('USERS_TABLE', None)
#     os.environ.pop('GAME_HISTORY_TABLE', None)
    
#     db_client = AmplifyDynamoDBClient()
    
#     assert db_client.users_table_name == 'gregs-games-users-local'
#     assert db_client.game_history_table_name == 'gregs-games-history-local'
#     mock_dynamodb.assert_called_once_with(
#         'dynamodb',
#         endpoint_url='http://localhost:8000',
#         region_name='us-east-1',
#         aws_access_key_id='dummy',
#         aws_secret_access_key='dummy'
#     )

# def test_init_production_environment(mock_dynamodb):
#     """Tests the __init__ method in a production environment."""
#     os.environ['ENVIRONMENT'] = 'production'
#     os.environ['USERS_TABLE'] = 'prod-users-table'
#     os.environ['GAME_HISTORY_TABLE'] = 'prod-history-table'
    
#     db_client = AmplifyDynamoDBClient()
    
#     assert db_client.users_table_name == 'prod-users-table'
#     assert db_client.game_history_table_name == 'prod-history-table'
#     mock_dynamodb.assert_called_once_with('dynamodb')

def test_init_local_with_custom_table_names(mock_dynamodb):
    """Tests local init with environment variables set."""
    os.environ['ENVIRONMENT'] = 'local'
    os.environ['USERS_TABLE'] = 'custom-users'
    os.environ['GAME_HISTORY_TABLE'] = 'custom-history'

    db_client = AmplifyDynamoDBClient()

    assert db_client.users_table_name == 'custom-users'
    assert db_client.game_history_table_name == 'custom-history'

def test_get_users_table_success(mock_dynamodb):
    """Tests that get_users_table returns the correct table object."""
    os.environ['ENVIRONMENT'] = 'local'
    db_client = AmplifyDynamoDBClient()
    
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    table = db_client.get_users_table()
    
    mock_dynamodb.Table.assert_called_once_with('gregs-games-users-local')
    assert table == mock_table

def test_get_users_table_none_name_raises_error(mock_dynamodb):
    """Tests that get_users_table raises a ValueError if name is None."""
    os.environ['ENVIRONMENT'] = 'production'
    os.environ.pop('USERS_TABLE', None)
    db_client = AmplifyDynamoDBClient()
    
    with pytest.raises(ValueError, match="DynamoDB USERS_TABLE environment variable not set or is None."):
        db_client.get_users_table()

def test_get_game_history_table_success(mock_dynamodb):
    """Tests that get_game_history_table returns the correct table object."""
    os.environ['ENVIRONMENT'] = 'local'
    db_client = AmplifyDynamoDBClient()
    
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    table = db_client.get_game_history_table()
    
    mock_dynamodb.Table.assert_called_once_with('gregs-games-history-local')
    assert table == mock_table

def test_get_game_history_table_none_name_raises_error(mock_dynamodb):
    """Tests that get_game_history_table raises a ValueError if name is None."""
    os.environ['ENVIRONMENT'] = 'production'
    os.environ.pop('GAME_HISTORY_TABLE', None)
    db_client = AmplifyDynamoDBClient()
    
    with pytest.raises(ValueError, match="DynamoDB GAME_HISTORY_TABLE environment variable not set or is None."):
        db_client.get_game_history_table()


def test_create_tables_in_local_environment(mock_dynamodb, mock_print):
    """Tests that tables are created in a local environment."""
    os.environ['ENVIRONMENT'] = 'local'
    db_client = AmplifyDynamoDBClient()
    
    db_client.create_tables()
    
    assert mock_dynamodb.create_table.call_count == 2
    mock_print.assert_any_call("Created gregs-games-users-local table")
    mock_print.assert_any_call("Created gregs-games-history-local table")

def test_create_tables_in_production_environment(mock_dynamodb, mock_print):
    """Tests that table creation is skipped in a production environment."""
    os.environ['ENVIRONMENT'] = 'production'
    db_client = AmplifyDynamoDBClient()
    
    db_client.create_tables()
    
    mock_dynamodb.create_table.assert_not_called()
    mock_print.assert_called_once_with("Table creation skipped - not in local environment")

def test_create_tables_handles_resource_in_use_exception(mock_dynamodb, mock_print):
    """Tests that ResourceInUseException is handled gracefully."""
    os.environ['ENVIRONMENT'] = 'local'
    db_client = AmplifyDynamoDBClient()
    
    # Simulate the first table existing
    mock_dynamodb.create_table.side_effect = [
        ClientError({'Error': {'Code': 'ResourceInUseException'}}, 'CreateTable'),
        MagicMock()  # For the second table
    ]
    
    db_client.create_tables()
    
    # Assert that create_table was still called for both tables, despite the error
    assert mock_dynamodb.create_table.call_count == 2
    mock_print.assert_any_call("Created gregs-games-history-local table")
    assert "Table creation skipped" not in mock_print.call_args_list[0][0]

def test_create_tables_re_raises_other_client_errors(mock_dynamodb):
    """Tests that other ClientErrors are re-raised."""
    os.environ['ENVIRONMENT'] = 'local'
    db_client = AmplifyDynamoDBClient()
    
    # Simulate a different error, like an invalid parameter
    mock_dynamodb.create_table.side_effect = ClientError(
        {'Error': {'Code': 'InvalidParameterValueException', 'Message': 'Invalid parameter.'}},
        'CreateTable'
    )
    
    with pytest.raises(ClientError, match='InvalidParameterValueException'):
        db_client.create_tables()