import uuid
from .hand import Hand


class Player:
    def __init__(self, name, hand=None, player_id=None):
        self.name = name
        self.hand = Hand()
        self.rank = None
        self.is_active = True
        self.is_out = False
        self.player_id = player_id if player_id is not None else str(uuid.uuid4())

    def add_card(self, card):
        self.hand.add_card(card)

    def play_cards(self, cards_to_play):
        """Removes the specified cards from the player's hand."""
        for card in cards_to_play:
            if card in self.hand.cards:
                self.hand.remove_card(card)
            else:
                print(f"Error: {self.name} tried to play a card they don't have: {card}")

    def has_card(self, card):
        """Checks if the player has a specific card in their hand."""
        return card in self.hand.cards
    
    def get_hand(self):
        return self.hand
    
    def __eq__(self, other):
        if not isinstance(other, Player):
            return NotImplemented
        return self.player_id == other.player_id

    def __hash__(self):
        return hash(self.player_id)

    def __str__(self):
        return f"Player: {self.name}, Hand: {self.hand}"
    
    def __repr__(self):
        return f"Player(name='{self.name}', hand='{self.hand}')"
    
    # Method to represent player for API (e.g., in lists of players)
    def to_dict(self):
        return {
            'name': self.name,
            'id': self.player_id,
            'is_active': self.is_active,
            'is_out': self.is_out,
            'rank': self.rank,
            'hand_size': len(self.hand.cards)
        }