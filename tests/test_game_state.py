import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from card_game_engine import GameState, Player, Card, Deck # Import necessary classes

class TestGameStateClass(unittest.TestCase):
    def test_initial_state(self):
        player_names = ["Alice", "Bob", "Charlie"]
        game_state = GameState(player_names)

        self.assertEqual(len(game_state.deck), 0)
        self.assertEqual(len(game_state.players), 3)
        self.assertIsNotNone(game_state.get_current_player())
        self.assertEqual(len(game_state.get_game_pile()), 0)
        self.assertFalse(game_state.is_game_over())

    def test_starting_player_scenario(self):
        player_names = ["Alice", "Bob", "Charlie"]
        game_state = GameState(player_names)  # Creates and deals a shuffled deck

        three_of_clubs = Card("Clubs", 3)

        # Find if anyone has the 3 of Clubs and remove it
        for player in game_state.players:
            if three_of_clubs in player.get_hand().cards:
                player.get_hand().cards.remove(three_of_clubs)
                break

        # Add the 3 of Clubs to Charlie's hand (Charlie is at index 2)
        game_state.players[2].get_hand().add_card(three_of_clubs)

        # Determine the starting player
        starting_player_index = game_state.determine_starting_player()
        starting_player = game_state.get_current_player()

        self.assertEqual(starting_player.name, "Charlie")

if __name__ == "__main__":
    unittest.main()