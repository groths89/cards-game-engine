import random

from .card import Card

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
            return self.cards.pop(0) # Remove and return the top card
        return None
    
    def __len__(self):
        return len(self.cards)
    
    def __str__(self):
        return ", ".join(str(card) for card in self.cards)

    def __repr__(self):
        return f"Deck(cards={[repr(card) for card in self.cards]})"