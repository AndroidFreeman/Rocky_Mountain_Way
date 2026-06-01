import math,cv2
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely import offset_curve
from tkinter import filedialog

MAX_POINT1 = 20000

pi2 = 2*math.pi
LINE_THRESH = 80       # 线条灰度阈值(越小越容易识别细线)
MAX_POINT = 3000       # 最多提取坐标数

MAX_RHO_GAP = 0.1      # 极径(rho)最大允许差值(0~1范围)
MAX_THETA_GAP = 0.5     # 弧度(theta)最大允许差值
INSERT_CNT = 4       # 两点之间插入几个过渡点

P = -7                  #-7:疏,-3:密

def apiece_convert_polar(img,polar_thr :str = "polar.thr"):# 传入图img
    h, w = img.shape[:2]
    xy_txt = "save_.txt"
    polar_txt = "polar_.txt"
    # img = img_to_spiral(img)
    piece_convert_xy(img,xy_txt)
    batch_convert_xy_to_polar(xy_txt,polar_txt,w,h)
    fill_polar(polar_txt,polar_thr)

#
def img_to_spiral(img, offset=P):
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()  # 已经是灰度，直接用
    _, bin_ = cv2.threshold(gray, LINE_THRESH, 255, cv2.THRESH_BINARY)
    cnts, _ = cv2.findContours(bin_, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    main_cnt = max(cnts, key=cv2.contourArea).squeeze()
    line = LineString(main_cnt)
    res = np.zeros_like(img)
    pts_list = []
    for i in range(50):
        try:
            l = offset_curve(line, offset*i)
            p = np.array(l.coords, np.int32)
            if i%2: p = p[::-1]
            pts_list.extend(p)
        except: break
    if pts_list:
        cv2.polylines(res, [np.array(pts_list)], False, 255, 2)
    return res
"""
def get_shape_spiral(img, step=-5):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, bin_img = cv2.threshold(gray, LINE_THRESH, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    # 最大外轮廓
    cnt = max(contours, key=cv2.contourArea).squeeze()
    line = LineString(cnt)
    h,w = img.shape[:2]
    res = np.zeros((h,w,3),np.uint8)
    for i in range(1,50):
        try:
            inner = offset_curve(line, step*i)
            pts = np.array(list(inner.coords),np.int32)
            cv2.polylines(res,[pts],True,(255,255,0),1)
        except:
            break
    return res
"""

def piece_convert_xy(img, save_txt: str):
    h, w = img.shape[:2]
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    # 二值化 白底黑线用INV，白线去掉INV
    _, binary = cv2.threshold(gray, LINE_THRESH, 255, cv2.THRESH_BINARY)
    binary = binary // 255

    # 优化细化，减少断线
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    skel = np.zeros_like(binary, np.uint8)
    temp = binary.copy()
    cross = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
    while True:
        eroded = cv2.erode(temp, cross)
        temp_dilate = cv2.dilate(eroded, cross)
        skel |= temp - temp_dilate
        temp = eroded
        if np.sum(temp) == 0:
            break

    skeleton = skel.copy()

    # 修复：处理所有轮廓而不是只取最大
    contours, _ = cv2.findContours(skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        print("未检测到线条")
        return

    center_x = w / 2
    center_y = h / 2
    all_points = []
    total_points = 0
    for idx, contour in enumerate(contours):
        ordered_points = [(p[0][0], p[0][1]) for p in contour]
        total_points += len(ordered_points)
        for x, y in ordered_points:
            cx_val = x - center_x
            cy_val = center_y - y
            all_points.append(f"{cx_val},{cy_val}")

    with open(save_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(all_points))

    print(f"✅ 完整线条提取完成！共 {len(contours)} 条轮廓，总点数 {total_points}")
"""
def piece_convert_xy(img,save_txt: str):

    # 读取图像+灰度化
    h, w = img.shape[:2]
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    # 二值化提取线条（黑线条白背景/白线条黑背景自行调换）
    _, binary = cv2.threshold(gray, LINE_THRESH, 255, cv2.THRESH_BINARY)

    # 以图像中心为原点计算坐标
    # 图像像素原点：左上角(0,0)；中心原点：(0,0)在图片正中心
    center_x = w / 2
    center_y = h / 2

    # 获取所有线条像素坐标
    y_coords, x_coords = np.where(binary > 0)

    points = []
    for x, y in zip(x_coords, y_coords):
        # 转换为【中心为原点】XY
        cx = x - center_x
        cy = center_y - y
        points.append(f"{cx},{cy}")
    # 写入TXT
    with open(save_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(points))

    print(f"提取完成！共{len(points)}个坐标点，已保存至 {save_txt}")
"""
def deal_point(x: float, y: float, img_w: int, img_h: int, last_theta: float = 0.0) -> tuple[float, float]:
    """
    中心原点XY转**连续递增/递减弧度角度**
    转圈时角度持续增大/减小, 不会跳变, 范围可远超±2π
    :param x: 中心原点x
    :param y: 中心原点y
    :param img_w: 图像宽度
    :param img_h: 图像高度
    :param last_theta: 上一个点的连续角度
    :return: 当前连续角度theta, 归一化rho, 本次基准弧度
    """
    # atan2=arctan函数(返回 -Pi ~ +Pi)
    arc = math.atan2(y, x)
    last_ang = last_theta % pi2
    if last_ang > math.pi:
        last_ang -=pi2
    
    # 保证角度连续
    diff = arc - last_ang
    if diff > math.pi:
        diff -= pi2
    elif diff < -math.pi:
        diff += pi2
    theta = last_theta + diff
    # 勾股求(x,y)的模长
    raw_rho = math.hypot(x, y)
    # 最长线/图的半径
    max_r = math.hypot(img_w, img_h)/2
    # 归一化到 0~1
    rho = raw_rho/max_r
    # 限制范围 0≤ρ≤1
    rho = max(0.0, min(1.0, rho))
    return theta, rho


def batch_convert_xy_to_polar(txt_in_path: str, txt_out_path: str, img_width: int, img_height: int):
    """
    批量读取txt每行x,y 批量转极坐标 覆盖写入输出txt
    :param txt_in_path: 原始坐标txt路径 格式：每行 x,y
    :param txt_out_path: 输出极坐标txt路径
    :param img_width: 图像宽度
    :param img_height: 图像高度
    """
    result_list = []
    last_angle = 0.0
    # 读取原始坐标
    with open(txt_in_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            #空行则退出
            if not line:
                continue
            try:
                # .split(",") ","分隔才能读取
                px, py = map(float, line.split(","))
                t, r = deal_point(px, py, img_width, img_height, last_angle)
                last_angle = t
                result_list.append(f"{t:.3f} {r:.3f}")
            except:
                continue
    # 覆盖写入文件
    with open(txt_out_path, "w", encoding="utf-8") as fw:
        # "\n".join(列表)把列表里的每一项用\n连起来
        fw.write("\n".join(result_list))
    print(f"批量转换完成！共处理 {len(result_list)} 个坐标，已保存至 {txt_out_path}")

def lerp(a, b, t):
    return a + (b - a) * t

def process_polar_data(raw_points):
    res = []
    # 开头插入原点 0 0
    # res.append((0.0, 0.0))
    
    for tar_theta, tar_rho in raw_points:
        if not res:  # 第一个点直接加入，不做插值
            res.append((tar_theta, tar_rho))
            continue
        last_theta, last_rho = res[-1]
        
        # 同时判断弧度差、极径差，任一超标就补点
        theta_diff = abs(tar_theta - last_theta)
        rho_diff = abs(tar_rho - last_rho)
        
        if theta_diff > MAX_THETA_GAP or rho_diff > MAX_RHO_GAP:
            # 线性均匀插值
            for i in range(1, INSERT_CNT + 1):
                ratio = i / (INSERT_CNT + 1)
                mid_t = lerp(last_theta, tar_theta, ratio)
                mid_r = lerp(last_rho, tar_rho, ratio)
                res.append((mid_t, mid_r))

        # 存入原始目标点
        res.append((tar_theta, tar_rho))
    return res

def fill_polar(txt_in_path: str, thr_out_path: str):
    origin_data = []
    # 读取极坐标：弧度  rho(0~1)
    with open(txt_in_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            t, r = map(float, line.split())
            origin_data.append((t, r))
        
    # # 保证polar坐标<=
    # if len(origin_data) > MAX_POINT:
    #     step = len(origin_data)//MAX_POINT
    #     origin_data = origin_data[::step]

    # origin_data.append((0.0,0.0))

    final_points = process_polar_data(origin_data)

    # 写入输出文件
    with open(thr_out_path, "w", encoding="utf-8") as fw:
        for th, rh in final_points:
            fw.write(f"{th:.3f} {rh:.3f}\n")

    print(f"处理完成！")
    print(f"原始点数：{len(origin_data)}")
    print(f"处理后总点数：{len(final_points)}")
    print(f"已保存至 {thr_out_path}")

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

def merge_thr(thr_path_list, save_merge_path):
    """
    合并多个thr点位文件
    :param thr_path_list: 所有thr路径列表
    :param save_merge_path: 合并后保存路径
    """
    all_lines = []
    for path in thr_path_list:
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                all_lines.extend(lines)
        except Exception as e:
            print(f"跳过异常文件 {path}: {e}")
    
    if len(all_lines) > MAX_POINT1:
        step = len(all_lines)//MAX_POINT1
        all_lines = all_lines[::step]
    
    # 写入合并文件
    with open(save_merge_path, "w", encoding="utf-8") as fw:
        fw.writelines(all_lines)
    print(f"合并完成，共 {len(all_lines)} 个点位")

def Get_thr(out_path: str="polar.thr"):
    path = filedialog.askopenfilename()
    edge = gray(path)
    list = extract_layers(edge,edge)
    path_list = []
    for i,layer in enumerate(list):
        img = layer
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            img = img.copy()  # 已经是灰度，直接用
        s = "polar_" + str(i) + ".thr"
        apiece_convert_polar(img,s) 
        path_list.append(s)
        # img = tran.img_to_spiral(img)
        # cv2.imshow("abc", img)
        # cv2.waitKey(0)
    merge_thr(path_list,out_path)



if __name__ == "__main__":
    # tran.apiece_convert_polar()
    Get_thr()