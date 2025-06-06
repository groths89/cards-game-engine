import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import Card

class TestCardClass(unittest.TestCase):
    def test_card_creation(self):
        card = Card("Hearts", 5)
        self.assertEqual(card.suit, "Hearts")
        self.assertEqual(card.rank, 5)
        self.assertEqual(str(card), "H5")

    def test_card_value(self):
        card_ace = Card("Spades", 14)
        self.assertEqual(card_ace.get_value(), 14)
        card_two = Card("Diamonds", 2)
        self.assertEqual(card_two.get_value(), 15)
        card_three = Card("Clubs", 3)
        self.assertEqual(card_three.get_value(), 3)

if __name__ == '__main__':
    unittest.main()