from PIL import Image
import threading
from screeninfo import get_monitors
from pynput.mouse import Controller
import random
import pygame
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QSystemTrayIcon, QMenu
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QMovie, QIcon
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
    global app
    trayIcon = QSystemTrayIcon(QIcon("trayico.png"), parent=app)
    trayIcon.setToolTip("Screen Portals")
    menu = QMenu()
    menu.addAction("Quit", kill)
    trayIcon.setContextMenu(menu)
    trayIcon.show()


def get_current_screen(monitors, mouse_position):
    for i, m in enumerate(monitors):
        if (mouse_position[0] >= m.x and mouse_position[0]-m.x <= m.width and mouse_position[1] >= m.y and mouse_position[1]-m.y <= m.height):
            return i
    return 0


class WorkerThread(QThread):
    def __init__(self, portals):
        super().__init__()
        self.portals = portals
        self.image = portals[0].image_v

    def show_all(self):
        self.portals[0].show()
        self.portals[1].show()

    def hide_all(self):
        self.portals[0].hide()
        self.portals[1].hide()
        
    def set_vertical(self, flag):
        self.portals[0].set_vertical(flag)
        time.sleep(0.02)
        self.portals[1].set_vertical(flag)

    def run(self):
        global alive, app

        timestamp = time.time()
        mouse = Controller()
        last_pos = mouse.position
        last_screen = 0
        monitors = get_monitors()
        print(monitors)
        width, height = self.image.size
        half_height = int(height/2)
        half_width = half_height # Для горизонтали

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
                time.sleep(0.02)
                if (monitors[screen_index].x >= monitors[last_screen].x + monitors[last_screen].width):
                    # Текущий справа
                    self.set_vertical(True)
                    self.portals[0].move(monitors[last_screen].x + monitors[last_screen].width - width, last_pos[1] - half_height)
                    time.sleep(0.02)
                    self.portals[1].move(monitors[screen_index].x, last_pos[1] - half_height)
                    
                elif (monitors[last_screen].x >= monitors[screen_index].x + monitors[screen_index].width):
                    # Текущий слева
                    self.set_vertical(True)
                    self.portals[0].move(monitors[screen_index].x + monitors[screen_index].width - width, last_pos[1] - half_height)
                    time.sleep(0.02)
                    self.portals[1].move(monitors[last_screen].x,  last_pos[1] - half_height)
                    
                if (monitors[last_screen].y >= monitors[screen_index].y + monitors[screen_index].height):
                    # Текущий сверху
                    self.set_vertical(False)
                    # width == height_h
                    self.portals[0].move(last_pos[0] - half_width, monitors[screen_index].y + monitors[screen_index].height - width)
                    time.sleep(0.02)
                    self.portals[1].move(last_pos[0] - half_width, monitors[last_screen].y)
                    
                elif (monitors[screen_index].y >= monitors[last_screen].y + monitors[last_screen].height):
                    # Текущий снизу
                    self.set_vertical(False)
                    # width == height_h
                    self.portals[0].move(last_pos[0] - half_width, monitors[last_screen].y + monitors[last_screen].height - width)
                    time.sleep(0.02)
                    self.portals[1].move(last_pos[0] - half_width, monitors[screen_index].y)
                    
                last_screen = screen_index   
        app.quit()


def load_gif(gif_path):
    try:
        movie = QMovie(gif_path)
        if not movie.isValid():
            raise Exception(f"Не удалось загрузить GIF '{gif_path}'")
        return movie
    except Exception as e:
        print(f"Ошибка загрузки GIF: {e}")
        sys.exit(1)


class TransparentAnimatedGIFWindow(QWidget):
    def __init__(self, gif_path):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint |
                            Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        gif_v = gif_path + "_v.gif"
        gif_h = gif_path + "_h.gif"
        self.image_v = Image.open(gif_v)
        self.image_h = Image.open(gif_h)
        self.movie_v = load_gif(gif_v)
        self.movie_h = load_gif(gif_h)
        
        self.movie_label_v = QLabel(self)
        self.movie_label_v.setMovie(self.movie_v)
        self.movie_v.start()
        movie_size = self.movie_v.frameRect().size()
        self.movie_label_v.setGeometry(0, 0, movie_size.width(), movie_size.height())
        
        self.movie_label_h = QLabel(self)
        self.movie_label_h.setMovie(self.movie_h)
        self.movie_h.start()
        movie_size = self.movie_h.frameRect().size()
        self.movie_label_h.setGeometry(0, 0, movie_size.width(), movie_size.height())
        
        self.vertical = False
        self.set_vertical(True)

    def set_vertical(self, flag):
        if (self.vertical == flag):
            return
        self.vertical = flag
        movie = self.movie_v if flag else self.movie_h
        movie_size = movie.frameRect().size()
        self.setGeometry(0, 0, movie_size.width(), movie_size.height())
        if (self.vertical):
            self.movie_label_v.show()
            self.movie_label_h.hide()
        else:
            self.movie_label_v.hide()
            self.movie_label_h.show()


if __name__ == "__main__":
    app.setWindowIcon(QIcon("trayico.png"))
    portal = TransparentAnimatedGIFWindow("portal")
    portal2 = TransparentAnimatedGIFWindow("portal2")
    create_tray_icon()
    worker_thread = WorkerThread([portal, portal2])
    worker_thread.start()
    sys.exit(app.exec_())
