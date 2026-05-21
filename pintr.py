import cv2
import numpy as np
import math

class PintrLineGenerator:
    def __init__(self, step=2, density=15):
        self.step = step
        self.density = density
        self.dir_list = [(-1,0),(1,0),(0,-1),(0,1),
                         (-1,-1),(-1,1),(1,-1),(1,1)]

    def preprocess_img(self, img_path):
        # 读取图像灰度化+反转（暗区优先行走）
        img = cv2.imread(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = 255 - gray
        h, w = gray.shape
        return gray, w, h

    def get_next_pos(self, x, y, gray):
        h, w = gray.shape
        best_score = -1
        best_pos = (x, y)
        for dx, dy in self.dir_list:
            nx = int(x + dx * self.step)
            ny = int(y + dy * self.step)
            if 0<=nx<w and 0<=ny<h:
                score = gray[ny, nx]
                if score > best_score:
                    best_score = score
                    best_pos = (nx, ny)
        return best_pos

    def generate_continuous_points(self, img_path, start_x=None, start_y=None):
        """
        生成Pintr风格**一笔画连续时序坐标**
        return: [(x1,y1),(x2,y2)...] 有序无折返连续点
        """
        gray, w, h = self.preprocess_img(img_path)
        if start_x is None:
            start_x = w // 2
        if start_y is None:
            start_y = h // 2
        points = []
        cx, cy = start_x, start_y
        for _ in range(self.density * max(w, h)):
            points.append((cx, cy))
            nx, ny = self.get_next_pos(cx, cy, gray)
            cx, cy = nx, ny
        return points

# 你的原有极坐标转换函数
def deal_point(x: float, y: float, img_w: int, img_h: int, last_theta: float = 0.0) -> tuple[float, float]:
    arc = math.atan2(y, x)
    two_pi = 2 * math.pi
    last_norm = last_theta % two_pi
    if last_norm > math.pi:
        last_norm -= two_pi
    delta = arc - last_norm
    if delta > math.pi:
        delta -= two_pi
    elif delta < -math.pi:
        delta += two_pi
    theta = last_theta + delta
    raw_rho = math.hypot(x, y)
    max_r = math.hypot(img_w, img_h) / 2
    rho = raw_rho / max_r
    rho = max(0.0, min(1.0, rho))
    return theta, rho

# 统一流水线：图像→连续坐标→连续极角
def img_to_continuous_polar(img_path, save_txt_path, img_w, img_h):
    generator = PintrLineGenerator(step=2, density=12)
    # 生成一笔画连续XY坐标
    xy_points = generator.generate_continuous_points(img_path)
    last_angle = 0.0
    res = []
    for x, y in xy_points:
        t, r = deal_point(x, y, img_w, img_h, last_angle)
        last_angle = t
        res.append(f"{t} {r}")
    # 保存结果
    with open(save_txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(res))
    print(f"生成完成，连续极坐标已保存：{save_txt_path}")

# ========== 直接调用入口 ==========
if __name__ == "__main__":
    IMG_PATH = "flr.jpg"
    OUT_TXT = "polar.txt"
    W = 640
    H = 480
    img_to_continuous_polar(IMG_PATH, OUT_TXT, W, H)