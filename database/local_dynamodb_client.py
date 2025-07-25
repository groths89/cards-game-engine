import boto3
import os

class LocalDynamoDBClient:
    def __init__(self):
        # Local development configuration
        self.users_table_name = os.environ.get('USERS_TABLE', 'gregs-games-users-local')
        self.game_history_table_name = os.environ.get('GAME_HISTORY_TABLE', 'gregs-games-history-local')
        
        self.dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=os.environ.get('DYNAMODB_ENDPOINT', 'http://localhost:8000'),
            region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'dummy'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'dummy')
        )
    
    def get_users_table(self):
        return self.dynamodb.Table(self.users_table_name)
    
    def get_game_history_table(self):
        return self.dynamodb.Table(self.game_history_table_name)
