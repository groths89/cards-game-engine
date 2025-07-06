import random
import time
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
        self.interrupt_active_until = None
        self.players_responded_to_interrupt = set()
        self.INTERRUPT_TIMEOUT_SECONDS = 15

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
        super().start_game()

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
        self.player_went_out = 0
        self.pile = []
        self.current_play_count = 0 
        self.current_play_rank = None
        self.consecutive_passes = 0
        self.last_played_cards = []
        self.interrupt_active = False
        self.interrupt_type = None
        self.interrupt_initiator_player_id = None
        self.interrupt_rank = None
        self.interrupt_bids = []
        self.interrupt_original_skip_state = False
        self.cards_of_rank_played = {rank_str: 0 for rank_str in Rank.all_ranks()}
        self.rankings = {}

        self.deal_all_cards()
        self.current_player_index = self.determine_starting_player()
        start_player = self.get_current_player()

        if start_player:
            self.game_message = f"Game started! It's {start_player.name}'s turn (Ace of Spades)."
            self.round_leader_player_id = start_player.player_id
        else:
            self.game_message = "Game started, but could not determine first player's turn (Ace of Spades not found or no active players)." 
            if self.players:
                self.current_player_index = random.randint(0, len(self.players) - 1)
                start_player = self.players[self.current_player_index]
                self.game_message = f"Game started! Ace of Spades, {start_player.name} starts randomly."
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

    def check_and_perform_four_of_a_kind_clear(self, player, played_rank_value, played_rank_str):
        """
        Checks if the current play resulted in 4 of a kind on the pile.
        If so, clears the pile and sets the player as the current player.
        Returns True if a clear occurred, False otherwise.
        """
        if self.cards_of_rank_played[played_rank_value] == 4:
            self.game_message = f"{player.name} played all four {Card.get_rank_display(played_rank_str)}s! Pile cleared."
            print(self.game_message)
            self.clear_pile()
            self.current_player_index = self.players.index(player)
            self.advance_turn(skip_count=0)
            return True
        return False

    def play_cards(self, player_id, cards_to_play_data):
        """
        Overrides the play_turn method in GameState to implement Asshole-specific rules.
        """
        player = self.get_player_by_id(player_id)
        if not player:
            raise ValueError("Player not found in this game.")
        
        # Check if interrupt is active
        if self.interrupt_active:
            raise ValueError(f"An interrupt of type '{self.interrupt_type}' is active. You cannot make a regular play now. Please use the interrupt action if available.")     
        
        # Basic turn validation
        if player_id != self.get_current_player_id():
            raise ValueError("It's not this player's turn.")
        if not player.is_active:
            raise ValueError("This player is out of the game and cannot play.")

        cards_to_play = [Card(c['suit'], c['rank'], id=c.get('id')) for c in cards_to_play_data]
        
        if not cards_to_play:
            raise ValueError("No cards selected to play.")        
        
        # --- Basic checks (player's turn, has cards) ---
        current_player = self.get_current_player()
        if current_player != player:
            raise ValueError("It's not this player's turn.")
        
        # Check if player has the cards in their hand
        for card_to_play in cards_to_play:
            if card_to_play not in player.get_hand().cards:
                raise ValueError(f"{player.name} does not have the card {card_to_play} in their hand.")

        # Ensure all cards played are of the same rank
        if len(cards_to_play) > 1 and not all(card.rank == cards_to_play[0].rank for card in cards_to_play):
            raise ValueError("All cards played must be of the same rank.")
        
        played_rank_str = cards_to_play[0].rank
        played_rank_value = cards_to_play[0].get_value()
        played_count = len(cards_to_play)

        # --- Rule 1: Handle 2s (Clearing Card) ---
        if played_rank_str == Rank.TWO:
            player.play_cards(cards_to_play)
            self.pile.extend(cards_to_play)
            self.last_played_cards = cards_to_play
            self.clear_pile()
            self.current_player_index = self.players.index(player)
            self.game_message = f"{player.name} cleared the pile with {played_count} two(s)! New round starts with them."
            self.advance_turn(skip_count=0)
            return

        # --- Rule 2: Handle 3 plays (Initiates Interrupt) ---
        if played_rank_str == Rank.THREE:
            player.play_cards(cards_to_play)
            self.pile.extend(cards_to_play)
            self.last_played_cards = cards_to_play
            self.consecutive_passes = 0
            self.threes_played_this_round += played_count # Increment counter by the number of 3s played
            print(f"{player.name} has played {played_count} threes (total: {self.threes_played_this_round} this round).")
                
            self.record_interrupt_initiation(
                'three_play',
                player_id,
                played_rank_str,
                f"{player.name} played {played_count} {Card._rank_display_names[played_rank_str]}(s)! Other players can now play their 3s to counter."
            )
            return


        if self.threes_played_this_round >= 2:
            print("Second 3 played! Pile cleared. It starts with the player who played the second 3.")
            self.clear_pile()
            self.current_player_index = self.players.index(player) # It starts with the current player
            return # End the turn after playing a 3 for now
        else:
            self.advance_turn(skip_count=0)

        # --- General Play Rules (for non-2s, non-3s, and when no interrupt is active) ---
        if not self.pile:
            # Player starts a new round (pile is empty)
            player.play_cards(cards_to_play)
            self.pile.extend(cards_to_play)
            self.current_play_rank = played_rank_value
            self.current_play_count = played_count
            self.consecutive_passes = 0
            self.same_rank_streak = 1
            # Initialize count for this streak on the pile
            self.cards_of_rank_played[played_rank_value] = played_count

            if self.check_and_perform_four_of_a_kind_clear(player, played_rank_value, played_rank_str):
                return
            
            if 1 <= self.cards_of_rank_played[played_rank_value ] <= 3:
                self.record_interrupt_initiation(
                    'bomb_opportunity',
                    player_id,
                    played_rank_str,
                    f"A {Card.get_rank_display(played_rank_str)} bomb opportunity! Other players can now play remaining {4 - self.cards_of_rank_played[played_rank_value]} {Card.get_rank_display(played_rank_str)}s."
                )
                return # Interrupt active, halt regular turn progression
            
            self.game_message = f"{player.name} started a new round with {played_count} x {Card.get_rank_display(played_rank_str)}."
            self.advance_turn(skip_count=0)
        else:
            # Player plays on an existing pile
            # Rule: Must match the count of the last play
            if played_count != self.current_play_count:
                raise ValueError(f"You must play {self.current_play_count} card(s) to match the pile.")
            
            # Rule: Must be higher rank OR same rank
            if played_rank_value > self.current_play_rank:
                # Playing a higher rank, same count
                player.play_cards(cards_to_play)
                self.pile.extend(cards_to_play)
                
                self.last_played_cards = cards_to_play
                self.consecutive_passes = 0 # Reset passes on a successful play
                self.same_rank_streak = 1
                self.current_play_rank = played_rank_value
                self.current_play_count = played_count

                self.cards_of_rank_played = {rank: 0 for rank in range(2, 15)}
                self.cards_of_rank_played[played_rank_value] += played_count

                if self.check_and_perform_four_of_a_kind_clear(player, played_rank_value, played_rank_str):
                    return
                
                self.game_message = f"{player.name} played {played_count} x {Card.get_rank_display(played_rank_str)} (higher rank)."

                # Check for bomb opportunity if this play results in 1, 2, or 3 of the new rank on the pile
                if 1 <= self.cards_of_rank_played[played_rank_value] <= 3:
                    self.record_interrupt_initiation(
                        'bomb_opportunity',
                        player_id,
                        played_rank_str,
                        f"A {Card.get_rank_display(played_rank_str)} bomb opportunity! Other players can now play remaining {4 - self.cards_of_rank_played[played_rank_value]} {Card.get_rank_display(played_rank_str)}s."
                    )
                    return
                
                self.advance_turn(skip_count=0)

            elif played_rank_value == self.current_play_rank:
                # --- Rule: Same Rank Play (Skipping next player) ---
                print(f"{player.name} has matched the rank. Skipping next player.")
                player.play_cards(cards_to_play)
                self.pile.extend(cards_to_play)
                self.last_played_cards = cards_to_play
                self.consecutive_passes = 0
                self.same_rank_streak += 1
                self.cards_of_rank_played[played_rank_value] += played_count        
                
                if self.check_and_perform_four_of_a_kind_clear(player, played_rank_value, played_rank_str):
                    return
                
                # If not a 4-of-a-kind bomb by current player, but creates a bomb opportunity for others.
                # This happens if self.cards_of_rank_played[played_rank_value] is now 1, 2, or 3.
                current_rank_total = self.cards_of_rank_played[played_rank_value]
                if 1 <= current_rank_total <= 3:
                    self.record_interrupt_initiation(
                        'bomb_opportunity',
                        player_id,
                        played_rank_str,
                        f"A {Card.get_rank_display(played_rank_str)} bomb opportunity! Other players can now play remaining {4 - current_rank_total} {Card.get_rank_display(played_rank_str)}s."
                    )
                    return # Interrupt active, halt regular turn progression

                # If no 4-of-a-kind was achieved, and no bomb opportunity was initiated, then apply skip rule
                self.should_skip_next_player = True
                self.game_message = f"{player.name} matched the rank! Next player will be skipped."
                
                # Advance the turn, applying the skip
                self.advance_turn(skip_count=1 if self.should_skip_next_player else 0)
                self.should_skip_next_player = False

            else:
                raise ValueError(f"Your play ({Card.get_rank_display(played_rank_str)}) must be higher than or match the current top card ({Card.get_rank_display(played_rank_str)}).")
        
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
            self.current_player_index = self.players.index(last_player_to_play)
            self.consecutive_passes = 0
            self.threes_played_this_round = 0
            self.same_rank_streak = 0
            self.should_skip_next_player = False
            self.pile_cleared_this_turn = False
            self.cards_of_rank_played = {rank.get_value(): 0 for rank in Rank.all_ranks()}
            self.advance_turn(skip_count=0)
        else:
            self.advance_turn(skip_count=0)

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

        if self.is_game_over:
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
        self.interrupt_bids = []
        self.interrupt_active_until = time.time() + self.INTERRUPT_TIMEOUT_SECONDS
        self.players_responded_to_interrupt = set()

        self.players_responded_to_interrupt.add(initiator_player_id)

        for player in self.players:
            if player.is_out and player.player_id not in self.players_responded_to_interrupt:
                self.players_responded_to_interrupt.add(player.player_id)
        
        self.game_message = message
        self.interrupt_original_skip_state = self.should_skip_next_player
        self.should_skip_next_player = False
        print(f"DEBUG: Interrupt of type '{interrupt_type}' initiated by {initiator_player_id} for rank {interrupt_rank}. Active until {self.interrupt_active_until}")


    def add_interrupt_bid(self, player_id, cards_data):
        """
        Allows a player to submit a bid during an active interrupt window.
        """
        print(f"DEBUG: cards_data received: {cards_data}")
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
            if not all(card.rank == Rank.THREE for card in cards_to_play):
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
            # A "bomb" is always 4 of a kind, and completes the set of 4 for the current rank on pile.
            bomb_rank = cards_to_play[0].rank
            
            if not all(card.rank == bomb_rank for card in cards_to_play):
                raise ValueError("A bomb must consist of cards of the same rank.")

            if bomb_rank != self.interrupt_rank:
                raise ValueError(f"Your bomb ({Card.get_rank_display(bomb_rank)}) must be of the same rank as the current play ({Card.get_rank_display(self.interrupt_rank)}).")

            num_on_pile_of_rank = self.cards_of_rank_played.get(Card._numeric_rank_map.get(bomb_rank), 0)
            
            if len(cards_to_play) + num_on_pile_of_rank != 4:
                raise ValueError(f"To play a bomb, you must play exactly {4 - num_on_pile_of_rank} cards of rank {Card.get_rank_display(bomb_rank)} to complete a set of four.")

            if any(bid[0] == player_id for bid in self.interrupt_bids):
                raise ValueError("You have already submitted a bid for this bomb opportunity.")

        else:
            raise ValueError(f"Unknown interrupt type: {self.interrupt_type}. Cannot process bid.")

        self.interrupt_bids.append((player_id, cards_to_play))
        self.game_message = f"{player.name} has submitted an interrupt bid."
        print(f"Player {player_id} bid on interrupt with: {[str(c) for c in cards_to_play]}")

    def submit_interrupt_bid(self, player_id, cards_data=None):
        """
        Allows a player to submit cards for an interrupt bid or pass on the interrupt.
        cards_data: list of card dictionaries if bidding, None if passing.
        """
        if not self.interrupt_active:
            raise ValueError("No interrupt is currently active.")
        if player_id in self.players_responded_to_interrupt:
            raise ValueError("You have already responded to this interrupt.")
        if player_id == self.interrupt_initiator_player_id:
            raise ValueError("You initiated this interrupt opportunity and cannot bid on it.")

        player = self.get_player_by_id(player_id)
        if not player or player.is_out:
            raise ValueError("Only active players can respond to an interrupt.")

        self.players_responded_to_interrupt.add(player_id)

        if cards_data:
            cards_to_bid = [Card(c['suit'], c['rank'], id=c.get('id')) for c in cards_data]
            if not cards_to_bid:
                raise ValueError("No cards selected for interrupt bid.")
            
            # --- Basic Validation for the bid ---
            if self.interrupt_type == 'three_play':
                if not (len(cards_to_bid) == 1 and cards_to_bid[0].rank == Rank.THREE):
                    raise ValueError("For a three-play interrupt, you must play exactly one 3.")
            elif self.interrupt_type == 'bomb_opportunity':
                if not (len(cards_to_bid) == 4 and all(c.rank == cards_to_bid[0].rank for c in cards_to_bid)):
                    raise ValueError("A bomb bid must be exactly 4 cards of the same rank.")
                if cards_to_bid[0].get_value() != self.interrupt_rank:
                     raise ValueError(f"Bomb bid must be for rank {Card.get_rank_display(self.interrupt_rank)}.")
            else:
                raise ValueError("Invalid interrupt type to bid on.")

            # Check if player actually has the cards they are trying to bid
            for card_to_bid in cards_to_bid:
                if card_to_bid not in player.get_hand().cards:
                    raise ValueError(f"You do not have the card {card_to_bid} in your hand for the bid.")
            
            # Store the valid bid
            self.interrupt_bids.append({
                'player_id': player_id,
                'cards': cards_to_bid,
                'bid_time': time.time()
            })
            self.game_message = f"{player.name} placed a bid for the {self.interrupt_type} interrupt."
            print(f"DEBUG: {player.name} submitted interrupt bid: {cards_data}")
        else:
            self.game_message = f"{player.name} passed on the {self.interrupt_type} interrupt."
            print(f"DEBUG: {player.name} passed on interrupt.")

        # Check if all relevant players have responded.
        # Relevant players are all active players minus the initiator.
        all_active_players_except_initiator = {pid for pid in self.get_active_player_ids() if pid != self.interrupt_initiator_player_id}

        if self.players_responded_to_interrupt.issuperset(all_active_players_except_initiator):
            print("DEBUG: All players have responded to the interrupt. Resolving now.")
            self.resolve_interrupt()
        else:
            print(f"DEBUG: {len(self.players_responded_to_interrupt)}/{len(all_active_players_except_initiator) + 1} players responded.") # +1 to include initiator in total count

    def get_active_player_ids(self):
        """Returns a set of player IDs for players who are still in the game."""
        return {p.player_id for p in self.players if not p.is_out}

    def get_player_by_id(self, player_id):
        """Helper to get a player object by their ID."""
        for player in self.players:
            if player.player_id == player_id:
                return player
        return None

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
        all_relevant_plays.extend(self.interrupt_bids)

        if self.interrupt_type == 'three_play':
            # Logic to find the winning bid for a 3-play
            highest_bid_count = 0
            for bid in self.interrupt_bids:
                bid_count = len(bid['cards'])
                # Only consider valid 3-play bids (should be pre-validated in submit_interrupt_bid too)
                if all(c.rank == Rank.THREE for c in bid['cards']):
                    if bid_count > highest_bid_count:
                        highest_bid_count = bid_count
                        winner_id = bid['player_id']
                        winning_bid_cards = bid['cards']
                    elif bid_count == highest_bid_count:
                        # Tie-breaking rule for 3s: e.g., player earliest in turn order or first to bid.
                        # For simplicity, if tied, the first one submitted wins.
                        pass # Current logic keeps the first highest bid in the list

            if winning_bid_cards: # If someone successfully bid and won
                winner = self.get_player_by_id(winner_id)
                if not winner:
                    raise Exception("Interrupt winner not found.")

                # Remove cards from winner's hand
                for card_to_remove in winning_bid_cards:
                    if card_to_remove in winner.hand.cards: # Ensure card is still in hand
                        winner.hand.cards.remove(card_to_remove)
                    else:
                        print(f"WARNING: Card {card_to_remove} not found in {winner.name}'s hand during 3-play interrupt resolution.")
                
                self.pile.extend(winning_bid_cards) # Add winning 3s to the pile
                self.clear_pile() # A successful 3-play clears the pile
                self.game_message = f"{winner.name} won the 3-play interrupt by playing {len(winning_bid_cards)} three(s)! They clear the pile and start the next round."
                self.current_player_index = self.players.index(winner) # Winner starts next round

            else: # No one successfully countered the 3-play
                self.game_message = f"No one countered the 3-play interrupt. The play stands."
                # The turn should remain with the player who initiated the 3-play.
                self.current_player_index = self.players.index(self.get_player_by_id(self.interrupt_initiator_player_id))
            
            # Reset threes_played_this_round after resolution (this is important)
            self.threes_played_this_round = 0

        elif self.interrupt_type == 'bomb_opportunity':
            # For bomb, usually the first valid bomb bid wins.
            winning_bomb_bid = None
            for bid in self.interrupt_bids:
                # Check if it's a valid 4-of-a-kind of the correct rank
                if (len(bid['cards']) == 4 and 
                    all(c.rank == Card.get_rank_display(self.interrupt_rank) for c in bid['cards']) and
                    all(c.get_value() == self.interrupt_rank for c in bid['cards'])): # Double check rank value too
                    
                    # Also, re-confirm the player actually has these cards (safety check)
                    player_bid = self.get_player_by_id(bid['player_id'])
                    if player_bid and all(c in player_bid.hand.cards for c in bid['cards']):
                        winning_bomb_bid = bid
                        break # Found the first valid winning bomb bid
            
            if winning_bomb_bid:
                winner_id = winning_bomb_bid['player_id']
                winning_bid_cards = winning_bomb_bid['cards']
                winner = self.get_player_by_id(winner_id)
                if not winner:
                    raise Exception("Bomb interrupt winner not found.")

                for card_to_remove in winning_bid_cards:
                    if card_to_remove in winner.hand.cards:
                        winner.hand.cards.remove(card_to_remove)
                    else:
                        print(f"WARNING: Card {card_to_remove} not found in {winner.name}'s hand during bomb resolution.")
                
                self.pile.extend(winning_bid_cards)
                self.clear_pile() # Bomb clears the pile
                self.game_message = f"{winner.name} successfully bombed the pile with {Card.get_rank_display(self.interrupt_rank)}s! They clear the pile and start the next round."
                self.current_player_index = self.players.index(winner) # Winner starts next round
            else:
                self.game_message = f"No one successfully bombed the {Card.get_rank_display(self.interrupt_rank)}s. The play stands."
                # The turn should remain with the player who initiated the bomb opportunity.
                self.current_player_index = self.players.index(self.get_player_by_id(self.interrupt_initiator_player_id))

        else:
            self.game_message = "Interrupt resolved without a clear winner or unrecognized type. Turn proceeds."
            initiator_player_obj = self.get_player_by_id(self.interrupt_initiator_player_id)
            if initiator_player_obj and initiator_player_obj.is_active and not initiator_player_obj.is_out:
                self.current_player_index = self.players.index(initiator_player_obj)
            self.game_message = "Interrupt resolved." 

        # Always reset interrupt state after resolution
        self.interrupt_active = False
        self.interrupt_type = None
        self.interrupt_initiator_player_id = None
        self.interrupt_rank = None
        self.interrupt_bids = []
        self.interrupt_active_until = None
        self.players_responded_to_interrupt = set()

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