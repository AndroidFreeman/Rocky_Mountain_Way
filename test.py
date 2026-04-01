#沙画优化
import cv2


from tkinter import filedialog
import numpy as np
path = filedialog.askopenfilename()



def High_Contrast_Edge(image):#高对比边缘
    gray = cv2.imread(image,0)
    #edge = cv2.Canny(gray,200,256)#后两个参数起点调高敏感度降低
    sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=1)#ksize决定灵敏度
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=1)
    edge = cv2.magnitude(sobel_x, sobel_y)
    edge = cv2.convertScaleAbs(edge) 
    HC_image = cv2.convertScaleAbs(edge, alpha=1.5, beta=20)#a,b决定对比度和明度
    return HC_image

def Color_Change(gray_1):#改色&高斯
    gray = 255 - gray_1#反色
    edge = cv2.Canny(gray_1,200,256)
    edge_color = cv2.cvtColor(edge, cv2.COLOR_GRAY2BGR)
    #image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    #lower_w = (150, 150, 150)
    #upper_w = (255, 255, 255)
    #lower_b = (0, 0, 0)
    #upper_b = (150, 150, 150)
    #white = cv2.inRange(image, lower_w, upper_w)
    #black = cv2.inRange(image, lower_b, upper_b)
    #image[black > 0] = [100, 140, 180]
    #image[white > 0] = [0,0,0]
    sand = np.zeros((gray.shape[0], gray.shape[1], 3), dtype=np.uint8)

    # 根据灰度比例映射
    sand[:, :, 0] = gray * 0.4   # B
    sand[:, :, 1] = gray * 0.6   # G
    sand[:, :, 2] = gray * 0.8   # R

    return sand
    #blend = cv2.addWeighted(image, 0.8, edge_color, 0.6, 0)
    #blur = cv2.GaussianBlur(image, (15, 15), 0)#高斯模糊
    #return blur

def dilate(image):
    core = np.ones((3,3),np.uint8)
    after = cv2.dilate(image,core,iterations=1)#程度,次数
    return after

cv2.imshow("HC",High_Contrast_Edge(path))
cv2.waitKey(0)
cv2.destroyAllWindows()
cv2.imshow("dilate",dilate(High_Contrast_Edge(path)))
cv2.waitKey(0)
cv2.destroyAllWindows()
cv2.imshow("sand",Color_Change(dilate(High_Contrast_Edge(path))))
cv2.waitKey(0)
cv2.destroyAllWindows()