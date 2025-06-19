import tkinter as tk
from tkinter import filedialog, messagebox
import zipfile
import os
import time
import librosa
import soundfile as sf
import threading
import pygame
import tempfile
import numpy as np

class OsuMapGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title('osu! Beatmap Generator v0.1.0')
        self.mp3_path = ''
        self.output_path = ''
        self.map_name = tk.StringVar()
        self.artist = tk.StringVar()
        self.creator = tk.StringVar()
        self.hitobjects = []
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.root, text='osu! Beatmap Generator', font=('Arial', 18, 'bold')).pack(pady=10)
        tk.Button(self.root, text='Select MP3', command=self.select_mp3).pack(pady=5)
        self.mp3_label = tk.Label(self.root, text='No MP3 selected')
        self.mp3_label.pack(pady=2)
        tk.Label(self.root, text='Map Name:').pack()
        tk.Entry(self.root, textvariable=self.map_name).pack()
        tk.Label(self.root, text='Artist:').pack()
        tk.Entry(self.root, textvariable=self.artist).pack()
        tk.Label(self.root, text='Creator:').pack()
        tk.Entry(self.root, textvariable=self.creator).pack()
        tk.Button(self.root, text='Add Hit Circle', command=self.add_hit_circle).pack(pady=5)
        tk.Button(self.root, text='Auto-Generate Hit Circles (Detect Beats)', command=self.auto_generate_circles).pack(pady=5)
        tk.Button(self.root, text='Export .osz', command=self.export_osz).pack(pady=10)
        tk.Button(self.root, text='Preview Map', command=self.preview_map).pack(pady=5)
        self.status = tk.Label(self.root, text='')
        self.status.pack(pady=2)

    def select_mp3(self):
        path = filedialog.askopenfilename(filetypes=[('Audio Files', '*.mp3 *.aac *.m4a')])
        if path:
            self.mp3_path = path
            self.mp3_label.config(text=os.path.basename(path))

    def add_hit_circle(self):
        # Simple dialog for hit circle
        win = tk.Toplevel(self.root)
        win.title('Add Hit Circle')
        tk.Label(win, text='X:').grid(row=0, column=0)
        tk.Label(win, text='Y:').grid(row=1, column=0)
        tk.Label(win, text='Time (ms):').grid(row=2, column=0)
        x_var = tk.StringVar()
        y_var = tk.StringVar()
        t_var = tk.StringVar()
        tk.Entry(win, textvariable=x_var).grid(row=0, column=1)
        tk.Entry(win, textvariable=y_var).grid(row=1, column=1)
        tk.Entry(win, textvariable=t_var).grid(row=2, column=1)
        def add():
            try:
                x = int(x_var.get())
                y = int(y_var.get())
                t = int(t_var.get())
                self.hitobjects.append((x, y, t))
                self.status.config(text=f'Added hit circle at ({x},{y}) @ {t}ms')
                win.destroy()
            except Exception:
                messagebox.showerror('Error', 'Invalid input!')
        tk.Button(win, text='Add', command=add).grid(row=3, column=0, columnspan=2)

    def auto_generate_circles(self):
        if not self.mp3_path:
            messagebox.showerror('Error', 'Please select an audio file first!')
            return
        try:
            y, sr = librosa.load(self.mp3_path, sr=None)
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            times = librosa.frames_to_time(beats, sr=sr)
            self.hitobjects.clear()
            # Spread circles across the playfield
            import random
            for i, t in enumerate(times):
                x = random.randint(100, 700)
                y_ = random.randint(100, 500)
                ms = int(t * 1000)
                self.hitobjects.append((x, y_, ms))
            self.status.config(text=f'Generated {len(self.hitobjects)} hit circles from beats')
        except Exception as e:
            messagebox.showerror('Error', f'Beat detection failed: {e}')

    def export_osz(self):
        if not self.mp3_path or not self.hitobjects or not self.map_name.get():
            messagebox.showerror('Error', 'Please select an MP3, enter map name, and add at least one hit circle.')
            return
        save_path = filedialog.asksaveasfilename(defaultextension='.osz', filetypes=[('osu! Beatmap Archive', '*.osz')])
        if not save_path:
            return
        osu_filename = f"{self.map_name.get().replace(' ', '_')}.osu"
        # Write .osu file content
        osu_content = self.generate_osu_file()
        try:
            with zipfile.ZipFile(save_path, 'w') as z:
                z.write(self.mp3_path, os.path.basename(self.mp3_path))
                z.writestr(osu_filename, osu_content)
            self.status.config(text=f'Exported {os.path.basename(save_path)}')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to export: {e}')

    def generate_osu_file(self):
        # Minimal .osu file for circles only
        lines = [
            'osu file format v14',
            '',
            '[General]',
            f'AudioFilename: {os.path.basename(self.mp3_path)}',
            'AudioLeadIn: 0',
            '',
            '[Metadata]',
            f'Title:{self.map_name.get()}',
            f'Artist:{self.artist.get()}',
            f'Creator:{self.creator.get()}',
            '',
            '[Difficulty]',
            'HPDrainRate:5',
            'CircleSize:4',
            'OverallDifficulty:5',
            'ApproachRate:5',
            '',
            '[HitObjects]'
        ]
        for x, y, t in self.hitobjects:
            lines.append(f'{x},{y},{t},1,0,0:0:0:0:')
        return '\n'.join(lines)

    def preview_map(self):
        if not self.mp3_path or not self.hitobjects:
            messagebox.showerror('Error', 'Please select an audio file and generate/add hit circles first!')
            return
        # Run preview in a separate thread to avoid blocking the GUI
        threading.Thread(target=self._run_preview, daemon=True).start()

    def _run_preview(self):
        pygame.init()
        WIDTH, HEIGHT = 800, 600
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('osu! Map Preview')
        font = pygame.font.SysFont('Arial', 24)
        clock = pygame.time.Clock()
        # Audio compatibility: convert to wav if needed
        audio_path = self.mp3_path
        ext = os.path.splitext(audio_path)[1].lower()
        temp_wav = None
        if ext not in ['.wav', '.ogg']:
            try:
                y, sr = sf.read(audio_path, dtype='float32')
                temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                import scipy.io.wavfile
                # Normalize and convert to int16 for wav
                y16 = np.int16(y/np.max(np.abs(y)) * 32767)
                scipy.io.wavfile.write(temp_wav.name, sr, y16)
                audio_path = temp_wav.name
            except Exception as e:
                print('Audio conversion failed:', e)
        try:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
        except Exception as e:
            print('Audio playback failed:', e)
        start_time = pygame.time.get_ticks()
        running = True
        hitobjects = list(self.hitobjects)
        while running:
            now = pygame.time.get_ticks() - start_time
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            screen.fill((30, 30, 30))
            for i, (x, y, t) in enumerate(hitobjects):
                if 0 <= t - now < 1200:
                    approach = max(1.0, min(2.5, (t - now) / 1200 + 1))
                    pygame.draw.circle(screen, (100, 200, 255), (x, y), int(50 * approach), 2)
                if abs(now - t) < 300:
                    pygame.draw.circle(screen, (0, 180, 255), (x, y), 50)
                    pygame.draw.circle(screen, (255, 255, 255), (x, y), 50, 6)
                    text = font.render(str(i+1), True, (255,255,255))
                    rect = text.get_rect(center=(x, y))
                    screen.blit(text, rect)
            pygame.display.flip()
            clock.tick(60)
            if not pygame.mixer.music.get_busy():
                running = False
        pygame.quit()
        if temp_wav:
            os.unlink(temp_wav.name)

def main():
    root = tk.Tk()
    app = OsuMapGenerator(root)
    root.mainloop()

if __name__ == '__main__':
    main()
