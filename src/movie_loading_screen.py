from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QRect
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import  QLabel, QDialog
from PyQt5.QtCore import Qt

from src.app_module import icon_folder
from src.tmdb import find_movie_id


class FindMovieThread(QThread):
    finished = pyqtSignal(object)

    def __init__(self, current_movie, is_detail, is_add):
        super().__init__()
        self.current_movie = current_movie
        self.is_add = is_add
        self.is_detail = is_detail
        self.num_point = 0

    def run(self):
        movie_data = self.find_movie_id(self.current_movie, self.is_detail, self.is_add)
        self.finished.emit(movie_data)

    def find_movie_id(self, current_movie, is_detail, is_add):
        movie_data = find_movie_id(current_movie, is_add = is_add, is_detail = is_detail)
        return movie_data


class MovieLoadingScreen(QDialog):
    def __init__(self,current_movie, is_detail = False, is_add = False):
        super().__init__()

        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.movie_data = None

        self.setWindowTitle("Movie Finder")

        self.find_movie_thread = FindMovieThread(current_movie, is_detail, is_add)
        self.find_movie_thread.finished.connect(self.on_movie_found)

        self.init_ui()

        self.find_movie_thread.start()



    def update_label(self):
        self.find_movie_thread.num_point = (self.find_movie_thread.num_point + 1) % 4
        text = f"{self.find_movie_thread.num_point * '.'}{(4 - self.find_movie_thread.num_point) * ' '}"
        self.info_label.setText(f"Lütfen bekleyiniz {text}")

    def on_movie_found(self, movie_data):
        self.timer.stop()

        self.movie_data = movie_data

        self.info_label.setText(f"Başarıyla tamamlandı!")

        QTimer.singleShot(1000, self.close)

    def init_ui(self):
        x,y = 400, 117
        background = QLabel(self)
        background.setPixmap(QPixmap(icon_folder+"waiting_screen.png"))
        background.setGeometry(0,0,x,y)

        self.info_label = QLabel("Lütfen bekleyiniz...", self)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 30px; background-color: transparent; color: black;")
        self.info_label.setGeometry(QRect(x//40, y//3, 400,50))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_label)
        self.timer.start(350)


        self.setWindowIcon(QIcon(icon_folder+"waiting_screen_icon.png"))

        self.setFixedSize(x,y)