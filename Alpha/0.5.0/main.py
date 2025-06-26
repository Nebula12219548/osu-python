import pygame
import sys
import math
import random
import os
import datetime
import tempfile
import numpy as np
import shutil
import zipfile
import pygame.gfxdraw

# Global settings dictionary (to be updated and passed around)
SETTINGS = {
    'custom_cursor': True,
    'current_width': 800,  # Mutable global for current window width
    'current_height': 600, # Mutable global for current window height
    'music_volume': 0.5,   # New: Music volume (0.0 to 1.0)
    'sfx_volume': 0.7,     # New: SFX volume (0.0 to 1.0)
    'difficulty_multiplier': 1.0, # Placeholder for future difficulty
    'approach_circle_speed': 'Normal', # New: Example dropdown
}

# Initial window dimensions (can be changed by resizing)
INITIAL_WIDTH, INITIAL_HEIGHT = 800, 600
VERSION = "0.5.0"

# Constants that do not change with window size
FPS = 60
CIRCLE_RADIUS = 50
CIRCLE_OUTLINE = 6
# Define osu! inspired colors
OSU_BLUE = (0, 180, 255)
OSU_DARK_BLUE = (0, 120, 200)
OSU_LIGHT_BLUE = (100, 200, 255)
OSU_WHITE = (255, 255, 255)
OSU_YELLOW = (255, 255, 0)
OSU_RED = (255, 60, 60)
OSU_GREEN = (0, 255, 100)
OSU_DARK_GREEN = (0, 150, 70)
OSU_DARK_GREY = (30, 30, 30)
OSU_MEDIUM_GREY = (60, 60, 60)
OSU_LIGHT_GREY = (180, 180, 180)

CIRCLE_COLOR = OSU_BLUE
CIRCLE_OUTLINE_COLOR = OSU_WHITE
NUMBER_COLOR = OSU_WHITE
BACKGROUND_COLOR = OSU_DARK_GREY

# Global animation state dictionary for holiday elements
_ANIMATION_STATE = {
    'current_holiday_type': None, # Tracks which holiday is currently active to manage transitions
    'firework_particles': [],
    'firework_active': False,
    'firework_start_time': 0,
    'pumpkin_glow_phase': 0.0,
    'christmas_lights': [],
}

# HitCircle class
def draw_hit_circle(surface, pos, number, approach=1.0):
    # Draw approach circle (anti-aliased)
    approach_radius = int(CIRCLE_RADIUS * approach)
    if approach > 1.05:
        aa_circle(surface, (100, 200, 255), (int(pos[0]), int(pos[1])), approach_radius, 2)
    # Draw main circle (anti-aliased)
    aa_filled_circle(surface, CIRCLE_COLOR, (int(pos[0]), int(pos[1])), CIRCLE_RADIUS)
    aa_circle(surface, CIRCLE_OUTLINE_COLOR, (int(pos[0]), int(pos[1])), CIRCLE_RADIUS, CIRCLE_OUTLINE)
    # Draw number
    font = pygame.font.SysFont('Arial', 36, bold=True)
    text = font.render(str(number), True, NUMBER_COLOR)
    text_rect = text.get_rect(center=pos)
    surface.blit(text, text_rect)

def aa_circle(surface, color, pos, radius, width=1):
    # Draw anti-aliased circle using pygame.gfxdraw
    for w in range(width):
        pygame.gfxdraw.aacircle(surface, pos[0], pos[1], radius-w, color)

def aa_filled_circle(surface, color, pos, radius):
    pygame.gfxdraw.filled_circle(surface, pos[0], pos[1], radius, color)
    pygame.gfxdraw.aacircle(surface, pos[0], pos[1], radius, color)

class HitObject:
    def __init__(self, pos, time, number):
        self.pos = pos
        self.time = time
        self.number = number
        self.hit = False
        self.disappeared = False
        self.approach_time = 1200  # ms
        self.hit_window = 300      # ms
        self.lifetime = self.approach_time + self.hit_window

    def draw(self, surface, now):
        t = self.time - now
        if self.disappeared or self.hit:
            return
        approach = max(1.0, min(2.5, t / self.approach_time + 1))
        if t < self.approach_time:
            draw_hit_circle(surface, self.pos, self.number, approach)

    def update(self, now):
        if not self.hit and not self.disappeared:
            if now > self.time + self.hit_window:
                self.disappeared = True

    def check_hit(self, click_pos, now):
        if self.hit or self.disappeared:
            return False
        dist_sq = (click_pos[0] - self.pos[0])**2 + (click_pos[1] - self.pos[1])**2
        if dist_sq <= CIRCLE_RADIUS**2:
            time_diff = abs(now - self.time)
            if time_diff <= self.hit_window:
                self.hit = True
                return True
        return False

def generate_hitobjects(count):
    hitobjects = []
    t = 1000
    for i in range(count):
        x = random.randint(CIRCLE_RADIUS + 10, SETTINGS['current_width'] - CIRCLE_RADIUS - 10)
        y = random.randint(CIRCLE_RADIUS + 10, SETTINGS['current_height'] - CIRCLE_RADIUS - 10)
        hitobjects.append(HitObject((x, y), t, i+1))
        t += 800
    return hitobjects

def load_map(filepath):
    hitobjects = []
    map_name = os.path.splitext(os.path.basename(filepath))[0]
    lines = []
    if filepath.endswith('.osz'):
        try:
            with zipfile.ZipFile(filepath, 'r') as z:
                osu_files = [f for f in z.namelist() if f.endswith('.osu')]
                if osu_files:
                    with z.open(osu_files[0]) as f:
                        lines = [l.decode('utf-8').strip() for l in f.readlines()]
        except zipfile.BadZipFile:
            # Not a real zip, treat as plain text
            with open(filepath, 'r') as f:
                lines = [line.strip() for line in f]
    else:
        with open(filepath, 'r') as f:
            lines = [line.strip() for line in f]
    # Parse .osu or .osz (only circles supported)
    in_hitobjects = False
    for line in lines:
        if not line or line.startswith('#'):
            continue
        if line.startswith('[HitObjects]'):
            in_hitobjects = True
            continue
        if in_hitobjects:
            parts = line.split(',')
            if len(parts) >= 3:
                x, y, t = int(parts[0]), int(parts[1]), int(parts[2])
                hitobjects.append(HitObject((x, y), t, len(hitobjects)+1))
    if not hitobjects:  # fallback for custom format
        for line in lines:
            if not line or line.startswith('#'):
                continue
            parts = line.split(',')
            if parts[0] == 'circle':
                x, y, t = int(parts[1]), int(parts[2]), int(parts[3])
                hitobjects.append(HitObject((x, y), t, len(hitobjects)+1))
    return hitobjects, map_name

def draw_gradient_rect(surface, rect, color1, color2, vertical=True):
    x, y, w, h = rect
    for i in range(h if vertical else w):
        ratio = i / (h if vertical else w)
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        if vertical:
            pygame.draw.line(surface, (r, g, b), (x, y + i), (x + w, y + i))
        else:
            pygame.draw.line(surface, (r, g, b), (x + i, y), (x + i, y + h))

def draw_rounded_gradient(surface, rect, color1, color2, radius=24, vertical=True):
    x, y, w, h = rect
    temp = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h if vertical else w):
        ratio = i / (h if vertical else w)
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        a = 255
        if vertical:
            pygame.draw.line(temp, (r, g, b, a), (0, i), (w, i))
        else:
            pygame.draw.line(temp, (r, g, b, a), (i, 0), (i, h))
    # Draw rounded mask
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255,255,255,255), (0,0,w,h), border_radius=radius)
    temp.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(temp, (x, y))

def generate_hitsound(frequency=1000, duration=0.1, sample_rate=44100):
    """Generates a simple percussive hitsound as a pygame.Sound object."""
    num_samples = int(duration * sample_rate)
    t = np.linspace(0., duration, num_samples, endpoint=False)
    
    # Generate a sine wave for the sound
    amplitude = np.iinfo(np.int16).max * 0.5  # Use 50% of max volume
    data = amplitude * np.sin(2. * np.pi * frequency * t)
    
    # Apply a fast exponential decay envelope to make it sound percussive
    decay = np.exp(-t * 30)  # The multiplier (30) controls decay speed
    data *= decay
    
    # Ensure the data is in 16-bit format for pygame
    # The sound needs to be stereo (2 channels) for sndarray
    sound_array = np.column_stack((data, data)).astype(np.int16)
    
    # Create the pygame sound object from the numpy array
    sound = pygame.sndarray.make_sound(sound_array)
    return sound

