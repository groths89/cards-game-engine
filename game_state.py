from deck import Deck
from player import Player

from utils import get_rank_name
class GameState:
    def __init__(self, players):
        self.deck = Deck()
        self.players = [Player(name) for name in players]
        self.pile = []
        self.current_play_rank = None
        self.current_play_count = None
        self.current_player_index = self.determine_starting_player()
        self.game_over = False
    
    # Create a method that deals a card to each player in the list
    def deal_cards(self, num_cards):
        """Deals a specified number of cards to each player."""
        self.deck.shuffle()
        for _ in range(num_cards):
            for player in self.players:
                card = self.deck.deal_card()
                if card: # Check if a card was actually dealt
                    player.hand.add_card(card)

    # Create a method that determines the starting player
    def determine_starting_player(self):
        """
        Determines the starting player for the first round.
        This is a generic method that can be overridden by subclasses.
        By default, it returns the first player in the list.
        """
        return 0

    # Create a method to get the current player
    def get_current_player(self):
        if self.players:
            return self.players[self.current_player_index]
        return None

    def next_player(self, skip=False):
        """Advances to the next player's turn."""
        if not self.players:
            return None
        
        start_index = self.current_player_index
        increment = 2 if skip else 1

        while True:
            self.current_player_index = (self.current_player_index + increment) % len(self.players)
            if self.players[self.current_player_index].is_active:
                return self.players[self.current_player_index]
            if self.current_player_index == start_index:
                print("Warning: Looped through all players, none are active?")
                return None

    # Create a method for what happens on that players turn
    def play_turn(self, player, cards_to_play):
        current_player = self.get_current_player()
        if (current_player != player):
            print(f"It's not {player.name}'s turn. It's {current_player.name}'s turn.")
            return
        
        if not cards_to_play and self.pile: # Empty "cards_to_play" is now handled by "pass_turn" method
            print(f"{player.name} must use the pass action.")
            return
        elif not cards_to_play and not self.pile:
            print(f"{player.name} must play at least one card to start the round.")
            return

        # Basic logic - subclasses will add more specific validation
        player_hand = player.get_hand().cards
        for card_to_play in cards_to_play:
            if card_to_play not in player_hand:
                print(f"{player.name} does not have the card {card_to_play} in their hand.")
                return
        
        player.play_cards(cards_to_play)
        self.pile.extend(cards_to_play)
        self.next_player()

    def pass_turn(self, player):
        """Handles a player passing their turn. Subclasses might add more logic."""
        current_player = self.get_current_player()
        if player == current_player:
            print(f"{player.name} passes.")
        else:
            print(f"It's not {player.name}'s turn to pass.")

    # Create a method for the game pile
    def get_game_pile(self):
        # When method is called anywhere in the game state it returns the list "pile" that we initiated earlier
        return self.pile
    
    # Create a method to check for the game over state
    def is_game_over(self):
        num_active_players = 0 # Initialize the local variable counter "num_active_players"
        # Loops through the "players" from __init__ and creates a variable
        for player in self.players:
            # Then checks whether the attribute of a player "is_active" and adds 1 for each player that has "is_active" set to true
            if player.is_active:
                num_active_players += 1
        # When method is called it does the check whether game is over and returns true or false
        return num_active_players == 1