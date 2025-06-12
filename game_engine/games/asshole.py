from game_engine.card import Card, Rank, Suit
from game_engine.game_loop import GameLoop
from game_engine.game_state import GameState
from game_engine.player import Player
from game_engine.deck import Deck
class AssholeGame(GameState):


    def __init__(self, room_code=None, host_id=None, game_type="asshole"):
        super(AssholeGame, self).__init__(players=[])
        self.room_code = room_code
        self.host_id = host_id
        self.game_type = game_type
        self.status = "WAITING" if room_code else "CLI_MODE"
        self.deck.shuffle()
        self.special_card_rules = True
        self.MIN_PLAYERS = 4
        self.MAX_PLAYERS = 10        
        self.player_went_out = 0 # Counter to track when a player goes out
        self.threes_played_this_round = 0 # Initialize the counter
        self.consecutive_passes = 0 # Initialize the consecutive passes counter
        self.same_rank_streak = 0 # Track consecutive plays of the same rank
        self.turn_direction = "clockwise"
        self.should_skip_next_player = False
        self.pile_cleared_this_turn = False
        self.cards_of_rank_played = {rank: 0 for rank in range(2, 15)} # Track how many of each rank have been played

        if self.room_code:
            self.status = "WAITING"
        else:
            self.status = "CLI_MODE"
            print("AssholeGame initialized in CLI/direct setup mode.")
    
    def add_player(self, player_obj):
        if not isinstance(player_obj, Player):
            raise ValueError("Must add a Player object.")
        if len(self.players) >= self.MAX_PLAYERS:
            raise ValueError("Game is already full.")
        if self.room_code:
            if any(p.player_id == player_obj.player_id for p in self.players):
                pass
            if any(p.name == player_obj.name for p in self.players):
                pass

        self.players.append(player_obj)
        print(f"Player {player_obj.name} ({player_obj.player_id}) added to game {self.room_code if self.room_code else 'CLI/Local'}.")
        self.players.sort(key=lambda p: p.player_id if p.player_id else p.name)

    def remove_player(self, player_id):
        initial_count = len(self.players)
        self.players = [p for p in self.players if p.player_id != player_id]
        if len(self.players) == initial_count:
            raise ValueError(f"Player {player_id} not found in game {self.room_code}.")
        print(f"Player {player_id} removed from game {self.room_code}.")
        if self.is_game_started and self.get_current_player() and player_id == self.get_current_player_id():
            self.next_turn()

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
        self.status = "IN_PROGRESS"
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
        target_suit = Suit.SPADES
        target_rank = Rank.ACE

        for index, player in enumerate(self.players):
            hand_cards = player.get_hand().cards
            if not hand_cards:
                continue

            for card in hand_cards:
                if card.suit == target_suit and card.rank == target_rank:
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

    def play_cards(self, player_id, cards_to_play_data):
        """
        Overrides the play_turn method in GameState to implement Asshole-specific rules.
        """
        player = self.get_player_by_id(player_id)
        if not player:
            raise ValueError("Player not found in this game.")
        if player_id != self.get_current_player_id():
            raise ValueError("It's not this player's turn.")
        if not player.is_active:
            raise ValueError("This player is out of the game and cannot play.")

        cards_to_play = [Card(c['suit'], c['rank']) for c in cards_to_play_data]
        
        # --- Basic checks (player's turn, has cards) ---
        current_player = self.get_current_player()
        if current_player != player:
            print(f"It's not {player.name}'s turn.")
            return
        if not cards_to_play:
            raise ValueError("No cards selected to play.")
        
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
        
            if self.is_game_over:
                print("Game Over!")
                # Handle game over logic

    def pass_turn(self, player_id):
        player = self.get_player_by_id(player_id)
        if not player:
            raise ValueError("Player not found in this game.")
        if player_id != self.get_current_player_id():
            raise ValueError("It's not this player's turn to pass.")
        if not player.is_active:
            raise ValueError("This player is out of the game and cannot pass.")

        # Asshole-specific pass logic
        if not self.pile:
            raise ValueError(f"{player.name} cannot pass to start the round. Must play a card or set of cards.")
        
        self.consecutive_passes += 1
        print(f"{player.name} has passed (Consecutive passes: {self.consecutive_passes}).")
        
        active_players_count = self.get_num_active_players()
        if self.consecutive_passes >= active_players_count and active_players_count > 1:
            # Round ends when all active players pass after a play
            last_player_to_play = self.players[(self.current_player_index - self.consecutive_passes + len(self.players)) % len(self.players)]
            print(f"Round over. {last_player_to_play.name} leads the next round.")
            self.clear_pile()
            self.current_player_index = self.players.index(last_player_to_play) # Leader starts next round
            self.consecutive_passes = 0 # Reset passes after round end
            self.threes_played_this_round = 0
            self.same_rank_streak = 0
            self.should_skip_next_player = False
            self.pile_cleared_this_turn = False
            self.cards_of_rank_played = {rank.get_value(): 0 for rank in Rank.all_ranks()} # Reset for new round
            self.next_player() # Advance turn to the leader
        else:
            self.next_player() # Just advance turn if round not over
    
    def get_winner(self):
        if not self.is_game_over:
            return None
        
        for player in self.players:
            if player.is_active:
                return player
        return None #Should never happen
    
    def handle_player_out(self, player):
        if player.get_num_cards() == 0 and not player.is_out:
            player.is_out = True
            player.is_active = False
            self.player_went_out += 1
            player.rank = self.player_went_out
            rank_name = self.get_rank_name(player.rank, len(self.players))
            print(f"{player.name} went out and he is the {rank_name}")
            # If the current player went out, advance turn
            if self.get_current_player() and player.player_id == self.get_current_player_id():
                self.next_player() # Advance turn if current player went out

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
        # This method should be called when the game truly ends (e.g., only one player left)
        # It's better to set self.is_game_over = True and self.status = "FINISHED" here
        # and then call assign_final_ranks
        self.status = "FINISHED"
        self.assign_final_ranks()

        print("\n---- Game Over! ----")
        final_rankings = sorted(self.players, key=lambda p: p.rank if p.rank else float('inf'))
        num_players = len(self.players)

        print("\n---- Final Rankings ----")
        for player in final_rankings:
            rank_name = self.get_rank_name(player.rank, num_players) if player.rank is not None else "Still Playing"
            print(f"{player.name}: {rank_name}")

    def assign_final_ranks(self):
        unranked_players = [p for p in self.players if p.rank is None]

        unranked_players.sort(key=lambda p: p.player_id)

        current_rank_counter = len([p for p in self.players if p.rank is not None]) + 1

        for player in unranked_players:
            player.rank = current_rank_counter
            player.is_out = True
            player.is_active = False
            current_rank_counter += 1

        self.rankings = {p.player_id: p.rank for p in self.players}

    def get_rank_name(self, rank, num_players):
        if rank == 1:
            return "President"
        elif rank == 2:
            return "Vice President"
        elif rank == 3:
            return "Secretary of Keeping it Real"
        elif rank == 4:
            return "Commodore"
        elif 5 <= rank <= (num_players - 2):
            return "Peasant"
        elif rank == num_players - 1:
            return "Vice Asshole"        
        elif rank == num_players:
            return "Asshole"
        else:
            return f"Rank {rank}"
        
    @property
    def is_game_started(self):
        return self.status == "IN_PROGRESS"

    @property
    def is_game_over(self):
        return len([p for p in self.players if p.is_active and not p.is_out]) <= 1 or all(p.rank is not None for p in self.players)