def draw_health_bar_fill(surface, rect, health_percent, radius=16):
    # Interpolate color from green (1.0) to yellow (0.5) to red (0.0)
    if health_percent > 0.5:
        # Green to Yellow
        ratio = (health_percent - 0.5) / 0.5 # 0.0 to 1.0
        r = int(OSU_GREEN[0] * (1 - ratio) + OSU_YELLOW[0] * ratio)
        g = int(OSU_GREEN[1] * (1 - ratio) + OSU_YELLOW[1] * ratio)
        b = int(OSU_GREEN[2] * (1 - ratio) + OSU_YELLOW[2] * ratio)
    else:
        # Yellow to Red
        ratio = health_percent / 0.5 # 0.0 to 1.0
        r = int(OSU_YELLOW[0] * ratio + OSU_RED[0] * (1 - ratio))
        g = int(OSU_YELLOW[1] * ratio + OSU_RED[1] * (1 - ratio))
        b = int(OSU_YELLOW[2] * ratio + OSU_RED[2] * (1 - ratio))
    
    color1 = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
    color2 = (max(0, min(255, int(r*0.7))), max(0, min(255, int(g*0.7))), max(0, min(255, int(b*0.7)))) # Darker version for gradient

    draw_rounded_gradient(surface, rect, color1, color2, radius=radius)

