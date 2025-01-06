
from pystray import Icon, Menu, MenuItem
from PIL import Image
import threading
from screeninfo import get_monitors
from pynput.mouse import Controller
import random
import pygame
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QMovie
import time

app = QApplication(sys.argv)
alive = True


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


def kill():
    global alive
    alive = False


def create_tray_icon():
    image = Image.open("trayico.png")
    icon = Icon("TkinterApp", image, menu=Menu(
        MenuItem("Exit", kill, default=True)
    ))
    icon.run()


def run_tray_icon_in_thread():
    tray_thread = threading.Thread(target=create_tray_icon)
    tray_thread.daemon = True
    tray_thread.start()


def get_current_screen(monitors, mouse_position):
    for i, m in enumerate(monitors):
        if (mouse_position[0] >= m.x and mouse_position[0]-m.x <= m.width and mouse_position[1] >= m.y and mouse_position[1]-m.y <= m.height):
            return i
    return 0


class WorkerThread(QThread):
    def __init__(self, portals, image):
        super().__init__()
        self.portals = portals
        self.image = image

    def show_all(self):
        self.portals[0].show()
        self.portals[1].show()

    def hide_all(self):
        self.portals[0].hide()
        self.portals[1].hide()

    def run(self):
        global alive, app

        timestamp = time.time()
        mouse = Controller()
        last_pos = mouse.position
        last_screen = 0
        monitors = get_monitors()
        width, height = self.image.size
        half_height = int(height/2)

        while alive:
            if timestamp and time.time() * 1000 > timestamp + 600:
                timestamp = None
                self.hide_all()
            flag = mouse.position[0] == last_pos[0] and mouse.position[1] == last_pos[1]
            if (flag):
                continue
            screen_index = get_current_screen(monitors, mouse.position)
            last_pos = mouse.position
            if (screen_index != last_screen):
                timestamp = time.time() * 1000
                self.show_all()
                play_portal_enter()
                #
                if (last_pos[0] >= monitors[last_screen].x + monitors[last_screen].width):
                    self.portals[0].move(monitors[last_screen].width -
                                         width, last_pos[1] - half_height)
                    time.sleep(0.02)
                    self.portals[1].move(monitors[screen_index].x,
                                         last_pos[1] - half_height)
                else:
                    self.portals[0].move(monitors[screen_index].width -
                                         width, last_pos[1] - half_height)
                    time.sleep(0.02)
                    self.portals[1].move(monitors[last_screen].x,
                                         last_pos[1] - half_height)
                last_screen = screen_index
        app.quit()


class TransparentAnimatedGIFWindow(QWidget):
    def __init__(self, gif_path):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint |
                            Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        try:
            movie = QMovie(gif_path)
            if not movie.isValid():
                raise Exception("Не удалось загрузить GIF")
        except Exception as e:
            print(f"Ошибка загрузки GIF: {e}")
            sys.exit(1)

        self.movie_label = QLabel(self)
        self.movie_label.setMovie(movie)
        movie.start()
        movie_size = movie.frameRect().size()
        self.movie_label.setGeometry(
            0, 0, movie_size.width(), movie_size.height())
        self.setGeometry(300, 300, movie_size.width(), movie_size.height())


if __name__ == "__main__":
    portal = TransparentAnimatedGIFWindow("portal.gif")
    portal2 = TransparentAnimatedGIFWindow("portal2.gif")
    run_tray_icon_in_thread()
    worker_thread = WorkerThread([portal, portal2], Image.open("portal.gif"))
    worker_thread.start()
    sys.exit(app.exec_())
