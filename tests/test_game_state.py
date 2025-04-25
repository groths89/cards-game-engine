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
        players = [Player(name) for name in player_names]
        test_deck = Deck()
        three_of_clubs = None
        for card in test_deck.cards:
            if card.suit == "Clubs" and card.rank == 3:
                three_of_clubs = card
                break
        if three_of_clubs:
            test_deck.cards.remove(three_of_clubs)
            test_deck.cards.insert(2, three_of_clubs)
        game_state = GameState(player_names)
        game_state.deck.cards = test_deck.cards
        game_state.deal_cards_to_players()
        self.assertEqual(game_state.get_current_player().name, "Charlie")

if __name__ == "__main__":
    unittest.main()