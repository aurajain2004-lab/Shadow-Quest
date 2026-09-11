# Shadow Quest

Shadow Quest is a top-down 2D dungeon adventure built with Python 3 and Pygame. In Version 1.0.0, guide the hero through a dark, tile-based dungeon and reach the exit.

## Version 1.0.0

Implemented features:

- Main menu with Play, Instructions, and Quit buttons
- Instructions screen
- Smooth WASD and arrow-key movement
- Grid-based dungeon with rooms, corridors, walls, torches, and an exit door
- Rectangle collision with wall sliding
- Gameplay HUD with level and objective
- Pause, resume, restart, and main-menu actions
- Level-complete screen with replay support
- Mouse and keyboard menu navigation

Combat, enemies, weapons, items, power-ups, multiple levels, bosses, audio, and high scores are intentionally reserved for future releases.

## Controls

- `WASD` or Arrow Keys: Move
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