# -*- coding: utf-8 -*-
"""资源路径处理：兼容 PyInstaller 打包后的运行环境"""
import os
import sys


def resource_path(relative: str) -> str:
    """获取资源文件绝对路径，兼容开发态与 PyInstaller --onefile 运行态"""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)


def icon_path() -> str:
    return resource_path("icon.ico")
