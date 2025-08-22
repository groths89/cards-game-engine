import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import GameState, Player, Card, Deck # Import necessary classes

class TestGameStateClass(unittest.TestCase):
    def setUp(self):
        """Set up a basic game state with two players before each test."""
        self.player_names = ["Alice", "Bob"]
        self.game_state = GameState(self.player_names)
        self.alice = self.game_state.players[0]
        self.bob = self.game_state.players[1]

    def test_play_turn_valid_starting_play(self):
        # Arrange
        self.game_state.current_player_index = 0  # Alice's turn
        alice_plays = [Card("H", "5")]
        
        # Add the card to Alice's hand first
        self.game_state.players[0].hand.add_card(alice_plays[0])
        
        # Act
        result = self.game_state.play_turn(self.alice, alice_plays)
        
        # Assert
        # Check that the play was processed (pile has cards)
        self.assertEqual(len(self.game_state.pile), 1)
        # The basic GameState doesn't set current_play_rank - that's game-specific logic
        self.assertEqual(self.game_state.pile[0], alice_plays[0])

    def test_play_turn_wrong_player(self):
        # Arrange
        self.game_state.current_player_index = 0  # Alice's turn
        bob_tries_to_play = [Card("C", "2")]
        
        # Add the card to Bob's hand
        self.game_state.players[1].hand.add_card(bob_tries_to_play[0])
        
        # Act
        result = self.game_state.play_turn(self.bob, bob_tries_to_play)
        
        # Assert - The play should be rejected (pile remains empty)
        self.assertEqual(len(self.game_state.pile), 0)
        self.assertIsNone(self.game_state.current_play_rank)

    # TODO: Add more test methods for other scenarios (invalid card, invalid rank, etc.)
    # TODO: --Invalid Play - Player doesn't have the card: Test what happens when a player tries to play a card that is not in their hand. Assert that the pile remains empty and the turn doesn't advance.
    # TODO: --Invalid Starting Play - Different Ranks: Test if a player tries to start a trick with multiple cards of different ranks. Assert that the pile remains empty and the turn doesn't advance.
    # TODO: --Valid Play Over Pile - Higher Rank, Same Count: Test if a player can successfully play cards of a higher rank and the same count as the current play on the pile. Assert that the pile is updated, the current play rank and count are updated, and the turn advances.
    # TODO: --Invalid Play Over Pile - Lower Rank: Test if a player tries to play cards of a lower rank than the current play on the pile. Assert that the pile remains the same and the turn doesn't advance.
    # TODO: --Invalid Play Over Pile - Wrong Count: Test if a player tries to play a different number of cards than the current play on the pile. Assert that the pile remains the same and the turn doesn't advance.

if __name__ == "__main__":
    unittest.main()
