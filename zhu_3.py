import numpy as np
import cv2
import tkinter as tk
from tkinter import filedialog

b_d=7           #(src,d滤波直径,sigmaColor,sigmaSpace)
b_c=50          #sigmaColor
b_s=50          #sigmaSpace
canny_min=10    #最小阈值，低于则忽略
canny_max=60    #最大阀值，高于必边缘
canny_s=3       #1,3,5,7，越大越粗，但丢细节

bai=255         #白色,最大阀值
ed_bs=11        #以11*11计算亮度，越小越精细
ed_c=1          #越小线条越粗
ke_w=2          #kernel的宽高
ke_h=2
ke_i=1          #加粗大小
cla_lit=4.0     #对比度限制，越大越强
cla_w=10        #格子宽高
cla_h=10

sand_bl=[100, 160, 220] #沙画底色
sand_col=[40, 70, 100]  #换色颜色
gb_w=1                  #模糊核宽高，越大越糊
gb_h=1
gb_p=0.3                #搞事标准差，越小越接近原图
add_s=10                #饱和度加值
add_v=3                 #亮度加值

max_width=800#显示长宽
max_height=600


def pre(img):#预处理图像(高,宽)
    img = img.copy()
    if len(img.shape) == 3 and img.shape[2] == 4:  # 判断是否有透明通道
        bgr = img[..., :3]#分离 BGR 和 Alpha
        alpha = img[..., 3]
        bg = np.ones_like(bgr, dtype=np.uint8) * 255  #创建白色背景
        alpha = alpha[..., None] / 255.0  #按透明度融合
        img = (bgr * alpha + bg * (1 - alpha)).astype(np.uint8)
    img=cv2.cvtColor(img,cv2.COLOR_BGR2LAB)#RGB转为BGR
    pre=cv2.bilateralFilter(img,b_d,b_c,b_s)#双边滤波=模糊背景+保留边缘
    pre=pre.mean(axis=2).astype(np.uint8)#转为灰度图
    edges_canny = cv2.Canny(pre, canny_min, canny_max, apertureSize=canny_s, L2gradient=True)#更多线条
    edges_adaptive = cv2.adaptiveThreshold(
        pre, bai, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, blockSize=ed_bs, C=ed_c
    )#更小线条
    pre = cv2.bitwise_or(edges_canny, edges_adaptive)#两者融合用
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (ke_w, ke_h))#建一个刷子来加粗
    pre = cv2.dilate(pre, kernel, iterations=ke_i)# 加粗线条
    pre = cv2.morphologyEx(pre, cv2.MORPH_CLOSE, kernel, iterations=ke_i)#连线  
    cla=cv2.createCLAHE(clipLimit=cla_lit,tileGridSize=(cla_w,cla_h))#创建对比度增强器(对比度增强的强度,m*n个小格子里单独做对比度增强)
    pre=cla.apply(pre)#对pre进行对比增强

    return pre

def sand_c(pre):#转为沙色
    h, w = pre.shape[:2]
    sand = np.full((h, w, 3), sand_bl, dtype=np.uint8)#沙画底色
    line_mask = pre == bai
    sand[line_mask] = sand_col  # 换色，颜色更深，对比更强
    sand = cv2.GaussianBlur(sand, (gb_w, gb_h), gb_p)#去掉多余模糊

    #色调增强
    sand = cv2.cvtColor(sand, cv2.COLOR_BGR2HSV)#转为HSV
    h, s, v = cv2.split(sand)#h:色相（RGB），s:饱和度，v:亮度
    s = cv2.add(s, add_s)
    v = cv2.add(v, add_v)
    sand = cv2.merge((h, s, v))
    sand = cv2.cvtColor(sand, cv2.COLOR_HSV2BGR)

    return sand

def show_img(win_name, img, max_width, max_height):
    h, w = img.shape[:2]
    scale = min(max_width / w, max_height / h, 1)  # 不放大，只缩小

    if scale < 1:
        new_w = int(w * scale)
        new_h = int(h * scale)
        show_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        show_img = img

    cv2.imshow(win_name, show_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__=="__main__":
    tk.Tk().withdraw()#弹出选择窗口
    print("Please select an image...")#避免乱码
    filepath = filedialog.askopenfilename(
        title="Select Image",
        filetypes=(
            ("Image files", "*.webp *.png *.jpg *.jpeg"),
            ("WEBP", "*.webp"),
            ("PNG", "*.png"),
            ("JPG", "*.jpg"),
            ("All files", "*.*")
        )
    )
    if not filepath:#防止空文件
        print("No file selected.")
        exit()
    
    img = cv2.imread(filepath,cv2.IMREAD_UNCHANGED)
    if img is None:#防止非图片
        print("Failed to read image.")
        exit()
    
    hui=sand_c(pre(img))
    cv2.imwrite("sand.png", hui)    
    show_img("Real Sand Art", hui, max_width, max_height)