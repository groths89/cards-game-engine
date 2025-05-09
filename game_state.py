from deck import Deck
from player import Player

class GameState:
    def __init__(self, players):
        self.deck = Deck()
        self.deck.shuffle()
        self.players = [Player(name) for name in players]
        self.pile = []
        self.current_play_rank = None
        self.current_play_count = None
        self.deal_cards_to_players()
        self.current_player_index = self.determine_starting_player()
        self.threes_played_this_round = 0 # Initialize the counter
        self.consecutive_passes = 0 # Initialize the consecutive passes counter
        self.same_rank_streak = 0 # Track consecutive plays of the same rank
        self.cards_of_rank_played = {rank: 0 for rank in range(2, 15)} # Track how many of each rank have been played
    
    # Create a method that deals the entire deck to each player in the list
    def deal_cards_to_players(self):
        self.number_of_players = len(self.players)
        player_index = 0
        while len(self.deck) > 0:
            card_to_deal = self.deck.deal_card()
            if card_to_deal:
                self.players[player_index].hand.add_card(card_to_deal)
                player_index = (player_index + 1) % self.number_of_players

    # Create a method that determines the starting player
    def determine_starting_player(self):
        self.starting_card_suit = "Spades"
        self.starting_card_rank = 14

        for index, player in enumerate(self.players):
            for card in player.get_hand().cards:
                if card.suit == self.starting_card_suit and card.rank == self.starting_card_rank:
                    return index # Correctly returning the player's index
        return 0 # Default if 3 of Clubs isn't found (shouldn't happen)

    # Create a method to get the current player
    def get_current_player(self):
        if self.players:
            return self.players[self.current_player_index]
        return None

    def clear_pile(self):
        self.pile = []
        self.current_play_rank = None
        self.current_play_count = 0
        self.consecutive_passes = 0
        self.threes_played_this_round = 0
        self.same_rank_streak = 0
        self.cards_of_rank_played = {rank: 0 for rank in range(2, 15)}

    # Create a method for what happens on that players turn
    def play_turn(self, player, cards_to_play):
        current_player = self.get_current_player()
        if (current_player != player):
            print(f"It's not {player.name}'s turn. It's {current_player.name}'s turn.")
            return
        
        played_rank = cards_to_play[0].rank
        played_count = len(cards_to_play)
        player_hand = player.get_hand().cards

        for card_to_play in cards_to_play:
            if card_to_play not in player_hand:
                print(f"{player.name} does not have the card {card_to_play} in their hand.")
                return

        if not cards_to_play and self.pile: # Empty "cards_to_play" is now handled by "pass_turn" method
            print(f"{player.name} must use the pass action.")
            return
        elif not cards_to_play and not self.pile:
            print(f"{player.name} must play at least one card to start the round.")
            return

        played_rank = cards_to_play[0].rank
        if not all(card.rank == played_rank for card in cards_to_play):
            print(f"{player.name} must play cards of the same rank.")
            return

        # --- Handle 2s (Clearing Card) ---
        if played_rank == 2:
            print(f"{player.name} has played {played_count} two. Clearing the pile!")
            player.play_cards(cards_to_play)
            self.clear_pile()
            self.current_player_index = self.players.index(player)
            return

        # --- Detect and Handle 3 plays ---
        if played_rank == 3:
            self.threes_played_this_round += played_count # Increment counter by the number of 3s played
            print(f"{player.name} has played {played_count} threes (total: {self.threes_played_this_round} this round).")
            # Add the second 3 logic here later
            player.play_cards(cards_to_play)
            self.pile.extend(cards_to_play)
            self.consecutive_passes = 0 # Reset passes on a successful play

            if self.threes_played_this_round >= 2:
                print("Second 3 played! Pile cleared. It starts with the player who played the second 3.")
                self.clear_pile()
                self.current_player_index = self.players.index(player) # It starts with the current player
            else:
                self.current_player_index = (self.current_player_index + 1) % len(self.players)
            return # End the turn after playing a 3 for now

        # --- Handle non-3, non-2 plays ---
        if not self.pile:
            print(f"{player.name} has played {cards_to_play}.")
            player.play_cards(cards_to_play)
            self.pile.extend(cards_to_play)
            self.current_play_rank = cards_to_play[0].get_value()
            self.current_play_count = len(cards_to_play)
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            self.consecutive_passes = 0 # Reset passes on a successful play
            self.cards_of_rank_played[played_rank] = played_count
        elif len(cards_to_play) == self.current_play_count:
            played_value = cards_to_play[0].get_value()
            if played_value == self.current_play_rank:
                print(f"{player.name} has matched the rank. Skipping next player.")
                player.play_cards(cards_to_play)
                self.pile.extend(cards_to_play)
                self.current_play_rank = played_value
                self.current_play_count = len(cards_to_play)
                self.consecutive_passes = 0 # Reset passes on a successful play
                self.cards_of_rank_played[played_rank] += played_count

                if self.cards_of_rank_played[played_rank] == 4:
                    print("All 4 of this rank have been played! Clearing the pile.")
                    self.clear_pile()
                    self.current_player_index = self.players.index(player)
                elif self.same_rank_streak >= len(self.players):
                    print("All players have played the same rank! Clearing the pile.")
                    self.clear_pile()
                    self.current_player_index = self.players.index(player)
                else:
                    self.current_player_index = (self.current_player_index + 2) % len(self.players)

            elif played_value > self.current_play_rank:
                print(f"{player.name} has played {cards_to_play}.")
                player.play_cards(cards_to_play)
                self.pile.extend(cards_to_play)
                self.current_play_rank = played_value
                self.current_play_count = len(cards_to_play)
                self.current_player_index = (self.current_player_index + 1) % len(self.players)
                self.consecutive_passes = 0 # Reset passes on a successful play
                self.same_rank_streak = 1
                self.cards_of_rank_played[played_rank] = played_count #track
            else:
                print(f"{player.name}'s play is not higher than the current play.")
                return
        else:
            print(f"{player.name} must play {self.current_play_count} cards to match the pile.")
            return

        if self.is_game_over():
            print("Game Over!")
            # Handle game over logic

    def get_rank_name(self, rank):
        if 1 < rank < 11:
            return str(rank)
        elif rank == 11:
            return "Jack"
        elif rank == 12:
            return "Queen"
        elif rank == 13:
            return "King"
        elif rank == 14:
            return "Ace"
        return str(rank)

    def pass_turn(self, player):
        current_player = self.get_current_player()
        if player != current_player:
            print(f"It's not {player.name}'s turn to pass.")
            return
        
        if not self.pile:
            print(f"{player.name} cannot pass to start the round. Must play a card or set of cards.")
            return
        
        self.consecutive_passes += 1
        print(f"{player.name} has passed (Consecutive passes: {self.consecutive_passes}).")
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

        # Check if the round has ended
        if self.consecutive_passes == len(self.players):
            # The round ends when all other players have passed after the last play
            last_player_index = (self.current_player_index - 1 + len(self.players)) % len(self.players) # Initialize local variable "last_player_index" as a number to be used to determine "last_player"
            last_player = self.players[last_player_index]
            print(f"Round over. {last_player.name} leads the next round.")
            # Set all of the global variables back to initial state
            self.pile = []
            self.current_play_rank = None
            self.current_play_count = None
            self.threes_played_this_round = 0
            self.consecutive_passes = 0
            # Set the "current_player_index" to the "last_player_index" in this method
            self.current_player_index = last_player_index # The leader starts the next round

    def get_winner(self):
        if not self.is_game_over():
            return None
        
        for player in self.players:
            if player.is_active:
                return player
        return None #Should never happen

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