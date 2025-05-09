# Card Game Engine - Project Start

## Overview

This project aims to build a versatile card game engine, starting with support for the game "Asshole" (also known as "Presidents"). The eventual goal is to deploy this as a web application with multiple different card games.

## Initial Scope - "Asshole" (Single Round, Local Play)

- **Number of Players:** 4-8+
- **Card Ranking:** 3 (low) - 2 (high, special)
- **Gameplay Mechanics:**
  - Dealing cards
  - Players taking turns playing sets of cards of the same rank.
  - Following suit and rank (initially, just rank).
  - Passing turns.
  - Clearing the play pile.
  - Determining the winner (first to run out of cards).
- **Initial Exclusions:** Special card rules (2s, potentially 3s), persistent ranks between rounds, web interface.

## First Steps - Core Components

The initial development will focus on creating the fundamental building blocks:

- **Card Class:** Represents a single playing card (suit and rank).
- **Deck Class:** Manages a collection of cards, including creation, shuffling, and dealing.
- **Hand Class:** Represents a player's hand of cards, with methods for adding and removing cards.
- **Basic Game Initialization:** Setting up the deck, dealing to players.

## Features

- **Core Game Mechanics:**
  - Standard 52-card deck: Creation, shuffling, and dealing.
  - Multiple players: Supports gameplay with multiple players (4-8+ recommended).
  - Turn-based gameplay: Manages the progression of turns.
  - Card playing validation: Enforces rules for playing cards (matching rank, higher rank to play on the pile).
  - Passing turns.
  - Clearing the play pile.
  - Handling rounds of play: Logic for consecutive passes and starting new rounds.
- **"Asshole" Specific Rules:**
  - Card ranking: 3 (low) - 2 (high, special).
  - Ace of Spades starts: The player with the Ace of Spades goes first.
  - "Stall" card (3): Detects when a 3 is played.
  - "Clearing" second 3: Implements the rule where the second 3 played in a round clears the pile, and the player who played it leads the next round.
- **Player Interaction:**
  - Player input: Allows players to enter "Play" or "Pass" actions.
  - Card input parsing: Robustly parses player input to identify cards to play from their hand.
- **Game State:**
  - Basic game state tracking: Keeps track of the current player, cards on the pile, and the current play rank/count.
  - Basic game over detection: Determines when the game ends (one player left with cards).
- **Game Flow:**
  - Game loop: Implements a main game loop to drive the game flow.

## Planned Features

The following features are planned for future implementation:

- More "Asshole" Rules:
  - 2s can be played anytime
  - If all players play the same rank, the pile is cleared.
  - Passing twice starts a new round
  - Correct 2 value
  - Playing the same rank on top of the rank skips the next player
- Ranking and Game End:
  - Tracking the order in which players finish (ranking).
  - Tracking players who are out of the game.
  - Implementing the `handle_player_out()` method in the game loop.
  - Implementing the `end_game()` method to declare the "Asshole".
- User Interface:
  - Graphical user interface (GUI) development.
- Other Improvements:
  - Potentially adding support for more complex passing scenarios.
  - More comprehensive unit tests.

## How to Use

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/groths89/cards-game-engine
    cd card-game-engine
    ```

2.  **Run the game:**

    ```bash
    python -m main # Run the main.py module
    ```

## Development Status

This project is currently under development.

- Fix if 3 of the same rank is played it will allow the fourth of that rank to be played
- Add if a player has the last of the rank played it will allow them to play and not have to be next player

## Development Environment

- **Language:** Python(Game Engine), JavaScript (Front-End UI)

## Contributing

Contributions are welcome! If you have suggestions, bug reports, or would like to contribute code, please feel free to open an issue or submit a pull request.
