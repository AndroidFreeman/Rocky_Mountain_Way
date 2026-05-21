import cv2
from tkinter import filedialog
import numpy as np

def gray(image):
    gray = cv2.imread(image,0)
    gray_blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edge = cv2.Canny(gray_blur,80,160)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7))
    edge = cv2.morphologyEx(edge,cv2.MORPH_CLOSE,kernel)
    # cv2.imshow("gray",edge)
    # cv2.waitKey(0)
    return edge

def extract_layers(edge,gray_img,min_area=100):
    num_labels,labels=cv2.connectedComponents(edge)
    layers=[]
    for i in range(1,num_labels):
        mask=(labels==i).astype(np.uint8)*255
        if cv2.countNonZero(mask)<min_area:
            continue
        layer=cv2.bitwise_and(gray_img,gray_img,mask=mask)
        layers.append(layer)

    return layers

if __name__ == "__main__":
    path = filedialog.askopenfilename()
    edge = gray(path)
    extract_layers(edge, edge)
    
