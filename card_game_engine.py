import random

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        # How we want the card to be displayed
        rank_map = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
        rank_str = str(self.rank) if 2 <= self.rank <= 10 else rank_map.get(self.rank)
        return f"{self.suit[0]}{rank_str}" # Using the first letter of the suit for brevity
    
    def __repr__(self):
        return f"Card('{self.suit}', {self.rank})"
    
    def get_value(self):
        # Assign numerical values for comparing ranks in "Asshole"
        rank_values = {
            3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10,
            11: 11, 12: 12, 13: 13, 14: 14, 2: 15 # 2 is typically high and is the clearing card
        }
        return rank_values.get(self.rank)
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.suit == other.suit and self.rank == other.rank

class Deck:
    def __init__(self):
        self.cards = self._create_deck()

    def _create_deck(self):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks = list(range(2, 15)) # 2 to 14(Ace)
        return [Card(suit, rank) for suit in suits for rank in ranks]
    
    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self):
        if self.cards:
            return self.cards.pop() # Remove and return the top card
        return None
    
    def __len__(self):
        return len(self.cards)

class Hand:
    def __init__(self, cards=None):
        self.cards = cards if cards is not None else []

    def add_card(self, card):
        self.cards.append(card)
    
    def __str__(self):
        return ", ".join(str(card) for card in self.cards)
    
    def __repr__(self):
        return f"Hand(cards={[repr(card) for card in self.cards]})"
    
    def sort_by_rank(self):
        self.cards.sort(key=lambda card: card.get_value())

    def play_cards(self, cards_to_play):
        # For now, let's just remove the cards from the hand.
        # We'll add validation logic in the game state.
        played_cards = []
        indices_to_remove = sorted([self.cards.index(card) for card in cards_to_play], reverse=True)
        for index in indices_to_remove:
            played_cards.append(self.cards.pop(index))
        return played_cards
    
    def get_cards_by_rank(self, rank):
        return [card for card in self.cards if card.rank == rank]

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = Hand()

    def add_card(self, card):
        self.hand.add_card(card)

    def play_cards(self, cards_to_play):
        self.hand.play_cards(cards_to_play)

    def get_hand(self):
        return self.hand
    
    def __str__(self):
        return f"Player: {self.name}, Hand: {self.hand}"
    
    def __repr__(self):
        return f"Player(name='{self.name}', hand='{self.hand}')"
    
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

    # Create a method for what happens on that players turn
    def play_turn(self, player, cards_to_play):
        current_player = self.get_current_player()
        if (current_player != player):
            print(f"It's not {player.name}'s turn. It's {current_player.name}'s turn.")
            return
        
        player_hand = player.get_hand().cards
        for card_to_play in cards_to_play:
            if card_to_play not in player_hand:
                print(f"{player.name} does not have the card {card_to_play} in their hand.")
                return

        if not cards_to_play:
            print(f"{player.name} must play at least one card to start the trick.")

        played_rank = cards_to_play[0].rank
        if not all(card.rank == played_rank for card in cards_to_play):
            print(f"{player.name} must play cards of the same rank.")
            return

        # --- Detect and Handle 3 plays ---
        if played_rank == 3:
            self.threes_played_this_round += len(cards_to_play) # Increment counter by the number of 3s played
            print(f"{player.name} has played {len(cards_to_play)} threes (total: {self.threes_played_this_round} this round).")
            # Add the second 3 logic here later
            player.play_cards(cards_to_play)
            self.pile.extend(cards_to_play)

            if self.threes_played_this_round >= 2:
                print("Second 3 played! Pile cleared. It starts with the player who played the second 3.")
                self.pile = []
                self.current_play_rank = None # reset the rank
                self.current_play_count = None # reset the count
                self.current_player_index = self.players.index(player) # It starts with the current player
                self.threes_played_this_round = 0 # reset the counter for the next round
            else:
                self.current_player_index = (self.current_player_index + 1) % len(self.players)
            return # End the turn after playing a 3 for now

        # --- Handle non-3 plays ---
        if not self.pile:
            print(f"{player.name} has played {cards_to_play}.")
            player.play_cards(cards_to_play)
            self.pile.extend(cards_to_play)
            self.current_play_rank = cards_to_play[0].get_value()
            self.current_play_count = len(cards_to_play)
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        elif len(cards_to_play) == self.current_play_count:
            played_value = cards_to_play[0].get_value()
            if played_value > self.current_play_rank:
                print(f"{player.name} has played {cards_to_play}.")
                player.play_cards(cards_to_play)
                self.pile.extend(cards_to_play)
                self.current_play_rank = played_value # Use played_value here
                self.current_play_count = len(cards_to_play)
                self.current_player_index = (self.current_player_index + 1) % len(self.players)
            else:
                print(f"{player.name}'s play is not higher than the current play.")
                return
        else:
            print(f"{player.name} must play {self.current_play_count} cards to match the pile.")
            return

        if self.is_game_over():
            print("Game Over!")
            # Handle game over logic

    # Create a method for the game pile
    def get_game_pile(self):
        return self.pile
    
    # Create a method to check for the game over state
    def is_game_over(self):
        players_with_cards = 0
        for player in self.players:
            if len(player.get_hand().cards) > 0:
                players_with_cards += 1
        return players_with_cards == 1

def test_initial_state():
    player_names = ["Alice", "Bob", "Charlie"]
    game_state = GameState(player_names)

    print("--- Initial Game State ---")
    print(f"Number of cards in deck: {len(game_state.deck)}")
    for player in game_state.players:
        print(f"{player}") # This will print each player's hand

    starting_player = game_state.get_current_player()
    print(f"Starting player: {starting_player.name}")
    print(f"Initial pile: {game_state.get_game_pile()}")
    print(f"Is game over? {game_state.is_game_over()}")

if __name__ == "__main__":
    test_initial_state()