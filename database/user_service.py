from decimal import Decimal
from datetime import datetime
import os
import boto3
from botocore.exceptions import ClientError

class UserService:
    def __init__(self):
        # Import the appropriate client based on environment
        if os.environ.get('ENVIRONMENT') == 'local':
            from database.local_dynamodb_client import LocalDynamoDBClient
            self.db_client = LocalDynamoDBClient()
            self.users_table = self.db_client.get_users_table()
        else:
            from database.amplify_client import AmplifyDynamoDBClient
            self.db_client = AmplifyDynamoDBClient()
            self.users_table = self.db_client.get_users_table()

    def _format_profile_for_frontend(self, profile):
        """Helper to convert Decimal objects to floats/ints for frontend compatibility."""
        if not profile:
            return profile

        formatted_profile = profile.copy() # Work on a copy to avoid modifying original DynamoDB item

        # Convert Decimal types to appropriate numbers (int or float)
        if 'games_played' in formatted_profile and isinstance(formatted_profile['games_played'], Decimal):
            formatted_profile['games_played'] = int(formatted_profile['games_played'])
        if 'games_won' in formatted_profile and isinstance(formatted_profile['games_won'], Decimal):
            formatted_profile['games_won'] = int(formatted_profile['games_won'])
        if 'win_rate' in formatted_profile and isinstance(formatted_profile['win_rate'], Decimal):
            # Win rate should be a float, maybe format it to a certain precision
            formatted_profile['win_rate'] = float(formatted_profile['win_rate']) # Keep as float, frontend can format

        # You might also want to ensure any other numbers (if added later) are handled
        # Example:
        # if 'level' in formatted_profile and isinstance(formatted_profile['level'], Decimal):
        #     formatted_profile['level'] = int(formatted_profile['level'])

        return formatted_profile

    def get_user_profile(self, user_id):
        try:
            response = self.users_table.get_item(
                Key={'user_id': user_id}
            )

            if 'Item' in response:
                # Use the helper function here
                return {'success': True, 'profile': self._format_profile_for_frontend(response['Item'])}
            else:
                return {'success': False, 'error': 'User not found'}
        except ClientError as e:
            print(f"Error getting user: {e}")
            return {'success': False, 'error': str(e)}
        except Exception as e:
            print(f"Error getting user: {e}")
            return {'success': False, 'error': str(e)}

    def create_user_profile(self, user_id, username, email=None):
        try:
            item = {
                'user_id': user_id,
                'username': username,
                'email': email,
                'games_played': 0, # Stored as int/number, DynamoDB will handle it
                'games_won': 0,     # Stored as int/number
                'win_rate': Decimal('0.0'), # Stored as Decimal, will be converted on retrieval
                'user_type': 'registered',
                'created_at': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat()
            }

            self.users_table.put_item(Item=item)
            # When returning the newly created item, also format it
            return {'success': True, 'profile': self._format_profile_for_frontend(item)}
        except Exception as e:
            print(f"Error creating user: {e}")
            return {'success': False, 'error': str(e)}

    def update_user_stats(self, user_id, games_played_delta=0, games_won_delta=0):
        try:
            response = self.users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression='ADD games_played :gp, games_won :gw SET last_active = :la',
                ExpressionAttributeValues={
                    ':gp': games_played_delta,
                    ':gw': games_won_delta,
                    ':la': datetime.now().isoformat()
                },
                ReturnValues='ALL_NEW'
            )

            # Calculate win rate
            item = response['Attributes']
            if item['games_played'] > 0:
                # Ensure conversion to float for calculation if they are still Decimal here
                games_won_numeric = float(item['games_won']) if isinstance(item['games_won'], Decimal) else item['games_won']
                games_played_numeric = float(item['games_played']) if isinstance(item['games_played'], Decimal) else item['games_played']

                win_rate = Decimal(str(games_won_numeric)) / Decimal(str(games_played_numeric))
                self.users_table.update_item(
                    Key={'user_id': user_id},
                    UpdateExpression='SET win_rate = :wr',
                    ExpressionAttributeValues={':wr': win_rate}
                )
                item['win_rate'] = win_rate # Update the item dictionary with the calculated Decimal
            else:
                item['win_rate'] = Decimal('0.0') # Set to 0.0 if no games played


            return {'success': True, 'profile': self._format_profile_for_frontend(item)} # <--- Also format here
        except Exception as e:
            print(f"Error updating user stats: {e}")
            return {'success': False, 'error': str(e)}

    def create_user(self, user_id, username, user_type="anonymous", email=None):
        """Create a new user - alias for create_user_profile for compatibility"""
        return self.create_user_profile(user_id, username, email)

    def get_or_create_user(self, user_id, username, user_type="anonymous", email=None):
        """Get existing user or create new one"""
        try:
            # Try to get existing user first
            user_profile = self.get_user_profile(user_id)
            if user_profile and user_profile.get('success'):
                return user_profile['profile']
            
            # If user doesn't exist, create new one
            result = self.create_user_profile(user_id, username, email)
            if result and result.get('success'):
                return result['profile']
            
            return None
        except Exception as e:
            print(f"Error in get_or_create_user: {e}")
            return None

    def get_user(self, user_id):
        """Get user - alias for get_user_profile for compatibility"""
        result = self.get_user_profile(user_id)
        if result and result.get('success'):
            return result['profile']
        return None

# Create a global instance
user_service = UserService()



