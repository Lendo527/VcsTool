# -*- coding: utf-8 -*-
"""程序入口"""
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from config_manager import ConfigManager
from main_window import MainWindow
from resources import icon_path


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Vcs Tool")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口后仍由托盘维持运行
    app.setWindowIcon(QIcon(icon_path()))

    config = ConfigManager()
    win = MainWindow(config)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
