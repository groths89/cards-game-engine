import unittest
import uuid
from unittest.mock import patch, MagicMock

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from game_engine.player import Player
from game_engine.hand import Hand
from game_engine.card import Card, Suit, Rank

class TestPlayer(unittest.TestCase):
    """
    Unit tests for the Player class to ensure all methods
    behave as expected.
    """

    @patch('game_engine.player.Hand')
    def test_player_initialization(self, MockHand):
        """
        Tests that a Player instance is correctly initialized.
        """
        # Arrange
        mock_hand_instance = MockHand.return_value
        player_name = "Alice"
        
        # Act
        player = Player(name=player_name)
        
        # Assert
        self.assertEqual(player.name, player_name)
        self.assertIsInstance(player.player_id, str)
        self.assertIsNotNone(uuid.UUID(player.player_id, version=4))
        self.assertIs(player.hand, mock_hand_instance)
        self.assertIsNone(player.rank)
        self.assertTrue(player.is_active)
        self.assertFalse(player.is_out)

    @patch('game_engine.player.Hand')
    def test_player_initialization_with_custom_id(self, MockHand):
        """
        Tests that a Player instance is correctly initialized with a provided player_id.
        """
        # Arrange
        player_name = "Bob"
        player_id = "test-123"
        
        # Act
        player = Player(name=player_name, player_id=player_id)
        
        # Assert
        self.assertEqual(player.name, player_name)
        self.assertEqual(player.player_id, player_id)

    @patch('game_engine.player.Hand')
    def test_add_card(self, MockHand):
        """
        Tests that add_card correctly adds a card to the hand.
        """
        # Arrange
        player = Player(name="Charlie")
        mock_hand_instance = player.hand
        mock_card = MagicMock(spec=Card)
        
        # Act
        player.add_card(mock_card)
        
        # Assert
        mock_hand_instance.add_card.assert_called_once_with(mock_card)

    @patch('game_engine.player.Hand')
    def test_play_cards_success(self, MockHand):
        """
        Tests that play_cards successfully removes cards from the hand.
        """
        # Arrange
        player = Player(name="David")
        mock_hand_instance = player.hand
        mock_card_1 = MagicMock(spec=Card)
        mock_card_2 = MagicMock(spec=Card)
        
        mock_hand_instance.cards = [mock_card_1, mock_card_2]
        
        # Act
        player.play_cards([mock_card_1, mock_card_2])
        
        # Assert
        mock_hand_instance.remove_card.assert_any_call(mock_card_1)
        mock_hand_instance.remove_card.assert_any_call(mock_card_2)
        self.assertEqual(mock_hand_instance.remove_card.call_count, 2)

    @patch('game_engine.player.Hand')
    def test_play_cards_failure(self, MockHand):
        """
        Tests that play_cards handles trying to play a card not in the hand.
        """
        # Arrange
        player = Player(name="Eve")
        mock_hand_instance = player.hand
        mock_card_1 = MagicMock(spec=Card)
        mock_card_2 = MagicMock(spec=Card)
        
        mock_hand_instance.cards = [mock_card_1]
        
        # Act
        with patch('builtins.print') as mock_print:
            player.play_cards([mock_card_1, mock_card_2])
        
        # Assert
        mock_hand_instance.remove_card.assert_called_once_with(mock_card_1)
        mock_print.assert_called_with("Error: Eve tried to play a card they don't have: %s" % mock_card_2)

    @patch('game_engine.player.Hand')
    def test_has_card(self, MockHand):
        """
        Tests that has_card correctly checks for a card's presence.
        """
        # Arrange
        player = Player(name="Frank")
        mock_hand_instance = player.hand
        mock_card = MagicMock(spec=Card)
        
        mock_hand_instance.cards = [mock_card]
        
        # Act & Assert
        self.assertTrue(player.has_card(mock_card))
        self.assertFalse(player.has_card(MagicMock(spec=Card)))

    def test_get_hand(self):
        """
        Tests that get_hand returns the player's hand instance.
        """
        player = Player(name="Grace")
        self.assertIs(player.get_hand(), player.hand)

    def test_player_equality(self):
        """
        Tests that two players are equal if and only if they have the same player_id.
        """
        # Arrange
        player1_id = str(uuid.uuid4())
        player1 = Player(name="Heidi", player_id=player1_id)
        player2 = Player(name="Heidi", player_id=player1_id)
        player3 = Player(name="Ivan")
        
        # Act & Assert
        self.assertEqual(player1, player2)
        self.assertNotEqual(player1, player3)

    def test_player_hash(self):
        """
        Tests that players with the same player_id have the same hash value.
        """
        # Arrange
        player1_id = str(uuid.uuid4())
        player1 = Player(name="Judy", player_id=player1_id)
        player2 = Player(name="Judy", player_id=player1_id)
        
        # Act & Assert
        self.assertEqual(hash(player1), hash(player2))

    def test_to_dict(self):
        """
        Tests that to_dict returns a correct dictionary representation.
        """
        # Arrange
        player = Player(name="Kevin")
        player.hand.cards = [1, 2, 3]
        player.rank = 1
        player.is_out = True
        
        expected_dict = {
            'name': 'Kevin',
            'id': player.player_id,
            'is_active': True,
            'is_out': True,
            'rank': 1,
            'hand_size': 3
        }
        
        # Act
        player_dict = player.to_dict()
        
        # Assert
        self.assertEqual(player_dict, expected_dict)