"""
interleave.py
=============
    每个透镜覆盖的像素数   P      = DPI / LPI            (允许是小数)
    每帧条带的宽度(像素)  strip  = P / N                (N = 帧数)
    输出第 x 列取自哪一帧   frame  = floor(x * N / P) mod N

说明:
  · 输出图的某一"列"整列都来自被选中那一帧的同一列;帧号每 P 像素循环一次。
  · P 用浮点 + floor 处理,所以 DPI / LPI 不能整除也没问题(例如 1200/50.5)。
  · 当 N == DPI/LPI 时,每帧条带正好 1 像素,就是最常见的"每个透镜下 N 个点"。
  · 这是竖光栅(lenticule 竖直、左右交织)。要做横光栅,把列换成行即可,
"""

import numpy as np


def pixels_per_lens(dpi: float, lpi: float) -> float:
    """每个透镜下的像素数 P = DPI / LPI(可能是小数)。"""
    return dpi / lpi


def column_frame_map(width: int, dpi: float, lpi: float,
                     num_frames: int, phase: float = 0.0) -> np.ndarray:
    """
    返回长度为 width 的整型数组:第 x 个元素 = 输出第 x 列应使用的帧索引(0..N-1)。

    想换交织规律(比如改插值、改条带顺序、做交错/反向),改这一个函数就够了。

    phase: 相位偏移(像素),用来微调条带相对透镜的起始位置,默认 0。

    """
    P = pixels_per_lens(dpi, lpi)
    x = np.arange(width, dtype=np.float64) + phase
    return (np.floor(x * num_frames / P).astype(np.int64)) % num_frames


def interleave(frames: np.ndarray, dpi: float, lpi: float,
               phase: float = 0.0) -> np.ndarray:
    """
    竖光栅交织(列方向)。

    参数
      frames : 形状 (N, H, W, C) 的数组,N 帧都已缩放到相同的 (H, W)。
      dpi    : 打印分辨率
      lpi    : 真实光栅线数(pitch test 测出来的值)
      phase  : 可选相位偏移(像素)

    返回
      形状 (H, W, C) 的交织图(dtype 与输入一致)。
    """
    N, H, W, C = frames.shape
    col_idx = column_frame_map(W, dpi, lpi, N, phase)        # (W,)
    xs = np.arange(W)
    # 高级索引:对每一列 x,取 frames[col_idx[x], :, x, :]
    out = frames[col_idx, :, xs, :]                          # -> (W, H, C)
    out = np.transpose(out, (1, 0, 2))                       # -> (H, W, C)
    return np.ascontiguousarray(out)


def interleave_rows(frames: np.ndarray, dpi: float, lpi: float,
                    phase: float = 0.0) -> np.ndarray:
    """
    横光栅交织(行方向)版本。逻辑和上面完全对称,只是把"列"换成"行"。
    """
    N, H, W, C = frames.shape
    row_idx = column_frame_map(H, dpi, lpi, N, phase)        # (H,)
    ys = np.arange(H)
    out = frames[row_idx, ys, :, :]                          # -> (H, W, C)
    return np.ascontiguousarray(out)
