import re
from functools import partial

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import  Qt, QSize
from PyQt5.QtWidgets import  QLabel, QDialog, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, \
    QMessageBox, QCheckBox

from src.app_module import (icon_folder, get_features, hash_password,
                            cursor, conn, color_dict, make_image_transparent)
from src.verification_screen import VerificationScreen


class User:
    def __init__(self, username,mail, password,current_page):
        self.username = username
        self.mail = mail
        self.password = password
        self.current_page = current_page

    __str__ = lambda self: ("{}".format(self.username))


class SignUpWindow(QDialog): # KAPANIR KAPANMAZ LOGIN AÇ.
    def __init__(self):
        super().__init__()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.create_connection()
        self.create_trigger_function()
        self.success = False
        self.validation = False

        background = QLabel(self)
        pixmap = QPixmap(icon_folder + "sign_up_background.jpg")
        make_image_transparent(pixmap,0.01)
        background.setPixmap(pixmap)
        background.adjustSize()

        self.space_size = 32

        self.user_control_label = QLabel(self)
        self.mail_control_label = QLabel(self)
        self.password_control_label = QLabel(self)

        labels = [self.user_control_label,self.mail_control_label,self.password_control_label]
        for label in labels:
            label.setFixedSize(self.space_size, self.space_size)

        self.entered_list = list()
        self.init_ui()

    def customize_widget(self,widget, x=330,y=60,font="Kantumruy", font_size=20, color="black",
                         background_color=color_dict.get("light-gray"),
                         border=0, border_color="black", text=""):

        widget.setFixedSize(x,y)
        widget.setStyleSheet(get_features(font=font, size=font_size, color=color, background_color=background_color,
                                          border=border, border_color=border_color)+
                                        "border-radius: 10px;"+"padding: 10px;")
        widget.setText(text)

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress:
            if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
                username_area = self.entered_list[0]
                mail_area = self.entered_list[1]
                password_area = self.entered_list[2]
                self.sign_up(username_area, mail_area, password_area)
                return True

        return super().eventFilter(obj, event)

    def is_valid_email(self,email):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None


    def create_connection(self):
        cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
                        username VARCHAR(30) PRIMARY KEY,  
                        mail_address VARCHAR(255) UNIQUE NOT NULL,  
                        password VARCHAR(255) NOT NULL, 
                        is_authorized INT DEFAULT 0 CHECK (is_authorized IN (0, 1)),
                        is_blocked INT DEFAULT 0 CHECK (is_blocked IN (0, 1)),
                        current_page INT DEFAULT 1,  
                        active_button_name VARCHAR(30) DEFAULT 'id-asc' 
                            );""")

        cursor.execute("""CREATE TABLE IF NOT EXISTS UserAuthorizationHistory (
            id SERIAL PRIMARY KEY,
            username VARCHAR(30) NOT NULL,
            is_authorized INT DEFAULT 0 CHECK (is_authorized IN (0, 1)),
            admin_username VARCHAR(30) NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );""")
        conn.commit()

    def create_trigger_function(self):
        try:
            function_query = """
            CREATE OR REPLACE FUNCTION validate_user_input()
            RETURNS TRIGGER AS $$
            BEGIN
                IF LENGTH(NEW.username) < 3 THEN
                    RAISE EXCEPTION 'Kullanıcı adı en az 3 karakter içermelidir.';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            """

            trigger_query = """
            CREATE TRIGGER validate_user_input_trigger
            BEFORE INSERT OR UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION validate_user_input();
            """

            cursor.execute("DROP TRIGGER IF EXISTS validate_user_input_trigger ON users;")

            cursor.execute(function_query)

            cursor.execute(trigger_query)

            conn.commit()

        except Exception as e:
            print(f"Bir hata oluştu: {e}")
            conn.rollback()  # Hata durumunda işlemi geri al


    def sign_up(self,username_area,mail_area,password_area):
        username = username_area.text()
        mail = mail_area.text()
        password = password_area.text()
        hashed_password = hash_password(password)

        cursor.execute("SELECT * FROM Users WHERE username = %s",(username,))
        data = cursor.fetchall()
        check_username = (any(username for username in data))

        cursor.execute("SELECT * FROM Users WHERE mail_address = %s", (mail,))
        data = cursor.fetchall()
        check_mail = (any(mail for mail in data))


        if len(password) < 6:
            QMessageBox.warning(self, "Uyarı", "Şifreniz en az 6 karakterden oluşmalıdır.")
        elif not self.validation:
            QMessageBox.warning(self,"UYARI","Şifreler uyuşmuyor.")
        elif check_username:
            QMessageBox.warning(self, "UYARI", "Bu kullanıcı adı alınmış!")
        elif check_mail:
            QMessageBox.warning(self,"UYARI","Bu mail adresi başka bir hesaba ait!")
        elif not self.is_valid_email(mail):
            QMessageBox.warning(self, "UYARI", "Lütfen mail adresinizi doğru girdiğinizden emin olun.")
        else:
            verification_screen = VerificationScreen(mail = mail, username= username,
                                                     hashed_password=hashed_password)
            verification_screen.exec_()
            if verification_screen.is_closed:
                self.close()
                self.success = True


    def show_password(self,password_area,validation_area):
        echo, img_name = QLineEdit.Password, "hidden"
        password_box = self.sender()

        if password_box.isChecked():
            echo = QLineEdit.Normal
            img_name = "visible"

        password_area.setEchoMode(echo)
        password_box.setIcon(QIcon(icon_folder + img_name + "_password.png"))

        try:
            validation_area.setEchoMode(echo)
        except AttributeError:
            pass

    def has_invalid_characters(self,username):
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*'," ",",",".","!","-","=","^","+",
                         "%","&","{","}","[","]","(",")"]
        return any (char in username for char in invalid_chars) # en az bir tanesi doğruysa True döner.

    validate_user_input = lambda self,control : "verified" if control else "reject"

    def invalid_control(self):
        is_okay = True
        username_area = self.sender()

        user_input = username_area.text().lower()
        username_area.setText(user_input)

        if len(user_input) < 3:
            is_okay = False
        try:
            cursor.execute("SELECT username FROM Users WHERE username = %s",(user_input,))
            data = cursor.fetchone()[0]
            is_okay = False
        except TypeError:
            pass

        img = self.validate_user_input(is_okay)
        self.user_control_label.setPixmap(QPixmap(icon_folder+img+".png"))

        if self.has_invalid_characters(username_area.text()):  # girilen ifadeyi kontrol ediyor.
            invalid_char  = username_area.text()[len(username_area.text())-1] # sürekli olarak kontrol yapıldığı için
                                                                              # hatalı karakter son satırda.
            if invalid_char == " ":
                QMessageBox.warning(self, "Uyarı", f"Kullanıcı adı boşluk içeremez!")
            else:
                QMessageBox.warning(self, "Uyarı", f"Kullanıcı adı {invalid_char} içeremez!")

            username_area.setText(username_area.text().strip(invalid_char))  # geçersiz karakteri siler.

    def mail_control(self):
        is_okay = True
        mail_area = self.sender()
        mail_input = mail_area.text().lower()
        mail_area.setText(mail_input)

        cursor.execute("SELECT mail_address FROM Users WHERE mail_address = %s", (mail_input,))
        try:
            data = cursor.fetchone()[0]
            is_okay = False
        except TypeError:
            pass

        if not self.is_valid_email(mail_input):
            is_okay = False

        img = self.validate_user_input(is_okay)
        self.mail_control_label.setPixmap(QPixmap(icon_folder+img+".png"))

    def password_control(self,password_area, validation_area):
        is_okay = True
        validation = validation_area.text()
        password = password_area.text()

        if validation != password or len(password) < 6:
            is_okay = False

        self.validation = (validation == password)

        img = self.validate_user_input(is_okay)
        self.password_control_label.setPixmap(QPixmap(icon_folder+img+".png"))


    def create_password_area(self):
        password_area = QLineEdit(self)
        password_area.setEchoMode(QLineEdit.Password)
        password_area.installEventFilter(self)
        return password_area

    def create_password_layout(self, label_color = "white" , font_size = 25,
                               font = "Kantumry" , space_size = 60):

        password_area = self.create_password_area()
        self.customize_widget(password_area)

        password_label = QLabel("ŞİFRE\t\t         ", self)
        password_label.setStyleSheet(get_features(color=label_color, size=font_size,
                                                  font=font) + "font-weight: bold;")

        password_box = QCheckBox(self)
        password_box.setStyleSheet("QCheckBox::indicator { width: 0px; height: 0px; }")
        password_box.setIcon(QIcon(icon_folder + "hidden_password.png"))
        password_box.setIconSize(QSize(self.space_size,self.space_size))

        password_h_box = QHBoxLayout()
        password_h_box.addStretch()
        password_h_box.addSpacing(space_size)
        password_h_box.addWidget(password_area)
        password_h_box.addWidget(password_box)
        password_h_box.addStretch()

        password_layout = QVBoxLayout()
        password_layout.addStretch()
        password_layout.addWidget(password_label, alignment=Qt.AlignCenter)
        password_layout.addLayout(password_h_box)
        password_layout.addStretch()

        return password_box, password_area, password_layout


    def create_username_layout(self, label_color = "white" , font_size = 25, font = "Kantumry" ,
                               space_size = 60, is_sign_up = True):
        user_name_area = QLineEdit(self)
        user_name_area.setFocus()
        self.customize_widget(user_name_area)
        user_name_area.setMaxLength(30)
        if is_sign_up:
            user_name_area.installEventFilter(self)
            user_name_area.textChanged.connect(self.invalid_control)

        user_name_label = QLabel("KULLANICI ADI\t          ", self)
        user_name_label.setStyleSheet(get_features(color=label_color, size=font_size, font=font)
                                      + "font-weight: bold;")

        user_h_box = QHBoxLayout()
        user_h_box.addStretch()
        user_h_box.addSpacing(space_size // 1.2)
        user_h_box.addWidget(user_name_area)
        user_h_box.addWidget(self.user_control_label)
        user_h_box.addStretch()

        user_name_layout = QVBoxLayout()
        user_name_layout.addWidget(user_name_label, alignment=Qt.AlignCenter)
        user_name_layout.addLayout(user_h_box)
        return user_name_area,user_name_layout

    def create_validation_layout(self, label_color = "white" , font_size = 25,
                               font = "Kantumry" , space_size = 60, password_area = None):
        password_validation_layout = QVBoxLayout()
        password_validation = self.create_password_area()
        password_validation.textChanged.connect(partial(self.password_control, password_area,password_validation))
        self.customize_widget(password_validation)

        validation_label = QLabel("    ŞİFRE DOĞRULAMA\t", self)
        validation_label.setStyleSheet(
            get_features(color=label_color, size=font_size, font=font) + "font-weight: bold;")

        validation_h_box = QHBoxLayout()
        validation_h_box.addStretch()
        validation_h_box.addSpacing(space_size)
        validation_h_box.addWidget(password_validation)
        validation_h_box.addWidget(self.password_control_label)
        validation_h_box.addStretch()

        password_validation_layout.addStretch()
        password_validation_layout.addWidget(validation_label, alignment=Qt.AlignCenter)
        password_validation_layout.addLayout(validation_h_box)
        password_validation_layout.addStretch()

        return password_validation, password_validation_layout


    def create_mail_layout(self, label_color = "white" , font_size = 25, font = "Kantumry" ,
                               space_size = 60, is_sign_up = True):
        mail_area = QLineEdit(self)
        self.customize_widget(mail_area)
        mail_area.setMaxLength(255)
        if is_sign_up:
            mail_area.installEventFilter(self)
            mail_area.textChanged.connect(self.mail_control)

        mail_label = QLabel("E-MAIL\t\t         ", self)
        mail_label.setStyleSheet(get_features(color=label_color, size=font_size,
                                              font=font) + "font-weight: bold;")

        mail_h_box = QHBoxLayout()
        mail_h_box.addStretch()
        mail_h_box.addSpacing(space_size // 1.2)
        mail_h_box.addWidget(mail_area)
        mail_h_box.addWidget(self.mail_control_label)
        mail_h_box.addStretch()

        mail_layout = QVBoxLayout()
        mail_layout.addStretch()
        mail_layout.addWidget(mail_label, alignment=Qt.AlignCenter)
        mail_layout.addLayout(mail_h_box)
        mail_layout.addStretch()

        return mail_area, mail_layout

    def init_ui(self):
        space_size = 60
        layout = QVBoxLayout()

        user_name_area, user_name_layout = self.create_username_layout()

        password_box, password_area, password_layout = self.create_password_layout()

        mail_area, mail_layout = self.create_mail_layout()

        self.entered_list = [user_name_area,mail_area,password_area]

        password_validation, validation_layout = self.create_validation_layout(password_area=password_area)

        password_box.clicked.connect(partial(self.show_password, password_area, password_validation))

        sign_up_button = QPushButton(self)
        self.customize_widget(sign_up_button,x=200,background_color="transparent",color="white",
                              border=2,border_color="white", text = "KAYIT OL")
        sign_up_button.clicked.connect(partial(self.sign_up,user_name_area,mail_area,password_area))


        layout.addStretch()
        layout.addLayout(user_name_layout)
        layout.addSpacing(space_size//5)
        layout.addLayout(mail_layout)
        layout.addLayout(password_layout)
        layout.addLayout(validation_layout)
        layout.addSpacing(space_size//2)
        layout.addWidget(sign_up_button,alignment=Qt.AlignCenter)
        layout.addStretch()
  
        self.setLayout(layout)

        self.setWindowIcon(QIcon(icon_folder+"movie_icon.png"))
        self.setWindowTitle("KAYIT OL")
        self.setFixedSize(1600,900)