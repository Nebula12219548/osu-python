import pygame
import sys
import math
import random
import os
import tempfile
import shutil
import zipfile

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

# Constants that do not change with window size
FPS = 60
CIRCLE_RADIUS = 50
CIRCLE_OUTLINE = 6
CIRCLE_COLOR = (0, 180, 255)
CIRCLE_OUTLINE_COLOR = (255, 255, 255)
NUMBER_COLOR = (255, 255, 255)
BACKGROUND_COLOR = (30, 30, 30)

# HitCircle class
def draw_hit_circle(surface, pos, number, approach=1.0):
    # Draw approach circle (anti-aliased)
    approach_radius = int(CIRCLE_RADIUS * approach)
    if approach > 1.05:
        aa_circle(surface, (100, 200, 255), pos, approach_radius, 2)
    # Draw main circle (anti-aliased)
    aa_filled_circle(surface, CIRCLE_COLOR, pos, CIRCLE_RADIUS)
    aa_circle(surface, CIRCLE_OUTLINE_COLOR, pos, CIRCLE_RADIUS, CIRCLE_OUTLINE)
    # Draw number
    font = pygame.font.SysFont('Arial', 36, bold=True)
    text = font.render(str(number), True, NUMBER_COLOR)
    text_rect = text.get_rect(center=pos)
    surface.blit(text, text_rect)

def aa_circle(surface, color, pos, radius, width=1):
    # Draw anti-aliased circle using pygame.gfxdraw
    import pygame.gfxdraw
    for w in range(width):
        pygame.gfxdraw.aacircle(surface, pos[0], pos[1], radius-w, color)

def aa_filled_circle(surface, color, pos, radius):
    import pygame.gfxdraw
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
    import pygame.gfxdraw
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

