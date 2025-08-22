import unittest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from game_engine.hand import Hand
from game_engine.card import Card, Suit, Rank

class TestHand(unittest.TestCase):
    """
    Unit tests for the Hand class.
    """

    def test_init_with_no_cards(self):
        """Tests that a Hand is initialized with an empty list by default."""
        hand = Hand()
        self.assertEqual(hand.cards, [])

    def test_init_with_cards(self):
        """Tests that a Hand can be initialized with a list of cards."""
        card1 = MagicMock(spec=Card)
        card2 = MagicMock(spec=Card)
        hand = Hand(cards=[card1, card2])
        self.assertEqual(hand.cards, [card1, card2])

    def test_add_card(self):
        """Tests that add_card appends a single card to the hand."""
        hand = Hand()
        card = MagicMock(spec=Card)
        hand.add_card(card)
        self.assertEqual(hand.cards, [card])
        self.assertEqual(len(hand.cards), 1)

    def test_remove_card_success(self):
        """Tests that remove_card successfully removes a card present in the hand."""
        card1 = MagicMock(spec=Card)
        card2 = MagicMock(spec=Card)
        hand = Hand(cards=[card1, card2])
        hand.remove_card(card1)
        self.assertEqual(hand.cards, [card2])
        self.assertEqual(len(hand.cards), 1)

    def test_remove_card_not_in_hand(self):
        """Tests that remove_card handles the case where the card is not in the hand."""
        card1 = MagicMock(spec=Card)
        hand = Hand(cards=[card1])
        card_to_remove = MagicMock(spec=Card)
        with patch('builtins.print') as mock_print:
            hand.remove_card(card_to_remove)
            self.assertEqual(hand.cards, [card1])
            mock_print.assert_called_with(f"Error: Tried to remove a card not in hand: {card_to_remove}")
    
    def test_sort_by_rank(self):
        """Tests that sort_by_rank sorts the cards based on their rank value."""
        card2 = Card(Suit.SPADES, Rank.TWO)
        cardA = Card(Suit.CLUBS, Rank.ACE)
        cardK = Card(Suit.DIAMONDS, Rank.KING)
        card3 = Card(Suit.HEARTS, Rank.THREE)

        hand = Hand(cards=[cardA, card3, card2, cardK])
        hand.sort_by_rank()

        expected_order = [card2, card3, cardK, cardA]
        self.assertEqual(hand.cards, expected_order)

    def test_play_cards(self):
        """Tests that play_cards correctly removes and returns the specified cards."""
        card2 = MagicMock(spec=Card)
        cardA = MagicMock(spec=Card)
        cardK = MagicMock(spec=Card)
        card3 = MagicMock(spec=Card)
        
        card2.__hash__ = MagicMock(return_value=1)
        cardA.__hash__ = MagicMock(return_value=2)
        cardK.__hash__ = MagicMock(return_value=3)
        card3.__hash__ = MagicMock(return_value=4)

        hand = Hand(cards=[card2, card3, cardA, cardK])
        
        # Act
        played = hand.play_cards([cardA, card3])
        
        # Assert
        self.assertEqual(set(played), {cardA, card3})
        self.assertEqual(set(hand.cards), {card2, cardK})
        
    def test_clear(self):
        """Tests that clear removes all cards from the hand."""
        card1 = MagicMock(spec=Card)
        hand = Hand(cards=[card1])
        hand.clear()
        self.assertEqual(hand.cards, [])

    def test_get_cards_by_rank(self):
        """Tests that get_cards_by_rank returns all cards of a specific rank."""
        card2_s = Card(Suit.SPADES, Rank.TWO)
        card3_h = Card(Suit.HEARTS, Rank.THREE)
        card3_d = Card(Suit.DIAMONDS, Rank.THREE)
        
        hand = Hand(cards=[card2_s, card3_h, card3_d])
        
        # Act
        threes = hand.get_cards_by_rank(Rank.THREE)
        
        # Assert
        self.assertEqual(threes, [card3_h, card3_d])
        self.assertEqual(len(threes), 2)