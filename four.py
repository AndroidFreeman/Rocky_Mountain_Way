import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
from scipy.spatial import distance  # 用于快速计算距离

def get_image_path():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(
        title="请选择一张图片生成一笔画轨迹",
        filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp")]
    )
    return file_path

def generate_one_stroke_animation(image_path):
    # 1. 读取与预处理
    img = cv2.imread(image_path)
    if img is None:
        print("错误：无法读取图片，请确保路径没有中文或图片未损坏。")
        return

    # 调整大小以加快计算（最大宽度800）
    scale = 800 / img.shape[1]
    if scale < 1:
        img = cv2.resize(img, (800, int(img.shape[0] * scale)))

    # 转为灰度图并高斯模糊（去噪）
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 边缘检测 (Canny)
    # 这里的阈值可以根据图片调整，50和150是常用值
    edges = cv2.Canny(blurred, 50, 150)

    # 反转颜色：我们要追踪白色的线条（在黑色背景上）
    # 如果背景是白的，线条是黑的，我们需要反转一下逻辑
    # 这里我们假设我们要追踪 Canny 提取出的白色边缘
    coords = np.column_stack(np.where(edges > 0))

    if len(coords) == 0:
        print("未检测到任何边缘，请尝试更换图片。")
        return

    # 2. 构建一笔画路径 (最近邻算法)
    # 为了演示效果，我们限制最大点数，否则计算量太大电脑会卡死
    MAX_POINTS = 2000
    if len(coords) > MAX_POINTS:
        # 随机采样或每隔几个取一个，保持密度大致均匀
        indices = np.linspace(0, len(coords) - 1, MAX_POINTS, dtype=int)
        coords = coords[indices]

    # 转换为浮点数以便计算
    points = coords.astype(np.float32)

    # 创建画布用于显示动画
    canvas = np.zeros_like(img)
    cv2.imshow("One Stroke Drawing Simulation", canvas)
    cv2.waitKey(1)

    # 初始化路径
    current_idx = 0
    path = [points[current_idx]]
    remaining_indices = set(range(len(points)))
    remaining_indices.remove(current_idx)

    print(f"正在计算一笔画路径，共 {len(points)} 个点...")

    # 简单的最近邻贪婪算法
    # 注意：对于大量点，这个循环会比较慢
    for i in range(len(points) - 1):
        current_point = path[-1]
        # 获取剩余点的坐标
        remaining_points = points[list(remaining_indices)]

        # 计算距离
        dists = distance.cdist([current_point], remaining_points, 'euclidean')[0]

        # 找到最近的点
        min_dist_idx = np.argmin(dists)
        next_point_idx_in_remaining = list(remaining_indices)[min_dist_idx]

        path.append(points[next_point_idx_in_remaining])
        remaining_indices.remove(next_point_idx_in_remaining)

        # 每100步打印一次进度
        if i % 100 == 0:
            print(f"路径计算进度: {i}/{len(points)}")

    print("路径计算完成，开始播放动画！")

    # 3. 动画演示
    path = np.array(path).astype(int)

    # 创建一个显示窗口
    display_img = img.copy()

    for i in range(1, len(path)):
        start_point = tuple(path[i-1][::-1]) # (x, y)
        end_point = tuple(path[i][::-1])     # (x, y)

        # 画线 (连接轨迹)
        cv2.line(display_img, start_point, end_point, (0, 255, 0), 1) # 绿色线条

        # 画小球 (当前位置)
        # 先重绘上一帧的背景（为了只显示一个小球），但这会很慢
        # 这里我们采用简单的叠加方式：线条保留，小球移动

        # 画一个红色圆圈代表小球
        cv2.circle(display_img, tuple(path[i][::-1]), 3, (0, 0, 255), -1)

        cv2.imshow("One Stroke Drawing Simulation", display_img)

        # 按 'q' 退出，或者自动播放
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    path = get_image_path()
    if path:
        generate_one_stroke_animation(path)
    else:
        print("未选择图片")