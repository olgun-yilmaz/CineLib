from functools import partial

from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout,QMessageBox
from src.admin_panel import AdminPanel
from src.movies import CinemaLib
from src.reset_password import  SendMailScreen
from src.sign_up import SignUpWindow
from src.app_module import icon_folder, verify_password, cursor, customize_widget


class Login(QWidget):
    def __init__(self):
        super().__init__()
        self.entered_list = list()

        self.sign_up_success = False
        self.init_ui()

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress:
            if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
                username_area = self.entered_list[0]
                password_area = self.entered_list[1]
                self.login(username_area, password_area)
                return True

        return super().eventFilter(obj, event)

    def username_check(self):
        username_area = self.sender()

        user_input = username_area.text().lower()
        username_area.setText(user_input)

    def login(self,username_area,password_area):
        username = username_area.text()
        password = password_area.text()

        password = password.encode('utf-8')

        cursor.execute("SELECT password,is_authorized,is_blocked FROM Users WHERE username = %s",(username,))

        try:
            hashed_password , is_authorized, is_blocked = cursor.fetchone()
            if hashed_password:
                hashed_password = hashed_password.encode('utf-8')
                control = verify_password(password,hashed_password)
                if control:
                    if is_blocked:
                        QMessageBox.warning(self, 'Uyarı', 'Hesabınız erişime kapatılmıştır!')
                        return
                    else:
                        QMessageBox.information(self,f"HOŞGELDİN {username}".upper(),"Sisteme giriş yapılıyor...")
                    self.close()
                    if is_authorized:
                        adminPanel = AdminPanel(username)
                        adminPanel.exec_()
                        return
                    cineLib = CinemaLib(username=username)
                else:
                    QMessageBox.warning(self,"UYARI","Hatalı şifre!")


        except TypeError:
            QMessageBox.warning(self,"UYARI","Böyle bir kullanıcı yok.")


    def create_new_account(self):
        suw = SignUpWindow()
        suw.exec_()
        self.close()
        if suw.success:
            login = Login()
            login.show()

    def reset_password(self):
        send_m_screen = SendMailScreen()
        send_m_screen.exec_()


    def init_ui(self):
        window_background = QLabel(self)
        window_background.setPixmap(QPixmap(icon_folder+"login_background.jpg"))
        window_background.adjustSize()

        layout = QVBoxLayout()

        suw = SignUpWindow()

        user_name_area, user_name_layout = (suw.create_username_layout
                                            (is_sign_up = False))
        user_name_area.installEventFilter(self)
        user_name_area.textChanged.connect(self.username_check)

        password_box, password_area, password_layout = suw.create_password_layout()
        password_area.installEventFilter(self)

        password_box.clicked.connect(partial(suw.show_password, password_area))

        self.entered_list = [user_name_area,password_area]


        login_button = QPushButton(self)
        suw.customize_widget(login_button, x=200, background_color="transparent", color="white",
                              border=2, border_color="white", text="GİRİŞ YAP")
        login_button.clicked.connect(partial(self.login,user_name_area,password_area))

        sign_up_button = QPushButton(self)
        suw.customize_widget(sign_up_button, x=200, background_color="transparent", color="white",
                             border=2, border_color="white", text="KAYIT OL")
        sign_up_button.clicked.connect(self.create_new_account)

        forgotten_password_button =QPushButton(self)
        seperator = f"{'-'*32}\n"
        customize_widget(forgotten_password_button, background_color="transparent", border=0,
                         color="#add8e6", text=f"{seperator}ŞİFRENİ Mİ UNUTTUN?\n{seperator}")
        forgotten_password_button.clicked.connect(self.reset_password)


        layout.addStretch()
        layout.addSpacing(40)
        layout.addLayout(user_name_layout)
        layout.addLayout(password_layout)
        layout.addWidget(login_button,alignment=Qt.AlignCenter)
        layout.addWidget(forgotten_password_button,alignment=Qt.AlignCenter)
        layout.addWidget(sign_up_button, alignment=Qt.AlignCenter)
        layout.addStretch()


        self.setLayout(layout)

        self.setWindowIcon(QIcon(icon_folder+"movie_icon.png"))
        self.setWindowTitle("GİRİŞ YAP")
        self.setFixedSize(1600,900)