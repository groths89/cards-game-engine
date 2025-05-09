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
            2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10,
            11: 11, 12: 12, 13: 13, 14: 14
        }
        return rank_values.get(self.rank)
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.suit == other.suit and self.rank == other.rank