# https://waleedkhan.name/blog/pyqt-designer/

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow

## build the ui.py file
# pyuic5 -i 5 mainwindow.ui -o mainwindow_ui.py
# from .gui.mainwindow_ui import Ui_MainWindow

# class MainWindow(QMainWindow, Ui_MainWindow):
#     def __init__(self):
#         super(MainWindow, self).__init__()
#         self.setupUi(self)


# this needs to find the ui file automatically
from PyQt5 import uic
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('os.path.dirname(__file__)+'/gui/mainwindow.ui', self)
        self.show()


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
