import numpy as np
import cv2
def pre(file,x=600,y=800):#预处理图像(高,宽)
    img=cv2.imread(file)
    p1=cv2.resize(img,(y,x))#(宽,高)
    p2=cv2.GaussianBlur(p1,(5,5),1.5)#高斯去噪(src,(奇数，奇数),x向模糊,y向模糊)
    p3=cv2.bilateralFilter(p2,9,75,75)#双边滤波=模糊背景+保留边缘(src,d滤波直径,sigmaColor,sigmaSpace)
    p4=p3.mean(axis=2).astype(np.uint8)#转为灰度图
    cla=cv2.createCLAHE(clipLimit=4.0,tileGridSize=(10,10))#创建对比度增强器(对比度增强的强度,m*n个小格子里单独做对比度增强)
    p5=cla.apply(p4)#对p4进行对比增强

    return p5
def sand_c(hui):#转为沙色
    sha_c=np.array([
        [240,220,180],#深沙色
        [180,140,100],#浅沙色
        ],dtype=np.uint8)#沙子颜色
    co1=0                    #选定颜色
    r=(hui/255*sha_c[co1][0]).astype(np.uint8)
    g=(hui/255*sha_c[co1][1]).astype(np.uint8)
    b=(hui/255*sha_c[co1][2]).astype(np.uint8)
    sand=np.stack([b,g,r],axis=2)
    hui_img=sand.copy()
    return hui_img
def live_sand():#增加现实感
    return
def trans(file,x=600,y=800):
    pre_img=pre(file,x,y)
    sand_img=sand_c(pre_img)
    live_img=live_sand(sand_img)
    return live_img

hui=sand_c(pre("ren.jpg"))
cv2.imshow("image",hui)
cv2.waitKey(0)