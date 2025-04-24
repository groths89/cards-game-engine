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

## Next Steps

- Implement player turns and basic play validation.
- Handle passing and clearing the pile.
- Determine the winner of a round.

## Development Environment

- **Language:** Python(Game Engine), JavaScript (Front-End UI)
