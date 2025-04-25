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
    def __init__(self):
        self.cards = []

    def add_card(self, card):
        if card:
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
        incices_to_remove = sorted([self.cards.index(card) for card in cards_to_play], reverse=True)
        for index in incices_to_remove:
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
        return Hand.play_cards(cards_to_play)

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
        self.starting_card_suit = "Clubs"
        self.starting_card_rank = 3

        for index, player in enumerate(self.players):
            for card in player.get_hand().cards:
                if card.suit == self.starting_card_suit and card.rank == self.starting_card_rank:
                    return index
            return 0

    # Create a method to get the current player
    def get_current_player(self):
        return self.players[self.current_player_index]

    # Create a method for what happens on that players turn
    def on_players_turn(self):
        # It should take a player and a list of cards to play as an argument
        pass

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
