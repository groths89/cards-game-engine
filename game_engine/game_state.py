from .deck import Deck
from .player import Player

from .utils import get_rank_name
class GameState:
    def __init__(self, players):
        self.deck = Deck()
        self.players = [Player(name) for name in players]
        self.pile = []
        self.current_play_rank = None
        self.current_play_count = None
        self.current_player_index = self.determine_starting_player()
        self.status = "CLI_MODE"
    
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
        if self.players and 0 <= self.current_player_index < len(self.players):
            return self.players[self.current_player_index]
        return None
    
    def get_current_player_id(self):
        player = self.get_current_player()
        return player.player_id if player else None
    
    def get_player_by_id(self, player_id):
        for player in self.players:
            if player.player_id == player_id:
                return player
        return None
    
    def get_num_players(self):
        """Returns the total number of players in the game."""
        return len(self.players)

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
    
    @property
    def is_game_started(self):
        return self.status == "IN_PROGRESS"

    @property
    def is_game_over(self):
        return self.status == "FINISHED" # Use status attribute for clarity