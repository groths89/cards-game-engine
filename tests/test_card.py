import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import Card

class TestCardClass(unittest.TestCase):
    def test_card_creation(self):
        card = Card("H", "5")
        assert card.suit == "H"
        assert card.rank == "5"
        assert str(card) == "5H"

    def test_card_value(self):
        card_ace = Card("S", "A")
        self.assertEqual(card_ace.get_value(), 14)
        card_two = Card("D", "2")
        self.assertEqual(card_two.get_value(), 2)
        card_three = Card("C", "3")
        self.assertEqual(card_three.get_value(), 3)

if __name__ == '__main__':
    unittest.main()
