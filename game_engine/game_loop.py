import sys

from .card import Card
from .game_state import GameState

class GameLoop:
    def __init__(self, game_state):
        self.game_state = game_state
        
    def run(self):
        """
        The main loop that drives the game.
        """
        print(f"Game Over at start: {self.game_state.is_game_over()}")
        self.player_went_out = 0

        while not self.game_state.is_game_over():
            self.game_state.should_skip_next_player = False
            self.game_state.pile_cleared_this_turn = False
            current_player = self.game_state.get_current_player()
            print(f"\nIt's {current_player.name}'s turn.")
            print(f"{current_player.name}'s hand: {current_player.hand}")
            print(f"Pile: {self.game_state.pile}")
            if self.game_state.current_play_rank is not None:
                print(f"Current play: {self.game_state.current_play_count} of rank {self.game_state.current_play_rank}")

            action = self.get_player_action(current_player)

            if action == "play":
                cards_to_play = self.get_cards_to_play(current_player)
                if cards_to_play:
                    try:
                        self.game_state.play_turn(current_player, cards_to_play)
                        self.game_state.handle_player_out()
                    except ValueError as e:
                        print(f"Invalid play: {e}")
                else:
                    print("No cards selected to play.")
            elif action == "pass":
                self.game_state.pass_turn(current_player)
            else:
                print("Invalid action.")

        self.game_state.end_game()

    def get_player_action(self, player):
        """
        Gets the action (play or pass) from the current player.
        This needs to be adapted for your input method (e.g., text-based, UI).
        """
        while True:
            try:
                action = input(f"{player.name}, what do you want to do? (play/pass): ").lower()
                if action in ["play", "pass"]:
                    return action
                else:
                    print("Invalid action. Please enter 'play' or 'pass'.")
            except KeyboardInterrupt:
                print("\nGame interrupted by user. Exiting.")
                exit()

    def get_cards_to_play(self, player):
        """
        Gets the cards the player wants to play.
        This needs to be adapted for your input method.
        For a text-based interface, you'll need to parse the input.
        """
        while True:
            try:
                card_input = input(f"{player.name}, enter the cards you want to play (e.g., S3 H3 D3) or 'back': ").upper()
                if card_input.lower() == 'back':
                    return None # Player decided not to play after looking at their cards
                try:
                    cards_to_play = self.parse_card_input(player, card_input)
                    return cards_to_play
                except ValueError as e:
                    print(f"Invalid card input: {e}")
            except KeyboardInterrupt:
                print("\nGame interrupted by user. Exiting.")
                exit()

    def parse_card_input(self, player, card_input):
        print(f"{player.name}'s hand: {[str(card) for card in player.hand.cards]}")
        cards = []
        card_strings = card_input.split()
        if not card_strings:
            print("You must enter cards to play or 'Pass'.")
            return []

        for card_str in card_strings:
            print(f"Processing card string: {card_str}")  # Debug print
            if len(card_str) >= 2:
                suit_char = card_str[0].upper()
                rank_str = card_str[1:]
                suit = None
                rank = None
                print(f"  Suit char: {suit_char}, Rank str: {rank_str}") # Debug print
                if suit_char == 'S':
                    suit = "Spades"
                    print(f"  Suit: {suit}") # Debug print
                elif suit_char == 'H':
                    suit = "Hearts"
                    print(f"  Suit: {suit}") # Debug print
                elif suit_char == 'D':
                    suit = "Diamonds"
                    print(f"  Suit: {suit}") # Debug print
                elif suit_char == 'C':
                    suit = "Clubs"
                    print(f"  Suit: {suit}") # Debug print
                else:
                    raise ValueError(f"Invalid suit: {suit_char}")

                try:
                    rank = int(rank_str)
                    print(f"  Rank: {rank}") # Debug print                    
                    if not 2 <= rank <= 10 and rank not in [11, 12, 13, 14]:
                        raise ValueError(f"Invalid rank: {rank_str}")
                except ValueError:
                    if rank_str == 'J':
                        rank = 11
                    elif rank_str == 'Q':
                        rank = 12
                    elif rank_str == 'K':
                        rank = 13
                    elif rank_str == 'A':
                        rank = 14
                    else:
                        raise ValueError(f"Invalid rank: {rank_str}")

                card = Card(suit, rank)
                if not player.has_card(card):
                    raise ValueError(f"You don't have the card: {card}")
                cards.append(card)
            else:
                raise ValueError(f"Invalid card format: {card_str}")

        # Basic validation: all played cards must be the same rank
        if cards and not all(card.rank == cards[0].rank for card in cards):
            raise ValueError("All played cards must be of the same rank.")

        return cards