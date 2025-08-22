import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Dynamically add the project root to the Python path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the AssholeGame class and its dependencies for mocking
from game_engine.games.asshole import AssholeGame
from game_engine.deck import Deck
from game_engine.player import Player

class TestAssholeGameInit(unittest.TestCase):
    """
    Unit tests specifically for the __init__ method of the AssholeGame class.
    This ensures all attributes are correctly initialized.
    """

    @patch('game_engine.deck.Deck')
    def test_asshole_game_initialization(self, mock_deck):
        """
        Tests that an AssholeGame instance is correctly initialized with all its default values.
        """
        # Arrange - Mock the dependencies
        mock_deck_instance = MagicMock(spec=Deck)
        mock_deck.return_value = mock_deck_instance

        # Act - Initialize the AssholeGame with and without a room code
        game_with_room = AssholeGame(room_code="ABCD")
        game_without_room = AssholeGame()

        # Assert - Check all attributes for the room-based game
        self.assertEqual(game_with_room.room_code, "ABCD")
        self.assertIsNone(game_with_room.host_id)
        self.assertEqual(game_with_room.game_type, "asshole")
        self.assertEqual(game_with_room.status, "WAITING")
        self.assertEqual(game_with_room.MIN_PLAYERS, 4)
        self.assertEqual(game_with_room.MAX_PLAYERS, 10)
        # self.assertIsInstance(game_with_room.deck, mock_deck_instance)
        self.assertEqual(game_with_room.special_card_rules, True)
        self.assertEqual(game_with_room.player_went_out, 0)
        self.assertEqual(game_with_room.threes_played_this_round, 0)
        self.assertEqual(game_with_room.consecutive_passes, 0)
        self.assertEqual(game_with_room.same_rank_streak, 0)
        self.assertEqual(game_with_room.turn_direction, "clockwise")
        self.assertEqual(game_with_room.should_skip_next_player, False)
        self.assertEqual(game_with_room.pile_cleared_this_turn, False)
        self.assertEqual(game_with_room.cards_of_rank_played, {rank: 0 for rank in range(2, 15)})
        self.assertEqual(game_with_room.game_message, "Waiting for players to join...")
        self.assertEqual(game_with_room.last_played_cards, [])
        self.assertIsNone(game_with_room.current_play_rank)
        self.assertEqual(game_with_room.current_play_count, 0)
        self.assertIsNone(game_with_room.round_leader_player_id)
        self.assertIsNone(game_with_room.last_played_player_id)
        self.assertEqual(game_with_room.interrupt_active, False)
        self.assertIsNone(game_with_room.interrupt_type)
        self.assertIsNone(game_with_room.interrupt_initiator_player_id)
        self.assertIsNone(game_with_room.interrupt_rank)
        self.assertEqual(game_with_room.interrupt_bids, [])
        self.assertIsNone(game_with_room.interrupt_active_until)
        self.assertEqual(game_with_room.interrupt_initial_pile_count, 0)
        self.assertEqual(game_with_room.players_responded_to_interrupt, set())
        self.assertEqual(game_with_room.INTERRUPT_TIMEOUT_SECONDS, 15)

        # Assert - Check attributes for the CLI-based game
        self.assertIsNone(game_without_room.room_code)
        self.assertEqual(game_without_room.status, "CLI_MODE")
        # self.assertIsInstance(game_without_room.deck, MagicMock)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)