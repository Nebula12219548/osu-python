# osu!python Version Log

## v0.2.0 - 2025-06-19
**Current Bugs:**
- Tutorial does not work at all.
- Error: "File "/home/nebulagamr/Desktop/osu/0.2.0/main.py", line 1207, in <module>
    main()
    ~~~~^^
  File "/home/nebulagamr/Desktop/osu/0.2.0/main.py", line 943, in main
    SETTINGS = main_menu(screen, clock, SETTINGS) # Pass and receive updated settings
  File "/home/nebulagamr/Desktop/osu/0.2.0/main.py", line 660, in main_menu
    tutorial_screen(screen, clock)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/home/nebulagamr/Desktop/osu/0.2.0/main.py", line 460, in tutorial_screen
    run_tutorial_demo(screen, clock)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/home/nebulagamr/Desktop/osu/0.2.0/main.py", line 541, in run_tutorial_demo
    aa_circle(screen, (100, 200, 255), obj['pos'], int(CIRCLE_RADIUS * approach), 2)
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/nebulagamr/Desktop/osu/0.2.0/main.py", line 52, in aa_circle
    pygame.gfxdraw.aacircle(surface, pos[0], pos[1], radius-w, color)
    ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'float' object cannot be interpreted as an integer"
Appears on my computers every time I try to use the tutorial.
Will be fixed (hopefully) by 0.3.0!


**New Features & Improvements:**
- **Advanced Settings Menu:**
    - Added options for Music Volume (slider) and SFX Volume (slider, placeholder for full functionality).
    - Implemented an "Approach Circle Speed" setting with multiple discrete options (Slow, Normal, Fast).
    - Included a disabled "Difficulty Multiplier" slider (Work In Progress).
    - Settings are now dynamically rendered and interactable via keyboard (arrow keys, Enter) and mouse (click, slider drag).
    - Custom cursor setting is now part of the new settings menu.
- **Improved UI Elements:**
    - Buttons and sliders in the settings menu feature new visual styling with rounded corners and gradients.
- **Audio Handling Enhancements:**
    - Music volume from settings is now applied upon game start (May not work).

**Bug Fixes & Refinements:**
- Refactored `settings_menu` to accept and return the global `SETTINGS` dictionary, ensuring settings persist and are properly updated.
- Cursor visibility is now correctly toggled based on the 'custom_cursor' setting when entering/exiting settings and maps menus.
- Minor visual adjustments to various menu screens.

## v0.1.0 - Initial Release - 2025-06-18

**Features:**
- **Modern, Smooth UI:** Animated gradients, rounded buttons, and anti-aliased hit circles. No PNG images required.
- **Main Menu:** Start, Tutorial, Settings (placeholder), and About screens.
    - Smooth osu!python logo animation.
- **Map Selection:** Choose from any `.osz` (osu! or custom) map in the `maps/` folder.
    - "Back to Main Menu" button.
    - Custom glowing cursor in map selection screen.
- **Tutorial Mode:** Interactive tutorial with instructions and demonstration.
- **Gameplay:**
    - Click hit circles in order, one at a time.
    - Only one hit circle is visible at a time.
    - Approach circles indicate timing.
    - Scoring is based on timing accuracy (closer to perfect = more points).
    - Health bar increases on hit, decreases on miss (large enough for multiple misses).
    - Audio playback for `.mp3`, `.aac`, `.m4a`, `.wav`, and `.ogg` (auto-converts if needed) (does not work yet).
    - Robust audio handling and conversion for .osz files.
    - Pause menu (ESC or click), with Resume and Back to Menu options.
    - Level Cleared and Level Failed screens, with Retry and Back to Menu options (Retry restarts the map instantly).
    - Custom glowing cursor.
- **Map Format:** Supports both real osu! `.osz` files (with `.osu` inside) and simple custom `.osz` text maps.
    - Improved `.osz` file loading, including robust `.osu` and audio file identification.
    - Initial parsing for all hit object types (circles, sliders, spinners) from `.osu` files.
- **About Screen:** Credits and version info.
