"""
generate_lenticular.py
======================
读取 frames/ 里的原始帧 -> 缩放到目标尺寸 -> 调用 interleave 做光栅切片
-> 输出无损图(TIFF / BMP)。
"""

import argparse
import numpy as np

from interleave import interleave, pixels_per_lens
from io_utils import load_frames, save_lossless, RESAMPLE

# ============================ 配置 ============================
CONFIG = {
    "frames_dir":  "frames",                 # 原始帧文件夹
    "output":      "output_lenticular",  # 输出文件名(.tif 或 .bmp)
    "dpi":         600,                      # 打印分辨率(同时用于算 P=DPI/LPI 并写入文件 DPI)
    "lpi":         75.19,                      # 光栅线数(pitch test 测出来的真实值)
    "width_inch":  8.27,                       # 输出物理宽(英寸)-> 像素 = 宽 × dpi
    "height_inch": 11.7,                       # 输出物理高(英寸)
    "format":      "tiff",                    # tiff / bmp,都是无损
    "resample":    "lanczos",                 # 缩放算法:lanczos / bicubic / bilinear / nearest
    "phase":       0.0,                       # 条带相位微调(像素),一般留 0
}
# =============================================================


def run(cfg):
    width  = round(cfg["width_inch"]  * cfg["dpi"])
    height = round(cfg["height_inch"] * cfg["dpi"])
    P = pixels_per_lens(cfg["dpi"], cfg["lpi"])

    frames = load_frames(cfg["frames_dir"], (width, height), cfg["resample"])
    N = frames.shape[0]

    print(f"输出尺寸 {width} x {height}px @ {cfg['dpi']}dpi "
          f"({cfg['width_inch']} x {cfg['height_inch']} 英寸)")
    print(f"LPI={cfg['lpi']}  每透镜像素 P={P:.4f}  "
          f"每帧条带宽 {P / N:.4f}px  帧数 N={N}")
    if P / N < 1.0:
        print(f"⚠ 警告:每帧条带不足 1 像素({P / N:.3f}px),部分帧会混叠/丢失。"
              f"建议:减少帧数(当前 {N}),或提高 DPI,或降低 LPI。")

    out = interleave(frames, cfg["dpi"], cfg["lpi"], cfg["phase"])
    save_lossless(out, cfg["output"], cfg["format"], cfg["dpi"])
    print(f"✓ 已保存:{cfg['output']}")
    print("  打印时务必选『实际尺寸 / 100% / 不缩放』,否则节距对不上光栅。")


def parse_args():
    p = argparse.ArgumentParser(description="光栅切片(交织)生成器")
    p.add_argument("--frames-dir",  default=CONFIG["frames_dir"])
    p.add_argument("--output",      default=CONFIG["output"])
    p.add_argument("--dpi",         type=float, default=CONFIG["dpi"])
    p.add_argument("--lpi",         type=float, default=CONFIG["lpi"])
    p.add_argument("--width-inch",  type=float, default=CONFIG["width_inch"])
    p.add_argument("--height-inch", type=float, default=CONFIG["height_inch"])
    p.add_argument("--format",      default=CONFIG["format"], choices=["tiff", "tif", "bmp"])
    p.add_argument("--resample",    default=CONFIG["resample"], choices=list(RESAMPLE))
    p.add_argument("--phase",       type=float, default=CONFIG["phase"])
    a = p.parse_args()
    return {
        "frames_dir": a.frames_dir, "output": a.output, "dpi": a.dpi, "lpi": a.lpi,
        "width_inch": a.width_inch, "height_inch": a.height_inch,
        "format": a.format, "resample": a.resample, "phase": a.phase,
    }


if __name__ == "__main__":
    run(parse_args())
