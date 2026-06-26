"""
io_utils.py
===========
读写工具:加载 frames/ 里的帧、保存无损图(TIFF / BMP)。
"""

import os
import sys
import numpy as np
from PIL import Image

_EXTS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp")

RESAMPLE = {
    "lanczos": Image.LANCZOS,   # 缩放质量最高,默认
    "bicubic": Image.BICUBIC,
    "bilinear": Image.BILINEAR,
    "nearest": Image.NEAREST,   # 不插值,保留硬边
}


def load_frames(frames_dir: str, size, resample="lanczos") -> np.ndarray:
    """
    读取文件夹内所有图片(按文件名排序),统一转 RGB 并缩放到 size=(W,H)。
    返回形状 (N, H, W, 3) 的 uint8 数组。
    """
    if not os.path.isdir(frames_dir):
        sys.exit(f"错误:找不到文件夹 {frames_dir}/")
    files = sorted(f for f in os.listdir(frames_dir)
                   if f.lower().endswith(_EXTS))
    if not files:
        sys.exit(f"错误:{frames_dir}/ 里没有图片帧。把你的原始帧放进去再运行。")

    arr = []
    for f in files:
        im = Image.open(os.path.join(frames_dir, f)).convert("RGB")
        im = im.resize(size, RESAMPLE[resample])
        arr.append(np.asarray(im))
    print(f"读取 {len(files)} 帧(按顺序):{', '.join(files)}")
    return np.stack(arr, axis=0)

_EXT = {"tif": ".tif", "tiff": ".tif", "bmp": ".bmp"}
def save_lossless(img_array: np.ndarray, path: str, fmt: str, dpi: float):
    im = Image.fromarray(img_array)
    fmt = fmt.lower()
    if fmt not in _EXT:
        sys.exit(f"不支持的格式:{fmt}(只支持 tiff / bmp)")
    root, _ = os.path.splitext(path)
    path = root + _EXT[fmt]

    dpi_pair = (float(dpi), float(dpi))
    if fmt in ("tif", "tiff"):
        im.save(path, format="TIFF", compression="tiff_lzw", dpi=dpi_pair)
    else:  # bmp
        im.save(path, format="BMP", dpi=dpi_pair)

    return path
