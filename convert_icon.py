# -*- coding: utf-8 -*-
"""将生成的图标图片转换为多尺寸 .ico 文件"""
from PIL import Image
import os

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, "icon.jpg")
dst = os.path.join(here, "icon.ico")

img = Image.open(src).convert("RGBA")
# 生成多尺寸图标，适配系统各处显示
sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save(dst, format="ICO", sizes=sizes)
print("ico saved:", dst)
