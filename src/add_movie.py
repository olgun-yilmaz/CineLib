#GEREKLİ MODÜLLER IMPORT EDİLİYOR
from functools import partial

import psycopg2

from src.app_module import icon_folder, conn, cursor, CustomizeMessageBox, get_features, customize_widget

from PyQt5.QtCore import QSize, Qt, QRect, QTimer
from PyQt5.QtGui import QIcon, QIntValidator, QTextCursor, QPixmap
from PyQt5.QtWidgets import QPushButton, QLineEdit, QLabel, QMessageBox, QTextEdit, QDialog, QMenu, QAction, \
    QVBoxLayout, QHBoxLayout, QListWidgetItem, QListWidget, QAbstractItemView

from datetime import datetime

from src.movie_loading_screen import MovieLoadingScreen


class Movie:
    def __init__(self, name, year,category,user_rating = -1):
        self.name = name
        self.year = year
        self.category = category
        self.user_rating = user_rating

    __str__ = lambda self: ("{}".format(self.name))


class NewMovie(QDialog):  # film ekleme penceresi sınıfı

    def __init__(self,username,movie_name = str(),year = str(), category = "SEÇ...", is_add = True):
        super().__init__()
        self.username = username
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.area_counter = 0
        self.now = datetime.now()
        self.font_size = 25

        self.movie_table = f"Movies_{self.username}"
        self.movie_details_table = f"MovieDetails_{self.username}"

        self.movie_name = movie_name
        self.year = year
        self.category = category
        self.is_add = is_add

        self.category_text = "KATEGORİ : "
        self.chosen_categories = list()
        self.that_year = int(datetime.strftime(self.now, "%Y"))  # içinde bulunulan yıl
        self.state = False
        self.init_ui()



    def get_features(self,background_color="white", font=12, color="black"):
        return f"""
        QListWidget {{
            background-color: {background_color};
            font-size: {font}px;
            color: {color};
        }}
        QListWidget::item {{
            padding-left: 10px;
            padding-right: 10px;
            font-size: {font}px; 
        }}
        """

    def get_category(self):
        def items_to_text():
            if not self.chosen_categories:
                self.info_category.setText(self.category_text + "SEÇ...")
                return
            text = "/".join(self.chosen_categories)
            self.info_category.setText(self.category_text + text.upper())

        def apply(item, is_auto = False):
            category = item.text()
            print(category)

            if item.data(Qt.UserRole) == 0:
                if not is_auto:
                    self.chosen_categories.append(category)
                img = category
                item.setData(Qt.UserRole, 1)
            else:
                self.chosen_categories.remove(category)
                img = f"bw_{category}"
                item.setData(Qt.UserRole, 0)

            item.setIcon(QIcon(icon_folder + img + ".png"))
            items_to_text()

        def on_item_clicked(item):
            apply(item)


        list_widget = QListWidget()
        list_widget.setStyleSheet(self.get_features(background_color="white", font=30, color="black"))
        list_widget.setSelectionMode(QAbstractItemView.MultiSelection)


        all_categories = ["Aile","Aksiyon","Animasyon","Belgesel","Bilim-kurgu","Dram","Fantastik",
                          "Gizem","Gerilim","Komedi","Korku","Macera","Müzik","Romantik","Savaş","Suç",
                          "Tarih","Tv film","Vahşi batı","Diğer"]

        for category in all_categories:
            item = QListWidgetItem(category)
            item.setData(Qt.UserRole, 0)
            item.setIcon(QIcon(f"{icon_folder}bw_{category}.png"))
            list_widget.addItem(item)

            if category in self.chosen_categories:
                item.setSelected(True)
                apply(item, True)

        list_widget.itemClicked.connect(on_item_clicked)

        return list_widget


    def find_movie(self):
        movie_name = self.movie_name_edit.toPlainText()
        try:
            mls = MovieLoadingScreen(movie_name, is_add = True)
            mls.exec_()
            movieData = mls.movie_data
            self.movie_name_edit.setText(movieData.name)
            self.year_edit.setText(str(movieData.year))
            self.chosen_categories = movieData.categories

            self.get_category()

            movieData = None # sonraki film için nesne sıfırlanıyor.
        except ValueError:
            msg = CustomizeMessageBox(informative_text="")

    def save_movie(self):
        category = self.info_category.text().replace(self.category_text,"")
        movie_name = self.movie_name_edit.toPlainText()
        try:
            year = int(self.year_edit.text())
        except ValueError:
            year = 0
        text_length = len(movie_name)
        print(len(self.chosen_categories))
        movie = Movie(name=movie_name, year=year, category=category)
        if text_length < 2:
            QMessageBox.warning(self, 'Uyarı', 'Karakter uzunluğu 2 ile 60 arasında olmalıdır.')
        elif year > self.that_year or year < 1920:
            QMessageBox.warning(self, "Uyarı", "Lütfen yapım yılını doğru girdiğinizden emin olun!")
        elif len(self.chosen_categories) == 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir kategori seçin!")
        else:
            try:
                query = f"INSERT INTO {self.movie_table} (name,year,category) VALUES(%s,%s,%s)"
                msg = "{} filmi CineLib'e eklendi!"
                if not self.is_add:
                    query = (f"UPDATE {self.movie_table} SET name=%s, year=%s, category=%s"
                             f" WHERE name = '{self.movie_name}' ")
                    try:
                        cursor.execute(f"UPDATE MovieDetails_{self.username} SET name = %s"
                                   f" WHERE name = '{self.movie_name}' ", (movie.name,))
                        conn.commit()
                    except Exception as e:
                        print(e)
                        conn.rollback()
                    msg = "{} fimine ait bilgiler güncellendi."


                cursor.execute(query, (movie.name, movie.year, movie.category))
                conn.commit()

                QMessageBox.information(self, "KAYDEDİLDİ", msg.format(movie.name))
                self.state = True
                self.close()
            except psycopg2.errors.UniqueViolation:
                QMessageBox.warning(self, 'Uyarı', 'Film zaten sistemde kayıtlı!')

    def customize_text_area(self):
        user_input = self.movie_name_edit.toPlainText()

        if user_input != user_input.upper():
            user_input = user_input.upper()
            self.movie_name_edit.setText(user_input)
            self.movie_name_edit.moveCursor(QTextCursor.End)

        text_length = len(self.movie_name_edit.toPlainText())
        if text_length > 60:
            QMessageBox.warning(self, 'Uyarı', 'Film isminin uzunluğu 3 ile 60 karakter arasında olmalıdır.')


    def init_ui(self):
        button_size = 50
        background = QLabel(self)
        background.setPixmap(QPixmap(icon_folder+"add_movie_background"))
        background.adjustSize()

        find_button = QPushButton(self)
        find_button.setFixedSize(button_size,button_size)

        find_button.setIcon(QIcon(icon_folder + "find_button.png"))
        find_button.setIconSize(QSize(button_size,button_size))
        find_button.clicked.connect(self.find_movie)
        customize_widget(find_button, background_color="transparent")

        self.ok_button = QPushButton(self)
        self.ok_button.setIcon(QIcon(icon_folder+"ok.png"))
        self.ok_button.setIconSize(QSize(button_size,button_size))
        self.ok_button.setFixedSize(button_size,button_size)
        customize_widget(self.ok_button,background_color="transparent")
        self.ok_button.clicked.connect(self.save_movie)  # BUTON BAĞLANTISI

        self.year_edit = QLineEdit(self)

        self.movie_name_edit = QTextEdit(self)

        edit_areas = [self.movie_name_edit, self.year_edit]
        for edit_area in edit_areas:
            customize_widget(edit_area, background_color="transparent",font_size=self.font_size)
            if self.area_counter == 0:
                edit_area.setFixedSize(600,40)
                edit_area.setFocus()
                edit_area.textChanged.connect(self.customize_text_area)

            else:
                customize_widget(edit_area, background_color="transparent", border_color="black",
                                 border=2,font_size=self.font_size)
                edit_area.setFixedSize(75, 30)
                int_validator = QIntValidator(1920, self.that_year, self)
                edit_area.setValidator(int_validator)
            self.area_counter += 1

        try:
            self.movie_name_edit.setText(self.movie_name)
            self.year_edit.setText(self.year)
        except TypeError:
            pass

        info_movie = QLabel(self)
        customize_widget(info_movie,background_color="transparent",
                         color="black", text="FİLM ADI :",font_size=self.font_size)
        info_movie.setFixedHeight(40)

        name_layout = QHBoxLayout()
        name_layout.addWidget(info_movie)
        name_layout.addWidget(self.movie_name_edit, alignment=Qt.AlignCenter)
        name_layout.addStretch()

        info_year = QLabel(self)
        customize_widget(info_year,background_color="transparent", color="black", text="YAPIM YILI :",
                         font_size=self.font_size)

        year_layout = QHBoxLayout()
        year_layout.addWidget(info_year)
        year_layout.addWidget(self.year_edit)
        year_layout.addStretch()
        year_layout.addWidget(find_button)

        self.info_category =QLabel(self)
        customize_widget(self.info_category, background_color="transparent", font_size= self.font_size,
                         text=self.category_text + self.category)

        list_widget = self.get_category()
        list_widget.adjustSize()

        layout = QVBoxLayout()
        layout.addLayout(name_layout)
        layout.addSpacing(10)
        layout.addLayout(year_layout)
        layout.addWidget(self.info_category)
        layout.addWidget(list_widget)
        layout.addWidget(self.ok_button,alignment=Qt.AlignCenter)

        self.setLayout(layout)

        self.setWindowIcon(QIcon(icon_folder+"movie_icon.png"))  #PENCERE İKONU

        self.setWindowTitle("FİLM EKLE")

        self.setFixedSize(800,500)  # SABİTLENMİŞ PENCERE BOYUTU