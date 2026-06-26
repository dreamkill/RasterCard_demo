# 光栅切片工具(Lenticular Interlacing)

Python 实现的光栅卡交织 + pitch test 生成。输出无损 TIFF(LZW)或 BMP。

## 文件说明

| 文件 | 作用 |
|---|---|
| `interleave.py` | **切片算法核心,要改算法只动这个文件** |
| `io_utils.py` | 读帧 / 存无损图的工具 |
| `generate_lenticular.py` | 把 `frames/` 里的帧切片合成光栅图 |
| `generate_pitch_test.py` | 生成节距测试图(找真实 LPI 用) |
| `frames/` | **放原始帧的文件夹**(已附 4 张示例,换成你自己的) |

## 环境

```bash
pip install numpy pillow
```

## 用法

### 1. 先做 pitch test,测出真实 LPI

```bash
python generate_pitch_test.py --dpi 1200 --center-lpi 50.5 --step 0.05 --count 11
```

打印(**实际尺寸 / 100% / 不缩放**),把光栅贴上去,找最均匀、不跳波纹的那一条,
记下它标的 LPI 值。先用 step 0.1 粗测,再用 step 0.01 围着结果精测一遍。

### 2. 用测出来的 LPI 生成光栅图

把原始帧放进 `frames/`(按文件名排序 = 帧顺序),然后:

```bash
python generate_lenticular.py --dpi 1200 --lpi 50.52 --width-inch 6 --height-inch 4
```

同样用**不缩放**打印。

## 可调参数(命令行或改各脚本顶部的 `CONFIG`)

**交织**:`--dpi` `--lpi` `--width-inch` `--height-inch` `--format`(tiff/bmp)`--resample`(lanczos/bicubic/bilinear/nearest)`--frames-dir` `--output`

**pitch test**:`--dpi` `--center-lpi` `--step` `--count`(条带数量)`--width-inch` `--band-inch` `--duty`(黑线占空比)`--format`

## 算法

```
每透镜像素 P = DPI / LPI
每帧条带宽 = P / N        (N = 帧数)
第 x 列用第几帧 = floor(x * N / P) mod N
```

竖光栅(左右交织)。横光栅改用 `interleave.py` 里的 `interleave_rows()`。

## 注意

- **帧数 N、DPI、LPI 三者独立**:每帧条带宽 = (DPI/LPI)/N。若它 < 1 像素,脚本会警告 —— 这时要么减少帧数,要么提高 DPI,要么降低 LPI。
- 打印时**绝对不要缩放**,否则节距和光栅对不上,前面 pitch test 白做。
- TIFF 用 LZW 是无损压缩;要完全不压缩可改 `io_utils.py` 里的 `compression` 或用 BMP。
- 大图很吃内存:6×4 英寸 @1200dpi ≈ 7200×4800,N 帧会一次性载入。内存不够就分块或降 DPI 测试。
