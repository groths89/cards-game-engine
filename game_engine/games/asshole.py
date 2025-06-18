import random
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
        self.deck = Deck()
        self.special_card_rules = True
        self.MIN_PLAYERS = 4
        self.MAX_PLAYERS = 10        
        self.player_went_out = 0
        self.threes_played_this_round = 0
        self.consecutive_passes = 0
        self.same_rank_streak = 0
        self.turn_direction = "clockwise"
        self.should_skip_next_player = False
        self.pile_cleared_this_turn = False
        self.cards_of_rank_played = {rank: 0 for rank in range(2, 15)}
        self.game_message = "Waiting for players to join..."
        self.last_played_cards = []
        self.interrupt_active = False
        self.interrupt_type = None
        self.interrupt_initiator_player_id = None
        self.interrupt_rank = None
        self.interrupt_bids = []

        if self.room_code:
            self.status = "WAITING"
        else:
            self.status = "CLI_MODE"
            print("AssholeGame initialized in CLI/direct setup mode.")

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


        print(f"Starting game in room {self.room_code} with players: {[p.name for p in self.players]}")

        self.deck = Deck()
        self.deck.shuffle()
        for player in self.players:
            player.hand.clear()
            player.is_active = True
            player.is_out = False
            player.rank = None

        self.threes_played_this_round = 0
        self.same_rank_streak = 0
        self.should_skip_next_player = False
        self.pile_cleared_this_turn = False
        self.player_went_out = 0 # Reset player went out counter for new game/round
        self.pile = []
        self.current_play_count = 0 
        self.current_play_rank = None # Ensure this is reset too (string rank)
        self.consecutive_passes = 0
        self.last_played_cards = []
        self.interrupt_active = False
        self.interrupt_type = None
        self.interrupt_initiator_player_id = None
        self.interrupt_rank = None
        self.interrupt_bids = []
        self.cards_of_rank_played = {rank_str: 0 for rank_str in Rank.all_ranks()} # Reset card counts
        self.rankings = {} # Reset rankings for new game

        self.deal_all_cards()
        self.current_player_index = self.determine_starting_player()
        start_player = self.get_current_player()

        if start_player:
            self.game_message = f"Game started! It's {start_player.name}'s turn (3 of Clubs)."
            self.round_leader_player_id = start_player.player_id
        else:
            self.game_message = "Game started, but could not determine first player's turn (3 of Clubs not found or no active players)." 
            if self.players:
                self.current_player_index = random.randint(0, len(self.players) - 1)
                start_player = self.players[self.current_player_index]
                self.game_message = f"Game started! No 3 of Clubs, {start_player.name} starts randomly."
                self.round_leader_player_id = start_player.player_id
            else:
                self.game_message = "Game started, but no players found. Critical error state."

        self.last_played_player_id = None # No cards played yet
        self.players_who_passed_this_round = set()
        self.round_active_players = [p.player_id for p in self.players if p.is_active and not p.is_out]

        print(f"DEBUG: Game started! First player: {self.get_current_player().name if self.get_current_player() else 'N/A'}")

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
                    return index
        return 0

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
        self.last_played_cards = []
        self.interrupt_active = False
        self.interrupt_type = None
        self.interrupt_initiator_player_id = None
        self.interrupt_rank = None
        self.interrupt_bids = []

    def play_cards(self, player_id, cards_to_play_data):
        """
        Overrides the play_turn method in GameState to implement Asshole-specific rules.
        """
        player = self.get_player_by_id(player_id)
        if not player:
            raise ValueError("Player not found in this game.")
        
        if self.interrupt_active:
            raise ValueError(f"An interrupt of type '{self.interrupt_type}' is active. You cannot make a regular play now. Please use the interrupt action if available.")     
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
        

        for card_to_play in cards_to_play:
            if card_to_play not in player.get_hand().cards:
                print(f"{player.name} does not have the card {card_to_play} in their hand.")
                return

        played_rank = cards_to_play[0].rank
        played_count = len(cards_to_play)

        # --- Rule 1: Handle 2s (Clearing Card) ---
        if played_rank == 2:
            player.play_cards(cards_to_play)
            self.pile.extend(cards_to_play)
            self.last_played_cards = cards_to_play
            self.clear_pile()
            self.current_player_index = self.players.index(player)
            self.game_message = f"{player.name} cleared the pile with {played_count} two(s)! New round starts with them."
            self.advance_turn(skip_count=0)
            return

        # --- Rule 2: Handle 3 plays (Initiates Interrupt) ---
        if played_rank == 3:
            player.play_cards(cards_to_play)
            self.pile.extend(cards_to_play)
            self.last_played_cards = cards_to_play
            self.consecutive_passes = 0
            self.threes_played_this_round += played_count # Increment counter by the number of 3s played
            print(f"{player.name} has played {played_count} threes (total: {self.threes_played_this_round} this round).")
                
            self.record_interrupt_initiation(
                'three_play',
                player_id,
                played_rank,
                f"{player.name} played {played_count} Three(s)! Other players can now play their 3s to counter."
            )
            return


        if self.threes_played_this_round >= 2:
            print("Second 3 played! Pile cleared. It starts with the player who played the second 3.")
            self.clear_pile()
            self.current_player_index = self.players.index(player) # It starts with the current player
            return # End the turn after playing a 3 for now
        else:
            self.next_player()

        # --- General Play Rules (for non-2s, non-3s, and when no interrupt is active) ---
        if not self.pile:
            player.play_cards(cards_to_play)
            self.pile.extend(cards_to_play)
            self.current_play_rank = played_rank
            self.current_play_count = played_count
            self.consecutive_passes = 0
            self.same_rank_streak = 1
            self.cards_of_rank_played[played_rank] = played_count
            self.game_message = f"{player.name} started a new round with {played_count} x {self.get_rank_display(played_rank_value)}."
            self.next_player()
        else:
            if played_count != self.current_play_count:
                raise ValueError(f"You must play {self.current_play_count} cards to match the pile.")
            
            if played_rank > self.current_play_rank:
                print(f"{player.name} has matched the rank. Skipping next player.")
                player.play_cards(cards_to_play)
                self.pile.extend(cards_to_play)
                self.current_play_rank = played_rank
                self.last_played_cards = cards_to_play
                self.consecutive_passes = 0 # Reset passes on a successful play
                self.same_rank_streak = 1
                self.cards_of_rank_played[played_rank] += played_count
                self.game_message = f"{player.name} played {played_count} x {self.get_rank_display(played_rank)}."
            elif played_rank == self.current_play_rank:
                # --- Rule 3: Same Rank Play (Skipping next player, potentially leads to 4-of-a-kind clear) ---
                player.play_cards(cards_to_play)
                self.pile.extend(cards_to_play)
                self.last_played_cards = cards_to_play # Important for bomb rule
                self.consecutive_passes = 0 # Reset passes on a successful play
                self.same_rank_streak += 1 # Increment streak
                self.cards_of_rank_played[played_rank] += played_count # Track total of this rank on pile        
                
                if self.cards_of_rank_played[played_rank] == 4:
                    # --- Rule 4: 4-of-a-Kind (Immediate Pile Clear) ---
                    self.game_message = f"{player.name} played all four {self.get_rank_display(played_rank)}s! Pile cleared."
                    print(self.game_message) # For backend logging
                    self.clear_pile()
                    self.current_player_index = self.players.index(player)
                    self.advance_turn(skip_count=0)
                    return
                
                # If not a 4-of-a-kind bomb, apply skip rule
                self.should_skip_next_player = True
                self.game_message = f"{player.name} matched the rank! Next player will be skipped."

            else:
                raise ValueError(f"Your play ({self.get_rank_display(played_rank)}) must be higher than or match the current top card ({self.get_rank_display(self.current_play_rank)}).")
        
        # If no interrupt was initiated (i.e., not a 3-play and not a 4-of-a-kind bomb), advance turn
        # The `should_skip_next_player` will be consumed by advance_turn
        if not self.interrupt_active:
            self.advance_turn(skip_count=1 if self.should_skip_next_player else 0)
            self.should_skip_next_player = False

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

    def advance_turn(self, skip_count=0):
        """
        Advances the turn to the next active player, optionally skipping players.
        Updates player ranks if they run out of cards.
        """
        for player in self.players:
            if len(player.get_hand().cards) == 0 and player.is_active:
                player.is_active = False
                if player.rank is None:
                    taken_ranks = {p.rank for p in self.players if p.rank is not None}
                    new_rank = 1
                    while new_rank in taken_ranks:
                        new_rank += 1
                    player.rank = new_rank
                    self.rankings[player.player_id] = {'name': player.name, 'rank': self.get_rank_name_display(player.rank, len(self.players))}
                    self.game_message = f"{player.name} went out! They are the {self.get_rank_name_display(player.rank, len(self.players))}."

        if self.is_game_over():
            self.game_message = "Game Over!"
            self.status = "GAME_OVER"
            return

        num_players_to_skip = 1 + skip_count
        
        for _ in range(num_players_to_skip):
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            attempts = 0
            max_attempts = len(self.players) * 2
            while not self.players[self.current_player_index].is_active and attempts < max_attempts:
                self.current_player_index = (self.current_player_index + 1) % len(self.players)
                attempts += 1
                if attempts >= max_attempts:
                    print("WARNING: Could not find next active player. Game might be in an invalid state or nearly over.")
                    self.game_message = "Game in unexpected state, no next active player found."
                    return

        self.game_message = f"It's {self.get_current_player().name}'s turn."

    def record_interrupt_initiation(self, interrupt_type, initiator_player_id, interrupt_rank, message):
        """
        Records that an interrupt window has been opened.
        This should be called by game-specific play_cards methods when an interrupt condition is met.
        """
        self.interrupt_active = True
        self.interrupt_type = interrupt_type
        self.interrupt_initiator_player_id = initiator_player_id
        self.interrupt_rank = interrupt_rank
        self.interrupt_bids = [] # Clear any previous bids for a new interrupt window
        self.game_message = message
        print(f"Interrupt initiated: Type={interrupt_type}, Initiator={initiator_player_id}, Rank={interrupt_rank}")


    def add_interrupt_bid(self, player_id, cards_data):
        """
        Allows a player to submit a bid during an active interrupt window.
        """
        if not self.interrupt_active:
            raise ValueError("No interrupt is currently active to bid on.")
        if player_id == self.interrupt_initiator_player_id:
            raise ValueError("You cannot bid on an interrupt you initiated directly. Make your initial play via 'play_cards'.")

        player = self.get_player_by_id(player_id)
        if not player:
            raise ValueError("Player not found in this game.")

        cards_to_play = [Card(c['suit'], c['rank']) for c in cards_data]

        if not cards_to_play:
            raise ValueError("You must select cards for your interrupt bid.")
        
        if self.interrupt_type == 'three_play':
            if not all(card.rank == 3 for card in cards_to_play):
                raise ValueError("Only 3s can be played as an interrupt bid for a three-play.")
            player_hand_threes = [c for c in player.get_hand().cards if c.rank == 3]
            for bid_card in cards_to_play:
                if bid_card not in player_hand_threes:
                    raise ValueError(f"You do not have the card {str(bid_card)} in your hand to play this interrupt.")
                found_and_removed = False
                for i, hand_card in enumerate(player_hand_threes):
                    if hand_card.suit == bid_card.suit and hand_card.rank == bid_card.rank:
                        player_hand_threes.pop(i)
                        found_and_removed = True
                        break
                if not found_and_removed:
                     raise ValueError(f"You do not have the card {str(bid_card)} in your hand to play this interrupt.")

            if any(bid[0] == player_id for bid in self.interrupt_bids):
                raise ValueError("You have already submitted a bid for this three-play interrupt.")

        elif self.interrupt_type == 'bomb_opportunity':
            # A "bomb" is usually 4 of a kind, higher than the rank that triggered it.
            if len(cards_to_play) != 4 or not all(card.rank == cards_to_play[0].rank for card in cards_to_play):
                raise ValueError("A bomb must be exactly 4 cards of the same rank.")
            
            bomb_rank = cards_to_play[0].rank
            if bomb_rank <= self.interrupt_rank:
                raise ValueError(f"Your bomb ({self.get_rank_display(bomb_rank)}) must be higher than the interrupted rank ({self.get_rank_display(self.interrupt_rank)}).")
            
            player_hand_cards_of_rank = player.get_hand().get_cards_by_rank(bomb_rank)
            if len(player_hand_cards_of_rank) < 4:
                raise ValueError(f"You do not have 4 cards of rank {self.get_rank_display(bomb_rank)} in your hand to play this bomb.")
            
            if any(bid[0] == player_id for bid in self.interrupt_bids):
                raise ValueError("You have already submitted a bid for this bomb opportunity.")

        else:
            raise ValueError(f"Unknown interrupt type: {self.interrupt_type}. Cannot process bid.")

        self.interrupt_bids.append((player_id, cards_to_play))
        self.game_message = f"{player.name} has submitted an interrupt bid."
        print(f"Player {player_id} bid on interrupt with: {[str(c) for c in cards_to_play]}")


    def resolve_interrupt(self):
        """
        Resolves the active interrupt, determines the winner, and applies game effects.
        This should be called after the interrupt window closes (e.g., timed out or explicitly resolved).
        """
        if not self.interrupt_active:
            print("No interrupt active to resolve.")
            return

        winner_player_id = self.interrupt_initiator_player_id
        winning_cards = []
        
        all_relevant_plays = []
        if self.last_played_cards and self.last_played_cards[0].rank == self.interrupt_rank:
             all_relevant_plays.append((self.interrupt_initiator_player_id, self.last_played_cards))
        
        all_relevant_plays.extend(self.interrupt_bids)

        if self.interrupt_type == 'three_play':
            if all_relevant_plays:
                all_relevant_plays.sort(key=lambda x: len(x[1]), reverse=True)
                
                winner_player_id = all_relevant_plays[0][0]
                winning_cards = all_relevant_plays[0][1]

                for p_id, played_cards in all_relevant_plays:
                    if p_id != self.interrupt_initiator_player_id:
                        player_obj = self.get_player_by_id(p_id)
                        if player_obj and p_id == winner_player_id:
                            player_obj.play_cards(played_cards)
                            self.pile.extend(played_cards)
                            print(f"DEBUG: Player {player_obj.name} played {len(played_cards)} 3s as winning interrupt bid.")
                        elif player_obj:
                             print(f"DEBUG: Player {player_obj.name} played {len(played_cards)} 3s as losing interrupt bid (cards not removed from hand for now).")

            self.clear_pile()
            self.game_message = f"{self.get_player_by_id(winner_player_id).name} won the 3-play! New round starts with them."
            self.current_player_index = self.players.index(self.get_player_by_id(winner_player_id))
            self.threes_played_this_round = 0

        elif self.interrupt_type == 'bomb_opportunity':
            all_bomb_bids = [bid for bid in all_relevant_plays if len(bid[1]) == 4 and bid[1][0].rank > self.interrupt_rank]
            
            if all_bomb_bids:
                all_bomb_bids.sort(key=lambda bid: bid[1][0].rank, reverse=True)
                
                winner_player_id = all_bomb_bids[0][0]
                winning_cards = all_bomb_bids[0][1]

                winner_player_obj = self.get_player_by_id(winner_player_id)
                if winner_player_obj:
                    winner_player_obj.play_cards(winning_cards)
                    self.pile.extend(winning_cards)
                    print(f"DEBUG: Player {winner_player_obj.name} played a bomb of {winning_cards[0].rank}s!")

            self.clear_pile()
            self.game_message = f"{self.get_player_by_id(winner_player_id).name} played the winning bomb! New round starts with them."
            self.current_player_index = self.players.index(self.get_player_by_id(winner_player_id))
            self.cards_of_rank_played = {rank: 0 for rank in range(2, 15)}

        else:
            self.game_message = "Interrupt resolved without a clear winner or unrecognized type. Turn proceeds."
            self.clear_pile()
            if initiator_player:
                self.current_player_index = self.players.index(initiator_player)
            self.game_message = "Interrupt resolved. New round starts."

        self.interrupt_active = False
        self.interrupt_type = None
        self.interrupt_initiator_player_id = None
        self.interrupt_rank = None
        self.interrupt_bids = []

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