def about_screen(screen, clock):
    font_big = pygame.font.SysFont('Arial', 54, bold=True)
    font_small = pygame.font.SysFont('Arial', 32)
    version_font = pygame.font.SysFont('Arial', 24)
    running = True
    while running:
        current_width, current_height = screen.get_size()
        draw_gradient_rect(screen, (0, 0, current_width, current_height), (30, 60, 120), (10, 10, 40), vertical=True)
        title = font_big.render('About osu!python', True, (0, 180, 255))
        title_rect = title.get_rect(center=(current_width//2, current_height//2 - 100))
        screen.blit(title, title_rect)
        lines = [
            'osu!python is a osu! clone by Nebula12219548',
            'Inspired by osu! (ppy)',
            'For educational and fun purposes only.',
            'Version: v0.2.0',
            '',
            'Press any key or click to return.'
        ]
        for i, line in enumerate(lines):
            text = font_small.render(line, True, (255,255,255))
            rect = text.get_rect(center=(current_width//2, current_height//2 + i*40 - 20))
            screen.blit(text, rect)
        version_text = version_font.render('v0.2.0', True, (180, 180, 180))
        version_rect = version_text.get_rect(bottomright=(current_width-10, current_height-10))
        screen.blit(version_text, version_rect)

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
        draw_gradient_rect(screen, (0, 0, current_width, current_height), (30, 60, 120), (10, 10, 40), vertical=True)
        title = font_big.render('Settings', True, (0, 180, 255))
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
            pygame.draw.rect(screen, (255,255,255,180), rect.inflate(40, 10), 2, border_radius=12)
            screen.blit(text_surface, rect)

            # Draw slider bar if it's a slider type
            if opt['type'] == 'slider' and not opt.get('disabled', False):
                slider_width = 200
                slider_height = 10
                slider_x = current_width // 2 + rect.width // 2 + 30 # Adjust position
                slider_y = rect.centery - slider_height // 2

                slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
                pygame.draw.rect(screen, (80, 80, 80), slider_rect, border_radius=5)

                value_range = opt['max'] - opt['min']
                if value_range > 0:
                    handle_pos_x = slider_x + slider_width * ((settings[opt['setting']] - opt['min']) / value_range)
                    pygame.draw.circle(screen, (255, 255, 255), (int(handle_pos_x), rect.centery), 10)
                    pygame.draw.circle(screen, (0, 180, 255), (int(handle_pos_x), rect.centery), 8)


        version_text = version_font.render('v0.2.0', True, (180, 180, 180))
        version_rect = version_text.get_rect(bottomright=(current_width-10, current_height-10))
        screen.blit(version_text, version_rect)

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

def tutorial_screen(screen, clock):
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
        draw_gradient_rect(screen, (0, 0, current_width, current_height), (30, 60, 120), (10, 10, 40), vertical=True)
        title = font_big.render('Tutorial', True, (0, 180, 255))
        title_rect = title.get_rect(center=(current_width//2, 120))
        screen.blit(title, title_rect)
        for i, line in enumerate(instructions):
            text = font_small.render(line, True, (255,255,255))
            rect = text.get_rect(center=(current_width//2, 220 + i*40))
            screen.blit(text, rect)
        version_text = version_font.render('v0.2.0', True, (180, 180, 180))
        version_rect = version_text.get_rect(bottomright=(current_width-10, current_height-10))
        screen.blit(version_text, version_rect)

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
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                running = False
        clock.tick(FPS)

    # Run demonstration
    run_tutorial_demo(screen, clock)

def run_tutorial_demo(screen, clock):
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
                        current += 1
        # Missed
        if current < len(demo_hitobjects):
            obj = demo_hitobjects[current]
            if now > obj['time'] + hit_window and not clicked[current]:
                health = max(health - 30, 0)
                current += 1
        draw_gradient_rect(screen, (0, 0, current_width, current_height), (30, 60, 120), (10, 10, 40), vertical=True)
        # Health bar
        health_bar_width = int(current_width * 0.5)
        health_bar_height = 32
        health_bar_x = current_width // 2 - health_bar_width // 2
        health_bar_y = 20

        pygame.draw.rect(screen, (60,60,60), (health_bar_x, health_bar_y, health_bar_width, health_bar_height), border_radius=16)
        # Health bar fill with gradient
        health_fill_width = int(health_bar_width * health / max_health)
        draw_rounded_gradient(screen, (health_bar_x, health_bar_y, health_fill_width, health_bar_height), (0,220,180), (0,150,120), radius=16, vertical=False)
        pygame.draw.rect(screen, (255,255,255), (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 3, border_radius=16)

        # Draw hit circles
        for i, obj in enumerate(demo_hitobjects):
            t = obj['time'] - now
            approach = max(1.0, min(2.5, t / approach_time + 1))
            if not clicked[i] and t < approach_time and now < obj['time'] + hit_window:
                # Shadow
                shadow_surf = pygame.Surface((CIRCLE_RADIUS*2 + 8, CIRCLE_RADIUS*2 + 8), pygame.SRCALPHA)
                pygame.draw.circle(shadow_surf, (0,0,0,60), (CIRCLE_RADIUS+4, CIRCLE_RADIUS+4), CIRCLE_RADIUS+4)
                screen.blit(shadow_surf, (obj['pos'][0]-CIRCLE_RADIUS-4+4, obj['pos'][1]-CIRCLE_RADIUS-4+4)) # Adjust for shadow offset
                # Approach
                aa_circle(screen, (100, 200, 255), obj['pos'], int(CIRCLE_RADIUS * approach), 2)
                # Main
                aa_filled_circle(screen, CIRCLE_COLOR, obj['pos'], CIRCLE_RADIUS)
                aa_circle(screen, CIRCLE_OUTLINE_COLOR, obj['pos'], CIRCLE_RADIUS, CIRCLE_OUTLINE)
                text = font.render(str(i+1), True, (255,255,255))
                rect = text.get_rect(center=obj['pos'])
                screen.blit(text, rect)
        # Score
        score_text = font.render(f'Score: {score}', True, (255,255,255))
        screen.blit(score_text, (10, 10))
        # Instructions
        if current < len(demo_hitobjects):
            inst = font.render('Click the circle!', True, (255,255,0))
            screen.blit(inst, (current_width//2-inst.get_width()//2, current_height-60))
        else:
            inst = font.render('Tutorial Complete! Press any key or click.', True, (0,255,100))
            screen.blit(inst, (current_width//2-inst.get_width()//2, current_height-60))

        # Custom cursor
        if SETTINGS['custom_cursor']:
            mx, my = pygame.mouse.get_pos()
            for r in range(20, 8, -2):
                pygame.draw.circle(screen, (0,180,255,30), (mx, my), r, 2)
            pygame.draw.circle(screen, (255,255,255), (mx, my), 16, 2)

        pygame.display.flip()
        clock.tick(FPS)
        if current >= len(demo_hitobjects):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.VIDEORESIZE:
                    SETTINGS['current_width'], SETTINGS['current_height'] = event.w, event.h
                    screen = pygame.display.set_mode((SETTINGS['current_width'], SETTINGS['current_height']), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    running = False

def main_menu(screen, clock, settings):
    font_big = pygame.font.SysFont('Arial', 72, bold=True)
    font_small = pygame.font.SysFont('Arial', 40)
    version_font = pygame.font.SysFont('Arial', 24)
    menu_running = True
    buttons = ['Start', 'Tutorial', 'Settings', 'About']
    selected = 0
    while menu_running:
        current_width, current_height = screen.get_size()
        draw_gradient_rect(screen, (0, 0, current_width, current_height), (30, 60, 120), (10, 10, 40), vertical=True)
        
        # Smoother animation for logo
        time_ms = pygame.time.get_ticks()
        # Scale oscillates between 1.05 and 1.10
        scale = 1.05 + 0.05 * (math.sin(time_ms / 300.0) * 0.5 + 0.5) 
        
        title = font_big.render('osu!python', True, (0, 180, 255))
        title = pygame.transform.rotozoom(title, 0, scale)
        title_rect = title.get_rect(center=(current_width//2, current_height//2 - 120))
        for glow in range(8, 0, -2):
            glow_surf = font_big.render('osu!python', True, (0, 180, 255, 30))
            glow_surf = pygame.transform.rotozoom(glow_surf, 0, scale + glow*0.01)
            glow_rect = glow_surf.get_rect(center=title_rect.center)
            screen.blit(glow_surf, glow_rect)
        screen.blit(title, title_rect)
        # Draw buttons
        for i, label in enumerate(buttons):
            color = (255,255,0) if i == selected else (255,255,255)
            btn_text = font_small.render(label, True, color)
            btn_rect = btn_text.get_rect(center=(current_width//2, current_height//2 + 40 + i*70))
            # Smooth rounded gradient button
            btn_c1 = (0, 180, 255) if i == selected else (60,60,60)
            btn_c2 = (0, 120, 200) if i == selected else (40,40,40)
            draw_rounded_gradient(screen, btn_rect.inflate(60, 24), btn_c1, btn_c2, radius=16, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), btn_rect.inflate(60, 24), 3, border_radius=16)
            screen.blit(btn_text, btn_rect)
        version_text = version_font.render('v0.2.0', True, (180, 180, 180))
        version_rect = version_text.get_rect(bottomright=(current_width-10, current_height-10))
        screen.blit(version_text, version_rect)

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
                    selected = (selected - 1) % len(buttons)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(buttons)
                elif event.key == pygame.K_RETURN:
                    if buttons[selected] == 'Start':
                        menu_running = False
                    elif buttons[selected] == 'About':
                        about_screen(screen, clock)
                    elif buttons[selected] == 'Settings':
                        settings = settings_menu(screen, clock, settings) # Pass and update settings
                    elif buttons[selected] == 'Tutorial':
                        tutorial_screen(screen, clock)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, label in enumerate(buttons):
                    btn_text = font_small.render(label, True, (255,255,255))
                    btn_rect = btn_text.get_rect(center=(current_width//2, current_height//2 + 40 + i*70))
                    if btn_rect.inflate(60, 24).collidepoint(event.pos):
                        if label == 'Start':
                            menu_running = False
                        elif label == 'About':
                            about_screen(screen, clock)
                        elif label == 'Settings':
                            settings = settings_menu(screen, clock, settings) # Pass and update settings
                        elif label == 'Tutorial':
                            tutorial_screen(screen, clock)
        clock.tick(FPS)
    return settings # Return updated settings

def maps_menu(screen, clock):
    font_big = pygame.font.SysFont('Arial', 48, bold=True)
    font_small = pygame.font.SysFont('Arial', 32)
    version_font = pygame.font.SysFont('Arial', 24)
    maps_dir = os.path.join(os.path.dirname(__file__), 'maps')
    
    # Ensure 'maps' directory exists, if not, create it
    if not os.path.exists(maps_dir):
        os.makedirs(maps_dir)
    
    maps = [f for f in os.listdir(maps_dir) if f.endswith('.osz') or f.endswith('.osu')]
    
    # Add a 'Back' option to the main list of options
    menu_options = [{'label': m, 'type': 'map', 'path': os.path.join(maps_dir, m)} for m in maps]
    menu_options.append({'label': 'Back to Main Menu', 'type': 'action', 'path': None})

    selected = 0
    menu_running = True
    while menu_running:
        current_width, current_height = screen.get_size()
        t = pygame.time.get_ticks() / 1000.0
        c1 = (20, int(40+20*abs(pygame.math.Vector2(1,0).rotate(t*30).x)), 80)
        c2 = (40, 10, int(60+20*abs(pygame.math.Vector2(0,1).rotate(t*30).y)))
        draw_gradient_rect(screen, (0, 0, current_width, current_height), c1, c2, vertical=True)
        title = font_big.render('Select Map', True, (0, 180, 255))
        title_rect = title.get_rect(center=(current_width//2, 80))
        screen.blit(title, title_rect)

        for i, opt in enumerate(menu_options):
            color = (255,255,0) if i == selected else (255,255,255)
            text = font_small.render(opt['label'], True, color)
            rect = text.get_rect(center=(current_width//2, 180 + i*50))
            btn_c1 = (0, 180, 255) if i == selected else (60,60,60)
            btn_c2 = (0, 120, 200) if i == selected else (40,40,40)
            draw_rounded_gradient(screen, rect.inflate(40, 10), btn_c1, btn_c2, radius=12, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), rect.inflate(40, 10), 2, border_radius=12)
            screen.blit(text, rect)

        version_text = version_font.render('v0.2.0', True, (180, 180, 180))
        version_rect = version_text.get_rect(bottomright=(current_width-10, current_height-10))
        screen.blit(version_text, version_rect)

        # Custom cursor for maps menu
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
                    selected = (selected - 1) % len(menu_options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    if menu_options[selected]['type'] == 'map':
                        return menu_options[selected]['path']
                    elif menu_options[selected]['type'] == 'action' and menu_options[selected]['label'] == 'Back to Main Menu':
                        return None # Signal to go back to main menu
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, opt in enumerate(menu_options):
                    # Recalculate rect for click detection
                    text = font_small.render(opt['label'], True, (255,255,255))
                    rect = text.get_rect(center=(current_width//2, 180 + i*50))
                    if rect.inflate(40, 10).collidepoint(event.pos):
                        if opt['type'] == 'map':
                            return opt['path']
                        elif opt['type'] == 'action' and opt['label'] == 'Back to Main Menu':
                            return None # Signal to go back to main menu
        clock.tick(FPS)
    return None # Should not be reached but good for safety

def level_cleared_screen(screen, clock, score, map_name):
    font_big = pygame.font.SysFont('Arial', 64, bold=True)
    font_small = pygame.font.SysFont('Arial', 36)
    version_font = pygame.font.SysFont('Arial', 24)
    running = True
    selected = 0
    options = ['Retry', 'Back to Menu']
    while running:
        current_width, current_height = screen.get_size()
        t = pygame.time.get_ticks() / 1000.0
        c1 = (30, int(80+20*abs(pygame.math.Vector2(1,0).rotate(t*30).x)), 40)
        c2 = (10, int(30+20*abs(pygame.math.Vector2(0,1).rotate(t*30).y)), 10)
        draw_gradient_rect(screen, (0, 0, current_width, current_height), c1, c2, vertical=True)
        title = font_big.render('Level Cleared!', True, (0, 255, 100))
        score_text = font_small.render(f'Score: {score}', True, (255,255,255))
        map_text = font_small.render(f'Map: {map_name}', True, (0,180,255))
        version_text = version_font.render('v0.2.0', True, (180, 180, 180))
        title_rect = title.get_rect(center=(current_width//2, current_height//2 - 120))
        score_rect = score_text.get_rect(center=(current_width//2, current_height//2 - 40))
        map_rect = map_text.get_rect(center=(current_width//2, current_height//2 + 10))
        version_rect = version_font.render('v0.2.0', True, (180, 180, 180)).get_rect(bottomright=(current_width-10, current_height-10))
        screen.blit(title, title_rect)
        screen.blit(score_text, score_rect)
        screen.blit(map_text, map_rect)
        screen.blit(version_text, version_rect)
        for i, opt in enumerate(options):
            color = (255,255,0) if i == selected else (255,255,255)
            opt_text = font_small.render(opt, True, color)
            opt_rect = opt_text.get_rect(center=(current_width//2, current_height//2 + 80 + i*50))
            btn_c1 = (0, 180, 255) if i == selected else (60,60,60)
            btn_c2 = (0, 120, 200) if i == selected else (40,40,40)
            draw_rounded_gradient(screen, opt_rect.inflate(40, 10), btn_c1, btn_c2, radius=12, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), opt_rect.inflate(40, 10), 2, border_radius=12)
            screen.blit(opt_text, opt_rect)

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
                    return options[selected]
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, opt in enumerate(options):
                    opt_text = font_small.render(opt, True, (255,255,255))
                    opt_rect = opt_text.get_rect(center=(current_width//2, current_height//2 + 80 + i*50))
                    if opt_rect.collidepoint(event.pos):
                        return options[i]
        clock.tick(FPS)

def level_failed_screen(screen, clock, score, map_name):
    font_big = pygame.font.SysFont('Arial', 64, bold=True)
    font_small = pygame.font.SysFont('Arial', 36)
    version_font = pygame.font.SysFont('Arial', 24)
    running = True
    selected = 0
    options = ['Retry', 'Back to Menu']
    while running:
        current_width, current_height = screen.get_size()
        t = pygame.time.get_ticks() / 1000.0
        c1 = (int(80+20*abs(pygame.math.Vector2(1,0).rotate(t*30).x)), 30, 30)
        c2 = (int(30+20*abs(pygame.math.Vector2(0,1).rotate(t*30).y)), 10, 10)
        draw_gradient_rect(screen, (0, 0, current_width, current_height), c1, c2, vertical=True)
        title = font_big.render('Level Failed!', True, (255, 60, 60))
        score_text = font_small.render(f'Score: {score}', True, (255,255,255))
        map_text = font_small.render(f'Map: {map_name}', True, (0,180,255))
        version_text = version_font.render('v0.2.0', True, (180, 180, 180))
        title_rect = title.get_rect(center=(current_width//2, current_height//2 - 120))
        score_rect = score_text.get_rect(center=(current_width//2, current_height//2 - 40))
        map_rect = map_text.get_rect(center=(current_width//2, current_height//2 + 10))
        version_rect = version_font.render('v0.2.0', True, (180, 180, 180)).get_rect(bottomright=(current_width-10, current_height-10))
        screen.blit(title, title_rect)
        screen.blit(score_text, score_rect)
        screen.blit(map_text, map_rect)
        screen.blit(version_text, version_rect)
        for i, opt in enumerate(options):
            color = (255,255,0) if i == selected else (255,255,255)
            opt_text = font_small.render(opt, True, color)
            opt_rect = opt_text.get_rect(center=(current_width//2, current_height//2 + 80 + i*50))
            btn_c1 = (255,60,60) if i == selected else (60,60,60)
            btn_c2 = (200,40,40) if i == selected else (40,40,40)
            draw_rounded_gradient(screen, opt_rect.inflate(40, 10), btn_c1, btn_c2, radius=12, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), opt_rect.inflate(40, 10), 2, border_radius=12)
            screen.blit(opt_text, opt_rect)

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
                    return options[selected]
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, opt in enumerate(options):
                    opt_text = font_small.render(opt, True, (255,255,255))
                    opt_rect = opt_text.get_rect(center=(current_width//2, current_height//2 + 80 + i*50))
                    if opt_rect.collidepoint(event.pos):
                        return options[i]
        clock.tick(FPS)

def pause_menu(screen, clock):
    font_big = pygame.font.SysFont('Arial', 64, bold=True)
    font_small = pygame.font.SysFont('Arial', 36)
    running = True
    selected = 0
    options = ['Resume', 'Back to Menu']
    while running:
        current_width, current_height = screen.get_size()
        t = pygame.time.get_ticks() / 1000.0
        c1 = (40, 40, int(60+20*abs(pygame.math.Vector2(1,0).rotate(t*30).x)))
        c2 = (10, 10, int(30+20*abs(pygame.math.Vector2(0,1).rotate(t*30).y)))
        draw_gradient_rect(screen, (0, 0, current_width, current_height), c1, c2, vertical=True)
        title = font_big.render('Paused', True, (0, 180, 255))
        title_rect = title.get_rect(center=(current_width//2, current_height//2 - 80))
        screen.blit(title, title_rect)
        for i, opt in enumerate(options):
            color = (255,255,0) if i == selected else (255,255,255)
            opt_text = font_small.render(opt, True, color)
            opt_rect = opt_text.get_rect(center=(current_width//2, current_height//2 + 40 + i*50))
            btn_c1 = (0, 180, 255) if i == selected else (60,60,60)
            btn_c2 = (0, 120, 200) if i == selected else (40,40,40)
            draw_rounded_gradient(screen, opt_rect.inflate(40, 10), btn_c1, btn_c2, radius=16, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), opt_rect.inflate(40, 10), 2, border_radius=16)
            screen.blit(opt_text, opt_rect)

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
                    return options[selected]
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, opt in enumerate(options):
                    opt_text = font_small.render(opt, True, (255,255,255))
                    opt_rect = opt_text.get_rect(center=(current_width//2, current_height//2 + 40 + i*50))
                    if opt_rect.collidepoint(event.pos):
                        return options[i]
        clock.tick(FPS)

def main():
    pygame.init()
    screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption('osu!python v0.2.0')
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 24)

    # Use the global SETTINGS dictionary
    global SETTINGS

    # Set initial volume
    pygame.mixer.music.set_volume(SETTINGS['music_volume'])

    while True:
        SETTINGS = main_menu(screen, clock, SETTINGS) # Pass and receive updated settings

        # After returning from main_menu, update screen size based on SETTINGS
        screen = pygame.display.set_mode((SETTINGS['current_width'], SETTINGS['current_height']), pygame.RESIZABLE)
        pygame.mouse.set_visible(not SETTINGS['custom_cursor'])

        map_path = maps_menu(screen, clock)
        if map_path is None: # Back to main menu was selected
            continue

        # Ensure the screen is updated again after map selection in case of resize events during map_menu
        screen = pygame.display.set_mode((SETTINGS['current_width'], SETTINGS['current_height']), pygame.RESIZABLE)
        pygame.mouse.set_visible(not SETTINGS['custom_cursor'])

        hitobjects, map_name = load_map(map_path)
        # Audio support (fix: always extract and use a temp file for all formats)
        audio_file = None
        audio_path = None
        
        if map_path.endswith('.osz'):
            try:
                with zipfile.ZipFile(map_path, 'r') as z:
                    osu_files = [f for f in z.namelist() if f.endswith('.osu')]
                    audio_file = None
                    if osu_files:
                        with z.open(osu_files[0]) as f:
                            for line in f:
                                line = line.decode('utf-8').strip()
                                if line.startswith('AudioFilename:'):
                                    audio_file = line.split(':',1)[1].strip()
                                    break
                    if audio_file and audio_file in z.namelist():
                        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file)[1])
                        with z.open(audio_file) as src, open(temp_audio.name, 'wb') as dst:
                            shutil.copyfileobj(src, dst)
                        audio_path = temp_audio.name
            except zipfile.BadZipFile:
                audio_path = None
        else:
            # For non-.osz files, assume audio is in the same directory as the .osu file
            # or try to find a common audio file name if the .osu does not specify
            map_dir = os.path.dirname(map_path)
            try:
                with open(map_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('AudioFilename:'):
                            audio_file = line.split(':',1)[1].strip()
                            audio_path = os.path.join(map_dir, audio_file)
                            break
            except Exception:
                pass # Fall through if .osu cannot be read
            if not audio_path or not os.path.exists(audio_path):
                # Fallback to searching common audio file types
                for ext in ['.mp3', '.ogg', '.wav']:
                    potential_audio = os.path.join(map_dir, map_name + ext)
                    if os.path.exists(potential_audio):
                        audio_path = potential_audio
                        break
        
        if audio_path and os.path.exists(audio_path):
            try:
                # Use soundfile to load any format and convert to WAV if necessary for pygame mixer
                import soundfile as sf
                import numpy as np
                import scipy.io.wavfile
                
                y, sr = sf.read(audio_path, dtype='float32')
                
                # Create a temporary WAV file
                temp_wav_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                temp_wav_path = temp_wav_file.name
                temp_wav_file.close()

                y16 = np.int16(y / np.max(np.abs(y)) * 32767) # Convert to 16-bit PCM
                scipy.io.wavfile.write(temp_wav_path, sr, y16)
                
                pygame.mixer.music.load(temp_wav_path)
                pygame.mixer.music.play()
                
                # Store path to temp file to delete later
                current_audio_temp_file = temp_wav_path

            except Exception as e:
                print('Audio playback failed:', e)
                current_audio_temp_file = None # No temp file to delete
        else:
            current_audio_temp_file = None


        start_time = pygame.time.get_ticks()
        score = 0
        max_health = 300
        health = max_health
        pygame.mouse.set_visible(not SETTINGS['custom_cursor']) # Set cursor based on setting
        running = True
        paused = False
        # Group hitobjects into sets of 1 (only one circle at a time)
        sets = [[obj] for obj in hitobjects]
        set_index = 0
        current_set = sets[set_index] if sets else []
        next_circle_index = 0
        while running:
            now = pygame.time.get_ticks() - start_time
            current_width, current_height = screen.get_size()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                elif event.type == pygame.VIDEORESIZE:
                    SETTINGS['current_width'], SETTINGS['current_height'] = event.w, event.h
                    screen = pygame.display.set_mode((SETTINGS['current_width'], SETTINGS['current_height']), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    paused = True
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if (next_circle_index < len(current_set)):
                        obj = current_set[next_circle_index]
                        if not obj.hit and not obj.disappeared and obj.check_hit(event.pos, now):
                            # Calculate timing accuracy for scoring
                            t = abs(now - obj.time)
                            max_score = 300
                            min_score = 50
                            score_window = obj.hit_window
                            # Linear interpolation: closer = more points
                            points = int(max_score - (max_score - min_score) * (t / score_window))
                            points = max(min_score, min(points, max_score))
                            score += points
                            health = min(health + 10, max_health)
                            next_circle_index += 1
            
            if not running: # Check if QUIT event caused loop exit
                break

            if paused:
                pygame.mixer.music.pause()
                pause_result = pause_menu(screen, clock)
                if pause_result == 'Back to Menu':
                    running = False
                    break
                pygame.mixer.music.unpause()
                paused = False

            # Missed circles (only for current set)
            if not paused: # Only process misses if not paused
                for i, obj in enumerate(current_set):
                    if not obj.hit and obj.disappeared and not hasattr(obj, 'missed'):
                        health = max(health - 20, 0)
                        obj.missed = True
                        if i == next_circle_index: # Only advance if the current expected circle is missed
                            next_circle_index += 1

            screen.fill(BACKGROUND_COLOR)
            
            # Draw health bar (larger)
            health_bar_width = int(current_width * 0.5)
            health_bar_height = 32
            health_bar_x = current_width // 2 - health_bar_width // 2
            health_bar_y = 20

            pygame.draw.rect(screen, (60,60,60), (health_bar_x, health_bar_y, health_bar_width, health_bar_height), border_radius=16)
            
            # Health bar fill with gradient
            health_fill_width = int(health_bar_width * health / max_health)
            draw_rounded_gradient(screen, (health_bar_x, health_bar_y, health_fill_width, health_bar_height), (0,220,180), (0,150,120), radius=16, vertical=False)
            pygame.draw.rect(screen, (255,255,255), (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 3, border_radius=16)

            # Draw only current set
            for obj in current_set:
                obj.update(now)
                if not obj.hit and not obj.disappeared and obj.time - now < obj.approach_time:
                    # Shadow effect for hit circles
                    shadow_surf = pygame.Surface((CIRCLE_RADIUS*2 + 8, CIRCLE_RADIUS*2 + 8), pygame.SRCALPHA)
                    pygame.draw.circle(shadow_surf, (0,0,0,60), (CIRCLE_RADIUS+4, CIRCLE_RADIUS+4), CIRCLE_RADIUS+4) # Circle for shadow
                    screen.blit(shadow_surf, (obj.pos[0]-CIRCLE_RADIUS-4+4, obj.pos[1]-CIRCLE_RADIUS-4+4)) # Adjust for shadow offset
                obj.draw(screen, now)
            
            score_text = font.render(f'Score: {score}', True, (255,255,255))
            screen.blit(score_text, (10, 10))
            
            # Custom cursor with glow
            if SETTINGS['custom_cursor']: # Use the setting here
                mx, my = pygame.mouse.get_pos()
                for r in range(20, 8, -2):
                    pygame.draw.circle(screen, (0,180,255,30), (mx, my), r, 2)
                pygame.draw.circle(screen, (255,255,255), (mx, my), 16, 2)
            pygame.display.flip()
            clock.tick(FPS)
            
            # Check if set is done
            if next_circle_index >= len(current_set) and not paused: # Only advance if not paused
                set_index += 1
                if set_index < len(sets):
                    current_set = sets[set_index]
                    next_circle_index = 0
                else:
                    # All sets done
                    pygame.mixer.music.stop()
                    pygame.time.wait(500)
                    if current_audio_temp_file and os.path.exists(current_audio_temp_file):
                        os.remove(current_audio_temp_file)
                    result = level_cleared_screen(screen, clock, score, map_name)
                    if result == 'Retry':
                        # Restart this map from the beginning
                        set_index = 0
                        current_set = sets[set_index]
                        next_circle_index = 0
                        score = 0
                        health = max_health
                        start_time = pygame.time.get_ticks()
                        for obj in hitobjects:
                            obj.hit = False
                            obj.disappeared = False
                            if hasattr(obj, 'missed'):
                                del obj.missed
                        if audio_path and os.path.exists(audio_path):
                            try:
                                pygame.mixer.music.load(temp_wav_path if current_audio_temp_file else audio_path)
                                pygame.mixer.music.play()
                            except Exception as e:
                                print('Audio restart failed:', e)
                        continue
                    else:
                        running = False
            
            if health <= 0 and not paused: # Only fail if not paused
                pygame.mixer.music.stop()
                pygame.time.wait(500)
                if current_audio_temp_file and os.path.exists(current_audio_temp_file):
                    os.remove(current_audio_temp_file)
                result = level_failed_screen(screen, clock, score, map_name)
                if result == 'Retry':
                    # Restart this map from the beginning
                    set_index = 0
                    current_set = sets[set_index]
                    next_circle_index = 0
                    score = 0
                    health = max_health
                    start_time = pygame.time.get_ticks()
                    for obj in hitobjects:
                        obj.hit = False
                        obj.disappeared = False
                        if hasattr(obj, 'missed'):
                            del obj.missed
                    if audio_path and os.path.exists(audio_path):
                        try:
                            pygame.mixer.music.load(temp_wav_path if current_audio_temp_file else audio_path)
                            pygame.mixer.music.play()
                        except Exception as e:
                            print('Audio restart failed:', e)
                    continue
                else:
                    running = False
        
        # Clean up temporary audio file if it exists
        if current_audio_temp_file and os.path.exists(current_audio_temp_file):
            try:
                os.remove(current_audio_temp_file)
            except OSError as e:
                print(f"Error removing temporary audio file {current_audio_temp_file}: {e}")

        pygame.mouse.set_visible(True) # Ensure cursor is visible when returning to main menu

if __name__ == '__main__':
    main()
