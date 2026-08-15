# -*- coding: utf-8 -*-
"""将源图标转换为多尺寸 .ico 文件。

源图若为无 alpha 通道的格式（jpg），会自动把近白背景抠除为透明，
避免生成的 ico 在 Windows 大尺寸显示时出现整块白底。
用法: python convert_icon.py [源图] [目标ico]
"""
import os
import sys

from PIL import Image

here = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = os.path.join(here, "icon_source.jpg")
DEFAULT_DST = os.path.join(here, "icon.ico")

# 背景判白阈值：RGB 各通道 >= 此值视为背景
BG_THRESH = 238
# alpha 过渡区间宽度，用于柔化主体边缘的白色残留
FEATHER = 12


def _to_rgba_with_transparency(src: str) -> Image.Image:
    im = Image.open(src).convert("RGB")
    w, h = im.size
    rgba = Image.new("RGBA", (w, h))
    src_px = im.load()
    dst_px = rgba.load()
    for y in range(h):
        for x in range(w):
            r, g, b = src_px[x, y]
            # 以三通道最小值近似亮度，越接近 255 越像背景
            lightness = min(r, g, b)
            if lightness >= BG_THRESH:
                # 纯背景 -> 全透明
                alpha = 0
            elif lightness >= BG_THRESH - FEATHER:
                # 过渡区：线性渐变到透明，消除白边
                t = (BG_THRESH - lightness) / FEATHER
                alpha = int(255 * t)
            else:
                alpha = 255
            dst_px[x, y] = (r, g, b, alpha)
    return rgba


def convert(src: str = DEFAULT_SRC, dst: str = DEFAULT_DST) -> str:
    img = _to_rgba_with_transparency(src)
    # 生成多尺寸图标，适配系统各处显示（16~256）
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48),
             (64, 64), (128, 128), (256, 256)]
    img.save(dst, format="ICO", sizes=sizes)
    print("ico saved:", dst)
    return dst


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    dst = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_DST
    convert(src, dst)
