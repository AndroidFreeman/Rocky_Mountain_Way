import cv2
from tkinter import filedialog
import numpy as np

def gray(image):
    gray = cv2.imread(image)
    gray_blur = cv2.GaussianBlur(gray, (11, 11), 0)
    cv2.imshow("GOSE",gray_blur)
    cv2.waitKey(0)
    edge = cv2.Canny(gray_blur,80,160)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7))
    edge = cv2.morphologyEx(edge,cv2.MORPH_CLOSE,kernel)
    cv2.imshow("END",edge)
    cv2.waitKey(0)
    return edge



def extract_layers(edge, min_area=100):
    """
    输入:
        edge: 已闭合的黑白轮廓图
    输出:
        layers: 每个闭合区域一个mask
    """

    contours, hierarchy = cv2.findContours(
        edge,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_NONE
    )

    layers = []

    for i, cnt in enumerate(contours):

        area = cv2.contourArea(cnt)

        if area < min_area:
            continue

        # 创建单层mask
        mask = np.zeros_like(edge)

        cv2.drawContours(
            mask,
            [cnt],
            -1,
            255,
            thickness=cv2.FILLED
        )

        M = cv2.moments(cnt)

        if M["m00"] != 0:
            cx = int(M["m10"]/M["m00"])
            cy = int(M["m01"]/M["m00"])
        else:
            cx = cy = 0

        layers.append({
            "id": i,
            "mask": mask,
            "contour": cnt,
            "center": (cx,cy),
            "area": area
        })

    return layers




def outward_spiral_layer(layer):
    """
    输入:
        layer = extract_layers()[i]

    输出:
        spiral_points
        end_point
    """

    mask = layer["mask"]

    h,w = mask.shape[:2]

    image_center = np.array([w//2,h//2])

    # 起点：轮廓中心
    cx,cy = layer["center"]

    kernel=np.ones((3,3),np.uint8)

    spiral_points=[(cx,cy)]

    last_point=np.array([cx,cy])

    current=np.zeros_like(mask)

    current[cy,cx]=255

    outer_ring=None

    while True:

        expanded=cv2.dilate(current,kernel,iterations=1)

        expanded=cv2.bitwise_and(expanded,mask)

        ring=cv2.subtract(expanded,current)

        if not np.any(ring):
            break

        contours,_=cv2.findContours(ring,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)

        if len(contours)==0:
            break

        pts=contours[0][:,0,:]

        # 保证连续接线
        dists=np.sum((pts-last_point)**2,axis=1)

        start_idx=np.argmin(dists)

        pts=np.concatenate((pts[start_idx:],pts[:start_idx]))

        spiral_points.extend([tuple(p) for p in pts])

        last_point=pts[-1]

        outer_ring=pts.copy()

        current=expanded

    # 最后固定终点
    if outer_ring is not None:

        dists=np.sum((outer_ring-image_center)**2,axis=1)

        idx=np.argmin(dists)

        end_point=tuple(outer_ring[idx])

        spiral_points.append(end_point)

    else:
        end_point=(cx,cy)

    return spiral_points,end_point



path = filedialog.askopenfilename()
gray = gray(path)
layerlist = extract_layers(gray)
