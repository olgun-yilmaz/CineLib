import os
from functools import partial
import cv2

import psycopg2
import tkinter as tk
from tkinter import filedialog

from src.movie_loading_screen import MovieLoadingScreen

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap, QTextCursor, QPainter
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, \
    QDialog, QTextEdit, QMessageBox

from src.app_module import icon_folder, get_features, cursor, conn, customize_widget


def go_to_movie_details(username, current_movie, window):
    try:
        details_table = f"MovieDetails_{username}"
        cursor.execute(f"SELECT * FROM {details_table} WHERE name = %s", (current_movie,))
        data = cursor.fetchone()
        platforms = data[1].split("|")
        similar_movies = data[2].split("|")
        similar_movies = similar_movies[:-1]
        s_movies = list()

        for similar_movie in similar_movies:
            name, year = similar_movie[:-6], similar_movie[-5:-1]
            name = name[:-1]
            year = year.replace("((","(")
            year = year.replace("))",")")
            s_movies.append((name, year))

        similar_movies = s_movies

        vote_count = data[3]
        overview = data[4]
        vote_average = data[5]

    except (TypeError,psycopg2.errors.UndefinedTable):
        conn.rollback()
        mls = MovieLoadingScreen(current_movie, is_detail = True)
        mls.exec_()
        movieData = mls.movie_data
        platforms = movieData.providers
        similar_movies = movieData.similar_movies
        vote_average = movieData.vote_average
        vote_count = movieData.vote_count
        overview = movieData.overview

        movieData = None


    movie_details = MovieDetails(username, current_movie,
                                 vote_average, vote_count, similar_movies, platforms, overview)

    window.close()
    movie_details.exec_()

    if movie_details.check_if_closed():
        if not isinstance(window, MovieDetails):
            window.show()


