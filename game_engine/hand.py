class Hand:
    def __init__(self, cards=None):
        self.cards = cards if cards is not None else []

    def add_card(self, card):
        self.cards.append(card)
    
    def remove_card(self, card_to_remove):
        """Removes a specific card from the hand."""
        if card_to_remove in self.cards:
            self.cards.remove(card_to_remove)
        else:
            print(f"Error: Tried to remove a card not in hand: {card_to_remove}")

    def __str__(self):
        return ", ".join(str(card) for card in self.cards)
    
    def __repr__(self):
        return f"Hand(cards={[repr(card) for card in self.cards]})"
    
    def sort_by_rank(self):
        self.cards.sort(key=lambda card: card.get_value())

    def play_cards(self, cards_to_play):
        played_cards = []
        indices_to_remove = sorted([self.cards.index(card) for card in cards_to_play], reverse=True)
        for index in indices_to_remove:
            played_cards.append(self.cards.pop(index))
        return played_cards
    
    def clear(self):
        self.cards = []

    def get_cards_by_rank(self, rank):
        return [card for card in self.cards if card.rank == rank]