
from datetime import datetime, timedelta

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QDialog, QRadioButton, QMessageBox

from src.app_module import icon_folder, get_features, set_checkbox_icon, cursor, conn, customize_widget, sendMail


class Users:
    def __init__(self, username, mail_address, is_authorized, is_blocked): #0134
        self.username = username
        self.is_blocked = True if is_blocked == 1 else False
        self.mail_address = mail_address
        self.is_authorized = True if is_authorized == 1 else False


class AdminPanel(QDialog):
    def __init__(self,admin_username):
        super().__init__()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.admin = admin_username
        self.author_trigger()
    
        self.current_window_index = int()

        self.v_box = QVBoxLayout()

        self.num_showing_users = 6
        self.max_len = 24

        self.button_size = 50

        self.get_active_window_index()

        self.user_list = list()
        self.user_counter = 0

        self.showing_widgets = list()
        self.init_ui()

    def paintEvent(self, event):
        pixmap = QPixmap(icon_folder+"details_background.jpg")
        painter = QPainter(self)

        painter.drawPixmap(0, 0, self.width(), self.height(), pixmap)
        painter.end()



    def find_the_last_page(self):
        cursor.execute(f"SELECT COUNT(*) FROM Users")
        movie_count = cursor.fetchone()[0]
        if movie_count == 0:
            return 1
        elif movie_count % self.num_showing_users == 0:
            return int(movie_count / self.num_showing_users)
        else:
            return int(movie_count // self.num_showing_users) + 1

    def get_active_window_index(self):
        cursor.execute("SELECT current_page FROM Users WHERE username = %s", (self.admin,))
        self.current_window_index = cursor.fetchone()[0]


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
                           (self.current_window_index, self.admin))
            conn.commit()
            self.restart()

    def customize_widget(self, widget, size = (0,0),font="Arial Black", font_size=17, color="white",
                         background_color="transparent", border=0, border_color="black", text=""):
        widget.setFixedSize(size[0],size[1])
        widget.setStyleSheet(get_features(font=font, size=font_size, color=color, background_color=background_color,
                                          border=border, border_color=border_color))
        widget.setText(text)

    def author_trigger(self):
        function_query = f"""CREATE OR REPLACE FUNCTION log_is_authorized_update() 
        RETURNS TRIGGER AS $$
        BEGIN

            IF NEW.is_authorized <> OLD.is_authorized THEN
                INSERT INTO UserAuthorizationHistory (username, is_authorized, admin_username, updated_at)
                VALUES (
                    NEW.username,               
                    NEW.is_authorized,          
                    (SELECT admin_username FROM temp_admin LIMIT 1),
                    CURRENT_TIMESTAMP           
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;"""

        trigger_query = """CREATE TRIGGER is_authorized_update_trigger
        AFTER UPDATE ON Users
        FOR EACH ROW
        EXECUTE FUNCTION log_is_authorized_update();
        """
        try:
            cursor.execute("DROP TRIGGER IF EXISTS is_authorized_update_trigger ON users;")
            cursor.execute(function_query)
            cursor.execute(trigger_query)
            conn.commit()
        except Exception as e:
            conn.rollback()

    def block_user(self):
        button = self.sender()
        username = button.objectName()

        is_blocked, img = 0, "non_blocked.png"

        if button.isChecked():
            is_blocked = 1
            img = "blocked.png"

        set_checkbox_icon(checkbox = button, path = icon_folder + img, size = self.button_size)
        cursor.execute("UPDATE Users SET is_blocked = %s WHERE username = %s",(is_blocked, username))
        conn.commit()

    def authorize_user(self): # BLOKE EDİLMİŞ KULLANICIYA YETKİ VERDİRMEYEN TRIGGER
        button = self.sender()
        username = button.objectName()

        is_author, img = 0, "not_authorized.png"

        if button.isChecked():
            is_author = 1
            img = "authorized.png"

        set_checkbox_icon(checkbox=button, path=icon_folder + img, size = self.button_size)
        cursor.execute(f"CREATE TEMPORARY TABLE IF NOT EXISTS temp_admin (admin_username VARCHAR(255));")
        cursor.execute(f"TRUNCATE temp_admin;")  # Eğer önceki işlemler varsa, temizlik yapıyoruz
        cursor.execute(f"INSERT INTO temp_admin (admin_username) VALUES ('{self.admin}');")

        cursor.execute("UPDATE Users SET is_authorized = %s WHERE username = %s", (is_author, username))
        conn.commit()

    def create_new_push_button(self, icon_name="mail_icon", size = 100, username = ""):
        button = QPushButton(self)
        button.setObjectName(username)
        button.setIcon(QIcon(icon_folder + icon_name + ".png"))
        button.setIconSize(QSize(size,size))
        button.setStyleSheet(get_features(background_color="transparent"))
        return button

    def send_customize_mail(self):
        # HESAP BLOKE EDİLDİĞİNDE MAİL GÖNDEREN TRIGGER.
        username = self.sender().objectName()
        cmd = ChoseMailDialog(admin=self.admin,user = username)
        cmd.exec_()



    def show_the_users(self, dbQuery):
        cursor.execute(dbQuery)

        data = cursor.fetchall()

        try:
            for i in data:
                user = Users(username = i[0],mail_address= i[1], is_authorized = i[2], is_blocked= i[3])
                self.user_list.append(user)
        except IndexError:
            pass
        while self.user_counter < len(self.user_list):
            current_user = self.user_list[self.user_counter]

            author_button = self.create_new_checkbox(username=current_user.username)
            block_button = self.create_new_checkbox(username=current_user.username)


            if current_user.is_authorized:
                author_state = "authorized.png"
                author_button.setChecked(True)
                block_button.setEnabled(False)

            else:
                author_state = "not_authorized.png"

            if self.admin != 'admin': # cinlib dışındaki diğer adminler sadece yetki durumunu görüntüleyebiliyor.
                author_button.setEnabled(False)

            set_checkbox_icon(checkbox=author_button, path=icon_folder + author_state, size=self.button_size)
            author_button.clicked.connect(self.authorize_user)


            if current_user.is_blocked:
                block_state = "blocked.png"
                author_button.setEnabled(False)
            else:
                block_state = "non_blocked.png"

            set_checkbox_icon(checkbox=block_button, path=icon_folder + block_state, size = self.button_size)
            block_button.clicked.connect(self.block_user)

            id_label = QLabel(self)
            self.customize_widget(id_label, size = (50,50),
                                  text = str(self.user_counter + 1 + (self.current_window_index - 1) * self.num_showing_users))


            username_label = QLabel(self)
            self.customize_widget(widget=username_label, size=(300,50),text=current_user.username.upper())


            mail_label = QLabel(self)
            self.customize_widget(widget=mail_label, size=(500,50), text=current_user.mail_address)

            mail_button = self.create_new_push_button(username=current_user.username, size = self.button_size)
            mail_button.clicked.connect(self.send_customize_mail)

            h_box = QHBoxLayout()
            h_box.addWidget(id_label)
            h_box.addWidget(username_label)
            h_box.addWidget(mail_label)
            h_box.addWidget(mail_button)
            h_box.addWidget(block_button)
            h_box.addWidget(author_button)
            h_box.addStretch()

            self.v_box.addLayout(h_box)
            self.user_counter += 1
        self.v_box.addStretch()

    def create_new_checkbox(self, username = ""):
        check_box = QCheckBox(self)
        check_box.setObjectName(username)
        check_box.setStyleSheet(get_features(background_color="transparent"))
        return check_box

    def restart(self):
        self.close()
        adminPanel = AdminPanel(self.admin)
        adminPanel.exec_()

    def create_navigation_items(self):
        next_button = QPushButton(self)
        next_button.setObjectName("next")
        prev_button = QPushButton(self)
        prev_button.setObjectName("prev")

        page_label = QLabel(self)
        page_label.setAlignment(Qt.AlignCenter)
        page_label.setText(str(self.current_window_index) + "/" + str(self.find_the_last_page()))
        page_label.setStyleSheet(get_features(size=30, color="white"))

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


    def init_ui(self):
        window_background = QLabel(self)
        window_background.setPixmap(QPixmap(icon_folder + "admin_panel_background.jpg"))
        window_background.adjustSize()

        query = (f"SELECT username, mail_address, is_authorized, is_blocked FROM Users WHERE username != 'admin'"
                 f"ORDER BY username ASC LIMIT {self.num_showing_users}"
                 f" OFFSET {(self.current_window_index - 1) * self.num_showing_users};")

        self.show_the_users(query)

        navigation_layout = self.create_navigation_items()

        self.v_box.addLayout(navigation_layout)

        self.setLayout(self.v_box)
        self.setWindowTitle(f"{self.admin} : ADMIN PANEL")
        self.setWindowIcon(QIcon(icon_folder + "admin_icon.png"))


