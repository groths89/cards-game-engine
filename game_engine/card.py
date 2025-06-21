import uuid
class Suit:
    CLUBS = "C"
    DIAMONDS = "D"
    HEARTS = "H"
    SPADES = "S"
    ALL_SUITS = [CLUBS, DIAMONDS, HEARTS, SPADES]

class Rank:
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"

    @classmethod
    def all_ranks(cls):
        return [
            cls.TWO, cls.THREE, cls.FOUR, cls.FIVE, cls.SIX, cls.SEVEN,
            cls.EIGHT, cls.NINE, cls.TEN, cls.JACK, cls.QUEEN, cls.KING, cls.ACE  
        ]

class Card:
    def __init__(self, suit, rank):
        self.id = str(uuid.uuid4())
        self.suit = suit
        self.rank = rank

    _rank_display_names = {
        Rank.TWO: "2", Rank.THREE: "3", Rank.FOUR: "4", Rank.FIVE: "5",
        Rank.SIX: "6", Rank.SEVEN: "7", Rank.EIGHT: "8", Rank.NINE: "9",
        Rank.TEN: "10", Rank.JACK: "Jack", Rank.QUEEN: "Queen",
        Rank.KING: "King", Rank.ACE: "Ace"
    }

    def get_rank_display(self):
        return self._rank_display_names.get(self.rank, self.rank)

    def to_string(self):
        return f"{self.rank}{self.suit}"
    
    def __str__(self):
        return self.to_string()
    
    def __repr__(self):
        return f"Card('{self.suit}', {self.rank})"
    
    def get_value(self):
        rank_values = {
            Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5,
            Rank.SIX: 6, Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9,
            Rank.TEN: 10, Rank.JACK: 11, Rank.QUEEN: 12, Rank.KING: 13,
            Rank.ACE: 14
        }
        return rank_values.get(self.rank)
    @staticmethod
    def string_to_card(card_str):
        if len(card_str) < 2:
            return None

        # Correctly parse based on your Rank/Suit string formats
        # Handle '10' rank specifically as it's 2 chars
        if card_str.startswith('10'):
            rank_char = '10' # Or '10', depending on how you represent TEN internally
            suit_char = card_str[2].upper()
        else:
            rank_char = card_str[0].upper()
            suit_char = card_str[1].upper()

        # Map back to your Suit and Rank classes' values if needed, or directly to your stored values
        # This assumes your Card constructor expects 'C', 'D', 'H', 'S' for suit and '2', 'T', 'J' etc for rank
        if suit_char in [s.value for s in [Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES]]:
             suit = suit_char
        else:
            return None # Invalid suit

        if rank_char in [r.value for r in [
            Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX, Rank.SEVEN,
            Rank.EIGHT, Rank.NINE, Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE
        ]]:
            rank = rank_char
        else:
            return None # Invalid rank

        return Card(suit, rank)
        
    def to_dict(self):
        return {'id': self.id, 'rank': self.rank, 'suit': self.suit}

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.suit == other.suit and self.rank == other.rank