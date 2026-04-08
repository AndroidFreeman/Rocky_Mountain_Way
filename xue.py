import cv2
import numpy as np
import math
import matplotlib.pyplot as plt

def generate_correct_orientation_spiral():
    print("开始执行：修复坐标系反转问题...")
    img = cv2.imread("test_input.jpg", cv2.IMREAD_GRAYSCALE)
    if img is None:
        return
        
    h, w = img.shape
    size = min(h, w)
    start_y = (h - size) // 2
    start_x = (w - size) // 2
    img = img[start_y:start_y+size, start_x:start_x+size]
    
    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
    _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    img = cv2.GaussianBlur(img, (5, 5), 0)

    num_spirals = 80
    steps_per_spiral = 4000 
    total_steps = num_spirals * steps_per_spiral
    max_theta = num_spirals * 2 * math.pi
    
    thetas, rhos = [], []
    
    with open("10_correct_orientation.thr", "w") as f:
        for i in range(total_steps):
            theta = (i / total_steps) * max_theta
            base_rho = i / total_steps
            
            r_pixel = base_rho * (size / 2.0 - 1)
            x = int(size / 2.0 + r_pixel * math.cos(theta))
            
            # 【核心修复】：计算机图像处理的 Y 轴是向下的（原点在左上角），而数学极坐标的 Y 轴是向上的！
            # 必须用减号来翻转 Y 轴的映射，否则图案会上下颠倒
            y = int(size / 2.0 - r_pixel * math.sin(theta))
            
            x = np.clip(x, 0, size - 1)
            y = np.clip(y, 0, size - 1)
            
            darkness = 1.0 - (img[y, x] / 255.0)
            
            fixed_freq = 120 
            track_distance = 1.0 / num_spirals
            max_amplitude = track_distance * 0.8  
            
            if darkness > 0.1:
                wobble = max_amplitude * darkness * math.sin(fixed_freq * theta)
            else:
                wobble = 0.0
                
            final_rho = np.clip(base_rho + wobble, 0.0, 1.0)
            
            thetas.append(theta)
            rhos.append(final_rho)
            f.write(f"{theta:.4f} {final_rho:.4f}\n")
            
    dpi = 100
    figsize = size / dpi
    fig = plt.figure(figsize=(figsize, figsize), dpi=dpi, facecolor='white')
    ax = fig.add_axes([0, 0, 1, 1], projection='polar')
    
    line_width = max(0.5, 800.0 / size)
    ax.plot(thetas, rhos, color='black', linewidth=line_width, alpha=0.8, antialiased=True, solid_capstyle='round')
    ax.set_rmax(1.0)
    ax.axis('off')
    
    plt.savefig("10_correct_orientation_preview.png", dpi=dpi)
    plt.close()
    print("生成 10_correct_orientation.thr 成功！")

if __name__ == "__main__":
    generate_correct_orientation_spiral()