class MovieDetails(QDialog):
    def __init__(self,user_name,movie_name,vote_average,vote_count,similar_movies,platforms,overview):
        super().__init__()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.movie_table = f"Movies_{user_name}"
        self.details_table = f"MovieDetails_{user_name}"

        self.is_closed = False

        self.create_table()

        self.platforms = platforms
        self.vote_count = vote_count
        self.vote_average = vote_average
        self.similar_movies = similar_movies
        self.movie_overview = overview

        self.username = user_name

        self.movie_name = movie_name
        file_name = movie_name.lower().replace(' ', '_')

        self.poster_path = f"MoviePosters/{file_name}.jpg"

        if not os.path.isfile(self.poster_path):
            self.poster_path = "MoviePosters/no_movie.jpg"

        self.init_ui()
        self.save_data(movie_name, vote_count, vote_average)

    def closeEvent(self, event):
        self.is_closed = True
        event.accept()

    def paintEvent(self, event):
        pixmap = QPixmap(icon_folder+"details_background.jpg")
        painter = QPainter(self)

        painter.drawPixmap(0, 0, self.width(), self.height(), pixmap)
        painter.end()

    def check_if_closed(self):
        return self.is_closed

    def save_data(self,name,num_rating,imdb_rating):
        try:
            cursor.execute(f"INSERT INTO {self.details_table} (name,num_rating,imdb_rating,similar_movies,platforms,overview)"
                           f" VALUES (%s,%s,%s,%s,%s,%s)",
                           (name,num_rating,imdb_rating,self.all_similar_movies,self.all_platforms,self.movie_overview))
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            conn.rollback()

    def create_new_push_button(self, icon_name="edit_button", x=25, y=25):
        button = QPushButton(self)
        button.setObjectName(str(self.movie_list[self.movie_counter]))
        button.setIcon(QIcon(icon_folder+icon_name + ".png"))
        button.setIconSize(QSize(x, y))
        button.setStyleSheet(get_features(background_color="transparent"))
        return button

    def create_new_checkbox(self,icon_name = "unrated",x=25,y=25,number=0):
        check_box = QCheckBox(self)
        check_box.setObjectName(str(number)+icon_name)
        check_box.setStyleSheet(get_features(background_color="transparent"))
        return check_box

    def create_platform_label(self,platform_name,file_path):
        label = QLabel(self)
        label.adjustSize()
        label.setToolTip(platform_name)
        self.customize_widget(label,color="white")
        label.setPixmap(QPixmap(file_path))
        return label

    def show_the_platforms(self):
        platform_layout = QHBoxLayout()
        platform_text = str()
        for i,platform in enumerate(self.platforms):
            if i < len(self.platforms)-1:
                platform_text += str(platform.lower()) + "|"
            else:
                platform_text += str(platform.lower())

            file_name = platform.lower() + ".png"
            file_path = "ProviderLogos/" + file_name
            label = self.create_platform_label(platform,file_path)
            platform_layout.addWidget(label)

        platform_layout.addStretch()
        self.all_platforms = platform_text
        conn.commit()

        return platform_layout

    def edit_overview(self):
        overview_area = self.sender()
        updated_overview = overview_area.toPlainText()
        cursor.execute(f"UPDATE {self.details_table} set overview = %s WHERE name = %s",
                       (updated_overview,self.movie_name))
        conn.commit()

    def create_table(self):
        dbQuery = f"""
                    CREATE TABLE IF NOT EXISTS {self.details_table} (
                        name VARCHAR(255) UNIQUE NOT NULL,
                        platforms VARCHAR(255),
                        similar_movies TEXT DEFAULT ' ',
                        num_rating INT NOT NULL,
                        overview TEXT DEFAULT '',
                        imdb_rating INT CHECK (imdb_rating >= -1 AND imdb_rating <= 9)
                    );
                """
        cursor.execute(dbQuery)

        conn.commit()

    def show_similar_movies(self):
        similar_layout = QVBoxLayout()
        all_similar_movies = str()
        text_label = QLabel("BEĞENEBİLECEĞİNİZ FİLMLER:",self)
        text_label.setStyleSheet(get_features(background_color="transparent", color="black"))
        similar_layout.addSpacing(10)
        similar_layout.addWidget(text_label)
        for name, year in self.similar_movies:
            info = f"{name} ({year})"
            all_similar_movies += info + "|"
            label = QLabel(info,self)
            label.setWordWrap(True)
            label.setStyleSheet(get_features(background_color="transparent",color="black"))

            button = QPushButton(self)
            button.setFixedSize(64,64)
            customize_widget(button,background_color="transparent")
            button.setIcon(QIcon(icon_folder+"see_more.png"))
            button.clicked.connect(partial(go_to_movie_details,self.username,name,self))

            more_details_layout = QHBoxLayout()
            more_details_layout.addWidget(button)
            more_details_layout.addWidget(label)


            similar_layout.addLayout(more_details_layout)

        similar_layout.addStretch()
        self.all_similar_movies = all_similar_movies

        similar_layout.addStretch()
        return similar_layout

    def create_rate_label(self,is_filled=False):
        rate = QLabel(self)
        if is_filled:
            img = "rated.png"
        else:
            img = "unrated.png"

        rate.setPixmap(QPixmap(icon_folder+img))
        return rate

    def show_rating(self):
        rating_layout = QHBoxLayout()
        vote_average = int(self.vote_average)
        for i in range(10):
            is_filled = False
            if vote_average > i:
                is_filled = True
            rate = self.create_rate_label(is_filled)
            rating_layout.addWidget(rate)
        rating_layout.addStretch()
        return rating_layout

    def get_ratings(self):
        info_vote_count = f"yorum sayısı : {self.vote_count}"

        rating_layout = self.show_rating()

        vote_count = QLabel(self)
        self.customize_widget(vote_count,text_size=30,color = "black",border=0,text=info_vote_count)

        rating_layout.addWidget(vote_count)
        rating_layout.addStretch()

        return rating_layout


    disconnect = lambda self: conn.close()

    def customize_widget(self, widget,text_size=15,background_color="transparent"
                         ,color="black",border=2,border_color="black", text=""):

            widget.adjustSize()

            widget.setStyleSheet(
            get_features(size=text_size,background_color=background_color,color=color,
                         border=border,border_color=border_color))

            widget.setText(text)

    def change_poster(self,x,y):
        poster_button = self.sender()

        root = tk.Tk()
        root.withdraw()

        new_path = filedialog.askopenfilename()

        if new_path:
            try:
                img = cv2.imread(new_path)

                new_poster = cv2.resize(img,(x,y))

                cv2.imwrite(self.poster_path,new_poster)

                poster_button.setIcon(QIcon(self.poster_path))
                poster_button.setIconSize(QSize(x,y))
            except Exception as e:
                print(e)
                QMessageBox.warning(self, 'Uyarı', 'Lütfen fotoğraf seçtiğinizden emin olun!')

    def show_movie_poster(self):
        poster_layout = QHBoxLayout()
        x,y = 500,750

        poster = QPushButton(self)
        poster.adjustSize()
        self.customize_widget(poster, border=0)
        poster.setIcon(QIcon(self.poster_path))
        poster.setIconSize(QSize(x,y))
        poster.clicked.connect(partial(self.change_poster,x,y))

        poster_layout.addWidget(poster)
        poster_layout.addStretch()

        return poster_layout

    def show_overview(self):
        overview_layout = QHBoxLayout()
        overview_area = QTextEdit(self)
        overview_area.setFixedWidth(900)
        self.customize_widget(widget=overview_area, text_size=25,
                              background_color="transparent",
                              text=self.movie_overview)
        overview_area.moveCursor(QTextCursor.End)
        overview_area.textChanged.connect(self.edit_overview)
        overview_layout.addWidget(overview_area)

        return overview_layout


    def init_ui(self):
        x,y = 1600,900
        left_side = QVBoxLayout()
        right_side = QVBoxLayout()

        poster_layout = self.show_movie_poster()
        overview_layout = self.show_overview()

        similar_layout = self.show_similar_movies()
        vote_layout = self.get_ratings()
        platform_layout = self.show_the_platforms()

        left_side.addLayout(poster_layout)
        left_side.addLayout(platform_layout)
        left_side.addStretch()

        right_side.addLayout(overview_layout)
        right_side.addLayout(vote_layout)
        right_side.addLayout(similar_layout)


        layout = QHBoxLayout()
        layout.addLayout(left_side)
        layout.addLayout(right_side)
        layout.addStretch()

        self.setLayout(layout)
        self.setFixedSize(x,y)
        self.setWindowTitle(self.movie_name.upper())
        self.setWindowIcon(QIcon(icon_folder+"movie_icon.png"))