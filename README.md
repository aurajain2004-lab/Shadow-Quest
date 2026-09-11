# Shadow Quest

Shadow Quest is a top-down 2D dungeon adventure built with Python 3 and Pygame. In Version 1.1.0, guide the hero through a dark, tile-based dungeon, fight chaser enemies, and reach the exit.

## Version 1.1.0 — Combat Update

Implemented features:

- Main menu with Play, Instructions, and Quit buttons
- Instructions screen
- Smooth WASD and arrow-key movement
- Grid-based dungeon with rooms, corridors, walls, torches, and an exit door
- Rectangle collision with wall sliding
- Chaser enemies with wall-aware movement, health bars, and contact damage
- Directional attacks with cooldowns and hit feedback
- Player health bar, enemy count, and defeated-enemy counter
- Game Over screen with restart and main-menu actions
- Gameplay HUD with health, enemy status, level, and objective
- Pause, resume, restart, and main-menu actions
- Level-complete screen with replay support
- Mouse and keyboard menu navigation

Weapons beyond the basic attack, items, power-ups, multiple levels, bosses, audio, score, and high scores are intentionally reserved for future releases.

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

The game opens at 1000 x 700 pixels.

## Project Structure

```text
Catch-The-Objects/
├── main.py          # Game states, dungeon, player, UI, and main loop
├── requirements.txt # Pygame dependency
└── README.md        # Project documentation
```