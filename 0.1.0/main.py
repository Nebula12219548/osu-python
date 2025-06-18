import pygame
import sys
import math
import random
import os

# Constants
WIDTH, HEIGHT = 800, 600
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

    def check_hit(self, mouse_pos, now):
        t = abs(now - self.time)
        if t < self.hit_window and not self.disappeared:
            dx = mouse_pos[0] - self.pos[0]
            dy = mouse_pos[1] - self.pos[1]
            if math.hypot(dx, dy) < CIRCLE_RADIUS:
                self.hit = True
                return True
        return False

    def update(self, now):
        if not self.hit and not self.disappeared:
            if now > self.time + self.hit_window:
                self.disappeared = True

def generate_hitobjects(count):
    hitobjects = []
    t = 1000
    for i in range(count):
        x = random.randint(CIRCLE_RADIUS + 10, WIDTH - CIRCLE_RADIUS - 10)
        y = random.randint(CIRCLE_RADIUS + 10, HEIGHT - CIRCLE_RADIUS - 10)
        hitobjects.append(HitObject((x, y), t, i+1))
        t += 800
    return hitobjects

def load_map(filepath):
    import zipfile
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
        draw_gradient_rect(screen, (0, 0, WIDTH, HEIGHT), (30, 60, 120), (10, 10, 40), vertical=True)
        title = font_big.render('About osu!python', True, (0, 180, 255))
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
        screen.blit(title, title_rect)
        lines = [
            'osu!python is a osu! clone by Nebula12219548',
            'Inspired by osu! (ppy)',
            'For educational and fun purposes only.',
            'Version: v0.1.0',
            '',
            'Press any key or click to return.'
        ]
        for i, line in enumerate(lines):
            text = font_small.render(line, True, (255,255,255))
            rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 + i*40 - 20))
            screen.blit(text, rect)
        version_text = version_font.render('v0.1.0', True, (180, 180, 180))
        version_rect = version_text.get_rect(bottomright=(WIDTH-10, HEIGHT-10))
        screen.blit(version_text, version_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                running = False
        clock.tick(FPS)

def settings_menu(screen, clock):
    font_big = pygame.font.SysFont('Arial', 54, bold=True)
    font_small = pygame.font.SysFont('Arial', 32)
    version_font = pygame.font.SysFont('Arial', 24)
    running = True
    while running:
        draw_gradient_rect(screen, (0, 0, WIDTH, HEIGHT), (30, 60, 120), (10, 10, 40), vertical=True)
        title = font_big.render('Settings', True, (0, 180, 255))
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
        screen.blit(title, title_rect)
        lines = [
            'Settings will be added in v0.2.0.',
            '',
            'Press any key or click to return.'
        ]
        for i, line in enumerate(lines):
            text = font_small.render(line, True, (255,255,255))
            rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 + i*40 - 20))
            screen.blit(text, rect)
        version_text = version_font.render('v0.1.0', True, (180, 180, 180))
        version_rect = version_text.get_rect(bottomright=(WIDTH-10, HEIGHT-10))
        screen.blit(version_text, version_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                running = False
        clock.tick(FPS)

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
        draw_gradient_rect(screen, (0, 0, WIDTH, HEIGHT), (30, 60, 120), (10, 10, 40), vertical=True)
        title = font_big.render('Tutorial', True, (0, 180, 255))
        title_rect = title.get_rect(center=(WIDTH//2, 120))
        screen.blit(title, title_rect)
        for i, line in enumerate(instructions):
            text = font_small.render(line, True, (255,255,255))
            rect = text.get_rect(center=(WIDTH//2, 220 + i*40))
            screen.blit(text, rect)
        version_text = version_font.render('v0.1.0', True, (180, 180, 180))
        version_rect = version_text.get_rect(bottomright=(WIDTH-10, HEIGHT-10))
        screen.blit(version_text, version_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
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
    # Hardcoded demo hitobjects
    demo_hitobjects = [
        {'pos': (400, 300), 'time': 1000},
        {'pos': (600, 300), 'time': 2500},
        {'pos': (200, 300), 'time': 4000},
        {'pos': (400, 100), 'time': 5500},
        {'pos': (400, 500), 'time': 7000},
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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if current < len(demo_hitobjects):
                    obj = demo_hitobjects[current]
                    t = abs(now - obj['time'])
                    dx = event.pos[0] - obj['pos'][0]
                    dy = event.pos[1] - obj['pos'][1]
                    if t < hit_window and (dx*dx + dy*dy) < 50*50:
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
        draw_gradient_rect(screen, (0, 0, WIDTH, HEIGHT), (30, 60, 120), (10, 10, 40), vertical=True)
        # Health bar
        pygame.draw.rect(screen, (60,60,60), (WIDTH//2-200, 20, 400, 32), border_radius=16)
        pygame.draw.rect(screen, (0,220,180), (WIDTH//2-200, 20, int(400*health/max_health), 32), border_radius=16)
        pygame.draw.rect(screen, (255,255,255), (WIDTH//2-200, 20, 400, 32), 3, border_radius=16)
        # Draw hit circles
        for i, obj in enumerate(demo_hitobjects):
            t = obj['time'] - now
            approach = max(1.0, min(2.5, t / approach_time + 1))
            if not clicked[i] and t < approach_time and now < obj['time'] + hit_window:
                # Shadow
                shadow_surf = pygame.Surface((108, 108), pygame.SRCALPHA)
                pygame.draw.circle(shadow_surf, (0,0,0,60), (54,54), 54)
                screen.blit(shadow_surf, (obj['pos'][0]-54+4, obj['pos'][1]-54+4))
                # Approach
                pygame.draw.circle(screen, (100, 200, 255), obj['pos'], int(50 * approach), 2)
                # Main
                pygame.draw.circle(screen, (0, 180, 255), obj['pos'], 50)
                pygame.draw.circle(screen, (255, 255, 255), obj['pos'], 50, 6)
                text = font.render(str(i+1), True, (255,255,255))
                rect = text.get_rect(center=obj['pos'])
                screen.blit(text, rect)
        # Score
        score_text = font.render(f'Score: {score}', True, (255,255,255))
        screen.blit(score_text, (10, 10))
        # Instructions
        if current < len(demo_hitobjects):
            inst = font.render('Click the circle!', True, (255,255,0))
            screen.blit(inst, (WIDTH//2-100, HEIGHT-60))
        else:
            inst = font.render('Tutorial Complete! Press any key or click.', True, (0,255,100))
            screen.blit(inst, (WIDTH//2-200, HEIGHT-60))
        pygame.display.flip()
        clock.tick(FPS)
        if current >= len(demo_hitobjects):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    running = False

def main_menu(screen, clock):
    font_big = pygame.font.SysFont('Arial', 72, bold=True)
    font_small = pygame.font.SysFont('Arial', 40)
    version_font = pygame.font.SysFont('Arial', 24)
    menu_running = True
    pulse = 0
    buttons = ['Start', 'Tutorial', 'Settings', 'About']
    selected = 0
    while menu_running:
        draw_gradient_rect(screen, (0, 0, WIDTH, HEIGHT), (30, 60, 120), (10, 10, 40), vertical=True)
        pulse = (pulse + 1) % 120
        scale = 1.05 + 0.05 * (abs(60 - pulse) / 60)
        title = font_big.render('osu!python', True, (0, 180, 255))
        title = pygame.transform.rotozoom(title, 0, scale)
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 120))
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
            btn_rect = btn_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 40 + i*70))
            # Smooth rounded gradient button
            btn_c1 = (0, 180, 255) if i == selected else (60,60,60)
            btn_c2 = (0, 120, 200) if i == selected else (40,40,40)
            draw_rounded_gradient(screen, btn_rect.inflate(60, 24), btn_c1, btn_c2, radius=16, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), btn_rect.inflate(60, 24), 3, border_radius=16)
            screen.blit(btn_text, btn_rect)
        version_text = version_font.render('v0.1.0', True, (180, 180, 180))
        version_rect = version_text.get_rect(bottomright=(WIDTH-10, HEIGHT-10))
        screen.blit(version_text, version_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
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
                        settings_menu(screen, clock)
                    elif buttons[selected] == 'Tutorial':
                        tutorial_screen(screen, clock)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, label in enumerate(buttons):
                    btn_text = font_small.render(label, True, (255,255,255))
                    btn_rect = btn_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 40 + i*70))
                    if btn_rect.inflate(60, 24).collidepoint(event.pos):
                        if label == 'Start':
                            menu_running = False
                        elif label == 'About':
                            about_screen(screen, clock)
                        elif label == 'Settings':
                            settings_menu(screen, clock)
                        elif label == 'Tutorial':
                            tutorial_screen(screen, clock)
        clock.tick(FPS)

def maps_menu(screen, clock):
    font_big = pygame.font.SysFont('Arial', 48, bold=True)
    font_small = pygame.font.SysFont('Arial', 32)
    version_font = pygame.font.SysFont('Arial', 24)
    maps_dir = os.path.join(os.path.dirname(__file__), 'maps')
    maps = [f for f in os.listdir(maps_dir) if f.endswith('.osz')]
    selected = 0
    menu_running = True
    while menu_running:
        t = pygame.time.get_ticks() / 1000.0
        c1 = (20, int(40+20*abs(pygame.math.Vector2(1,0).rotate(t*30).x)), 80)
        c2 = (40, 10, int(60+20*abs(pygame.math.Vector2(0,1).rotate(t*30).y)))
        draw_gradient_rect(screen, (0, 0, WIDTH, HEIGHT), c1, c2, vertical=True)
        title = font_big.render('Select Map', True, (0, 180, 255))
        title_rect = title.get_rect(center=(WIDTH//2, 80))
        screen.blit(title, title_rect)
        for i, m in enumerate(maps):
            color = (255,255,0) if i == selected else (255,255,255)
            text = font_small.render(m, True, color)
            rect = text.get_rect(center=(WIDTH//2, 180 + i*50))
            btn_c1 = (0, 180, 255) if i == selected else (60,60,60)
            btn_c2 = (0, 120, 200) if i == selected else (40,40,40)
            draw_rounded_gradient(screen, rect.inflate(40, 10), btn_c1, btn_c2, radius=12, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), rect.inflate(40, 10), 2, border_radius=12)
            screen.blit(text, rect)
        version_text = version_font.render('v0.1.0', True, (180, 180, 180))
        version_rect = version_text.get_rect(bottomright=(WIDTH-10, HEIGHT-10))
        screen.blit(version_text, version_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(maps)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(maps)
                elif event.key == pygame.K_RETURN:
                    return os.path.join(maps_dir, maps[selected])
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, m in enumerate(maps):
                    text = font_small.render(m, True, (255,255,255))
                    rect = text.get_rect(center=(WIDTH//2, 180 + i*50))
                    if rect.collidepoint(event.pos):
                        return os.path.join(maps_dir, m)
        clock.tick(FPS)

def level_cleared_screen(screen, clock, score, map_name):
    font_big = pygame.font.SysFont('Arial', 64, bold=True)
    font_small = pygame.font.SysFont('Arial', 36)
    version_font = pygame.font.SysFont('Arial', 24)
    running = True
    selected = 0
    options = ['Retry', 'Back to Menu']
    while running:
        t = pygame.time.get_ticks() / 1000.0
        c1 = (30, int(80+20*abs(pygame.math.Vector2(1,0).rotate(t*30).x)), 40)
        c2 = (10, int(30+20*abs(pygame.math.Vector2(0,1).rotate(t*30).y)), 10)
        draw_gradient_rect(screen, (0, 0, WIDTH, HEIGHT), c1, c2, vertical=True)
        title = font_big.render('Level Cleared!', True, (0, 255, 100))
        score_text = font_small.render(f'Score: {score}', True, (255,255,255))
        map_text = font_small.render(f'Map: {map_name}', True, (0,180,255))
        version_text = version_font.render('v0.1.0', True, (180, 180, 180))
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 120))
        score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 40))
        map_rect = map_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 10))
        version_rect = version_text.get_rect(bottomright=(WIDTH-10, HEIGHT-10))
        screen.blit(title, title_rect)
        screen.blit(score_text, score_rect)
        screen.blit(map_text, map_rect)
        screen.blit(version_text, version_rect)
        for i, opt in enumerate(options):
            color = (255,255,0) if i == selected else (255,255,255)
            opt_text = font_small.render(opt, True, color)
            opt_rect = opt_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 80 + i*50))
            btn_c1 = (0, 180, 255) if i == selected else (60,60,60)
            btn_c2 = (0, 120, 200) if i == selected else (40,40,40)
            draw_rounded_gradient(screen, opt_rect.inflate(40, 10), btn_c1, btn_c2, radius=12, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), opt_rect.inflate(40, 10), 2, border_radius=12)
            screen.blit(opt_text, opt_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
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
                    opt_rect = opt_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 80 + i*50))
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
        t = pygame.time.get_ticks() / 1000.0
        c1 = (int(80+20*abs(pygame.math.Vector2(1,0).rotate(t*30).x)), 30, 30)
        c2 = (int(30+20*abs(pygame.math.Vector2(0,1).rotate(t*30).y)), 10, 10)
        draw_gradient_rect(screen, (0, 0, WIDTH, HEIGHT), c1, c2, vertical=True)
        title = font_big.render('Level Failed!', True, (255, 60, 60))
        score_text = font_small.render(f'Score: {score}', True, (255,255,255))
        map_text = font_small.render(f'Map: {map_name}', True, (0,180,255))
        version_text = version_font.render('v0.1.0', True, (180, 180, 180))
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 120))
        score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 40))
        map_rect = map_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 10))
        version_rect = version_text.get_rect(bottomright=(WIDTH-10, HEIGHT-10))
        screen.blit(title, title_rect)
        screen.blit(score_text, score_rect)
        screen.blit(map_text, map_rect)
        screen.blit(version_text, version_rect)
        for i, opt in enumerate(options):
            color = (255,255,0) if i == selected else (255,255,255)
            opt_text = font_small.render(opt, True, color)
            opt_rect = opt_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 80 + i*50))
            btn_c1 = (255,60,60) if i == selected else (60,60,60)
            btn_c2 = (200,40,40) if i == selected else (40,40,40)
            draw_rounded_gradient(screen, opt_rect.inflate(40, 10), btn_c1, btn_c2, radius=12, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), opt_rect.inflate(40, 10), 2, border_radius=12)
            screen.blit(opt_text, opt_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
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
                    opt_rect = opt_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 80 + i*50))
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
        t = pygame.time.get_ticks() / 1000.0
        c1 = (40, 40, int(60+20*abs(pygame.math.Vector2(1,0).rotate(t*30).x)))
        c2 = (10, 10, int(30+20*abs(pygame.math.Vector2(0,1).rotate(t*30).y)))
        draw_gradient_rect(screen, (0, 0, WIDTH, HEIGHT), c1, c2, vertical=True)
        title = font_big.render('Paused', True, (0, 180, 255))
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))
        screen.blit(title, title_rect)
        for i, opt in enumerate(options):
            color = (255,255,0) if i == selected else (255,255,255)
            opt_text = font_small.render(opt, True, color)
            opt_rect = opt_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 40 + i*50))
            btn_c1 = (0, 180, 255) if i == selected else (60,60,60)
            btn_c2 = (0, 120, 200) if i == selected else (40,40,40)
            draw_rounded_gradient(screen, opt_rect.inflate(40, 10), btn_c1, btn_c2, radius=16, vertical=False)
            pygame.draw.rect(screen, (255,255,255,180), opt_rect.inflate(40, 10), 2, border_radius=16)
            screen.blit(opt_text, opt_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
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
                    opt_rect = opt_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 40 + i*50))
                    if opt_rect.collidepoint(event.pos):
                        return options[i]
        clock.tick(FPS)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('osu!python v0.1.0')
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 24)
    while True:
        main_menu(screen, clock)
        map_path = maps_menu(screen, clock)
        hitobjects, map_name = load_map(map_path)
        # Audio support (fix: always extract and use a temp file for all formats)
        audio_file = None
        audio_path = None
        import tempfile
        import shutil
        if map_path.endswith('.osz'):
            import zipfile
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
            audio_path = None
        if audio_path and os.path.exists(audio_path):
            try:
                import soundfile as sf
                import numpy as np
                import scipy.io.wavfile
                ext = os.path.splitext(audio_path)[1].lower()
                if ext not in ['.wav', '.ogg']:
                    y, sr = sf.read(audio_path, dtype='float32')
                    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                    y16 = np.int16(y/np.max(np.abs(y)) * 32767)
                    scipy.io.wavfile.write(temp_wav.name, sr, y16)
                    audio_path = temp_wav.name
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
            except Exception as e:
                print('Audio playback failed:', e)
        start_time = pygame.time.get_ticks()
        score = 0
        max_health = 300
        health = max_health
        custom_cursor = True
        pygame.mouse.set_visible(False)
        running = True
        paused = False
        # Group hitobjects into sets of 1 (only one circle at a time)
        sets = [[obj] for obj in hitobjects]
        set_index = 0
        current_set = sets[set_index] if sets else []
        next_circle_index = 0
        while running:
            now = pygame.time.get_ticks() - start_time
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
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
            if paused:
                pygame.mixer.music.pause()
                pause_result = pause_menu(screen, clock)
                if pause_result == 'Back to Menu':
                    running = False
                    break
                pygame.mixer.music.unpause()
                paused = False
            # Missed circles (only for current set)
            for i, obj in enumerate(current_set):
                if not obj.hit and obj.disappeared and not hasattr(obj, 'missed'):
                    health = max(health - 20, 0)
                    obj.missed = True
                    if i == next_circle_index:
                        next_circle_index += 1
            screen.fill(BACKGROUND_COLOR)
            # Draw health bar (larger)
            pygame.draw.rect(screen, (60,60,60), (WIDTH//2-200, 20, 400, 32), border_radius=16)
            pygame.draw.rect(screen, (0,220,180), (WIDTH//2-200, 20, int(400*health/max_health), 32), border_radius=16)
            pygame.draw.rect(screen, (255,255,255), (WIDTH//2-200, 20, 400, 32), 3, border_radius=16)
            # Draw only current set
            for obj in current_set:
                obj.update(now)
                if not obj.hit and not obj.disappeared and obj.time - now < obj.approach_time:
                    shadow_surf = pygame.Surface((108, 108), pygame.SRCALPHA)
                    pygame.draw.circle(shadow_surf, (0,0,0,60), (54,54), 54)
                    screen.blit(shadow_surf, (obj.pos[0]-54+4, obj.pos[1]-54+4))
                obj.draw(screen, now)
            score_text = font.render(f'Score: {score}', True, (255,255,255))
            screen.blit(score_text, (10, 10))
            # Custom cursor with glow
            if custom_cursor:
                mx, my = pygame.mouse.get_pos()
                for r in range(20, 8, -2):
                    pygame.draw.circle(screen, (0,180,255,30), (mx, my), r, 2)
                pygame.draw.circle(screen, (255,255,255), (mx, my), 16, 2)
            pygame.display.flip()
            clock.tick(FPS)
            # Check if set is done
            if next_circle_index >= len(current_set):
                set_index += 1
                if set_index < len(sets):
                    current_set = sets[set_index]
                    next_circle_index = 0
                else:
                    # All sets done
                    pygame.mixer.music.stop()
                    pygame.time.wait(500)
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
                        pygame.mixer.music.rewind()
                        pygame.mixer.music.play()
                        continue
                    else:
                        running = False
            if health <= 0:
                pygame.mixer.music.stop()
                pygame.time.wait(500)
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
                    pygame.mixer.music.rewind()
                    pygame.mixer.music.play()
                    continue
                else:
                    running = False
        pygame.mouse.set_visible(True)

if __name__ == '__main__':
    main()
