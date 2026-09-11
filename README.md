# Shadow Quest

Shadow Quest is a 2D top-down dungeon adventure developed using Python and Pygame. Explore three handcrafted dungeons, collect keys and items, fight multiple enemy types, defeat the final boss, and escape.

## Version 2.0.0 — Final Release

Features:

- Multiple dungeon levels with wall collision
- Combat with directional attacks and hit feedback
- Chaser and patrol enemy types
- Final boss battle with a boss health bar
- Keys and locked exits
- Coins and scoring across all levels
- Health potions
- Temporary attack power-up
- Local high-score persistence
- Pause, restart, and Game Over screens
- Final Victory screen with replay and main-menu actions
- Resizable window and keyboard/mouse menu navigation

## Controls

- `WASD` or Arrow Keys: Move
- `SPACE`: Attack in the direction the hero is facing
- `ESC`: Pause or resume during gameplay
- Arrow Keys / `W` and `S`: Navigate menus
- `Enter` or `Space`: Activate the selected menu button

## Installation and Running

Use Python 3. Install the dependency from the project directory:

```text
python -m pip install -r requirements.txt
```

Start the game with:

```text
python main.py
```

The game opens at 1000 x 700 pixels. A local `shadow_quest_high_score.txt` file is created beside the game when a run records a score.

## Version History

- v1.0.0 - Dungeon Foundation
- v1.1.0 - Combat Update
- v2.0.0 - Final Release

The project is tracked using Git and GitHub with versioned releases.

## Project Structure

```text
Shadow-Quest/
├── main.py          # Game states, dungeon, player, UI, and main loop
├── requirements.txt # Pygame dependency
└── README.md        # Project documentation
```