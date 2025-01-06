import tkinter as tk
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageTk
import threading
from screeninfo import get_monitors
from pynput.mouse import Controller
import random
import pygame


def play_sound_with_volume(file_path, volume):
    pygame.mixer.init()
    try:
        sound = pygame.mixer.Sound(file_path)
        sound.set_volume(volume)
        sound.play()
        while pygame.mixer.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"Ошибка проигрывания звука: {e}")


def play_portal_enter():
    i = random.randint(1, 2)
    sound = threading.Thread(
        target=play_sound_with_volume, args=(f"portal_enter{i}.wav", 0.1,))
    sound.daemon = True
    sound.start()


def create_tray_icon(window):
    image = Image.open("trayico.png")
    icon = Icon("TkinterApp", image, menu=Menu(
        MenuItem("Exit", lambda: window.destroy(), default=True)
    ))
    icon.run()


def get_current_screen(monitors, mouse_position):
    for i, m in enumerate(monitors):
        if (mouse_position[0] >= m.x and mouse_position[0]-m.x <= m.width and mouse_position[1] >= m.y and mouse_position[1]-m.y <= m.height):
            return i
    return 0


def mouse_move(portals, image):
    after_id = None
    mouse = Controller()
    last_pos = mouse.position
    last_screen = 0
    monitors = get_monitors()
    width, height = image.size
    half_height = int(height/2)
    half_width = int(width/2)

    def show_all():
        portals[0].deiconify()
        portals[1].deiconify()

    def hide_all():
        portals[0].withdraw()
        portals[1].withdraw()

    while True:
        flag = mouse.position[0] == last_pos[0] and mouse.position[1] == last_pos[1]
        if (flag):
            continue
        screen_index = get_current_screen(monitors, mouse.position)
        last_pos = mouse.position
        if (screen_index != last_screen):
            if after_id:
                portals[0].after_cancel(after_id)
            show_all()
            play_portal_enter()
            #
            after_id = portals[0].after(700, hide_all)
            #

            if (last_pos[0] >= monitors[last_screen].x + monitors[last_screen].width):
                portals[0].geometry(
                    f"+{monitors[last_screen].width - width}+{last_pos[1] - half_height}")
                portals[1].geometry(
                    f"+{monitors[screen_index].x}+{last_pos[1]- half_height}")
            else:
                portals[0].geometry(
                    f"+{monitors[screen_index].width - width}+{last_pos[1] - half_height}")
                portals[1].geometry(
                    f"+{monitors[last_screen].x}+{last_pos[1]- half_height}")
            last_screen = screen_index


def run_tray_icon_in_thread(window):
    tray_thread = threading.Thread(target=create_tray_icon, args=(window,))
    tray_thread.daemon = True
    tray_thread.start()


def run_mouse_move_thread(portals, image):
    mouse_thread = threading.Thread(target=mouse_move, args=(portals, image,))
    mouse_thread.daemon = True
    mouse_thread.start()


class AnimatedGIF(tk.Label):
    def __init__(self, master, path, **kwargs):
        tk.Label.__init__(self, master, **kwargs)
        try:
            self.frames = []
            self.image_object = Image.open(path)
            if not self.image_object.is_animated:
                raise Exception("Изображение не анимировано")
            for frame_number in range(self.image_object.n_frames):
                self.image_object.seek(frame_number)
                frame = self.image_object.copy()
                frame = frame.convert(
                    "RGBA") if frame.mode != "RGBA" else frame
                self.frames.append(ImageTk.PhotoImage(frame)
                                   )
            self.current_frame = 0
            self.animate_gif()
        except Exception as e:
            print(f"Ошибка: {e}")
            return

    def animate_gif(self):
        try:
            self.config(image=self.frames[self.current_frame])
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.after(self.image_object.info.get('duration', 100),
                       self.animate_gif)
        except Exception as e:
            print(f"Произошла ошибка {e}")


def start_second_portal(root, image_path):
    window = tk.Toplevel(root)
    window.attributes('-fullscreen', False)
    window.attributes('-transparentcolor', '#0078FF')
    window.attributes('-topmost', True)
    window.attributes('-toolwindow', True)
    window.overrideredirect(True)
    window.grab_set()
    #
    image = Image.open(image_path)
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    width, height = image.size
    window.geometry(f"{width}x{height}")
    #
    gif_widget = AnimatedGIF(window, path=image_path,  bg='#0078FF')
    gif_widget.pack()
    return window


def start_portal_window(image_path, image_path2):
    window = tk.Tk()
    window.attributes('-fullscreen', False)
    window.attributes('-transparentcolor', '#BC4B00')
    window.attributes('-topmost', True)
    window.attributes('-toolwindow', True)
    window.overrideredirect(True)
    #
    image = Image.open(image_path)
    width, height = image.size
    window.geometry(f"{width}x{height}")
    #
    gif_widget = AnimatedGIF(window, path=image_path,  bg='#BC4B00')
    gif_widget.pack()
    #
    run_tray_icon_in_thread(window)
    p2 = start_second_portal(window, image_path2)
    run_mouse_move_thread([window, p2], image)
    p2.withdraw()
    window.withdraw()
    window.mainloop()


def start_portal_daemon(portal):
    portal_thread = threading.Thread(target=lambda: portal.mainloop())
    portal_thread.daemon = True
    portal_thread.start()


if __name__ == '__main__':
    start_portal_window("portal.gif", "portal2.gif")
