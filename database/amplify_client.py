import boto3
import os
from botocore.exceptions import ClientError

class AmplifyDynamoDBClient:
    def __init__(self):
        # Use Amplify-generated table names in production
        if os.environ.get('ENVIRONMENT') == 'production':
            # These will be set by Amplify deployment
            self.users_table_name = os.environ.get('AMPLIFY_USER_TABLE_NAME')
            self.game_history_table_name = os.environ.get('AMPLIFY_GAME_HISTORY_TABLE_NAME')
            self.dynamodb = boto3.resource('dynamodb')
        else:
            # Local development
            self.users_table_name = os.environ.get('USERS_TABLE', 'gregs-games-users-local')
            self.game_history_table_name = os.environ.get('GAME_HISTORY_TABLE', 'gregs-games-history-local')
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url='http://localhost:8000',
                region_name='us-east-1',
                aws_access_key_id='dummy',
                aws_secret_access_key='dummy'
            )
    
    def get_users_table(self):
        return self.dynamodb.Table(self.users_table_name)
    
    def get_game_history_table(self):
        return self.dynamodb.Table(self.game_history_table_name)
    
    def create_tables(self):
        """Create tables - only works for local development"""
        if os.environ.get('ENVIRONMENT') != 'local':
            print("Table creation skipped - not in local environment")
            return
            
        try:
            # Users table
            self.dynamodb.create_table(
                TableName=self.users_table_name,
                KeySchema=[
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            print(f"Created {self.users_table_name} table")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise
        
        try:
            # Game history table
            self.dynamodb.create_table(
                TableName=self.game_history_table_name,
                KeySchema=[
                    {'AttributeName': 'game_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'user_id', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'game_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'UserGameHistory',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'game_id', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            print(f"Created {self.game_history_table_name} table")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise

# Global instance
amplify_db_client = AmplifyDynamoDBClient()
