# -*- coding: utf-8 -*-
"""将源图标转换为多尺寸 .ico 文件。

处理流程：
  1. 抠白：源图若为无 alpha 通道的格式（jpg），自动把近白背景置透明
  2. 反色：主体（深色）转为白色，适配深色托盘/任务栏
  3. 裁剪放大：裁掉多余空白边距，主体放大到充满画布（留少量安全边距）
用法: python convert_icon.py [源图] [目标ico]
"""
import os
import sys

from PIL import Image

here = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = os.path.join(here, "icon_source.jpg")
DEFAULT_DST = os.path.join(here, "icon.ico")

# 背景判白阈值：RGB 各通道最小值 >= 此值视为背景
BG_THRESH = 230
# alpha 过渡区间宽度，用于柔化主体边缘的白色残留
FEATHER = 15
# 裁剪后四周保留的安全边距占画布的比例
MARGIN_RATIO = 0.05


def _mask_alpha(im: Image.Image) -> Image.Image:
    """根据亮度生成 alpha：背景透明、主体不透明、边缘渐变"""
    w, h = im.size
    rgba = Image.new("RGBA", (w, h))
    src_px = im.load()
    dst_px = rgba.load()
    for y in range(h):
        for x in range(w):
            r, g, b = src_px[x, y]
            lightness = min(r, g, b)
            if lightness >= BG_THRESH:
                alpha = 0
            elif lightness >= BG_THRESH - FEATHER:
                t = (BG_THRESH - lightness) / FEATHER
                alpha = int(255 * t)
            else:
                alpha = 255
            dst_px[x, y] = (r, g, b, alpha)
    return rgba


def _invert_subject(rgba: Image.Image) -> Image.Image:
    """主体（不透明区）反色为白：RGB 取反后，仅作用于 alpha>0 的像素"""
    w, h = rgba.size
    inv = rgba.convert("RGB").point(lambda v: 255 - v)
    out = Image.new("RGBA", (w, h))
    src_px = rgba.load()
    inv_px = inv.load()
    dst_px = out.load()
    for y in range(h):
        for x in range(w):
            _, _, _, a = src_px[x, y]
            r, g, b = inv_px[x, y]
            dst_px[x, y] = (r, g, b, a)
    return out


def _tight_crop(rgba: Image.Image) -> Image.Image:
    """裁剪到主体边界，再贴回带安全边距的新画布"""
    bbox = rgba.getbbox()  # alpha 非零区域
    if not bbox:
        return rgba
    cropped = rgba.crop(bbox)
    cw, ch = cropped.size
    side = max(cw, ch)
    margin = max(1, int(side * MARGIN_RATIO))
    canvas_size = side + margin * 2
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    # 居中粘贴
    off_x = (canvas_size - cw) // 2
    off_y = (canvas_size - ch) // 2
    canvas.paste(cropped, (off_x, off_y), cropped)
    return canvas


def convert(src: str = DEFAULT_SRC, dst: str = DEFAULT_DST) -> str:
    im = Image.open(src).convert("RGB")
    rgba = _mask_alpha(im)
    rgba = _invert_subject(rgba)
    rgba = _tight_crop(rgba)
    # 生成多尺寸图标，适配系统各处显示（16~256）
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48),
             (64, 64), (128, 128), (256, 256)]
    rgba.save(dst, format="ICO", sizes=sizes)
    print("ico saved:", dst)
    return dst


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    dst = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_DST
    convert(src, dst)
