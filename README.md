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

- **Standard 52-card deck:** Includes creation, shuffling, and dealing of a standard deck of cards.
- **Multiple players:** Supports gameplay with multiple players.
- **Turn-based gameplay:** Manages the progression of turns between players.
- **Card playing validation:** Enforces rules for playing cards (same rank, higher rank to play on the pile).
- **"Stall" card (3):** Detects when a 3 is played as a stall.
- **"Clearing" second 3:** Implements the rule where the second 3 played in a round clears the pile and gives the turn to the player who played it (acting as a 2).
- **Ace of Spades starts:** Implements the rule where the player holding the Ace of Spades goes first.
- **Game over detection:** Determines when the game ends (only one player left with cards).
- **Basic game state tracking:** Keeps track of the current player, the cards on the pile, and the current play rank and count.

## Next Steps

- Detecting the end of a "round of play based on consecutive passes
- Allowing the last player to play to lead the next round
- Tracking when a player runs out of cards and is out of the game
- Determining the game over condition (only one player left with cards)
- Tracking the order in which players go out to determine their rank

## How to Use

1.  **Clone the repository** (if you haven't already).
2.  **Run the game** (you'll need to add code to instantiate and run the game loop, which is the next step in development).

    ```bash
    python card_game_engine.py
    ```

## Development Status

This project is currently under development. The following features are planned for future implementation:

- Handling a complete round of play (consecutive passes).
- Tracking players who are out of the game.
- Determining the order in which players go out (ranking).
- Implementing a basic game loop to drive the game flow.
- Potentially adding support for passing.
- More comprehensive unit tests.

## Development Environment

- **Language:** Python(Game Engine), JavaScript (Front-End UI)

## Contributing

Contributions are welcome! If you have suggestions, bug reports, or would like to contribute code, please feel free to open an issue or submit a pull request.
