import sys

from card import Card
from game_state import GameState

class GameLoop:
    def __init__(self, game_state):
        self.player_went_out = 0 # Counter to track when a player goes out
        self.game_state = game_state
        game_state.determine_starting_player()
        
    def run(self):
        while not self.game_state.is_game_over():
            self.current_player = self.game_state.get_current_player()
            print(f"\nIt's {self.current_player.name}'s turn.")
            print("Player's action (Play or Pass):")
            current_player_action = input().strip().lower() # Asks the player for input then strips the trailing white space and makes it all lower case
            if current_player_action == "pass":
                self.game_state.pass_turn(self.current_player)
                self.handle_player_out()
            elif current_player_action == "play":
                cards_to_play = self.get_cards_to_play_from_input(self.current_player)
                if cards_to_play:
                    self.game_state.play_turn(self.current_player, cards_to_play)
                    self.handle_player_out()
                else:
                    print("You must select cards to play.")
            else:
                print("Invalid action. Please enter 'Play' or 'Pass'.")
            
        # Determine and print the winner
        winner = self.game_state.get_winner()
        print(f"\nGame Over! The winner is {winner.name}!")

        # Print the final ranks of all players
        print("\nFinal Rankings:")
        for player in sorted(self.game_state.players, key=lambda p: p.rank if p.rank else float('inf')):  # Sort by rank, inactive last
            rank_name = self.get_rank_name(player.rank, len(self.game_state.players)) if player.rank else "Not Finished"
            print(f"{player.name}: {rank_name}")

    def get_cards_to_play_from_input(self, player):
        print(f"{player.name}'s hand: {[str(card) for card in player.hand.cards]}")
        card_strings = input("Enter the cards you want to play (e.g., H5 S5): ").strip().upper().split()
        cards_to_play = []
        hand_copy = player.hand.cards[:]

        if not card_strings:
            print("You must enter cards to play or 'Pass'.")
            return []

        for s in card_strings:
            print(f"Processing card string: {s}")  # Debug print
            suit = None
            rank = None
            if len(s) < 2:
                print(f"Invalid card format: {s}")
                return []
            suit_char = s[0]  # Get the first character for the suit
            rank_str = s[1:]  # Get the rest for the rank
            print(f"  Suit char: {suit_char}, Rank str: {rank_str}") # Debug print

            suit_map = {'H': 'Hearts', 'S': 'Spades', 'D': 'Diamonds', 'C': 'Clubs'}
            suit = suit_map.get(suit_char)
            print(f"  Suit: {suit}") # Debug print

            rank_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
            rank = rank_map.get(rank_str)
            print(f"  Rank: {rank}") # Debug print

            if suit and rank:
                card_to_find = Card(suit, rank)
                if card_to_find in hand_copy:
                    cards_to_play.append(card_to_find)
                    hand_copy.remove(card_to_find)
                else:
                    print(f"You don't have another {card_to_find} in your hand.")
                    return []
            else:
                print(f"Invalid card format: {s}")
                return []
        return cards_to_play

    def handle_player_out(self):
        for player in self.game_state.players:
            if len(player.get_hand().cards) == 0 and player.is_active:
                player.is_active = False
                self.player_went_out += 1
                player.rank = self.player_went_out
                rank_name = self.get_rank_name(player.rank, len(self.game_state.players))
                print(f"{player.name} went out and he is the {rank_name}")

    def get_rank_name(self, rank, num_players):
        if rank == 1:
            return "President"
        elif rank == 2:
            return "Vice-President"
        elif rank == 3:
            return "Secretary of Keeping it Real"
        elif rank == 4:
            return "Commodore"
        elif 5 <= rank <= (num_players - 2):
            return "Peasant"
        elif rank == num_players - 1:
            return "Vice-Asshole"        
        elif rank == num_players:
            return "Asshole"
        else:
            return f"Rank {rank}"