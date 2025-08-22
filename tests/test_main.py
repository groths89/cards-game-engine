import unittest
from unittest.mock import patch

import main

class TestMain(unittest.TestCase):
    """
    Unit tests for the main.py script.
    """

    @patch('main.AssholeGame')
    @patch('builtins.print')
    def test_main_execution(self, mock_print, mock_AssholeGame):
        """
        Tests that the main script block correctly initializes a game
        and prints the start message.
        """
        # Arrange

        # Act
        main.main()

        # Assert
        mock_AssholeGame.assert_called_once()
        mock_print.assert_called_once_with("Card game engine started!")

if __name__ == '__main__':
    unittest.main()