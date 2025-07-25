import uuid
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from .dynamodb_client import db_client
from .user_service import user_service

class GameHistoryService:
    def __init__(self):
        self.game_history_table = db_client.get_game_history_table()
    
    def save_game_result(self, game):
        """Save completed game results and update player stats"""
        if not game.is_game_over:
            print("Warning: Attempting to save incomplete game")
            return False
        
        game_id = str(uuid.uuid4())
        completed_at = datetime.now(timezone.utc).isoformat()
        
        # Calculate game duration (you might want to track start time in game)
        duration_minutes = 0  # TODO: Add game start time tracking
        
        # Save game history for each player
        for player in game.players:
            game_record = {
                'game_id': game_id,
                'user_id': player.player_id,
                'room_code': game.room_code,
                'game_type': game.game_type,
                'final_rank': player.rank,
                'completed_at': completed_at,
                'duration_minutes': duration_minutes,
                'total_players': len(game.players),
                'players': [
                    {
                        'user_id': p.player_id,
                        'username': p.name,
                        'final_rank': p.rank
                    } for p in game.players
                ]
            }
            
            try:
                self.game_history_table.put_item(Item=game_record)
                
                # Update player stats
                games_won = 1 if player.rank == 1 else 0
                user_service.update_user_stats(
                    player.player_id,
                    games_played_increment=1,
                    games_won_increment=games_won
                )
                
            except ClientError as e:
                print(f"Error saving game result for player {player.player_id}: {e}")
        
        print(f"Game {game_id} results saved for {len(game.players)} players")
        return True
    
    def get_user_game_history(self, user_id, limit=10):
        """Get recent games for a user"""
        try:
            response = self.game_history_table.query(
                IndexName='UserGameHistory',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            return response.get('Items', [])
        except ClientError as e:
            print(f"Error getting user game history: {e}")
            return []
    
    def get_user_stats_summary(self, user_id):
        """Get aggregated stats for a user"""
        user = user_service.get_user(user_id)
        if not user:
            return None
        
        recent_games = self.get_user_game_history(user_id, limit=5)
        
        return {
            'user_id': user_id,
            'username': user['username'],
            'user_type': user['user_type'],
            'games_played': user.get('games_played', 0),
            'games_won': user.get('games_won', 0),
            'win_rate': user.get('games_won', 0) / max(user.get('games_played', 1), 1),
            'recent_games': recent_games,
            'member_since': user.get('created_at'),
            'last_active': user.get('last_active')
        }

# Global instance
game_history_service = GameHistoryService()

