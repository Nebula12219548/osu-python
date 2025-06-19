# osu!python

A Python-based rhythm game inspired by osu! (ppy), built with pygame. This project is for educational and fun purposes only.

## Features

- **Modern, Smooth UI**: Animated gradients, rounded buttons, and anti-aliased hit circles. No PNG images required.
- **Main Menu**: Start, Tutorial, Settings (placeholder), and About screens.
- **Map Selection**: Choose from any `.osz` (osu! or custom) map in the `maps/` folder.
- **Tutorial Mode**: Interactive tutorial with instructions and demonstration.
- **Gameplay**:
  - Click hit circles in order, one at a time.
  - Only one hit circle is visible at a time.
  - Approach circles indicate timing.
  - Scoring is based on timing accuracy (closer to perfect = more points).
  - Health bar increases on hit, decreases on miss (large enough for multiple misses).
  - Audio playback for `.mp3`, `.aac`, `.m4a`, `.wav`, and `.ogg` (auto-converts if needed) (also may not work as this is very early).
  - Pause menu (ESC or click), with Resume and Back to Menu options.
  - Level Cleared and Level Failed screens, with Retry and Back to Menu options (Retry restarts the map instantly).
  - Custom glowing cursor.
- **Map Format**: Supports both real osu! `.osz` files (with `.osu` inside) and simple custom `.osz` text maps.
- **About Screen**: Credits and version info.
- **Settings Menu**: Placeholder, will be functional in a future update.

## Planned for v0.2.0
- **Settings**: Adjustable game and UI options.

## How to Play
1. Run `main.py`.
2. Select a map or try the tutorial.
3. Click circles in order as the approach circle closes in.
4. Try to get the highest score by clicking with perfect timing!

## Requirements
See `requirements.txt` for dependencies.

## Legal
osu!python is not affiliated with or endorsed by ppy or the official osu! game. For educational use only.
