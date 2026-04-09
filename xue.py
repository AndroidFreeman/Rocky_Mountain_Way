import cv2
import numpy as np
import math

def generate_correct_orientation_spiral():
    img = cv2.imread('test_input.jpg', cv2.IMREAD_GRAYSCALE)
    # 来读一个文件, 并转化成黑白照片
    if img is None:
        return
    # 没找到图片就润

    # Part 1
    # 这一块是用来做前期处理的, 相当于初始化了

    h, w = img.shape
    # 量一下长宽
    size = min(h, w)
    # 设定一个正方形先
    start_y = (h - size) // 2
    start_x = (w - size) // 2
    # 起始位置在画面中心
    img = img[start_y:start_y+size, start_x:start_x+size]
    # 切一个正方形先
    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
    # 调整一下对比度
    # 这个函数是
    _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    # 保守派觉得激进派太保守了, 去掉灰色部分
    # 这个函数是
    img = cv2.GaussianBlur(img, (5, 5), 0)
    # 给照片来个磨皮

    # Part 2
    # 我们来走线

    num_spirals = 80
    # 画多少圈
    steps_per_spiral = 4000
    # 画一圈取多少个点
    total_steps = num_spirals * steps_per_spiral
    # 总共有多少个点
    max_theta = num_spirals * 2 * math.pi
    # 总共要转多少度

    i_array = np.arange(total_steps)
    # 写编号
    thetas = (i_array / total_steps) * max_theta
    # 算转到什么角度位置
    base_rhos = i_array / total_steps
    # 算离圆心多远

    r_pixels = base_rhos * (size / 2.0 - 1)
    # 算真实距离
    xs = np.clip(size / 2.0 + r_pixels * np.cos(thetas), 0, size - 1).astype(int)
    # 算横坐标
    ys = np.clip(size / 2.0 - r_pixels * np.sin(thetas), 0, size - 1).astype(int)
    # 算纵坐标

    darkness = 1.0 - (img[ys, xs] / 255.0)
    # 扣像素, 看看灰度

    fixed_freq = 120
    # 抖动频率
    track_distance = 1.0 / num_spirals
    # 间距
    max_amplitude = track_distance * 0.8
    # 抖动最大幅度

    wobbles = np.where(darkness > 0.1, max_amplitude * darkness * np.sin(fixed_freq * thetas), 0.0)
    final_rhos = np.clip(base_rhos + wobbles, 0.0, 1.0)
    # 平滑加上抖动

    # Part 3
    # 存入数据

    data_to_save = np.column_stack((thetas, final_rhos))
    # 两个数据拼在一起
    np.savetxt('rocky_mountain_way.thr', data_to_save, fmt='%.4f %.4f')
    # 存数据, 给机器人看的图纸

    draw_rs = final_rhos * (size / 2.0 - 1)
    # 轨迹换算像素
    draw_xs = np.clip(size / 2.0 + draw_rs * np.cos(thetas), 0, size - 1).astype(np.int32)
    # 抖动后横坐标
    draw_ys = np.clip(size / 2.0 - draw_rs * np.sin(thetas), 0, size - 1).astype(np.int32)
    # 抖动后纵坐标

    preview_img = np.full((size, size), 255, dtype=np.uint8)
    # 来一张正方形的白画板
    points = np.column_stack((draw_xs, draw_ys)).reshape((-1, 1, 2))
    # 坐标点打包    
    cv2.polylines(preview_img, [points], isClosed=False, color=0, thickness=1, lineType=cv2.LINE_AA)
    # 画线

    cv2.imwrite('rocky_mountain_way_preview.png', preview_img)
    # 存入png图片

if __name__ == '__main__':
    generate_correct_orientation_spiral()
