import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog

def make_sand(img):
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # ==========================
    # 超强提取白色细线（专治你这张图）
    # ==========================
    # 直接提取亮线，阈值非常低，确保细线全抓到
    _, line = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)

    # 去噪点，不破坏线条
    kernel = np.ones((1,1), np.uint8)
    line = cv2.morphologyEx(line, cv2.MORPH_OPEN, kernel, iterations=1)

    # 沙画底色
    sand = np.full((h,w,3), (100, 160, 220), dtype=np.uint8)

    # 线条画成深沙色
    sand[line > 0] = (50, 80, 110)

    return sand

# 等比例显示
def show(img):
    h, w = img.shape[:2]
    max_size = 800
    scale = min(max_size/w, max_size/h, 1)
    if scale < 1:
        img = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
    cv2.imshow("sand", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# 主程序
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    fp = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.webp")])
    if not fp: exit()

    img = cv2.imread(fp)
    res = make_sand(img)

    cv2.imwrite("sand_result.png", res)
    show(res)