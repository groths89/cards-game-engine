import unittest
import sys
import os

# Assume a similar structure to previous tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from game_engine.utils import get_rank_name

class TestUtils(unittest.TestCase):
    """
    Unit tests for the utility functions in utils.py.
    """

    def test_get_rank_name_numerical_ranks(self):
        """
        Test that numerical ranks (2 through 10) are converted to strings.
        """
        for rank in range(2, 11):
            with self.subTest(rank=rank):
                self.assertEqual(get_rank_name(rank), str(rank))

    def test_get_rank_name_face_cards(self):
        """
        Test that face card ranks are converted to their names.
        """
        self.assertEqual(get_rank_name(11), "Jack")
        self.assertEqual(get_rank_name(12), "Queen")
        self.assertEqual(get_rank_name(13), "King")

    def test_get_rank_name_ace(self):
        """
        Test that the Ace rank is converted to its name.
        """
        self.assertEqual(get_rank_name(14), "Ace")

    def test_get_rank_name_out_of_range(self):
        """
        Test that ranks outside the expected range are handled gracefully.
        """
        self.assertEqual(get_rank_name(1), "1")
        self.assertEqual(get_rank_name(15), "15")
        self.assertEqual(get_rank_name(0), "0")
        self.assertEqual(get_rank_name(-5), "-5")
        self.assertEqual(get_rank_name(100), "100")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)