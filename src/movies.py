import os.path
from functools import partial

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, \
    QMessageBox, QCheckBox

from src.add_movie import NewMovie, Movie
from src.app_module import icon_folder, RoundButton, get_features, set_checkbox_icon, cursor,conn
from src.movie_details import go_to_movie_details


class SortLabelSizes:
    def __init__(self,id=(0,0),name=(0,0),year=(0,0),category=(0,0),rating=(0,0)):
        self.id = id
        self.name = name
        self.year = year
        self.category = category
        self.rating = rating


class CinemaLib(QWidget):
    def __init__(self, username):
        super().__init__()

        self.username = username
        self.current_window_index = int()

        self.movie_table = f"movies_{self.username}"
        self.details_table = f"moviedetails_{self.username}"

        self.create_table()
        self.v_box = QVBoxLayout()

        self.num_showing_movie = 12
        self.max_len = 24

        self.get_active_window_index()
        self.get_sorting_method()

        self.movie_list = list()
        self.movie_counter = 0

        self.showing_widgets = list()
        self.init_ui()

    get_toolTip_text = lambda self, name="": f"""
                                <html>
                                    <head>
                                        <style>
                                            .tooltip {{
                                                background-color: white;
                                                color: black;
                                                border: 1px solid black;
                                                font-size: 17px;
                                                font-family: 'Kantumruy'; 
                                            }}
                                        </style>
                                    </head>
                                    <body>
                                        <div class="tooltip">{name}</div>
                                    </body>
                                </html>
                            """

    def create_new_push_button(self, icon_name="edit_button", x=25, y=25):
        button = QPushButton(self)
        button.setObjectName(str(self.movie_list[self.movie_counter]))
        button.setIcon(QIcon(icon_folder + icon_name + ".png"))
        button.setIconSize(QSize(x, y))
        button.setStyleSheet(get_features(background_color="transparent"))
        return button

    def create_new_checkbox(self, icon_name="unrated", number=0):
        check_box = QCheckBox(self)
        check_box.setObjectName(str(number) + icon_name)
        check_box.setStyleSheet(get_features(background_color="transparent"))
        return check_box


    def showSearchResults(self, user_search):
        self.movie_counter = 0
        cursor.execute(f"SELECT COUNT(*) FROM {self.movie_table} WHERE name LIKE %s",
                       ('%' + user_search + '%',))
        num_found = cursor.fetchone()[0]

        dbQuery = (f"SELECT * FROM {self.movie_table} WHERE name LIKE %s LIMIT"
                   f" {self.num_showing_movie};")
        safe_search = f"%{user_search}%"
        cursor.execute(dbQuery, (safe_search,))
        data = cursor.fetchall()

        try:
            for i in data:
                movie = Movie(i[1], i[2], i[3], i[4])
                self.movie_list.append(movie)
        except IndexError:
            pass
        while self.movie_counter < len(self.movie_list):
            current_movie = self.movie_list[self.movie_counter]

            delete_button = self.create_new_push_button(icon_name="delete_button")
            delete_button.clicked.connect(self.del_movie)

            edit_button = self.create_new_push_button(icon_name="edit_button")
            edit_button.clicked.connect(self.edit_movie)

            id_label = QLabel(self)
            self.customize_widget(widget=id_label, size = self.sizes.id,
                                  text=str(self.movie_counter + 1))

            movie_name_button = QPushButton(self)
            movie_name_button.clicked.connect(partial(go_to_movie_details,
                                                      self.username,current_movie.name,self))

            showing_name = current_movie.name

            if len(current_movie.name) > self.max_len:
                movie_name_button.setToolTip(self.get_toolTip_text(current_movie.name))
                showing_name = current_movie.name[:self.max_len-3] + "..."

            self.customize_widget(widget=movie_name_button, size=self.sizes.name,
                                  text= showing_name.upper(), color="black")

            movie_year_label = QLabel(self)
            self.customize_widget(widget=movie_year_label,color = "black", size=self.sizes.year,
                                  text=str(current_movie.year))

            movie_category_label = QLabel(self)
            cat_text = current_movie.category.upper()
            if len(cat_text) > 19:
                cat_text = cat_text[:19] + "..."
                movie_category_label.setToolTip(self.get_toolTip_text(current_movie.category))

            self.customize_widget(widget=movie_category_label, size=self.sizes.category,
                                  text=cat_text)


            widgets = [id_label,movie_name_button, movie_year_label, movie_category_label, edit_button, delete_button]
            self.showing_widgets.append(widgets)

            rate_box_list = list()  # her filme ait rate grubu ayrı listelerde tutuluyor.
            rate_layout = QHBoxLayout()
            rate_layout.addStretch()

            for rate_counter in range(10):
                rate_box = self.create_new_checkbox(icon_name="unrated", number=rate_counter)
                if current_movie.user_rating >= rate_counter:
                    set_checkbox_icon(checkbox=rate_box, path=icon_folder + "rated.png")
                else:
                    set_checkbox_icon(checkbox=rate_box, path=icon_folder + "unrated.png")
                rate_box_list.append(rate_box)
                widgets.append(rate_box)
                rate_layout.addWidget(rate_box)
                rate_box.clicked.connect(partial(self.get_rate, rate_box_list, current_movie))

            h_box = QHBoxLayout()
            for widget in widgets:
                if type(widget) != QCheckBox:
                    h_box.addWidget(widget)
                    h_box.addStretch()
            h_box.addLayout(rate_layout)
            h_box.addStretch()
            self.v_box.addLayout(h_box)
            self.movie_counter += 1
        self.v_box.addStretch(100)

        result_text = f"{num_found} sonuç bulundu".upper()
        if num_found == 0:
            result_text = "EŞLEŞEN SONUÇ YOK!"

        while True:  # result_label' a text yerleştirilene kadar.
            try:
                self.customize_widget(widget=self.search_result_label, size=(200, 100),
                                      text=result_text)
                break
            except AttributeError:
                self.search_result_label = QLabel(self)

        self.v_box.addWidget(self.search_result_label, alignment=Qt.AlignRight)



    def search(self):
        if self.search_bar.text().strip() == str():
            pass
        else:
            self.clear_screen()
            user_search = self.search_bar.text().strip()
            self.showSearchResults(user_search.upper())

    def clear_screen(self):
        for widgets in self.showing_widgets:
            for widget in widgets:
                widget.setParent(None)
        try:
            self.search_result_label.setParent(None)
        except AttributeError:
            pass
        self.movie_list = list()

    def sort(self):
        self.movie_counter = 0
        button = self.sender()
        cursor.execute("SELECT active_button_name FROM Users WHERE username = %s",(self.username,))
        data = cursor.fetchone()[0]
        _, self.sort_order = data.split("-")

        self.sorting_type = button.objectName()[:button.objectName().index("-")]

        self.sort_order = "asc" if self.sort_order == "desc" else "desc" # sıralama yönünü tersine çevir.

        active_button_name = f"{self.sorting_type}-{self.sort_order}"
        cursor.execute("UPDATE Users SET active_button_name = %s  WHERE username = %s",(active_button_name, self.username))
        conn.commit()

        self.restart()

    def find_the_last_page(self):
        cursor.execute(f"SELECT COUNT(*) FROM {self.movie_table}")
        movie_count = cursor.fetchone()[0]
        if movie_count == 0:
            return 1
        elif movie_count % self.num_showing_movie == 0:
            return int(movie_count / self.num_showing_movie)
        else:
            return int(movie_count // self.num_showing_movie) + 1

    def get_active_window_index(self):
        cursor.execute("SELECT current_page FROM Users WHERE username = %s", (self.username,))
        self.current_window_index = cursor.fetchone()[0]

    def get_sorting_method(self):
        cursor.execute("SELECT active_button_name FROM Users WHERE username = %s",(self.username,))
        data = cursor.fetchone()[0]
        self.sorting_type, self.sort_order = data.split("-")


    def change_window(self, navigation=""):
        if not navigation:
            button = self.sender()
            navigation = button.objectName()

        control = bool()
        if navigation == "prev" and self.current_window_index > 1:
            self.current_window_index -= 1
            control = True
        elif navigation == "next" and self.current_window_index < self.find_the_last_page():
            self.current_window_index += 1
            control = True
        if control:
            cursor.execute("UPDATE Users SET current_page = %s WHERE username = %s",
                           (self.current_window_index, self.username))
            conn.commit()
            self.restart()

    def get_rate(self, rate_box_list, movie):
        rate_box = self.sender()
        rating = int(rate_box.objectName()[0])

        for box in rate_box_list:
            if box == rate_box:
                is_checked = rate_box.objectName()[1:]
                if is_checked == "unrated":
                    rate_box.setObjectName(str(rating) + is_checked[2:])
                else:
                    rate_box.setObjectName(str(rating) + "un" + is_checked)
                    rating = -1
        movie.rating = rating
        cursor.execute(f"UPDATE {self.movie_table} SET user_rating = %s WHERE Name = %s",
                       (movie.rating, movie.name,))
        conn.commit()

        for box in rate_box_list:
            if rate_box.objectName()[1:] == "rated" and int(box.objectName()[0]) <= rating:
                box.setChecked(True)
                set_checkbox_icon(box, path=icon_folder + "rated.png")
            else:
                set_checkbox_icon(box, path=icon_folder + "unrated.png")



    def show_the_movies(self, dbQuery):
        cursor.execute(dbQuery)

        data = cursor.fetchall()

        try:
            for i in data:
                movie = Movie(i[1], i[2], i[3], i[4])
                self.movie_list.append(movie)
        except IndexError:
            pass
        while self.movie_counter < len(self.movie_list):
            current_movie = self.movie_list[self.movie_counter]

            delete_button = self.create_new_push_button(icon_name="delete_button")
            delete_button.clicked.connect(self.del_movie)

            edit_button = self.create_new_push_button(icon_name="edit_button")
            edit_button.clicked.connect(self.edit_movie)

            id_label = QLabel(self)
            self.customize_widget(widget=id_label, size = self.sizes.id,
                                  text=str(self.movie_counter + 1 + (self.current_window_index - 1) * self.num_showing_movie))

            movie_name_button = QPushButton(self)
            movie_name_button.clicked.connect(partial(go_to_movie_details,
                                                      self.username,current_movie.name,self))

            showing_name = current_movie.name

            if len(current_movie.name) > self.max_len:
                movie_name_button.setToolTip(self.get_toolTip_text(current_movie.name))
                showing_name = current_movie.name[:self.max_len-3] + "..."


            self.customize_widget(widget=movie_name_button, size=self.sizes.name,
                                  text= showing_name.upper())

            movie_year_label = QLabel(self)
            self.customize_widget(widget=movie_year_label,color = "black", size=self.sizes.year,
                                  text=str(current_movie.year))

            movie_category_label = QLabel(self)
            cat_text = current_movie.category.upper()
            if len(cat_text) > 19:
                cat_text = cat_text[:19] + "..."
                movie_category_label.setToolTip(self.get_toolTip_text(current_movie.category))

            self.customize_widget(widget=movie_category_label, size=self.sizes.category,
                                  text=cat_text)


            widgets = [id_label,movie_name_button, movie_year_label, movie_category_label, edit_button, delete_button]
            self.showing_widgets.append(widgets)

            rate_box_list = list()  # her filme ait rate grubu ayrı listelerde tutuluyor.
            rate_layout = QHBoxLayout()
            rate_layout.addStretch()

            for rate_counter in range(10):
                rate_box = self.create_new_checkbox(icon_name="unrated", number=rate_counter)
                if current_movie.user_rating >= rate_counter:
                    set_checkbox_icon(checkbox=rate_box, path=icon_folder + "rated.png")
                else:
                    set_checkbox_icon(checkbox=rate_box, path=icon_folder + "unrated.png")
                rate_box_list.append(rate_box)
                widgets.append(rate_box)
                rate_layout.addWidget(rate_box)
                rate_box.clicked.connect(partial(self.get_rate, rate_box_list, current_movie))

            h_box = QHBoxLayout()
            for widget in widgets:
                if type(widget) != QCheckBox:
                    h_box.addWidget(widget)
                    h_box.addStretch()
            h_box.addLayout(rate_layout)
            h_box.addStretch()
            self.v_box.addLayout(h_box)
            self.movie_counter += 1
        self.v_box.addStretch()

    def restart(self):
        self.close()
        cine_lib = CinemaLib(self.username)

    def create_navigation_items(self):
        next_button = QPushButton(self)
        next_button.setObjectName("next")
        prev_button = QPushButton(self)
        prev_button.setObjectName("prev")

        page_label = QLabel(self)
        page_label.setAlignment(Qt.AlignCenter)
        page_label.setText(str(self.current_window_index) + "/" + str(self.find_the_last_page()))
        page_label.setStyleSheet(get_features(size=30))

        navigation_widgets = [prev_button, page_label, next_button]
        navigation_layout = QHBoxLayout()
        navigation_layout.addStretch()
        for widget in navigation_widgets:
            navigation_layout.addWidget(widget)
            if widget.objectName() == "prev" or widget.objectName() == "next":
                widget.setIcon(QIcon(icon_folder + widget.objectName() + ".png"))
                widget.setIconSize(QSize(50, 50))
                widget.setStyleSheet('background: transparent; border: none;')
                widget.clicked.connect(self.change_window)

        navigation_layout.addStretch()
        return navigation_layout

    def create_table(self):
        dbQuery = f"""
            CREATE TABLE IF NOT EXISTS {self.movie_table} (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                year INT NOT NULL,
                category VARCHAR(255),
                user_rating INT CHECK (user_rating >= -1 AND user_rating <= 9) DEFAULT -1
            );
        """
        cursor.execute(dbQuery)

        conn.commit()

    disconnect = lambda self: conn.close()

    def customize_widget(self, widget, size = (0,0),font="Arial Black", font_size=17, color="black",
                         background_color="transparent", border=0, border_color="black", text=""):
        widget.setFixedSize(size[0],size[1])
        widget.setStyleSheet(get_features(font=font, size=font_size, color=color, background_color=background_color,
                                          border=border, border_color=border_color))
        widget.setText(text)

    def add_movie(self, movie_name="", year="", category="SEÇ...", is_add = True):
        new_movie = NewMovie(username=self.username, movie_name=movie_name, year=str(year),
                             category=category, is_add=is_add)
        new_movie.exec_()
        if new_movie.state:
            cursor.execute("UPDATE Users SET current_page = %s where username = %s",
                           (self.find_the_last_page(), self.username))
            conn.commit()
            self.restart()

    def edit_movie(self):
        movie_name = self.sender().objectName()
        cursor.execute(f"SELECT year,category FROM {self.movie_table} WHERE name = %s", (movie_name,))
        data = cursor.fetchone()
        year = data[0]
        category = data[1].upper()

        self.add_movie(movie_name=movie_name.upper(), year=year, category=category, is_add = False)

    def del_movie(self):
        movie_name = self.sender().objectName()  # silme butonuna filmin adı verilir.
        msgBox = QMessageBox(self)
        msgBox.setWindowTitle("Onay Penceresi")
        msgBox.setText("{} filmini silmek istediğinizden emin misiniz?".format(movie_name))

        yes_button = msgBox.addButton('Evet', QMessageBox.YesRole)
        no_button = msgBox.addButton('Hayır', QMessageBox.NoRole)

        msgBox.setDefaultButton(no_button)

        msgBox.exec_()

        cursor.execute(f"SELECT name FROM {self.movie_table}")
        name_tuple = cursor.fetchall()
        i = 0
        for names in name_tuple:
            for name in names:
                if name == movie_name:
                    break
                i += 1

        if msgBox.clickedButton() == yes_button:
            try:
                cursor.execute(
                    "CALL delete_movie_dynamic(%s, %s, %s)",
                    (movie_name, self.movie_table, self.details_table)
                )
                conn.commit()
            except Exception as e:
                print(e)
                conn.rollback()

            poster_name = movie_name.replace(" ", "_")
            poster_name = poster_name.lower()

            poster_path = f"MoviePosters/{poster_name}.jpg"
            if os.path.isfile(poster_path):
                os.remove(poster_path)

            QMessageBox.information(self, "SİLME İŞLEMİ", f"{movie_name} filmi başarıyla silindi!")

            if i % self.num_showing_movie == 0:
                self.change_window(navigation="prev")

            self.restart()

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress:
            if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
                self.search()
                return True

        return super().eventFilter(obj, event)

    def init_ui(self):
        x,y = 1600,900
        window_background = QLabel(self)
        window_background.setPixmap(QPixmap(icon_folder + "cinema_background.jpg"))
        window_background.adjustSize()

        add_button = QPushButton(self)
        add_button.setIcon(QIcon(icon_folder + "add_button.png"))
        add_button.setIconSize(QSize(100, 60))
        add_button.setStyleSheet(get_features())
        add_button.clicked.connect(partial(self.add_movie, ))

        navigation_layout = self.create_navigation_items()

        h_box = QHBoxLayout()
        h_box.addWidget(add_button)
        h_box.addStretch()

        self.search_bar = QLineEdit(self)
        self.search_bar.installEventFilter(self)
        self.customize_widget(widget=self.search_bar, size=(900, 60), border=5, border_color="black")
        h_box.addWidget(self.search_bar)
        h_box.setSpacing(20)

        search_button = RoundButton(text="ARA")
        h_box.addWidget(search_button)
        h_box.addStretch()
        search_button.clicked.connect(self.search)

        h_box.addLayout(navigation_layout)

        sort_layout = QHBoxLayout()

        self.sizes = SortLabelSizes()
        size_width = 50


        self.sizes.id = (50,size_width)
        id_sort_button = QPushButton(self)
        self.customize_widget(widget=id_sort_button, color = "black", size=self.sizes.id, text="ID")
        id_sort_button.setObjectName("id-sort")

        self.sizes.name = (300,size_width)
        name_sort_button = QPushButton(self)
        self.customize_widget(widget=name_sort_button, color = "black",size=self.sizes.name, text="FİLM")
        name_sort_button.setObjectName("name-sort")

        self.sizes.year = (50,size_width)
        year_sort_button = QPushButton(self)
        self.customize_widget(widget=year_sort_button, color = "black", size=self.sizes.year, text="YIL")
        year_sort_button.setObjectName("year-sort")

        self.sizes.category = (240,size_width)
        category_sort_button = QPushButton(self)
        self.customize_widget(widget=category_sort_button, color = "black", size=self.sizes.category, text="KATEGORİ")
        category_sort_button.setObjectName("category-sort")

        self.sizes.rating = (250,size_width)
        rating_sort_button = QPushButton(self)
        self.customize_widget(widget=rating_sort_button, color = "black", size=self.sizes.rating, text="RATING")
        rating_sort_button.setObjectName("user_rating-sort")

        sort_buttons = [id_sort_button,name_sort_button, year_sort_button, category_sort_button, rating_sort_button]
        for i,sort_button in enumerate(sort_buttons):
            if i < 3:
                if i != 0:
                    sort_layout.addSpacing(65)

                sort_layout.addWidget(sort_button)

            elif i == 3:
                sort_layout.addWidget(category_sort_button)
                sort_layout.addStretch()

            else:
                sort_layout.addStretch()
                sort_layout.addWidget(sort_button)
                sort_layout.addStretch()

            sort_button.clicked.connect(self.sort)

        self.v_box.addLayout(h_box)
        self.v_box.addLayout(sort_layout)


        self.show_the_movies(dbQuery=(f"SELECT * FROM {self.movie_table} ORDER BY {self.sorting_type} {self.sort_order} LIMIT "
                                      f"{self.num_showing_movie} OFFSET "
                                      f"{(self.current_window_index - 1) * self.num_showing_movie};"))

        self.setLayout(self.v_box)
        self.setFixedSize(x,y)
        self.setWindowTitle("CINE-LIB")
        self.setWindowIcon(QIcon(icon_folder + "movie_icon.png"))
        self.show()