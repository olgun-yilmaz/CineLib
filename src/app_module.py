from psycopg2 import sql

import bcrypt

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import psycopg2
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QPushButton, QMessageBox

from src.config import ADMIN_EMAIL_ADDRESS, GMAIL_API_KEY, PG_PASSWORD

icon_folder = "app_icons/"

timer = QTimer()
timer.setSingleShot(True)


def create_database(db_name =  "cinelib"):
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="o2004b",
        host="localhost",
        options = "-c client_encoding=UTF8"
    )

    conn.autocommit = True
    cursor = conn.cursor()

    try:
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
    except psycopg2.errors.DuplicateDatabase:
        pass

    cursor.close()
    conn.close()

create_database()
conn = psycopg2.connect(
        dbname="cinelib",
        user="postgres",
        password=PG_PASSWORD,
        host="localhost"
    )
cursor = conn.cursor()

create_delete_function = """
CREATE OR REPLACE PROCEDURE delete_movie_dynamic(
    movie_name VARCHAR, 
    movie_table VARCHAR, 
    details_table VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN

    EXECUTE format('DELETE FROM %I WHERE name = $1', movie_table) USING movie_name;


    EXECUTE format('DELETE FROM %I WHERE name = $1', details_table) USING movie_name;

END;
$$;
"""

try:
    cursor.execute(create_delete_function)
except:
    pass


conn.commit()

class Texts:
    def __init__(self, offer="", security="", block="", prize=""):
        self.offer = offer
        self.security = security
        self.block = block
        self.prize = prize

text = Texts()
cursor.execute("SELECT text FROM Texts")
data = cursor.fetchall()

text.block = data[0][0]
text.offer = data[1][0]
text.security = data[2][0]
text.prize = data[3][0]


get_prize_text = lambda username,admin_name,date : text.prize.format(username,date,admin_name)

get_offer_text = lambda username,admin_name,date :  text.offer.format(username,date,admin_name)


get_security_warning_text = lambda username,admin_name,date : text.security.format(username,admin_name)

get_block_warning_text = lambda username,admin_name,date : text.block.format(username,date,admin_name)

mail_dict = {"KISITLAMA" : get_block_warning_text,
             "ÖDÜLLER" : get_prize_text,
             "KAMPANYALAR": get_offer_text,
             "HESAP GÜVENLİĞİ": get_security_warning_text }


def sendMail(mail_address="", username="user ", date="29/09/2024 - 17:14:27",admin_name = "",
             subject="CineLib Giriş Doğrulama", verification_code="052486", reference_code="", reason = "Doğrulama", is_default = True):

    admin = ADMIN_EMAIL_ADDRESS
    app_password = GMAIL_API_KEY

    to = mail_address
    subject = subject
    content = f"""
Merhaba {username},
{date} tarihli {reason.lower()} kodunuz aşağıdadır.

{reason} Kodu : {verification_code}    

REFERANS : {reference_code}

Lütfen bu kodu kimseyle paylaşmayın!
Eğer bu işlemi siz gerçekleştirmediyseniz bu e-postayı dikkate almayın."""

    if not is_default:
        func = mail_dict.get(subject)
        content = func(username,admin_name,date)


    msg = MIMEMultipart()
    msg['From'] = admin
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(content, 'plain'))

    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=3)
    server.starttls()
    server.login(admin, app_password)
    server.send_message(msg)
    server.quit()


color_dict = {"light-gray": "rgba(169, 169, 169, 0.5)"}


def make_image_transparent(pixmap, alpha = 0.5):
    width = pixmap.width()
    height = pixmap.height()

    image = pixmap.toImage()

    for x in range(width):
        for y in range(height):
            color = QColor(image.pixel(x, y))

            color.setAlphaF(alpha)

            image.setPixel(x, y, color.rgba())

    pixmap.convertFromImage(image)


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    if isinstance(hashed_password, bytes):
        hashed_password = hashed_password.decode('utf-8')
    return hashed_password


def verify_password(password, hashed_password):
    return bcrypt.checkpw(password, hashed_password)


def set_checkbox_icon(checkbox, path, size = 25):
    checkbox.setStyleSheet(f'''
        QCheckBox::indicator {{
            width: {size}px;
            height: {size}px;
            border-image: url('{path}');
        }}
    ''')


class RoundButton(QPushButton):
    def __init__(self, x=100, y=60, text="Go", color="black", font_size=15, background_color="#D9D9D9"):
        super().__init__()
        self.setFixedSize(x, y)
        self.setText(text)
        self.setStyleSheet(f"""
    QPushButton {{
        border-radius: {y // 2}px;
        background-color: {background_color};
        color: {color};
        font-size: {font_size}px
    }}
    QPushButton:hover {{
        background-color: #45a049;
    }}
""")


class AnimatedButton(QPushButton):
    def __init__(self, text, x=100, y=60, font="Segoe Print", font_size=17, color="black",
                 background_color="transparent", \
                 border=0):
        super().__init__(text)
        self.setStyleSheet(get_features(font=font, size=font_size, color=color, border_color=background_color,
                                        border=border))
        self.default_size = QSize(x, y)  # Varsayılan boyut
        self.hovered_size = QSize(int(x * 1.2), int(y * 1.25))  # Üzerine gelindiğinde boyut
        self.setFixedSize(self.default_size)  # Başlangıçta varsayılan boyutu ayarla

    def enterEvent(self, event):
        # Fare butonun üzerine geldiğinde boyutu büyüt
        self.setFixedSize(self.hovered_size)
        super(AnimatedButton, self).enterEvent(event)

    def leaveEvent(self, event):
        # Fare butonun üzerinden ayrıldığında boyutu eski haline getir
        self.setFixedSize(self.default_size)
        super(AnimatedButton, self).leaveEvent(event)


class CustomizeMessageBox(QMessageBox):
    def __init__(self, text="Lütfen internet bağlantınızı kontrol edin.", informative_text="Mail gönderilemedi.",
                 title="BAĞLANTI HATASI", icon_path="connection_error"):
        super().__init__()
        self.setText(text)
        self.setInformativeText(informative_text)
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(icon_folder + icon_path))
        self.setStandardButtons(QMessageBox.Ok)
        self.exec_()


get_features = lambda font="Kantumruy", size=17, color="black", background_color="transparent", \
                      border=0, border_color="black": (
    "font-family: {}; font-size: {}px; color: {};background-color: {};border: {}px solid {};"
    .format(font, size, color, background_color, border, border_color))


def customize_widget(widget, font="Kantumruy", font_size=17, color="black",
                     background_color=color_dict.get("light-gray"),
                     border=0, border_color=color_dict.get("light-gray"), text=""):
    widget.adjustSize()
    widget.setStyleSheet(get_features(font=font, size=font_size, color=color, background_color=background_color,
                                      border=border, border_color=border_color))
    widget.setText(text)

