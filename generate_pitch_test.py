"""
generate_pitch_test.py
================================
生成光栅 pitch test(节距测试)图,用来测出真实 LPI。
"""

import argparse
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from io_utils import save_lossless

# ============================ 配置 ============================
CONFIG = {
    "output":           "pitch_test",
    "dpi":              600,                       # 打印分辨率(要和正式出图一致;喷墨多为 720/600)
    "center_lpi":       75.15,                       # 中心候选 LPI(填光栅标称值附近)
    "step":             0.01,                       # 相邻条带 LPI 步长(粗测 0.1 / 精测 0.01)
    "count":            11,                         # 候选条带数量(建议奇数)
    "colors":           [(0, 255, 0), (255, 0, 0)],  # 彩条循环色:2 色黄/青;给 3 个就是 3 色
    "page_width_inch":  8.27,                        # 纸张/画布宽(英寸)
    "page_height_inch": 11.7,                        # 纸张/画布高(英寸)
    "margin_inch":      0.1,                        # 四周留白
    "format":           "tif",                     # tiff / bmp,都无损
    "gap":              0.01,
}
# =============================================================


def _get_font(px):
    for name in ("C:/Windows/Fonts/arial.ttf",
                 "C:/Windows/Fonts/msyh.ttc",
                 "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, int(px))
        except Exception:
            continue
    return ImageFont.load_default()


def make_color_band(width, height, dpi, lpi, colors):
    period = dpi / lpi
    n = len(colors)
    pal = np.asarray(colors, np.uint8)                       # (n,3)
    x = np.arange(width, dtype=np.float64)
    seg = (np.mod(x, period) / period * n).astype(np.int64) % n   # 每列落在周期内第几段 (W,)
    row = pal[seg]                                           # (W,3)
    return np.repeat(row[None, :, :], height, axis=0)        # (H,W,3)


def run(cfg):
    dpi = cfg["dpi"]
    colors = cfg["colors"]
    count = cfg["count"]

    page_w = round(cfg["page_width_inch"] * dpi)
    page_h = round(cfg["page_height_inch"] * dpi)
    margin = round(cfg["margin_inch"] * dpi)
    avail_w = page_w - 2 * margin
    avail_h = page_h - 2 * margin
    if avail_w <= 0 or avail_h <= 0:
        sys.exit("错误:留白比纸张还大,减小 margin_inch 或加大纸张尺寸。")
    gap = round(cfg["gap"]*dpi)
    bandh = int(avail_h/count)-gap
    content_h = bandh * count + gap * (count - 1)
    lpis = [cfg["center_lpi"] + (i - (count - 1) / 2) * cfg["step"] for i in range(count)]

    # 纸张尺寸白底画布,内容垂直居中
    canvas = np.full((page_h, page_w, 3), 255, np.uint8)
    y_start = margin + max(0, (avail_h - content_h) // 2)
    for i, lpi in enumerate(lpis):
        y0 = y_start + i * (bandh + gap)
        canvas[y0:y0 + bandh, margin:margin + avail_w] = make_color_band(avail_w, bandh, dpi, lpi, colors)

    # 画标签(每条左侧白底 + LPI 数字)+ 顶部一行自述信息
    img = Image.fromarray(canvas)
    draw = ImageDraw.Draw(img)
    font = _get_font(round(dpi*0.05))
    for i, lpi in enumerate(lpis):
        y0 = y_start + i * (bandh+gap)
        label = f"{lpi:.4f} LPI"
        tw = draw.textlength(label, font=font)
        draw.rectangle([margin, y0, margin + tw + 16, y0 + bandh // 3 + 8], fill=(255, 255, 255))
        draw.text((margin + 8, y0 + 4), label, fill=(0, 0, 0), font=font)
    info = f"{dpi}dpi   {len(colors)}色   step {cfg['step']}   range {lpis[0]:.4f}-{lpis[-1]:.4f}"
    draw.text((margin, max(2, y_start - round(0.16 * dpi))), info, fill=(0, 0, 0), font=_get_font(max(12, dpi // 60)))

    save_lossless(np.asarray(img), cfg["output"], cfg["format"], dpi)
    print(f"✓ 已生成 {count} 条候选 · {len(colors)}色 · LPI {lpis[0]:.4f}→{lpis[-1]:.4f}(步长 {cfg['step']})")
    print(f"  画布 {page_w}x{page_h}px = {cfg['page_width_inch']}x{cfg['page_height_inch']} 英寸 @ {dpi}dpi -> {cfg['output']}")
    print("  打印:实际尺寸 / 100% / 不缩放,别进 PS 改 PPI。贴光栅,挑颜色最均匀、不跑色那条,读它的 LPI。")


def make_band(width, height, dpi, lpi, duty=0.5):
    period = dpi / lpi
    x = np.arange(width, dtype=np.float64)
    row = np.where(np.mod(x, period) < period * duty, 0, 255).astype(np.uint8)
    return np.repeat(row[None, :], height, axis=0)


def _parse_colors(s):
    if not s:
        return None
    out = []
    for tok in s.split(","):
        tok = tok.strip().lstrip("#")
        if len(tok) != 6:
            sys.exit(f"颜色格式错误:'{tok}',应为 6 位十六进制如 FFFF00")
        out.append((int(tok[0:2], 16), int(tok[2:4], 16), int(tok[4:6], 16)))
    if len(out) < 2:
        sys.exit("至少要 2 个颜色")
    return out


def parse_args():
    p = argparse.ArgumentParser(description="光栅彩色 pitch test 生成器")
    p.add_argument("--output",     default=CONFIG["output"])
    p.add_argument("--dpi",        type=float, default=CONFIG["dpi"])
    p.add_argument("--center-lpi", type=float, default=CONFIG["center_lpi"])
    p.add_argument("--step",       type=float, default=CONFIG["step"])
    p.add_argument("--count",      type=int,   default=CONFIG["count"])
    p.add_argument("--gap",        type=float, default=CONFIG["gap"])
    p.add_argument("--colors",     type=str,   default=None,
                   help="逗号分隔的十六进制色,如 FFFF00,00FFFF 或 FFFF00,FF0000,0000FF")
    p.add_argument("--page-w",     type=float, default=CONFIG["page_width_inch"])
    p.add_argument("--page-h",     type=float, default=CONFIG["page_height_inch"])
    p.add_argument("--margin",     type=float, default=CONFIG["margin_inch"])
    p.add_argument("--format",     default=CONFIG["format"], choices=["tiff", "tif", "bmp"])
    a = p.parse_args()
    return {
        "output": a.output, "dpi": a.dpi, "center_lpi": a.center_lpi, "step": a.step,
        "count": a.count, "colors": _parse_colors(a.colors) or CONFIG["colors"],
        "page_width_inch": a.page_w, "page_height_inch": a.page_h,
        "margin_inch": a.margin, "format": a.format,"gap": a.gap,
    }


if __name__ == "__main__":
    run(parse_args())