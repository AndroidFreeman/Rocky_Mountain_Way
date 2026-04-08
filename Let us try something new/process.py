import cv2
import numpy as np
import math

def image_to_spiral_sand_art(image_path, output_thr, num_spirals=100, frequency=200, max_amplitude=0.015):
    # 1. 图像预处理：读取为灰度图，并调整为正方形
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (1000, 1000))
    # 增强对比度（让黑的更黑，白的更白，沙画效果更好）
    img = cv2.equalizeHist(img)
    
    max_theta = num_spirals * 2 * math.pi
    steps_per_spiral = 1000
    total_steps = num_spirals * steps_per_spiral
    
    with open(output_thr, 'w') as f:
        for i in range(total_steps):
            # 基础螺旋线角度与半径
            theta = (i / total_steps) * max_theta
            base_rho = i / total_steps  # 半径从 0 逐渐增大到 1.0
            
            # 2. 坐标映射：将极坐标 (theta, rho) 映射回图像的笛卡尔坐标 (x, y)
            # 图像坐标范围是 0~999，中心点在 (500, 500)
            x = int((base_rho * math.cos(theta) + 1.0) * 499)
            y = int((base_rho * math.sin(theta) + 1.0) * 499)
            
            # 防止越界
            x = np.clip(x, 0, 999)
            y = np.clip(y, 0, 999)
            
            # 3. 采样与调制：获取该点的像素亮度 (0=黑, 255=白)
            pixel_value = img[y, x]
            
            # 归一化暗度 (darkness: 1.0 为纯黑，0.0 为纯白)
            darkness = 1.0 - (pixel_value / 255.0)
            
            # 4. 计算抖动量 (Wobble)
            # 只有在暗区才发生抖动，且暗度越大，抖动幅度越大
            wobble = max_amplitude * darkness * math.sin(frequency * theta)
            
            # 计算最终的 rho，并限制在 0.0 ~ 1.0 的有效沙盘范围内
            final_rho = np.clip(base_rho + wobble, 0.0, 1.0)
            
            # 5. 输出为 dune-weaver 支持的 .thr 格式
            f.write(f"{theta:.3f} {final_rho:.3f}\n")

# 调用示例
# image_to_spiral_sand_art("portrait.jpg", "portrait.thr", num_spirals=150)