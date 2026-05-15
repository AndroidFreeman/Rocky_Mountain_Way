from PIL import Image
import numpy as np
import cv2
def pre(file,x=600,y=800):#预处理图像(高,宽)
    with Image.open(file) as img:
        img=img.convert("RGB")#转为三色
        img=np.array(img)
        img=cv2.cvtColor(img,cv2.COLOR_BGR2LAB)#RGB转为BGR
    pre=cv2.resize(img,(y,x))#(宽,高)
    pre=cv2.GaussianBlur(pre,(5,5),1.5)#高斯去噪(src,(奇数，奇数),x向模糊,y向模糊)
    pre=cv2.bilateralFilter(pre,9,75,75)#双边滤波=模糊背景+保留边缘(src,d滤波直径,sigmaColor,sigmaSpace)
    ker=np.array([[0,-1,0],[-1,5,-1],[0,-1,0]],np.float32)#创建锐化器([核])
    pre=cv2.filter2D(pre,-1,ker)#对pre进行锐化,-1:深度不变
    pre=pre.mean(axis=2).astype(np.uint8)#转为灰度图
    cla=cv2.createCLAHE(clipLimit=4.0,tileGridSize=(10,10))#创建对比度增强器(对比度增强的强度,m*n个小格子里单独做对比度增强)
    pre=cla.apply(pre)#对pre进行对比增强

    return pre
def sand_c(hui):#转为沙色
    sha_c=np.array([
        [240,220,180],    #深沙色
        [180,140,100],    #浅沙色
        ],dtype=np.uint8)#沙子颜色
    co1=0                    #选定颜色
    r=(hui/255*sha_c[co1][0]).astype(np.uint8)
    g=(hui/255*sha_c[co1][1]).astype(np.uint8)
    b=(hui/255*sha_c[co1][2]).astype(np.uint8)
    sand=np.stack([b,g,r],axis=2)
    return sand
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