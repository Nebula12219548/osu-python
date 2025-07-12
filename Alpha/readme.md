# osu!python Version Log
- All versions below 1.0.0 are alpha versions. (0.1.0 ,0.2.0, 0.3.0, etc.)


## v0.6.0 - 2025-07-11

**Major UI & Graphics Revamp 2:**
- All game graphics and UI elements are now programmatically generated (no PNG images required).
- Modern osu!-inspired visuals: animated gradients, glowing/shadowed buttons, anti-aliased hit circles, custom glowing cursor.
- Main menu, settings, map selection, tutorial, and gameplay screens feature dynamic gradients, rounded corners, and smooth transitions.
- Approach circles, health bar, and feedback popups are visually enhanced and animated.
- All menus and gameplay now scale responsively to window size.
- Custom cursor and button effects throughout the UI.
- Improved visual feedback for hits, misses, and combo.
- All UI changes are documented and versioned for future reference.


## v0.5.0 - 2025-06-26
 
**New Features & Improvements:**
- **Dynamic Holiday Greetings:** Added a system to display animated greetings for various holidays (Canada Day, Halloween, Christmas, New Year's) on the main menu.
- **Enhanced Canada Day Feature:** The Canadian flag now includes a programmatically drawn maple leaf and features a subtle wave animation.
- **UI Layout Fix:** Repositioned holiday greetings to the top of the screen to prevent overlap with main menu buttons.

## v0.4.0 - 2025-06-22

**New Features & Improvements:**
- **Enhanced UI and Sound:** The entire user interface has been updated to more closely resemble the aesthetic of the actual osu! game, without using any PNG images. This includes:
    - Refined color palette with osu!-inspired blues, whites, and grays.
    - Programmatically generated hitsounds for hit circles (no external audio files needed) (Very Basic)
    - Dynamic health bar that changes color from green to yellow to red based on health percentage.
    - Improved button styling and hover/selection effects across all menus.
- **Main Menu Logo Animation:** Re-introduced and enhanced the pulsing and glowing animation for the "osu!python" logo on the main menu.
- **UI Layout Adjustments:** Corrected the positioning of main menu buttons to prevent overlap with the animated logo, ensuring proper spacing and visual hierarchy.


## v0.3.0 - 2025-06-19

**New Features & Improvements:**
- **Revamped UI and all older features:** The user interface and all functionalities present in previous versions have undergone a significant revamp and received comprehensive updates.
- **Tutorial Fixes:** The tutorial has been fixed and improved for a better user experience.

**Bug Fixes & Refinements:**
- Refactored `settings_menu` to accept and return the global `SETTINGS` dictionary, ensuring settings persist and are properly updated.
- Cursor visibility is now correctly toggled based on the 'custom_cursor' setting when entering/exiting settings and maps menus.
- Minor visual adjustments to various menu screens.

## v0.2.0 - 2025-06-19

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
- Tutorial currently does not work at all.

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