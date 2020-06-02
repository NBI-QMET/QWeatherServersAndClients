#Analog output configuration popup window

from PyQt5.QtWidgets import *
from PyQt5 import QtGui,QtCore
import sys
import asyncio
from qweather import QWeatherClient
import time
import numpy as np
import pyqtgraph as pg
import pandas as pd

from PyQt5 import QtWidgets



class LoginWindow(QtWidgets.QWidget):

    got_password = QtCore.pyqtSignal(str)

    def __init__(self):
        super(LoginWindow, self).__init__()

        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        send_button = QtWidgets.QPushButton("Send")
        close_button = QtWidgets.QPushButton("Close")

        send_button.clicked.connect(self.send_clicked)
        close_button.clicked.connect(self.close)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.password)
        layout.addWidget(send_button)
        layout.addWidget(close_button)

        self.setLayout(layout)
        self.setWindowTitle("Login")
        self.setMinimumWidth(350)

    def send_clicked(self):
        self.got_password.emit(self.password.text())


class MyWindow(QtWidgets.QWidget):

    def __init__(self):
        super(MyWindow, self).__init__()

        self.login = LoginWindow()
        self.login.got_password.connect(self.show_it)

        self.edit = QtWidgets.QLineEdit()
        button = QtWidgets.QPushButton("Get input from window")
        button.clicked.connect(self.get_login)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.edit)
        layout.addWidget(button)
        self.setLayout(layout)

    def get_login(self):
        self.login.show()

    def show_it(self, the_password):
        self.edit.setText(the_password)


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())