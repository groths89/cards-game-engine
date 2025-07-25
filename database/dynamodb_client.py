import os
from .amplify_client import amplify_db_client

# Use Amplify client for production, local client for development
if os.environ.get('ENVIRONMENT') == 'production':
    db_client = amplify_db_client
else:
    # Keep your existing local DynamoDB client
    from .local_dynamodb_client import LocalDynamoDBClient
    db_client = LocalDynamoDBClient()
