#沙画优化
import cv2
from tkinter import filedialog
import numpy as np

def resize_image(image, width, height):
    resized_image = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    return resized_image

path = filedialog.askopenfilename()
#参数设置
gose = 7
ksize_s = 3
contrast = 1.5
bright = 20
dilate_s = 3
dilatetime_s = 1

#参数更改
def change_parameters():
    global gose, ksize_s, contrast, bright, dilate_s, dilatetime_s
    gose = int(input("请输入高斯模糊核大小（建议为11）："))
    ksize_s = int(input("请输入Sobel算子核大小（建议为3）："))
    contrast = float(input("请输入对比度调整系数（建议1.5）："))
    bright = int(input("请输入亮度调整值（建议为10）："))
    dilate_s = int(input("请输入膨胀核大小（建议为3）："))
    dilatetime_s = int(input("请输入膨胀迭代次数："))

def High_Contrast_Edge(image):#高对比边缘
    gray = cv2.imread(image,0)
    #gray = resize_image(gray, 1280, 860)
    gray_blur = cv2.GaussianBlur(gray, (gose, gose), 0)#高斯
    #edge = cv2.Canny(gray_blur,200,256)#后两个参数起点调高敏感度降低
    sobel_x = cv2.Sobel(gray_blur, cv2.CV_64F, 1, 0, ksize=ksize_s)#ksize决定灵敏度
    sobel_y = cv2.Sobel(gray_blur, cv2.CV_64F, 0, 1, ksize=ksize_s)
    edge = cv2.magnitude(sobel_x, sobel_y)
    edge = cv2.convertScaleAbs(edge) 
    #_, edge = cv2.threshold(edge, 50, 255, cv2.THRESH_BINARY)
    HC_image = cv2.convertScaleAbs(edge, alpha=contrast, beta=bright)#a,b决定对比度和明度
    return HC_image

def Color_Change(gray_1):#改色
    gray = 255 - gray_1#反色
    edge = cv2.Canny(gray_1,200,256)
    edge_color = cv2.cvtColor(edge, cv2.COLOR_GRAY2BGR)
    sand = np.zeros((gray.shape[0], gray.shape[1], 3), dtype=np.uint8)
    # 根据灰度比例映射
    sand[:, :, 0] = gray * 0.4   # B
    sand[:, :, 1] = gray * 0.6   # G
    sand[:, :, 2] = gray * 0.8   # R
    return sand

def dilate(image):
    core = np.ones((dilate_s,dilate_s),np.uint8)
    after = cv2.dilate(image,core,iterations=dilatetime_s)#程度,次数
    return after
def output(image):
    cv2.imshow("HC",High_Contrast_Edge(path))
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cv2.imshow("dilate",dilate(High_Contrast_Edge(path)))
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cv2.imshow("sand",Color_Change(dilate(High_Contrast_Edge(path))))
    cv2.waitKey(0)
    cv2.destroyAllWindows()


while True:
    check = input("调整参数？(y/n): ")
    if check.lower() == 'n':
        output(path)
        check = input("是否换图？(y/n): ")
        if check.lower() == 'y':
            path = filedialog.askopenfilename()
            pass
        else:
            print("程序结束。")
            exit()
    else:
        change_parameters()
        output(path)
        check = input("是否继续调整参数？(y/n): ")
        if check.lower() == 'y':
            continue
        else:
            print("程序结束。")
            exit()

