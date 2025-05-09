from game_loop import GameLoop
from game_state import GameState
from player import Player

class AssholeGame(GameState):
    def __init__(self, players):
        super(AssholeGame, self).__init__(players)
        self.special_card_rules = True # Example

    def play_turn(self, player, cards_to_play):
        """
        Overrides the play_turn method in GameState to implement Asshole-specific rules.
        """
    
        super(AssholeGame, self).play_turn(player, cards_to_play) # Call the superclass method
        #  implement Asshole game logic