def draw_holiday_elements(screen, font_medium):
    """Checks for holidays and draws a greeting and icon if applicable."""
    global _ANIMATION_STATE # Declare intent to modify the global dictionary

    today = datetime.date.today()
    month = today.month
    day = today.day
    current_width, current_height = screen.get_size()
    current_time_ms = pygame.time.get_ticks()

    greeting = None
    color = None
    icon_type = None

    # --- Define Holidays ---
    # Canada Day
    if month == 7 and day == 1:
        greeting, color, icon_type = "Happy Canada Day!", OSU_RED, "canada_flag"
    # Halloween
    elif month == 10 and day == 31:
        greeting, color, icon_type = "Happy Halloween!", (255, 165, 0), "halloween_pumpkin" # Orange
    # Christmas
    elif month == 12 and day == 25:
        greeting, color, icon_type = "Merry Christmas!", OSU_GREEN, "christmas_tree"
    # New Year's Day
    elif month == 1 and day == 1:
        greeting, color, icon_type = "Happy New Year!", OSU_YELLOW, "new_year_firework"

    # Manage animation state transitions
    if icon_type != _ANIMATION_STATE['current_holiday_type']:
        # Reset all animation states if holiday changes or no holiday is active
        _ANIMATION_STATE['firework_particles'] = []
        _ANIMATION_STATE['firework_active'] = False
        _ANIMATION_STATE['firework_start_time'] = 0
        _ANIMATION_STATE['pumpkin_glow_phase'] = 0.0
        _ANIMATION_STATE['christmas_lights'] = []
        _ANIMATION_STATE['current_holiday_type'] = icon_type # Update current active holiday

    # If a holiday is found, draw its elements
    if greeting:
        # --- Positioning ---
        # Move elements to the top of the screen to avoid button overlap
        greeting_y = 40
        icon_base_y = 70 # Base Y for the top of the icon area

        # Draw Text
        holiday_text = font_medium.render(greeting, True, color)
        holiday_rect = holiday_text.get_rect(center=(current_width // 2, greeting_y))
        screen.blit(holiday_text, holiday_rect)

        # Draw Icon
        if icon_type == "canada_flag":
            flag_height = 40
            flag_width = 80
            flag_x_start = current_width // 2 - flag_width // 2
            
            # Wave animation parameters
            wave_amplitude = 2.0
            wave_frequency = 0.1
            wave_speed = 250.0

            # Simplified maple leaf polygon (normalized coordinates)
            maple_leaf_poly = [
                (0.0, -0.9), (-0.07, -0.5), (-0.35, -0.45), (-0.25, -0.2),
                (-0.5, -0.15), (-0.3, 0.05), (-0.35, 0.35), (-0.1, 0.2),
                (0.0, 0.6), (0.1, 0.2), (0.35, 0.35), (0.3, 0.05),
                (0.5, -0.15), (0.25, -0.2), (0.35, -0.45), (0.07, -0.5)
            ]
            leaf_scale = flag_height * 0.55 # Scale leaf to be 55% of flag height

            # Draw flag with wave by drawing vertical lines
            for x_offset in range(flag_width):
                y_offset = math.sin(current_time_ms / wave_speed + x_offset * wave_frequency) * wave_amplitude
                
                col_x = flag_x_start + x_offset
                # Determine color based on x position (1:2:1 ratio)
                if x_offset < flag_width // 4 or x_offset >= flag_width * 3 // 4:
                    flag_color = OSU_RED
                else:
                    flag_color = OSU_WHITE
                
                pygame.draw.line(screen, flag_color, (col_x, icon_base_y + y_offset), (col_x, icon_base_y + flag_height + y_offset))

            # Draw maple leaf on top of the waving flag
            leaf_center_x = current_width // 2
            leaf_center_y = icon_base_y + flag_height // 2
            
            # The leaf should also wave with the flag's center
            leaf_wave_offset = math.sin(current_time_ms / wave_speed + (flag_width // 2) * wave_frequency) * wave_amplitude
            
            final_leaf_points = [(leaf_center_x + p[0] * leaf_scale, leaf_center_y + p[1] * leaf_scale + leaf_wave_offset) for p in maple_leaf_poly]
            
            pygame.draw.polygon(screen, OSU_RED, final_leaf_points)
            pygame.gfxdraw.aapolygon(screen, final_leaf_points, OSU_RED)
        
        elif icon_type == "halloween_pumpkin":
            icon_x = current_width // 2
            icon_y = icon_base_y + 20 # Center of pumpkin
            pygame.draw.circle(screen, (255, 165, 0), (icon_x, icon_y), 20) # Pumpkin body
            pygame.draw.rect(screen, OSU_DARK_GREEN, (icon_x - 5, icon_y - 25, 10, 10)) # Stem

            # Pulsating glow for eyes and mouth
            _ANIMATION_STATE['pumpkin_glow_phase'] = (current_time_ms / 150.0) % (2 * math.pi)
            glow_intensity = (math.sin(_ANIMATION_STATE['pumpkin_glow_phase']) * 0.5 + 0.5)
            
            eye_color_base = (255, 200, 0)
            eye_color = (
                min(255, int(eye_color_base[0] + (255 - eye_color_base[0]) * glow_intensity * 0.5)),
                min(255, int(eye_color_base[1] + (255 - eye_color_base[1]) * glow_intensity * 0.5)),
                min(255, int(eye_color_base[2] + (255 - eye_color_base[2]) * glow_intensity * 0.5))
            )

            # Eyes (triangles) and mouth (polygon)
            pygame.draw.polygon(screen, eye_color, [(icon_x - 10, icon_y - 5), (icon_x - 5, icon_y - 15), (icon_x, icon_y - 5)])
            pygame.draw.polygon(screen, eye_color, [(icon_x + 10, icon_y - 5), (icon_x + 5, icon_y - 15), (icon_x, icon_y - 5)])
            pygame.draw.polygon(screen, eye_color, [(icon_x - 10, icon_y + 10), (icon_x - 5, icon_y + 15), (icon_x, icon_y + 10), (icon_x + 5, icon_y + 15), (icon_x + 10, icon_y + 10)])

        elif icon_type == "christmas_tree":
            icon_x = current_width // 2
            icon_y = icon_base_y # Top of the tree
            pygame.draw.polygon(screen, OSU_DARK_GREEN, [(icon_x, icon_y), (icon_x - 25, icon_y + 25), (icon_x + 25, icon_y + 25)])
            pygame.draw.polygon(screen, OSU_GREEN, [(icon_x, icon_y + 15), (icon_x - 20, icon_y + 40), (icon_x + 20, icon_y + 40)])
            pygame.draw.rect(screen, (139, 69, 19), (icon_x - 5, icon_y + 40, 10, 10)) # Brown color

            # Initialize lights if not already
            if not _ANIMATION_STATE['christmas_lights']:
                for _ in range(8): # 8 lights
                    light_x = random.randint(icon_x - 20, icon_x + 20)
                    light_y = random.randint(icon_y + 5, icon_y + 35)
                    blink_offset = random.uniform(0, 2 * math.pi) # Random phase for blinking
                    _ANIMATION_STATE['christmas_lights'].append(((light_x, light_y), blink_offset))
            
            # Draw blinking lights
            for pos, blink_offset in _ANIMATION_STATE['christmas_lights']:
                blink_phase = (current_time_ms / 300.0 + blink_offset) % (2 * math.pi)
                if math.sin(blink_phase) > 0: # Simple on/off blinking
                    pygame.draw.circle(screen, OSU_YELLOW, pos, 3)

        elif icon_type == "new_year_firework":
            icon_x = current_width // 2
            icon_y = icon_base_y + 20 # Center of explosion

            # Trigger firework animation once
            if not _ANIMATION_STATE['firework_active']:
                _ANIMATION_STATE['firework_active'] = True
                _ANIMATION_STATE['firework_start_time'] = current_time_ms
                _ANIMATION_STATE['firework_particles'] = []
                for _ in range(30): # 30 particles
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(0.5, 2.0)
                    # Store [x, y, angle, speed, start_alpha]
                    _ANIMATION_STATE['firework_particles'].append([icon_x, icon_y, angle, speed, 255])
            
            # Update and draw firework particles
            animation_duration = 1200
            elapsed = current_time_ms - _ANIMATION_STATE['firework_start_time']

            if elapsed < animation_duration:
                for p in _ANIMATION_STATE['firework_particles']:
                    p[0] += p[3] * math.cos(p[2]) # Update x
                    p[1] += p[3] * math.sin(p[2]) # Update y
                    p[4] = max(0, int(255 * (1 - elapsed / animation_duration))) # Fade out

                    # Create a temporary surface for the particle to handle alpha
                    particle_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
                    pygame.draw.circle(particle_surf, OSU_YELLOW + (p[4],), (2, 2), 2)
                    screen.blit(particle_surf, (int(p[0]) - 2, int(p[1]) - 2))
            else:
                # Reset for next time
                _ANIMATION_STATE['firework_active'] = False

def about_screen(screen, clock):
    font_big = pygame.font.SysFont('Arial', 54, bold=True)
    font_small = pygame.font.SysFont('Arial', 32)
    version_font = pygame.font.SysFont('Arial', 24)
    running = True
    while running:
        current_width, current_height = screen.get_size()
        draw_gradient_rect(screen, (0, 0, current_width, current_height), OSU_DARK_GREY, (10, 10, 40), vertical=True) # Adjusted start color
        title = font_big.render('About osu!python', True, OSU_BLUE)
        title_rect = title.get_rect(center=(current_width//2, current_height//2 - 100))
        screen.blit(title, title_rect)
        lines = [
            'osu!python is a osu! clone by Nebula12219548',
            'Inspired by osu! (ppy)',
            'For educational and fun purposes only.',
            f'Version: v{VERSION}',
            'GitHub: https://github.com/Nebula12219548/osu-python',
            '',
            'Press any key or click to return.'
        ]
        for i, line in enumerate(lines):
            text = font_small.render(line, True, OSU_WHITE)
            rect = text.get_rect(center=(current_width//2, current_height//2 + i*40 - 20))
            screen.blit(text, rect)
        version_text = version_font.render(f'v{VERSION}', True, OSU_LIGHT_GREY)
        version_rect = version_text.get_rect(bottomright=(current_width-10, current_height-10))
        screen.blit(version_text, version_rect)

        # Custom cursor
        if SETTINGS['custom_cursor']:
            mx, my = pygame.mouse.get_pos()
            for r in range(20, 8, -2): # Outer glow
                pygame.draw.circle(screen, OSU_BLUE + (30,), (mx, my), r, 2)
            pygame.draw.circle(screen, OSU_WHITE, (mx, my), 16, 2) # Inner circle

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                SETTINGS['current_width'], SETTINGS['current_height'] = event.w, event.h
                screen = pygame.display.set_mode((SETTINGS['current_width'], SETTINGS['current_height']), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                running = False
        clock.tick(FPS)

def settings_menu(screen, clock, settings):
    font_big = pygame.font.SysFont('Arial', 54, bold=True)
    font_medium = pygame.font.SysFont('Arial', 36)
    font_small = pygame.font.SysFont('Arial', 32)
    version_font = pygame.font.SysFont('Arial', 24)
    running = True
    selected = 0
    
    # Define options for the settings menu
    options = [
        {'label': 'Custom Cursor', 'setting': 'custom_cursor', 'type': 'toggle'},
        {'label': 'Music Volume', 'setting': 'music_volume', 'type': 'slider', 'min': 0.0, 'max': 1.0, 'step': 0.05},
        {'label': 'SFX Volume', 'setting': 'sfx_volume', 'type': 'slider', 'min': 0.0, 'max': 1.0, 'step': 0.05},
        {'label': 'Approach Circle Speed', 'setting': 'approach_circle_speed', 'type': 'dropdown', 'values': ['Slow', 'Normal', 'Fast']},
        {'label': 'Difficulty Multiplier (WIP)', 'setting': 'difficulty_multiplier', 'type': 'slider', 'min': 0.5, 'max': 2.0, 'step': 0.1, 'disabled': True}, # Example disabled option
        {'label': 'Back to Main Menu', 'type': 'action'}
    ]

    while running:
        current_width, current_height = screen.get_size()
        draw_gradient_rect(screen, (0, 0, current_width, current_height), OSU_DARK_GREY, (10, 10, 40), vertical=True) # Adjusted start color
        title = font_big.render('Settings', True, OSU_BLUE)
        title_rect = title.get_rect(center=(current_width//2, 80))
        screen.blit(title, title_rect)

        for i, opt in enumerate(options):
            is_selected = (i == selected)
            color = (255,255,0) if is_selected else (255,255,255)
            btn_c1 = (0, 180, 255) if is_selected else (60,60,60)
            btn_c2 = (0, 120, 200) if is_selected else (40,40,40)

            display_text = opt['label']
            if opt['type'] == 'toggle':
                display_text += f": {'On' if settings[opt['setting']] else 'Off'}"
            elif opt['type'] == 'slider':
                display_text += f": {settings[opt['setting']]:.2f}"
            elif opt['type'] == 'dropdown':
                display_text += f": {settings[opt['setting']]}"
            if opt.get('disabled', False):
                color = (150, 150, 150)
                btn_c1 = (30, 30, 30)
                btn_c2 = (20, 20, 20)

            text_surface = font_medium.render(display_text, True, color)
            rect = text_surface.get_rect(center=(current_width//2, 180 + i*60))

            draw_rounded_gradient(screen, rect.inflate(40, 10), btn_c1, btn_c2, radius=12, vertical=False)
            pygame.draw.rect(screen, OSU_WHITE + (180,), rect.inflate(40, 10), 2, border_radius=12) # White border
            screen.blit(text_surface, rect)

            # Draw slider bar if it's a slider type
            if opt['type'] == 'slider' and not opt.get('disabled', False):
                slider_width = 200
                slider_height = 10
                slider_x = current_width // 2 + rect.width // 2 + 30 # Adjust position
                slider_y = rect.centery - slider_height // 2

                slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
                pygame.draw.rect(screen, OSU_MEDIUM_GREY, slider_rect, border_radius=5) # Slider track

                value_range = opt['max'] - opt['min']
                if value_range > 0:
                    handle_pos_x = slider_x + slider_width * ((settings[opt['setting']] - opt['min']) / value_range)
                    pygame.draw.circle(screen, OSU_WHITE, (int(handle_pos_x), rect.centery), 10) # Handle outline
                    pygame.draw.circle(screen, OSU_BLUE, (int(handle_pos_x), rect.centery), 8) # Handle fill


        version_text = version_font.render(f'v{VERSION}', True, (180, 180, 180))
        version_rect = version_text.get_rect(bottomright=(current_width-10, current_height-10))
        screen.blit(version_text, version_rect)

        # Custom cursor
        if SETTINGS['custom_cursor']:
            mx, my = pygame.mouse.get_pos()
            for r in range(20, 8, -2): # Outer glow
                pygame.draw.circle(screen, OSU_BLUE + (30,), (mx, my), r, 2)
            pygame.draw.circle(screen, OSU_WHITE, (mx, my), 16, 2) # Inner circle

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                SETTINGS['current_width'], SETTINGS['current_height'] = event.w, event.h
                screen = pygame.display.set_mode((SETTINGS['current_width'], SETTINGS['current_height']), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    opt = options[selected]
                    if opt.get('disabled', False): # Cannot activate disabled options
                        continue
                    if opt['type'] == 'toggle':
                        settings[opt['setting']] = not settings[opt['setting']]
                        pygame.mouse.set_visible(not settings['custom_cursor']) # Update cursor visibility immediately
                    elif opt['type'] == 'action' and opt['label'] == 'Back to Main Menu':
                        running = False
                    elif opt['type'] == 'dropdown':
                        current_value_index = opt['values'].index(settings[opt['setting']])
                        next_value_index = (current_value_index + 1) % len(opt['values'])
                        settings[opt['setting']] = opt['values'][next_value_index]
                elif event.key == pygame.K_LEFT:
                    opt = options[selected]
                    if opt.get('disabled', False):
                        continue
                    if opt['type'] == 'slider':
                        current_value = settings[opt['setting']]
                        new_value = max(opt['min'], current_value - opt['step'])
                        settings[opt['setting']] = round(new_value, 2) # Round to avoid float precision issues
                        if opt['setting'] == 'music_volume':
                            pygame.mixer.music.set_volume(settings['music_volume'])
                        # Add SFX volume adjustment here if you have specific SFX playing
                    elif opt['type'] == 'dropdown':
                        current_value_index = opt['values'].index(settings[opt['setting']])
                        prev_value_index = (current_value_index - 1 + len(opt['values'])) % len(opt['values'])
                        settings[opt['setting']] = opt['values'][prev_value_index]
                elif event.key == pygame.K_RIGHT:
                    opt = options[selected]
                    if opt.get('disabled', False):
                        continue
                    if opt['type'] == 'slider':
                        current_value = settings[opt['setting']]
                        new_value = min(opt['max'], current_value + opt['step'])
                        settings[opt['setting']] = round(new_value, 2)
                        if opt['setting'] == 'music_volume':
                            pygame.mixer.music.set_volume(settings['music_volume'])
                        # Add SFX volume adjustment here if you have specific SFX playing
                    elif opt['type'] == 'dropdown':
                        current_value_index = opt['values'].index(settings[opt['setting']])
                        next_value_index = (current_value_index + 1) % len(opt['values'])
                        settings[opt['setting']] = opt['values'][next_value_index]

            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, opt in enumerate(options):
                    display_text = opt['label']
                    if opt['type'] == 'toggle':
                        display_text += f": {'On' if settings[opt['setting']] else 'Off'}"
                    elif opt['type'] == 'slider':
                        display_text += f": {settings[opt['setting']]:.2f}"
                    elif opt['type'] == 'dropdown':
                        display_text += f": {settings[opt['setting']]}"

                    text_surface = font_medium.render(display_text, True, (255,255,255))
                    rect = text_surface.get_rect(center=(current_width//2, 180 + i*60))
                    
                    if opt.get('disabled', False):
                        continue

                    if rect.inflate(40, 10).collidepoint(event.pos):
                        if opt['type'] == 'toggle':
                            settings[opt['setting']] = not settings[opt['setting']]
                            pygame.mouse.set_visible(not settings['custom_cursor']) # Update cursor visibility immediately
                        elif opt['type'] == 'action' and opt['label'] == 'Back to Main Menu':
                            running = False
                        elif opt['type'] == 'dropdown':
                            current_value_index = opt['values'].index(settings[opt['setting']])
                            next_value_index = (current_value_index + 1) % len(opt['values'])
                            settings[opt['setting']] = opt['values'][next_value_index]
                    
                    # Handle slider click/drag
                    if opt['type'] == 'slider':
                        slider_width = 200
                        slider_height = 10
                        slider_x = current_width // 2 + rect.width // 2 + 30
                        slider_y = rect.centery - slider_height // 2
                        slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)

                        if slider_rect.collidepoint(event.pos):
                            normalized_x = (event.pos[0] - slider_x) / slider_width
                            value_range = opt['max'] - opt['min']
                            new_value = opt['min'] + normalized_x * value_range
                            new_value = round(max(opt['min'], min(opt['max'], new_value)), 2)
                            settings[opt['setting']] = new_value
                            if opt['setting'] == 'music_volume':
                                pygame.mixer.music.set_volume(settings['music_volume'])
                            # Add SFX volume adjustment here if you have specific SFX playing


        clock.tick(FPS)
    return settings # Return updated settings

def tutorial_screen(screen, clock, hit_sound):
    font_big = pygame.font.SysFont('Arial', 54, bold=True)
    font_small = pygame.font.SysFont('Arial', 32)
    version_font = pygame.font.SysFont('Arial', 24)
    instructions = [
        'Welcome to osu!python Tutorial!',
        '',
        '1. Click the circles as they appear.',
        '2. You must click them in order.',
        '3. Try to click when the approach circle closes in.',
        '4. Missing circles will reduce your health.',
        '',
        'Press SPACE to start the demonstration.'
    ]
    running = True
    while running:
        current_width, current_height = screen.get_size()
        draw_gradient_rect(screen, (0, 0, current_width, current_height), OSU_DARK_GREY, (10, 10, 40), vertical=True) # Adjusted start color
        title = font_big.render('Tutorial', True, OSU_BLUE)
        title_rect = title.get_rect(center=(current_width//2, 120))
        screen.blit(title, title_rect)
        for i, line in enumerate(instructions):
            text = font_small.render(line, True, (255,255,255))
            rect = text.get_rect(center=(current_width//2, 220 + i*40))
            screen.blit(text, rect)
        version_text = version_font.render(f'v{VERSION}', True, (180, 180, 180))
        version_rect = version_text.get_rect(bottomright=(current_width-10, current_height-10))
        screen.blit(version_text, version_rect)

        # Custom cursor
        if SETTINGS['custom_cursor']:
            mx, my = pygame.mouse.get_pos()
            for r in range(20, 8, -2): # Outer glow
                pygame.draw.circle(screen, OSU_BLUE + (30,), (mx, my), r, 2)
            pygame.draw.circle(screen, OSU_WHITE, (mx, my), 16, 2) # Inner circle

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                SETTINGS['current_width'], SETTINGS['current_height'] = event.w, event.h
                screen = pygame.display.set_mode((SETTINGS['current_width'], SETTINGS['current_height']), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                running = False
        clock.tick(FPS)

    # Run demonstration
    run_tutorial_demo(screen, clock, hit_sound)

def run_tutorial_demo(screen, clock, hit_sound):
    import time
    font = pygame.font.SysFont('Arial', 32)
    # Hardcoded demo hitobjects (positions adapted for resizing)
    demo_hitobjects = [
        {'pos': (SETTINGS['current_width'] * 0.5, SETTINGS['current_height'] * 0.5), 'time': 1000},
        {'pos': (SETTINGS['current_width'] * 0.75, SETTINGS['current_height'] * 0.5), 'time': 2500},
        {'pos': (SETTINGS['current_width'] * 0.25, SETTINGS['current_height'] * 0.5), 'time': 4000},
        {'pos': (SETTINGS['current_width'] * 0.5, SETTINGS['current_height'] * 0.16), 'time': 5500},
        {'pos': (SETTINGS['current_width'] * 0.5, SETTINGS['current_height'] * 0.83), 'time': 7000},
    ]
    approach_time = 1200
    hit_window = 300
    health = 100
    max_health = 100
    score = 0
    start_time = pygame.time.get_ticks()
    current = 0
    clicked = [False]*len(demo_hitobjects)
    running = True
    while running:
        now = pygame.time.get_ticks() - start_time
        current_width, current_height = screen.get_size()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                SETTINGS['current_width'], SETTINGS['current_height'] = event.w, event.h
                screen = pygame.display.set_mode((SETTINGS['current_width'], SETTINGS['current_height']), pygame.RESIZABLE)
                # Re-calculate demo hitobjects positions based on new size
                demo_hitobjects = [
                    {'pos': (SETTINGS['current_width'] * 0.5, SETTINGS['current_height'] * 0.5), 'time': 1000},
                    {'pos': (SETTINGS['current_width'] * 0.75, SETTINGS['current_height'] * 0.5), 'time': 2500},
                    {'pos': (SETTINGS['current_width'] * 0.25, SETTINGS['current_height'] * 0.5), 'time': 4000},
                    {'pos': (SETTINGS['current_width'] * 0.5, SETTINGS['current_height'] * 0.16), 'time': 5500},
                    {'pos': (SETTINGS['current_width'] * 0.5, SETTINGS['current_height'] * 0.83), 'time': 7000},
                ]
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if current < len(demo_hitobjects):
                    obj = demo_hitobjects[current]
                    t = abs(now - obj['time'])
                    dx = event.pos[0] - obj['pos'][0]
                    dy = event.pos[1] - obj['pos'][1]
                    if t < hit_window and (dx*dx + dy*dy) < CIRCLE_RADIUS*CIRCLE_RADIUS:
                        clicked[current] = True
                        score += 300
                        health = min(health + 20, max_health)
                        hit_sound.set_volume(SETTINGS['sfx_volume'])
                        hit_sound.play()
                        current += 1
        
        # Missed
        if current < len(demo_hitobjects):
            obj = demo_hitobjects[current]
            if now > obj['time'] + hit_window and not clicked[current]:
                health = max(health - 30, 0)
                current += 1

        draw_gradient_rect(screen, (0, 0, current_width, current_height), OSU_DARK_GREY, (10, 10, 40), vertical=True) # Adjusted start color

        # Health bar
        health_bar_width = int(current_width * 0.5)
        health_bar_height = 32
        health_bar_x = current_width // 2 - health_bar_width // 2
        health_bar_y = 20
        pygame.draw.rect(screen, (60,60,60), (health_bar_x, health_bar_y, health_bar_width, health_bar_height), border_radius=16)
        # Health bar fill with gradient
        health_fill_width = int(health_bar_width * health / max_health) # Health bar background
        draw_health_bar_fill(screen, (health_bar_x, health_bar_y, health_fill_width, health_bar_height), health / max_health, radius=16)
        pygame.draw.rect(screen, (255,255,255), (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2, border_radius=16)
        health_text = font.render(f'Health: {health}', True, (255,255,255))
        health_text_rect = health_text.get_rect(center=(current_width//2, health_bar_y + health_bar_height//2))
        screen.blit(health_text, health_text_rect)

        # Score display
        score_text = font.render(f'Score: {score}', True, (255,255,255))
        score_text_rect = score_text.get_rect(topleft=(20, 20))
        screen.blit(score_text, score_text_rect)

        # Draw hitobjects
        for i, obj in enumerate(demo_hitobjects):
            if not clicked[i]:
                # Calculate approach circle scale based on time
                t = obj['time'] - now
                if t < approach_time and t > -hit_window:
                    approach = max(1.0, min(2.5, t / approach_time + 1))
                    draw_hit_circle(screen, obj['pos'], i+1, approach)
                elif t <= -hit_window:
                    # Mark as disappeared if missed and not clicked
                    pass # Handled by the 'Missed' section above for single pass

        # Custom cursor
        if SETTINGS['custom_cursor']:
            mx, my = pygame.mouse.get_pos()
            for r in range(20, 8, -2): # Outer glow
                pygame.draw.circle(screen, OSU_BLUE + (30,), (mx, my), r, 2)
            pygame.draw.circle(screen, OSU_WHITE, (mx, my), 16, 2) # Inner circle

        pygame.display.flip()
        clock.tick(FPS)

        if current >= len(demo_hitobjects) or health <= 0:
            running = False
            # Short delay before returning
            pygame.time.wait(1000)

    # After demo, return to tutorial screen or main menu
    return # Goes back to tutorial_screen which then returns to main_menu

def maps_menu(screen, clock):
    font_big = pygame.font.SysFont('Arial', 54, bold=True)
    font_medium = pygame.font.SysFont('Arial', 36)
    version_font = pygame.font.SysFont('Arial', 24)

    maps_dir = os.path.join(os.path.dirname(__file__), 'maps')
    # Ensure the 'maps' directory exists
    os.makedirs(maps_dir, exist_ok=True)

    map_files = []
    for root, _, files in os.walk(maps_dir):
        for file in files:
            if file.endswith('.osu') or file.endswith('.osz') or file.endswith('.txt'):
                map_files.append(os.path.join(root, file))

    options = [{'label': os.path.splitext(os.path.basename(f))[0], 'path': f} for f in map_files]
    options.append({'label': 'Back to Main Menu', 'path': None})

    selected = 0
    running = True

    while running:
        current_width, current_height = screen.get_size()
        draw_gradient_rect(screen, (0, 0, current_width, current_height), OSU_DARK_GREY, (10, 10, 40), vertical=True) # Adjusted start color
        title = font_big.render('Select a Map', True, OSU_BLUE)
        title_rect = title.get_rect(center=(current_width//2, 80))
        screen.blit(title, title_rect)

        for i, opt in enumerate(options):
            is_selected = (i == selected) # Use OSU_YELLOW for selected text
            color = OSU_YELLOW if is_selected else OSU_WHITE
            btn_c1 = OSU_BLUE if is_selected else OSU_MEDIUM_GREY
            btn_c2 = OSU_DARK_BLUE if is_selected else OSU_DARK_GREY

            text_surface = font_medium.render(opt['label'], True, color)
            rect = text_surface.get_rect(center=(current_width//2, 180 + i*60))

            draw_rounded_gradient(screen, rect.inflate(40, 10), btn_c1, btn_c2, radius=12, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), rect.inflate(40, 10), 2, border_radius=12)
            screen.blit(text_surface, rect)
        
        version_text = version_font.render(f'v{VERSION}', True, OSU_LIGHT_GREY)
        version_rect = version_text.get_rect(bottomright=(current_width-10, current_height-10))
        screen.blit(version_text, version_rect)

        # Custom cursor
        if SETTINGS['custom_cursor']:
            mx, my = pygame.mouse.get_pos()
            for r in range(20, 8, -2): # Outer glow
                pygame.draw.circle(screen, OSU_BLUE + (30,), (mx, my), r, 2)
            pygame.draw.circle(screen, OSU_WHITE, (mx, my), 16, 2) # Inner circle

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                SETTINGS['current_width'], SETTINGS['current_height'] = event.w, event.h
                screen = pygame.display.set_mode((SETTINGS['current_width'], SETTINGS['current_height']), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    return options[selected]['path']
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, opt in enumerate(options):
                    text_surface = font_medium.render(opt['label'], True, OSU_WHITE)
                    rect = text_surface.get_rect(center=(current_width//2, 180 + i*60))
                    if rect.inflate(40, 10).collidepoint(event.pos):
                        return opt['path']
        clock.tick(FPS)
    return None

current_audio_temp_file = None # Global variable to keep track of temp audio file

def play_game(screen, clock, map_filepath, map_name, hit_sound):
    global current_audio_temp_file
    hitobjects, map_name_from_file = load_map(map_filepath)
    if not hitobjects:
        print(f"No hitobjects found in map: {map_filepath}")
        return 'Maps' # Go back to maps menu

    # Sort hitobjects by time for correct playback order
    hitobjects.sort(key=lambda x: x.time)

    # Audio handling
    audio_path = None
    # Check for common audio file extensions within the map's directory (if it's a folder)
    map_dir = os.path.dirname(map_filepath)
    base_name_no_ext = os.path.splitext(os.path.basename(map_filepath))[0]
    
    # Try to find audio based on .osu file content if it's an .osz or .osu
    if map_filepath.endswith('.osz'):
        try:
            with zipfile.ZipFile(map_filepath, 'r') as z:
                osu_files = [f for f in z.namelist() if f.endswith('.osu')]
                if osu_files:
                    with z.open(osu_files[0]) as f:
                        osu_content = [l.decode('utf-8').strip() for l in f.readlines()]
                        for line in osu_content:
                            if line.startswith('AudioFilename:'):
                                audio_filename = line.split(':', 1)[1].strip()
                                # Look for this audio file within the .osz zip
                                if audio_filename in z.namelist():
                                    # Extract audio to a temp file for pygame.mixer
                                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_filename)[1]) as temp_audio:
                                        temp_audio.write(z.read(audio_filename))
                                        audio_path = temp_audio.name
                                        current_audio_temp_file = audio_path # Store for cleanup
                                    print(f"Extracted audio from .osz: {audio_filename}")
                                    break
                if not audio_path: # If no audio filename found or extracted from .osu
                    # Check for common audio files directly in the .osz root
                    for member in z.namelist():
                        if member.endswith(('.mp3', '.ogg', '.wav')):
                            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(member)[1]) as temp_audio:
                                temp_audio.write(z.read(member))
                                audio_path = temp_audio.name
                                current_audio_temp_file = audio_path
                            print(f"Found and extracted generic audio from .osz: {member}")
                            break
        except zipfile.BadZipFile:
            print(f"Warning: {map_filepath} is not a valid zip file. Attempting to load as plain text map.")
            # Fallback to direct folder search if not a valid zip
            for ext in ['.mp3', '.ogg', '.wav']:
                candidate_audio_path = os.path.join(map_dir, base_name_no_ext + ext)
                if os.path.exists(candidate_audio_path):
                    audio_path = candidate_audio_path
                    print(f"Found audio in same directory as .txt map: {audio_path}")
                    break
    elif map_filepath.endswith('.osu'):
        # For a standalone .osu file, read AudioFilename from it
        with open(map_filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('AudioFilename:'):
                    audio_filename = line.split(':', 1)[1].strip()
                    candidate_audio_path = os.path.join(map_dir, audio_filename)
                    if os.path.exists(candidate_audio_path):
                        audio_path = candidate_audio_path
                        print(f"Found audio specified in .osu file: {audio_path}")
                        break
    
    if not audio_path:
        # Fallback for .txt or if no audio found in .osu/.osz specific logic
        # Look for audio file with the same name as the map file in the same directory
        for ext in ['.mp3', '.ogg', '.wav']:
            candidate_audio_path = os.path.join(map_dir, base_name_no_ext + ext)
            if os.path.exists(candidate_audio_path):
                audio_path = candidate_audio_path
                print(f"Found audio by map name in directory: {audio_path}")
                break

    if audio_path and os.path.exists(audio_path):
        try:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.set_volume(SETTINGS['music_volume'])
            pygame.mixer.music.play()
            print(f"Playing audio: {audio_path}")
        except pygame.error as e:
            print(f"Could not load or play audio: {e}")
            audio_path = None # Set to None to prevent further issues

    # Game variables
    next_circle_index = 0
    score = 0
    health = 100
    max_health = 100
    combo = 0
    last_hit_time = 0 # To track combo breaks
    
    font = pygame.font.SysFont('Arial', 32)
    combo_font = pygame.font.SysFont('Arial', 48, bold=True)
    hit_feedback_font = pygame.font.SysFont('Arial', 30, bold=True)

    hit_feedbacks = [] # List to store feedback texts and their display times

    # Adjustable hit windows (example values)
    perfect_hit_window = 50
    great_hit_window = 100
    good_hit_window = 200
    miss_window_threshold = 300 # After this, it's a definite miss

    running = True
    start_time = pygame.time.get_ticks()
    
    # Custom cursor
    pygame.mouse.set_visible(not SETTINGS['custom_cursor'])

    while running:
        now = pygame.time.get_ticks() - start_time
        current_width, current_height = screen.get_size()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return 'Quit'
            elif event.type == pygame.VIDEORESIZE:
                SETTINGS['current_width'], SETTINGS['current_height'] = event.w, event.h
                screen = pygame.display.set_mode((SETTINGS['current_width'], SETTINGS['current_height']), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Pause menu or return to main menu
                    pygame.mixer.music.pause()
                    result = pause_menu(screen, clock, map_name)
                    pygame.mouse.set_visible(not SETTINGS['custom_cursor']) # Restore cursor visibility
                    if result == 'Resume':
                        pygame.mixer.music.unpause()
                    else:
                        if audio_path and current_audio_temp_file and os.path.exists(current_audio_temp_file):
                            try:
                                os.remove(current_audio_temp_file)
                                current_audio_temp_file = None
                            except OSError as e:
                                print(f"Error removing temporary audio file {current_audio_temp_file}: {e}")
                        return result # 'Quit', 'Retry', or 'Maps'

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    found_hit = False
                    for i in range(next_circle_index, len(hitobjects)):
                        obj = hitobjects[i]
                        if not obj.hit and not obj.disappeared:
                            time_diff = abs(now - obj.time)
                            dist_sq = (event.pos[0] - obj.pos[0])**2 + (event.pos[1] - obj.pos[1])**2

                            # Check if click is within circle radius AND within an acceptable time window
                            if dist_sq <= CIRCLE_RADIUS**2:
                                if time_diff <= perfect_hit_window:
                                    score += 300
                                    health = min(health + 5, max_health)
                                    combo += 1
                                    obj.hit = True
                                    hit_sound.set_volume(SETTINGS['sfx_volume'])
                                    hit_sound.play()
                                    hit_feedbacks.append({'text': 'Perfect!', 'time': pygame.time.get_ticks(), 'color': (0, 255, 0), 'pos': event.pos})
                                    found_hit = True
                                    last_hit_time = now
                                    break
                                elif time_diff <= great_hit_window:
                                    score += 100
                                    health = min(health + 2, max_health)
                                    combo += 1
                                    obj.hit = True
                                    hit_sound.set_volume(SETTINGS['sfx_volume'])
                                    hit_sound.play()
                                    hit_feedbacks.append({'text': 'Great!', 'time': pygame.time.get_ticks(), 'color': (0, 200, 255), 'pos': event.pos})
                                    found_hit = True
                                    last_hit_time = now
                                    break
                                elif time_diff <= good_hit_window:
                                    score += 50
                                    health = min(health + 1, max_health)
                                    combo += 1
                                    obj.hit = True
                                    hit_sound.set_volume(SETTINGS['sfx_volume'])
                                    hit_sound.play()
                                    hit_feedbacks.append({'text': 'Good!', 'time': pygame.time.get_ticks(), 'color': (255, 255, 0), 'pos': event.pos})
                                    found_hit = True
                                    last_hit_time = now
                                    break
                                else:
                                    # Too early/late click within circle, but outside good window - a miss
                                    health = max(health - 20, 0)
                                    combo = 0 # Break combo
                                    obj.disappeared = True # Mark as disappeared to prevent re-hits
                                    hit_feedbacks.append({'text': 'Miss!', 'time': pygame.time.get_ticks(), 'color': (255, 0, 0), 'pos': event.pos})
                                    found_hit = True
                                    break # Only process one click per object
                            elif i == next_circle_index and dist_sq > CIRCLE_RADIUS**2 and time_diff <= miss_window_threshold:
                                # Clicked too far from the current circle within its active window
                                health = max(health - 20, 0)
                                combo = 0 # Break combo
                                hit_feedbacks.append({'text': 'Miss!', 'time': pygame.time.get_ticks(), 'color': (255, 0, 0), 'pos': event.pos})
                                found_hit = True
                                # Don't mark obj.disappeared here, let the time-based check handle it
                                break

                    # If no hit object was clicked, it's a general miss (clicking empty space)
                    if not found_hit:
                        # Optionally, penalize for random clicks outside of hit objects
                        # For now, no penalty for clicking empty space
                        pass

        # Update hitobjects (check for misses based on time)
        while next_circle_index < len(hitobjects):
            obj = hitobjects[next_circle_index]
            if not obj.hit and not obj.disappeared:
                if now > obj.time + good_hit_window: # If current time passed hit window
                    health = max(health - 20, 0)
                    combo = 0 # Break combo
                    obj.disappeared = True
                    hit_feedbacks.append({'text': 'Miss!', 'time': pygame.time.get_ticks(), 'color': (255, 0, 0), 'pos': obj.pos})
                    next_circle_index += 1
                else:
                    break # Current object not yet missed, wait for it
            else:
                next_circle_index += 1 # Move to next object if current one is hit or disappeared

        draw_gradient_rect(screen, (0, 0, current_width, current_height), (30, 60, 120), (10, 10, 40), vertical=True)

        # Health bar
        health_bar_width = int(current_width * 0.5)
        health_bar_height = 32
        health_bar_x = current_width // 2 - health_bar_width // 2
        health_bar_y = 20
        pygame.draw.rect(screen, (60,60,60), (health_bar_x, health_bar_y, health_bar_width, health_bar_height), border_radius=16)
        # Health bar fill with gradient
        health_fill_width = int(health_bar_width * health / max_health)
        draw_rounded_gradient(screen, (health_bar_x, health_bar_y, health_fill_width, health_bar_height), (0,220,180), (0,150,200), radius=16)
        pygame.draw.rect(screen, (255,255,255), (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 2, border_radius=16)
        health_text = font.render(f'Health: {health}', True, (255,255,255))
        health_text_rect = health_text.get_rect(center=(current_width//2, health_bar_y + health_bar_height//2))
        screen.blit(health_text, health_text_rect)

        # Score display
        score_text = font.render(f'Score: {score}', True, (255,255,255))
        score_text_rect = score_text.get_rect(topleft=(20, 20))
        screen.blit(score_text, score_text_rect)

        # Combo display
        if combo > 0:
            combo_text = combo_font.render(f'{combo}x', True, (255,255,0))
            combo_text_rect = combo_text.get_rect(topright=(current_width - 20, 20))
            screen.blit(combo_text, combo_text_rect)

        # Draw hitobjects
        for obj in hitobjects:
            obj.draw(screen, now) # Pass current time for drawing approach circles

        # Draw hit feedback
        current_time_ms = pygame.time.get_ticks()
        feedbacks_to_keep = []
        for fb in hit_feedbacks:
            elapsed_time = current_time_ms - fb['time']
            if elapsed_time < 1000: # Display for 1 second
                alpha = max(0, 255 - int(255 * (elapsed_time / 1000)))
                feedback_color_with_alpha = fb['color'] + (alpha,)
                feedback_surface = hit_feedback_font.render(fb['text'], True, feedback_color_with_alpha)
                feedback_rect = feedback_surface.get_rect(center=(fb['pos'][0], fb['pos'][1] - elapsed_time * 0.05)) # Move up slowly
                screen.blit(feedback_surface, feedback_rect)
                feedbacks_to_keep.append(fb)
        hit_feedbacks = feedbacks_to_keep


        # Custom cursor
        if SETTINGS['custom_cursor']:
            mx, my = pygame.mouse.get_pos()
            for r in range(20, 8, -2):
                pygame.draw.circle(screen, (0,180,255,30), (mx, my), r, 2)
            pygame.draw.circle(screen, (255,255,255), (mx, my), 16, 2)

        pygame.display.flip()
        clock.tick(FPS)

        # Game over conditions
        if health <= 0:
            if audio_path and os.path.exists(audio_path):
                pygame.mixer.music.stop()
            result = game_over_screen(screen, clock, score, 'Failed')
            if audio_path and current_audio_temp_file and os.path.exists(current_audio_temp_file):
                try:
                    os.remove(current_audio_temp_file)
                    current_audio_temp_file = None
                except OSError as e:
                    print(f"Error removing temporary audio file {current_audio_temp_file}: {e}")
            return result
        
        # Check if all hitobjects have been processed or disappeared
        if all(obj.hit or obj.disappeared for obj in hitobjects):
            if audio_path and os.path.exists(audio_path):
                pygame.mixer.music.stop()
            result = game_over_screen(screen, clock, score, 'Completed')
            if audio_path and current_audio_temp_file and os.path.exists(current_audio_temp_file):
                try:
                    os.remove(current_audio_temp_file)
                    current_audio_temp_file = None
                except OSError as e:
                    print(f"Error removing temporary audio file {current_audio_temp_file}: {e}")
            return result

    if audio_path and current_audio_temp_file and os.path.exists(current_audio_temp_file):
        try:
            os.remove(current_audio_temp_file)
        except OSError as e:
            print(f"Error removing temporary audio file {current_audio_temp_file}: {e}")
    return 'Maps' # Default return if loop exits unexpectedly

def pause_menu(screen, clock, map_name):
    font_big = pygame.font.SysFont('Arial', 54, bold=True)
    font_medium = pygame.font.SysFont('Arial', 36)
    
    options = ['Resume', 'Retry', 'Back to Maps', 'Quit']
    selected = 0
    running = True

    # Darken the background
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) # Dark transparent overlay

    while running:
        screen.blit(overlay, (0, 0)) # Draw overlay on top of game state

        current_width, current_height = screen.get_size()

        title = font_big.render(f'{map_name} - Paused', True, (255, 255, 255))
        title_rect = title.get_rect(center=(current_width//2, current_height//2 - 150))
        screen.blit(title, title_rect)

        for i, opt_label in enumerate(options):
            is_selected = (i == selected)
            color = (0, 180, 255) if is_selected else (255, 255, 255)
            btn_c1 = (0, 180, 255) if is_selected else (60,60,60)
            btn_c2 = (0, 120, 200) if is_selected else (40,40,40)

            text_surface = font_medium.render(opt_label, True, color)
            rect = text_surface.get_rect(center=(current_width//2, current_height//2 - 50 + i*60))

            draw_rounded_gradient(screen, rect.inflate(40, 10), btn_c1, btn_c2, radius=12, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), rect.inflate(40, 10), 2, border_radius=12)
            screen.blit(text_surface, rect)

        # Custom cursor
        if SETTINGS['custom_cursor']:
            mx, my = pygame.mouse.get_pos()
            for r in range(20, 8, -2):
                pygame.draw.circle(screen, (0,180,255,30), (mx, my), r, 2)
            pygame.draw.circle(screen, (255,255,255), (mx, my), 16, 2)
        
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                SETTINGS['current_width'], SETTINGS['current_height'] = event.w, event.h
                screen = pygame.display.set_mode((SETTINGS['current_width'], SETTINGS['current_height']), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if options[selected] == 'Resume':
                        return 'Resume'
                    elif options[selected] == 'Retry':
                        return 'Retry'
                    elif options[selected] == 'Back to Maps':
                        return 'Maps'
                    elif options[selected] == 'Quit':
                        return 'Quit'
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, opt_label in enumerate(options):
                    text_surface = font_medium.render(opt_label, True, (255,255,255))
                    rect = text_surface.get_rect(center=(current_width//2, current_height//2 - 50 + i*60))
                    if rect.inflate(40, 10).collidepoint(event.pos):
                        if options[i] == 'Resume':
                            return 'Resume'
                        elif options[i] == 'Retry':
                            return 'Retry'
                        elif options[i] == 'Back to Maps':
                            return 'Maps'
                        elif options[i] == 'Quit':
                            return 'Quit'
        clock.tick(FPS)

def game_over_screen(screen, clock, final_score, status):
    font_big = pygame.font.SysFont('Arial', 54, bold=True)
    font_medium = pygame.font.SysFont('Arial', 36)
    
    options = ['Retry', 'Back to Maps', 'Quit']
    selected = 0
    running = True

    # Darken the background
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) # Dark transparent overlay

    while running:
        screen.blit(overlay, (0, 0)) # Draw overlay on top of game state

        current_width, current_height = screen.get_size()

        status_text = font_big.render(f'Map {status}!', True, (0, 180, 255) if status == 'Completed' else (255, 50, 50))
        status_rect = status_text.get_rect(center=(current_width//2, current_height//2 - 150))
        screen.blit(status_text, status_rect)

        score_text = font_medium.render(f'Final Score: {final_score}', True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(current_width//2, current_height//2 - 90))
        screen.blit(score_text, score_rect)

        for i, opt_label in enumerate(options):
            is_selected = (i == selected)
            color = (0, 180, 255) if is_selected else (255, 255, 255)
            btn_c1 = (0, 180, 255) if is_selected else (60,60,60)
            btn_c2 = (0, 120, 200) if is_selected else (40,40,40)

            text_surface = font_medium.render(opt_label, True, color)
            rect = text_surface.get_rect(center=(current_width//2, current_height//2 - 20 + i*60))

            draw_rounded_gradient(screen, rect.inflate(40, 10), btn_c1, btn_c2, radius=12, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), rect.inflate(40, 10), 2, border_radius=12)
            screen.blit(text_surface, rect)

        # Custom cursor
        if SETTINGS['custom_cursor']:
            mx, my = pygame.mouse.get_pos()
            for r in range(20, 8, -2):
                pygame.draw.circle(screen, (0,180,255,30), (mx, my), r, 2)
            pygame.draw.circle(screen, (255,255,255), (mx, my), 16, 2)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                SETTINGS['current_width'], SETTINGS['current_height'] = event.w, event.h
                screen = pygame.display.set_mode((SETTINGS['current_width'], SETTINGS['current_height']), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if options[selected] == 'Retry':
                        return 'Retry'
                    elif options[selected] == 'Back to Maps':
                        return 'Maps'
                    elif options[selected] == 'Quit':
                        return 'Quit'
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, opt_label in enumerate(options):
                    text_surface = font_medium.render(opt_label, True, (255,255,255))
                    rect = text_surface.get_rect(center=(current_width//2, current_height//2 - 20 + i*60))
                    if rect.inflate(40, 10).collidepoint(event.pos):
                        if options[i] == 'Retry':
                            return 'Retry'
                        elif options[i] == 'Back to Maps':
                            return 'Maps'
                        elif options[i] == 'Quit':
                            return 'Quit'
        clock.tick(FPS)


def main_menu(screen, clock, settings, hit_sound):
    font_big = pygame.font.SysFont('Arial', 54, bold=True)
    font_medium = pygame.font.SysFont('Arial', 36)
    version_font = pygame.font.SysFont('Arial', 24)

    options = ['Start', 'Settings', 'Tutorial', 'About', 'Quit']
    selected = 0
    running = True

    while running:
        current_width, current_height = screen.get_size()
        draw_gradient_rect(screen, (0, 0, current_width, current_height), OSU_DARK_GREY, (10, 10, 40), vertical=True) # Adjusted start color
        
        # Smoother animation for logo
        time_ms = pygame.time.get_ticks()
        # Scale oscillates between 1.05 and 1.10
        scale = 1.05 + 0.05 * (math.sin(time_ms / 300.0) * 0.5 + 0.5) 
        
        title = font_big.render('osu!python', True, OSU_BLUE)
        title = pygame.transform.rotozoom(title, 0, scale)
        title_rect = title.get_rect(center=(current_width//2, current_height//2 - 120))
        for glow in range(8, 0, -2):
            glow_surf = font_big.render('osu!python', True, (0, 180, 255, 30))
            glow_surf = pygame.transform.rotozoom(glow_surf, 0, scale + glow*0.01)
            glow_rect = glow_surf.get_rect(center=title_rect.center)
            screen.blit(glow_surf, glow_rect)
        screen.blit(title, title_rect)
        for i, opt_label in enumerate(options):
            is_selected = (i == selected) # Use OSU_BLUE for selected text
            color = OSU_BLUE if is_selected else OSU_WHITE
            btn_c1 = OSU_BLUE if is_selected else OSU_MEDIUM_GREY
            btn_c2 = OSU_DARK_BLUE if is_selected else OSU_DARK_GREY

            text_surface = font_medium.render(opt_label, True, color)
            rect = text_surface.get_rect(center=(current_width//2, current_height//2 + 40 + i*60))
            
            draw_rounded_gradient(screen, rect.inflate(40, 10), btn_c1, btn_c2, radius=12, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), rect.inflate(40, 10), 2, border_radius=12)
            screen.blit(text_surface, rect)

        # Holiday Greeting System
        draw_holiday_elements(screen, font_medium)

        version_text = version_font.render(f'v{VERSION}', True, (180, 180, 180))
        version_rect = version_text.get_rect(bottomright=(current_width-10, current_height-10))
        screen.blit(version_text, version_rect)

        # Custom cursor
        if SETTINGS['custom_cursor']:
            mx, my = pygame.mouse.get_pos()
            for r in range(20, 8, -2): # Outer glow
                pygame.draw.circle(screen, OSU_BLUE + (30,), (mx, my), r, 2)
            pygame.draw.circle(screen, OSU_WHITE, (mx, my), 16, 2) # Inner circle

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                SETTINGS['current_width'], SETTINGS['current_height'] = event.w, event.h
                screen = pygame.display.set_mode((SETTINGS['current_width'], SETTINGS['current_height']), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if options[selected] == 'Start':
                        return settings
                    elif options[selected] == 'Settings':
                        settings = settings_menu(screen, clock, settings) # Pass and receive updated settings
                    elif options[selected] == 'Tutorial':
                        tutorial_screen(screen, clock, hit_sound)
                    elif options[selected] == 'About':
                        about_screen(screen, clock)
                    elif options[selected] == 'Quit':
                        pygame.quit()
                        sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, opt_label in enumerate(options):
                    text_surface = font_medium.render(opt_label, True, (255,255,255))
                    rect = text_surface.get_rect(center=(current_width//2, current_height//2 + 40 + i*60))
                    if rect.inflate(40, 10).collidepoint(event.pos):
                        if options[i] == 'Start':
                            return settings
                        elif options[i] == 'Settings':
                            settings = settings_menu(screen, clock, settings) # Pass and receive updated settings
                        elif options[i] == 'Tutorial':
                            tutorial_screen(screen, clock, hit_sound)
                        elif options[i] == 'About':
                            about_screen(screen, clock)
                        elif options[i] == 'Quit':
                            pygame.quit()
                            sys.exit()
        clock.tick(FPS)

def main():
    pygame.init()
    pygame.font.init() # Initialize font module

    # 1. Attempt to initialize the mixer
    mixer_initialized = False
    try:
        pygame.mixer.init() # Initialize mixer module
        mixer_initialized = True
    except pygame.error as e:
        print(f"Warning: Pygame mixer could not be initialized. Running in silent mode. Error: {e}")

    # 2. Attempt to generate hitsound if mixer is up
    hit_sound = None
    if mixer_initialized:
        try:
            hit_sound = generate_hitsound()
        except pygame.error as e:
            print(f"Warning: Could not generate hitsound. SFX will be disabled. Error: {e}")

    # 3. Create dummy objects for whatever failed
    if not mixer_initialized:
        class DummyMusic:
            def load(self, *args, **kwargs): pass
            def play(self, *args, **kwargs): pass
            def pause(self, *args, **kwargs): pass
            def unpause(self, *args, **kwargs): pass
            def stop(self, *args, **kwargs): pass
            def set_volume(self, *args, **kwargs): pass
        pygame.mixer.music = DummyMusic()
    if not hit_sound:
        class DummySound:
            def play(self, *args, **kwargs): pass
            def set_volume(self, *args, **kwargs): pass
        hit_sound = DummySound()

    screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("osu!python")

    clock = pygame.time.Clock()

    global SETTINGS # Declare that we intend to modify the global SETTINGS
    global current_audio_temp_file

    running = True
    while running:
        SETTINGS = main_menu(screen, clock, SETTINGS, hit_sound) # Pass and receive updated settings

        if SETTINGS is None: # This could happen if main_menu decides to quit
            running = False
            break

        # If 'Start' was selected in main_menu, go to maps_menu
        selected_map_path = maps_menu(screen, clock)

        if selected_map_path:
            map_name = os.path.splitext(os.path.basename(selected_map_path))[0]
            result = play_game(screen, clock, selected_map_path, map_name, hit_sound)

            if result == 'Quit':
                running = False
            elif result == 'Retry':
                # Restart this map from the beginning
                continue # Loop back to play_game with the same map
            elif result == 'Maps':
                continue # Loop back to maps_menu
        else:
            # If maps_menu returned None (Back to Main Menu) or no map selected, loop back to main_menu
            continue 
    
    # Clean up temporary audio file if it exists
    if current_audio_temp_file and os.path.exists(current_audio_temp_file):
        try:
            os.remove(current_audio_temp_file)
        except OSError as e:
            print(f"Error removing temporary audio file {current_audio_temp_file}: {e}")

    pygame.mouse.set_visible(True) # Ensure cursor is visible when returning to main menu

if __name__ == '__main__':
    main()
    pygame.quit()
    sys.exit()
