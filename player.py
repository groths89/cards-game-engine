from hand import Hand


class Player:
    def __init__(self, name):
        self.name = name
        self.hand = Hand()
        self.rank = None
        self.is_active = True

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