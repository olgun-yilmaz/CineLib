import socket
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QPushButton, QVBoxLayout, QMessageBox

from src.app_module import cursor, CustomizeMessageBox, get_features, hash_password, \
    verify_password, conn, icon_folder
from src.sign_up import SignUpWindow
from src.verification_screen import VerificationScreen

class ResetPasswordScreen(QDialog):
    def __init__(self,username):
        super().__init__()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.suw = SignUpWindow()
        self.username = username
        self.init_ui()

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress:
            if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
                self.send()
                return True

        return super().eventFilter(obj, event)

    def send(self):
        self.suw.password_control(self.password_area,self.password_validation)
        if self.suw.validation:
            new_password = self.password_area.text()
            new_hashed_password = hash_password(new_password)

            cursor.execute("SELECT password FROM Users WHERE username = %s", (self.username,))
            old_hashed_password = cursor.fetchone()[0]
            old_hashed_password = old_hashed_password.encode('utf-8')
            password = new_password.encode('utf-8')

            if verify_password(password, old_hashed_password):
                QMessageBox.warning(self,"UYARI","Eski şifrenizle yeni şifreniz aynı olamaz.")

            else:
                cursor.execute("UPDATE Users SET password = %s WHERE username = %s",
                               (new_hashed_password,self.username))
                conn.commit()

                QMessageBox.information(self,"Şifre Değiştirme",
                                        f"{self.username} adlı hesabınız için şifreniz başarıyla değiştirildi.",
                                        QMessageBox.Ok)
            self.close()
        else:
            QMessageBox.warning(self,"UYARI","Şifreler eşleşmiyor.")


    def init_ui(self):
        password_box, self.password_area, password_layout = self.suw.create_password_layout()
        self.password_area.installEventFilter(self)
        self.password_validation, validation_layout = (self.suw.create_validation_layout
                                                       (password_area = self.password_area))
        self.password_validation.installEventFilter(self)
        password_box.clicked.connect(partial(self.suw.show_password,
                                             self.password_area,self.password_validation))

        send_button = QPushButton(self)
        self.suw.customize_widget(send_button, x=200, background_color="transparent", color="white",
                             border=2, border_color="white", text="GÖNDER")
        send_button.clicked.connect(self.send)

        layout = QVBoxLayout()
        layout.addLayout(password_layout)
        layout.addLayout(validation_layout)
        layout.addWidget(send_button,alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.setStyleSheet(get_features(background_color="black", color="white"))
        self.setWindowTitle("Şifre Sıfırlama Ekranı")
        self.setWindowIcon(QIcon(icon_folder + "reset_password_icon.png"))

class SendMailScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()

    def send_mail(self):
        mail_address = self.mail_area.text()
        cursor.execute("SELECT username FROM Users WHERE mail_address = %s", (mail_address,))
        try:
            username = cursor.fetchone()[0]
            rps = ResetPasswordScreen(username)
            vs = VerificationScreen(mail = mail_address, username = username, subject = "Şifre Sıfırlama Talebi",
                                    reason = "Şifre Sıfırlama", is_sign_up = False, rps= rps)
            self.close()
            vs.exec_()

        except TypeError:
            QMessageBox.warning(self, "UYARI", "Lütfen mail adresinizi doğru girdiğinizden emin olun.")
        except (socket.timeout, socket.gaierror):
            msg = CustomizeMessageBox()

    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress:
            if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
                self.send_mail()
                return True

        return super().eventFilter(obj, event)

    def init_ui(self):
        self.suw = SignUpWindow()
        self.mail_area, mail_layout = self.suw.create_mail_layout(is_sign_up=False)
        self.mail_area.installEventFilter(self)

        send_button = QPushButton(self)
        self.suw.customize_widget(send_button, x = 200, background_color = "transparent", color = "white",
                              border = 2, border_color = "white", text = "GÖNDER")
        send_button.clicked.connect(self.send_mail)

        layout = QVBoxLayout()
        layout.addLayout(mail_layout)
        layout.addStretch()
        layout.addWidget(send_button,alignment=Qt.AlignCenter)

        self.setLayout(layout)

        self.setStyleSheet(get_features(background_color = "black", color = "white"))
        self.setWindowIcon(QIcon(icon_folder+"reset_password_icon.png"))

        self.setWindowTitle("Şifre Sıfırlama Ekranı")