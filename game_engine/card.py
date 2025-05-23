class Suit:
    CLUBS = "C"
    DIAMONDS = "D"
    HEARTS = "H"
    SPADES = "S"

class Rank:
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "T"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def to_string(self):
        return f"{self.rank}{self.suit}"
    
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
    
    def string_to_card(self, card_str):
        if len(card_str) < 2:
            return None
        
        suit_char = card_str[0].upper()
        rank_str = card_str[1:]

        suit_map = {'H': 'Hearts', 'D': 'Diamonds', 'C': 'Clubs', 'S': 'Spades'}
        rank_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

        suit = suit_map.get(suit_char);
        rank = rank_map.get(rank_str)

        if suit and rank:
            return Card(suit, rank)
        else:
            return None

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.suit == other.suit and self.rank == other.rank