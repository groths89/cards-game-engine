# Card Game Engine - Project Start

## Overview

This project aims to build a versatile card game engine, starting with support for the game "Asshole" (also known as "Presidents"). The eventual goal is to deploy this as a web application with multiple different card games.

## Initial Scope - "Asshole" (Single Round, Local Play)

- **Number of Players:** 4-8+
- **Gameplay Mechanics:**
  - Dealing cards
  - Players taking turns playing sets of cards of the same rank.
  - Following suit and rank (initially, just rank).
  - Passing turns.
  - Clearing the play pile.
  - Determining the winner (first to run out of cards).

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
  - Turn-based gameplay: Manages the progression of turns, ensuring only active players participate.
  - Card playing validation: Enforces rules for playing cards (matching rank, higher rank to play on the pile).
  - Passing turns: Allows players to pass if they cannot or choose not to play. Consecutive passes by all other active players clear the pile.
  - Clearing the play pile: Occurs when a player plays all four cards of a rank or when all other active players pass consecutively. The player who cleared the pile leads the next play.
  - Handling rounds of play: Manages the flow of turns within a single round.
- **"Asshole" Specific Rules:**
  - Card ranking: 3 (low) - 2 (high, special).
  - Ace of Spades starts: The player with the Ace of Spades goes first.
  - "Stall" card (3): Detects when a 3 is played, resetting the current play rank.
  - Clearing with the second 3: Implements the rule where playing a 3 resets the pile's rank.
- **Player Interaction:**
  - Player input: Allows players to enter "Play" or "Pass" actions.
  - Card input parsing: Robustly parses player input to identify cards to play from their hand.
- **Game State:**
  - Comprehensive game state tracking: Keeps track of the current player, cards on the pile, the current play rank/count, and active/inactive players.
  - Game over detection: Determines when the game ends (only one active player remains).
  - Tracking player ranking: Records the order in which players run out of cards.
- **Game Flow:**
  - Main game loop: Drives the game flow, handling player turns and actions.
  - Handling players going out: Correctly marks players as out and records their rank.
  - End game logic: Determines the "Asshole" (last player out) and displays the final rankings.

## Planned Features

The following features are planned for future implementation:

- More "Asshole" Rules:
  - Implement special rules for the card '2' (pile clear).
  - Persistent ranks and card passing between rounds based on the previous round's rankings.
- User Interface:
  - Graphical user interface (GUI) development.
- Other Improvements:
  - Potentially adding support for more complex passing scenarios or rule variations.
  - More comprehensive unit tests.
  - Deployment as a web application.

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
- Fix if all 4 of a rank is played it should clear to the player that played the last of the rank
- Fix when a player goes out the passing gets out of sync

## Development Environment

- **Language:** Python(Game Engine), JavaScript (Front-End UI)

## Contributing

Contributions are welcome! If you have suggestions, bug reports, or would like to contribute code, please feel free to open an issue or submit a pull request.
