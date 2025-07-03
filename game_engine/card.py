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
    _numeric_rank_map = {
        Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5,
        Rank.SIX: 6, Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9,
        Rank.TEN: 10, Rank.JACK: 11, Rank.QUEEN: 12, Rank.KING: 13,
        Rank.ACE: 14
    }

    _rank_display_names = {
        Rank.TWO: "2", Rank.THREE: "3", Rank.FOUR: "4", Rank.FIVE: "5",
        Rank.SIX: "6", Rank.SEVEN: "7", Rank.EIGHT: "8", Rank.NINE: "9",
        Rank.TEN: "10", Rank.JACK: "Jack", Rank.QUEEN: "Queen",
        Rank.KING: "King", Rank.ACE: "Ace"
    }

    _suit_display_names = {
        Suit.CLUBS: 'Clubs', Suit.DIAMONDS: 'Diamonds',
        Suit.HEARTS: 'Hearts', Suit.SPADES: 'Spades'      
    }

    def __init__(self, suit: str, rank: str, id: str = None):
        if suit not in Suit.ALL_SUITS:
            raise ValueError(f"Invalid suit: {suit}. Must be one of {Suit.ALL_SUITS}")
        if rank not in Rank.all_ranks():
            raise ValueError(f"Invalid rank: {rank}. Must be one of {Rank.all_ranks()}")
        self.id = id if id else str(uuid.uuid4())
        self.suit = suit
        self.rank = rank

    def to_string(self):
        return f"{self.rank}{self.suit}"
    
    def __str__(self):
        return self.to_string()
    
    def __repr__(self):
        return f"Card('{self.suit}', '{self.rank}', id='{self.id[:8]}...')"
    
    def get_value(self):
        return self._numeric_rank_map.get(self.rank)
    
    @staticmethod
    def get_rank_display(rank_str: str):
        return Card._rank_display_names.get(rank_str, rank_str)

    def get_suit_display(self):
        return self._suit_display_names.get(self.suit, self.suit)

    def to_dict(self):
        return {'id': self.id, 'rank': self.rank, 'suit': self.suit, 'numeric_rank': self.get_value(), 'name': self.get_rank_display(self.rank),  'full_name': f"{self.get_rank_display(self.rank)} of {self.get_suit_display()}"}

    @staticmethod
    def string_to_card(card_str):
        if len(card_str) < 2:
            return None

        if card_str.startswith('10'):
            rank_char = '10'
            suit_char = card_str[2].upper()
        else:
            rank_char = card_str[0].upper()
            suit_char = card_str[1].upper()

        if suit_char not in Suit.ALL_SUITS:
            return None

        if rank_char not in Rank.all_ranks():
            return None

        return Card(suit_char, rank_char)

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.suit == other.suit and self.rank == other.rank
    
    def __hash__(self):
        return hash((self.id, self.suit, self.rank))
    
    def __lt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_value() < other.get_value()
    
    def __le__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_value() <= other.get_value()