class ChoseMailDialog(QDialog):
    def __init__(self,admin = "admin",user = "0lgun"):
        super().__init__()
        self.admin = admin
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.user = user
        self.option_list = ["ÖDÜLLER", "KISITLAMA", "HESAP GÜVENLİĞİ", "KAMPANYALAR"]
        self.color_list = ["#eee9e9", "#bcd2ee", "#add8e6", "#e6e6fa"]
        self.rb_list = list()
        self.init_ui()

    def paintEvent(self, event):
        pixmap = QPixmap(icon_folder+"send_mail_background.jpg")
        painter = QPainter(self)

        painter.drawPixmap(0, 0, self.width(), self.height(), pixmap)
        painter.end()

    def send_auto_mail(self):
        cursor.execute("SELECT mail_address FROM Users WHERE username = %s",(self.user,))
        mail_address = cursor.fetchone()[0]

        final_date = datetime.now() + timedelta(5)

        final_date = final_date.strftime("%d/%m/%Y")


        for rb in self.rb_list:
            if rb.isChecked():
                sendMail(mail_address=mail_address, username=self.user, admin_name=self.admin,
                         date=final_date, subject=rb.text(), is_default=False)
                QMessageBox.information(self,"BAŞARILI","MAİL GÖNDERİLDİ")
                self.close()

    def init_ui(self):
        layout = QVBoxLayout()
        for option, color in (zip(self.option_list, self.color_list)):
            rb = QRadioButton(self)
            self.rb_list.append(rb)
            customize_widget(widget=rb, background_color=color, text=option, color="black", font_size=25)
            layout.addWidget(rb)
            layout.addStretch()

        send_button = QPushButton(self)
        send_button.clicked.connect(self.send_auto_mail)
        customize_widget(widget=send_button, background_color="#dda0dd", text="GÖNDER",
                         border = 1, font_size=25, border_color="black")

        send_icon = QLabel(self)
        send_icon.setPixmap(QPixmap(icon_folder + "send_mail.png"))
        send_icon.setFixedSize(32,32)

        send_layout = QHBoxLayout()
        send_layout.addStretch()
        send_layout.addWidget(send_icon)
        send_layout.addWidget(send_button)
        send_layout.addSpacing(100)

        layout.addLayout(send_layout)

        self.setLayout(layout)
        self.setWindowIcon(QIcon(icon_folder + "send_mail.png"))
        self.setWindowTitle(f"{self.admin} --> {self.user}")
        self.setFixedSize(600,300)