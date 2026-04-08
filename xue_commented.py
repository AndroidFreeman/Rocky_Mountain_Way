import cv2
import numpy as np
import math
import matplotlib.pyplot as plt
import argparse
import os
import time


def generate_rocky_mountain_way_spiral(
    input_path,
    thr_path,
    preview_path,
    *,
    num_spirals=80,
    steps_per_spiral=4000,
    fixed_freq=120,
    darkness_threshold=0.1,
    blur_ksize=5,
):
    """生成一条连续螺旋轨迹来“编码”图片明暗，并导出 `.thr` 与预览图。

    输出 `.thr` 的每一行是：
    - `theta`：极角（弧度）
    - `rho`：归一化半径（0~1）

    你答辩时可以这样讲：
    - 我用一条从中心向外的螺旋扫描图片；
    - 每扫到一个点，我读取该像素灰度，转成“黑度”；
    - 黑度越大，我就给半径加更大的周期扰动（wobble）；
    - 最终一条连续轨迹在视觉上就能表达明暗纹理。

    本版本做了两点“更稳/更快”的优化：
    - 参数化：输入/输出与采样参数都可从命令行传入，答辩展示更可控；
    - 向量化：用 NumPy 一次性计算全部点（比 Python for 循环更快、更不容易卡）。
    """

    t0 = time.time()
    input_path = os.path.abspath(input_path)
    thr_path = os.path.abspath(thr_path)
    preview_path = os.path.abspath(preview_path)
    os.makedirs(os.path.dirname(thr_path), exist_ok=True)
    os.makedirs(os.path.dirname(preview_path), exist_ok=True)

    print("开始执行：生成 rocky_mountain_way 螺旋轨迹...")
    print(f"input: {input_path}")

    if blur_ksize % 2 == 0 or blur_ksize < 1:
        raise ValueError("blur_ksize 必须是 >=1 的奇数")
    if num_spirals <= 0 or steps_per_spiral <= 0:
        raise ValueError("num_spirals / steps_per_spiral 必须为正")

    # 1) 读取为灰度图（0~255）
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"读取失败：{input_path}")

    # 2) 裁剪成正方形：极坐标映射更对称
    h, w = img.shape
    size = int(min(h, w))
    start_y = (h - size) // 2
    start_x = (w - size) // 2
    img = img[start_y : start_y + size, start_x : start_x + size]

    # 3) 归一化到 0~255：降低曝光差异影响
    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)

    # 4) 二值化 + 模糊：把随机噪声变成更连续的“灰度场”，避免轨迹毛刺
    _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    img = cv2.GaussianBlur(img, (blur_ksize, blur_ksize), 0)

    # 5) 生成采样序列
    total_steps = int(num_spirals) * int(steps_per_spiral)
    max_theta = float(num_spirals) * 2.0 * math.pi

    # i: 0..total_steps-1
    i = np.arange(total_steps, dtype=np.float64)
    theta = (i / total_steps) * max_theta
    base_rho = i / total_steps

    # 6) 极坐标 -> 像素坐标
    # r_pixel：把归一化半径换成像素半径
    r_pixel = base_rho * (size / 2.0 - 1.0)
    center = size / 2.0

    x = np.floor(center + r_pixel * np.cos(theta)).astype(np.int32)

    # 重点：y 轴用减号翻转（图像坐标 y 向下为正）
    y = np.floor(center - r_pixel * np.sin(theta)).astype(np.int32)

    x = np.clip(x, 0, size - 1)
    y = np.clip(y, 0, size - 1)

    # 7) 黑度计算（0~1）
    # img[y, x]：用向量化索引一次性取出所有采样点的像素值
    pixel = img[y, x].astype(np.float64)
    darkness = 1.0 - (pixel / 255.0)

    # 8) 黑度 -> 半径扰动（wobble）
    track_distance = 1.0 / float(num_spirals)
    max_amplitude = track_distance * 0.8

    wobble = np.zeros_like(base_rho)
    mask = darkness > float(darkness_threshold)
    wobble[mask] = max_amplitude * darkness[mask] * np.sin(float(fixed_freq) * theta[mask])

    final_rho = np.clip(base_rho + wobble, 0.0, 1.0)

    # 9) 写 `.thr`
    data = np.column_stack([theta, final_rho])
    np.savetxt(thr_path, data, fmt="%.4f %.4f")

    # 10) 生成预览：把 (theta, rho) 用极坐标画出来
    dpi = 120
    figsize = size / dpi
    fig = plt.figure(figsize=(figsize, figsize), dpi=dpi, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1], projection="polar")

    # 输入越大，线宽越细，保证观感相对一致
    line_width = max(0.5, 800.0 / size)
    ax.plot(
        theta,
        final_rho,
        color="black",
        linewidth=line_width,
        alpha=0.85,
        antialiased=True,
        solid_capstyle="round",
    )
    ax.set_rmax(1.0)
    ax.axis("off")

    plt.savefig(preview_path, dpi=dpi)
    plt.close()

    dt = time.time() - t0
    print(f"thr: {thr_path}")
    print(f"preview: {preview_path}")
    print(f"耗时: {dt:.2f}s, 点数: {total_steps}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", default="test_input.jpg")
    parser.add_argument("--thr", default="rocky_mountain_way.thr")
    parser.add_argument("--preview", default="rocky_mountain_way_preview.png")
    parser.add_argument("--num-spirals", type=int, default=80)
    parser.add_argument("--steps-per-spiral", type=int, default=4000)
    parser.add_argument("--fixed-freq", type=float, default=120)
    parser.add_argument("--darkness-threshold", type=float, default=0.1)
    parser.add_argument("--blur-ksize", type=int, default=5)
    args = parser.parse_args()

    generate_rocky_mountain_way_spiral(
        args.input,
        args.thr,
        args.preview,
        num_spirals=args.num_spirals,
        steps_per_spiral=args.steps_per_spiral,
        fixed_freq=args.fixed_freq,
        darkness_threshold=args.darkness_threshold,
        blur_ksize=args.blur_ksize,
    )

