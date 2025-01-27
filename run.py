


import sys

from PyQt5.QtWidgets import QApplication

from src.login import Login

if __name__ == '__main__':
    app = QApplication(sys.argv)
    new_user_login = Login()
    new_user_login.show()
    sys.exit(app.exec_())
