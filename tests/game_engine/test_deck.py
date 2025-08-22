import unittest
import random
from unittest.mock import patch
import sys
import os

class Suit:
    HEARTS, DIAMONDS, CLUBS, SPADES = 'Hearts', 'Diamonds', 'Clubs', 'Spades'

class Rank:
    TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, TEN = '2', '3', '4', '5', '6', '7', '8', '9', '10'
    JACK, QUEEN, KING, ACE = 'Jack', 'Queen', 'King', 'Ace'

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __repr__(self):
        return f"Card(suit='{self.suit}', rank='{self.rank}')"
    
    def __str__(self):
        return f"{self.rank} of {self.suit}"
    
    def __eq__(self, other):
        return isinstance(other, Card) and self.suit == other.suit and self.rank == other.rank

class Deck:
    def __init__(self):
        self.cards = self._create_deck()

    def _create_deck(self):
        suits = [Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS, Suit.SPADES]
        ranks = [
            Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX, Rank.SEVEN,
            Rank.EIGHT, Rank.NINE, Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE
        ]
        return [Card(suit, rank) for suit in suits for rank in ranks]
    
    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self):
        if self.cards:
            return self.cards.pop(0)
        return None
    
    def __len__(self):
        return len(self.cards)
    
    def __str__(self):
        return ", ".join(str(card) for card in self.cards)

    def __repr__(self):
        return f"Deck(cards={[repr(card) for card in self.cards]})"

class TestDeck(unittest.TestCase):
    def setUp(self):
        """Set up a fresh deck before each test."""
        self.deck = Deck()
    
    def test_deck_creation(self):
        """Test that a new deck is created with 52 cards."""
        self.assertEqual(len(self.deck), 52)
        
        first_card = self.deck.cards[0]
        self.assertEqual(first_card.suit, Suit.HEARTS)
        self.assertEqual(first_card.rank, Rank.TWO)
        
        last_card = self.deck.cards[-1]
        self.assertEqual(last_card.suit, Suit.SPADES)
        self.assertEqual(last_card.rank, Rank.ACE)

    @patch('random.shuffle')
    def test_shuffle(self, mock_shuffle):
        """Test that the shuffle method calls random.shuffle."""
        initial_cards = list(self.deck.cards)
        
        self.deck.shuffle()
        
        mock_shuffle.assert_called_once_with(self.deck.cards)
        
        self.assertEqual(self.deck.cards, initial_cards)

    def test_deal_card_removes_top_card(self):
        """Test that deal_card removes the top card and reduces the deck size."""
        initial_len = len(self.deck)
        first_card = self.deck.cards[0]
        
        dealt_card = self.deck.deal_card()
        
        self.assertEqual(dealt_card, first_card)
        self.assertEqual(len(self.deck), initial_len - 1)
        self.assertNotIn(first_card, self.deck.cards)

    def test_deal_card_returns_none_when_empty(self):
        """Test that deal_card returns None when the deck is empty."""
        for _ in range(52):
            self.deck.deal_card()
            
        self.assertEqual(len(self.deck), 0)
        
        dealt_card = self.deck.deal_card()
        
        self.assertIsNone(dealt_card)

    def test_len_returns_correct_size(self):
        """Test the __len__ method returns the correct deck size."""
        self.assertEqual(len(self.deck), 52)
        self.deck.deal_card()
        self.assertEqual(len(self.deck), 51)
        
    def test_str_representation(self):
        """Test the string representation of the deck."""
        self.deck.deal_card()
        self.deck.deal_card()
        
        self.assertEqual(str(self.deck.cards[0]), "4 of Hearts")
        self.assertEqual(str(self.deck.cards[1]), "5 of Hearts")

    def test_repr_representation(self):
        """Test the developer-friendly representation of the deck."""
        repr_str = repr(self.deck)
        self.assertTrue(repr_str.startswith("Deck(cards=["))
        self.assertTrue(repr_str.endswith("])"))
        self.assertIn("Card(suit='Hearts', rank='2')", repr_str)
        
        self.deck.deal_card()
        self.deck.deal_card()
        repr_str = repr(self.deck)
        self.assertTrue(repr_str.startswith("Deck(cards=["))
        self.assertNotIn("Card(suit='Hearts', rank='2')", repr_str)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)