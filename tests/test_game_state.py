import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from card_game_engine import GameState, Player, Card, Deck # Import necessary classes

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
        alice_plays = [Card("Hearts", 5)]
        self.alice.hand.cards = [Card("Hearts", 5), Card("Clubs", 2)]

        # Act
        self.game_state.play_turn(self.alice, alice_plays)

        # Assert
        self.assertEqual(len(self.game_state.pile), 1)
        self.assertIn(Card("Hearts", 5), self.game_state.pile)
        self.assertNotIn(Card("Hearts", 5), self.alice.hand.cards)
        self.assertEqual(self.game_state.get_current_player(), self.bob)

    def test_play_turn_wrong_player(self):
        # Arrange
        self.game_state.current_player_index = 0  # Alice's turn
        bob_tries_to_play = [Card("Clubs", 2)]
        self.bob.hand.cards = [Card("Clubs", 2)]

        # Act
        self.game_state.play_turn(self.bob, bob_tries_to_play)

        # Assert
        self.assertEqual(len(self.game_state.pile), 0)
        self.assertEqual(self.game_state.get_current_player(), self.alice)
        self.assertIn(Card("Clubs", 2), self.bob.hand.cards)

    # TODO: Add more test methods for other scenarios (invalid card, invalid rank, etc.)
    # TODO: --Invalid Play - Player doesn't have the card: Test what happens when a player tries to play a card that is not in their hand. Assert that the pile remains empty and the turn doesn't advance.
    # TODO: --Invalid Starting Play - Different Ranks: Test if a player tries to start a trick with multiple cards of different ranks. Assert that the pile remains empty and the turn doesn't advance.
    # TODO: --Valid Play Over Pile - Higher Rank, Same Count: Test if a player can successfully play cards of a higher rank and the same count as the current play on the pile. Assert that the pile is updated, the current play rank and count are updated, and the turn advances.
    # TODO: --Invalid Play Over Pile - Lower Rank: Test if a player tries to play cards of a lower rank than the current play on the pile. Assert that the pile remains the same and the turn doesn't advance.
    # TODO: --Invalid Play Over Pile - Wrong Count: Test if a player tries to play a different number of cards than the current play on the pile. Assert that the pile remains the same and the turn doesn't advance.

if __name__ == "__main__":
    unittest.main()