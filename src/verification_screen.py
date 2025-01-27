import string
from functools import partial

import random

import psycopg2
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon, QIntValidator, QPixmap, QPainter
from PyQt5.QtWidgets import  QLineEdit, QLabel, QHBoxLayout, QVBoxLayout, QMessageBox, QDialog

from datetime import datetime

from _socket import gaierror

from src.app_module import (get_features, icon_folder, RoundButton, sendMail,
                            cursor, conn, CustomizeMessageBox, customize_widget)


#gerekli modüller import ediliyor.

class VerificationScreen(QDialog): # doğrulama penceresi sınıfı

    def __init__(self,mail,username,hashed_password = None,reason = "Doğrulama",
                 subject="CineLib Giriş Doğrulama",is_sign_up = True, rps = None):
        super().__init__()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.reason, self.subject, self.is_sign_up = reason, subject, is_sign_up
        self.rps = rps

        self.input_list = list()
        self.timer = QTimer()
        self.counter = 59
        self.mail = mail
        self.username = username
        self.hashed_password = hashed_password
        self.color = "#438B90"
        self.is_closed = False
        self.reference_label = None
        self.send_layout = QHBoxLayout()
        self.v_box = QVBoxLayout()
        self.input_layout = QHBoxLayout()
        self.init_ui()

    def clearLayout(self):
        while self.send_layout.count() > 0:
            item = self.send_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                self.send_layout.removeWidget(widget)

    def paintEvent(self, event):
        pixmap = QPixmap(icon_folder+"verification_background.jpg")
        painter = QPainter(self)

        painter.drawPixmap(0, 0, self.width(), self.height(), pixmap)
        painter.end()

    def addWidgetsToLayout(self,send_button):
        counter_layout = QVBoxLayout()
        self.counter_img = QLabel(self)
        self.counter_img.setPixmap(QPixmap(icon_folder+"counter.png"))

        counter_layout.addWidget(self.counter_img)
        counter_layout.addWidget(self.send_label)

        self.send_layout.addStretch()
        self.send_layout.addLayout(counter_layout)
        self.send_layout.addSpacing(10)
        self.send_layout.addWidget(send_button)
        self.send_layout.addStretch()
        self.v_box.addLayout(self.send_layout)

    def update_label(self,button):
        self.counter -= 1
        if self.counter == 0:
            button.setEnabled(True)
            self.timer.stop()
            self.send_label.setObjectName("None")
            self.send_label.setParent(None)
            self.counter_img.setParent(None)
        else:
            self.send_label.setText(f"{self.counter} SANİYE SONRA")

    def createSendLabel(self):
        self.send_label = QLabel(self)
        self.customize_widget(widget=self.send_label, size=(160, 30), color="black",
                              text=f"{self.counter} SANİYE SONRA", font_size=19)


    def verification(self):
        entered_code = "".join(input_line.text() for input_line in self.input_list)
        if entered_code == self.verification_code:
            if self.is_sign_up:
                try:
                    is_authorized = 0 if self.username != "admin" else 1
                    cursor.execute("INSERT INTO Users (username, mail_address, password, is_authorized) VALUES "
                                   "(%s, %s, %s,%s)",
                                   (self.username, self.mail, self.hashed_password,is_authorized))

                    conn.commit()

                    QMessageBox.information(self, "BAŞARILI",
                                            f"tebrikler, {self.username}!\nKayıt işleminiz başarıyla tamamlandı.")

                except psycopg2.errors.RaiseException as e:
                    error_message = e.pgerror
                    start_idx = error_message.index(":") + 2
                    end_idx = error_message.index("C")
                    QMessageBox.warning(self,"UYARI",str(error_message)[start_idx:end_idx])
                    conn.rollback()
                self.close()

            else:
                self.close()
                self.rps.exec_()

            self.is_closed = True

        else:
            QMessageBox.warning(self,"UYARI","Kodu hatalı girdiniz.")
            for input_line in self.input_list:
                input_line.setParent(None) # ekran temizleniyor.
            self.input_list = list()
            self.create_input_number_boxes()

    def create_reference_code(self):
        self.reference_code = str()

        chars = string.ascii_uppercase
        self.reference_code = ''.join(random.choice(chars) for _ in range(10))


    def create_verification_code(self,button):
        self.create_reference_code()
        self.counter = 59
        if self.send_label.objectName() == "None":
            self.clearLayout()
            self.createSendLabel()
            self.addWidgetsToLayout(button)

        button.setEnabled(False)
        self.timer.start(1000)  # 1 sn
        self.verification_code = str()
        now = datetime.strftime(datetime.now(), "%d/%m/%Y - %X") # kodun oluşturulduğu an
        verification_numbers = [random.randint(0,9) for i in range(6)]
        for number in verification_numbers:
            self.verification_code += str(number)

        if not self.reference_label is None:
            self.reference_label.setText(f"referans kodu : {self.reference_code}")

        sendMail(mail_address=self.mail,username=self.username,date=now,reason=self.reason,subject=self.subject,
                 verification_code=self.verification_code,reference_code = self.reference_code)

    def create_input_number_boxes(self):
        for i in range(6):
            input_number_box = QLineEdit(self)
            self.customize_widget(widget=input_number_box,size=(60,60),border=2, background_color="white")
            int_validator = QIntValidator(0, 9, self)
            input_number_box.setValidator(int_validator)
            if i == 0:
                input_number_box.setFocus()
            index = i
            self.input_list.append(input_number_box)
            input_number_box.textChanged.connect(partial(self.press_tab,index))
            self.input_layout.addWidget(input_number_box)

    def press_tab(self,index):
        try:
            self.input_list[index+1].setFocus()
        except (AttributeError,IndexError): # son elemana giriş yapıldıysa kal.
            pass
        if index == 5:
            self.verification()

    # Widget özelleştirme
    def customize_widget(self, widget, size = (0,0), font_size = 50, background_color = "transparent",
                         color =  "black", border =  0 , border_color = "black", text=""):
            widget.setFixedSize(size[0],size[1])
            widget.setStyleSheet(
            get_features(size=font_size,background_color=background_color,color=color,
                         border=border,border_color=border_color))
            widget.setText(text)

    def init_ui(self):
        try:
            x,y = 600,300

            self.create_input_number_boxes()

            send_button = RoundButton(text="TEKRAR GÖNDER",color = "black",
                                      x=120, y=50, font_size=15, background_color=self.color)

            send_button.clicked.connect(partial(self.create_verification_code, send_button))

            self.timer.timeout.connect(partial(self.update_label, send_button))

            self.createSendLabel()

            self.create_verification_code(send_button)

            self.reference_label = QLabel(self)
            customize_widget(widget=self.reference_label, text=f"referans kodu : {self.reference_code}",
                             border=2, background_color="white", border_color="black", font_size=30)
            self.reference_label.setFixedHeight(30)

            self.v_box.addWidget(self.reference_label, alignment=Qt.AlignCenter)

            self.v_box.addLayout(self.input_layout)

            self.addWidgetsToLayout(send_button)

            self.setLayout(self.v_box)

            self.setWindowIcon(QIcon(icon_folder+"verification_icon.png")) # pencere ikonu

            self.setFixedSize(x,y) # sabit pencere boyutu

            self.setWindowTitle("DOĞRULAMA")


        except (TimeoutError,gaierror):
            msg = CustomizeMessageBox()