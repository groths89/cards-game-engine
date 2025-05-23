from game_engine.game_loop import GameLoop
from game_engine.game_state import GameState
from game_engine.player import Player
from game_engine.deck import Deck
class AssholeGame(GameState):
    MIN_PLAYERS = 4
    MAX_PLAYERS = 10

    def __init__(self, players):
        super(AssholeGame, self).__init__(players)
        self.host_id = None
        self.is_game_started = False
        self.deck.shuffle()
        self.special_card_rules = True
        self.player_went_out = 0 # Counter to track when a player goes out
        self.threes_played_this_round = 0 # Initialize the counter
        self.consecutive_passes = 0 # Initialize the consecutive passes counter
        self.same_rank_streak = 0 # Track consecutive plays of the same rank
        self.should_skip_next_player = False
        self.pile_cleared_this_turn = False
        self.cards_of_rank_played = {rank: 0 for rank in range(2, 15)} # Track how many of each rank have been played

    def start_game(self):
        """
        Initializes and starts a new round of Asshole.
        Call this when enough players have joined the room.
        """
        if len(self.players) < self.MIN_PLAYERS:
            raise ValueError(f"Need at least {self.MIN_PLAYERS} players to start. Current: {len(self.players)}.")
        if len(self.players) > self.MAX_PLAYERS:
            raise ValueError(f"Cannot exceed {self.MAX_PLAYERS} players. Current: {len(self.players)}.")

        if self.is_game_started:
            raise ValueError("Game has already started.")
        if len(self.players) < 2: # Or 3, 4 depending on your minimum player count
            raise ValueError("Not enough players to start the game.")

        print(f"Starting game in room {self.room_code} with players: {[p.name for p in self.players]}")

        # Reset game state for a new round
        self.deck = Deck() # Re-initialize a full deck
        self.deck.shuffle()
        for player in self.players:
            player.hand.clear() # Clear existing hands
            player.is_active = True
            player.rank = None
        self.pile = []
        self.current_play_rank = None
        self.current_play_count = 0
        self.consecutive_passes = 0
        self.threes_played_this_round = 0
        self.same_rank_streak = 0
        self.should_skip_next_player = False
        self.pile_cleared_this_turn = False
        self.cards_of_rank_played = {rank: 0 for rank in range(2, 15)}
        self.player_went_out = 0 # Reset rank counter

        self.deal_all_cards()
        self.current_player_index = self.determine_starting_player()
        self.is_game_started = True # Set to True once setup is complete
        print(f"Game started! First player: {self.get_current_player().name}")

    # Create a method to deal all the cards to players
    def deal_all_cards(self):
        """Deals all the cards from the deck to the players in a round-robin fashion."""
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
        return 0 # Default if Ace of Spades isn't found (shouldn't happen)

    def clear_pile(self):
        self.pile = []
        self.current_play_rank = None
        self.current_play_count = 0
        self.consecutive_passes = 0
        self.threes_played_this_round = 0
        self.same_rank_streak = 0
        self.should_skip_next_player = False
        self.pile_cleared_this_turn = True
        self.cards_of_rank_played = {rank: 0 for rank in range(2, 15)}

    def play_turn(self, player, cards_to_play):
        """
        Overrides the play_turn method in GameState to implement Asshole-specific rules.
        """
        # --- Basic checks (player's turn, has cards) ---
        current_player = self.get_current_player()
        if current_player != player:
            print(f"It's not {player.name}'s turn.")
            return
        if not cards_to_play:
            self.pass_turn(player) # Delegate to the pass_turn method
            return
        
        if cards_to_play:
            played_rank = cards_to_play[0].rank
            played_count = len(cards_to_play)

            for card_to_play in cards_to_play:
                if card_to_play not in player.get_hand().cards:
                    print(f"{player.name} does not have the card {card_to_play} in their hand.")
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
                    return # End the turn after playing a 3 for now
                else:
                    self.next_player()

            # --- Handle non-3, non-2 plays ---
            if not self.pile:
                print(f"{player.name} has played {cards_to_play}.")
                player.play_cards(cards_to_play)
                self.pile.extend(cards_to_play)
                self.current_play_rank = cards_to_play[0].get_value()
                self.current_play_count = len(cards_to_play)
                self.consecutive_passes = 0 # Reset passes on a successful play
                self.cards_of_rank_played[played_rank] = played_count
                self.next_player()
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
                        return True
                    elif self.same_rank_streak >= len(self.players):
                        print("All players have played the same rank! Clearing the pile.")
                        self.clear_pile()
                        self.current_player_index = self.players.index(player)
                        return True
                    else:
                        self.should_skip_next_player = True
                        self.next_player(self.should_skip_next_player)
                        self.should_skip_next_player = False

                elif played_value > self.current_play_rank:
                    print(f"{player.name} has played {cards_to_play}.")
                    player.play_cards(cards_to_play)
                    self.pile.extend(cards_to_play)
                    self.current_play_rank = played_value
                    self.current_play_count = len(cards_to_play)
                    self.next_player()
                    self.consecutive_passes = 0 # Reset passes on a successful play
                    self.same_rank_streak = 1
                    self.cards_of_rank_played[played_rank] = played_count #track
                else:
                    print(f"{player.name}'s play is not higher than the current play.")
                    return False
            else:
                print(f"{player.name} must play {self.current_play_count} cards to match the pile.")
                return False
        
            played_rank = cards_to_play[0].rank
            if not all(card.rank == played_rank for card in cards_to_play):
                print(f"{player.name} must play cards of the same rank.")
                return False
        
            if self.is_game_over():
                print("Game Over!")
                # Handle game over logic

    def pass_turn(self, player):
        """Handles a player passing their turn."""
        super().pass_turn(player)
        if not self.pile:
            print(f"{player.name} cannot pass to start the round. Must play a card or set of cards.")
            return
        
        self.consecutive_passes += 1
        print(f"{player.name} has passed (Consecutive passes: {self.consecutive_passes}).")
        self.next_player()
        
        active_players = 0
        for player in self.players:
            if player.is_active:
                active_players += 1

        # Check if the round has ended
        if self.consecutive_passes >= active_players and active_players > 1:
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
    
    def handle_player_out(self):
        for player in self.players:
            if len(player.get_hand().cards) == 0 and player.is_active:
                player.is_active = False
                self.player_went_out += 1
                player.rank = self.player_went_out
                rank_name = self.get_rank_name(player.rank, len(self.players))
                print(f"{player.name} went out and he is the {rank_name}")

    def get_num_active_players(self):
        num_active_players = 0 # Initialize the local variable counter "num_active_players"
        # Loops through the "players" from __init__ and creates a variable
        for player in self.players:
            # Then checks whether the attribute of a player "is_active" and adds 1 for each player that has "is_active" set to true
            if player.is_active:
                num_active_players += 1
        # When method is called it does the check whether game is over and returns true or false
        return num_active_players    

    def end_game(self):
        last_player_out = None
        first_player_out = None

        print("\n---- Game Over! ----")

        # Assign rank to the last remaining active player (the Asshole)
        remaining_active_players = [p for p in self.players if p.is_active]
        if remaining_active_players:
            asshole_player = remaining_active_players[0]
            self.player_went_out += 1
            asshole_player.rank = self.player_went_out
            asshole_player.is_active = False # Mark as inactive
            print(f"{asshole_player.name} is the Asshole!")

        final_rankings = sorted(self.players, key=lambda p: p.rank if p.rank else float('inf'))
        num_players = len(self.players) 

        # Print the final ranks of all players
        print("\n---- Final Rankings ----")
        for player in final_rankings:
            rank_name = self.get_rank_name(player.rank, len(self.players)) if player.rank is not None else "Still Playing"
            print(f"{player.name}: {rank_name}")
            if player.rank == num_players:
                last_player_out = player.name
            elif player.rank == 1:
                first_player_out = player.name

        self.is_game_started = False # Reset game state after it ends

    def get_rank_name(self, rank, num_players):
        if rank == 1:
            return "President"
        elif rank == 2:
            return "Vice-President"
        elif rank == 3:
            return "Secretary of Keeping it Real"
        elif rank == 4:
            return "Commodore"
        elif 5 <= rank <= (num_players - 2):
            return "Peasant"
        elif rank == num_players - 1:
            return "Vice-Asshole"        
        elif rank == num_players:
            return "Asshole"
        else:
            return f"Rank {rank}"