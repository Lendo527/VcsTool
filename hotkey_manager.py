# -*- coding: utf-8 -*-
"""全局快捷键管理：使用 keyboard 库注册系统级热键，通过 Qt 信号通知主线程"""
import keyboard
from PyQt5.QtCore import QObject, pyqtSignal


class HotkeyManager(QObject):
    triggered = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._handler = None
        self._current = None

    def register(self, hotkey):
        self.unregister()
        if not hotkey:
            return False
        try:
            self._handler = keyboard.add_hotkey(hotkey, self._on_hotkey, suppress=False)
            self._current = hotkey
            return True
        except Exception:
            self._handler = None
            self._current = None
            return False

    def unregister(self):
        if self._handler is not None:
            try:
                keyboard.remove_hotkey(self._handler)
            except Exception:
                pass
            self._handler = None
        self._current = None

    @property
    def current(self):
        return self._current

    def _on_hotkey(self):
        # keyboard 回调在子线程，通过信号切回主线程
        self.triggered.emit()
