import math,cv2
import numpy as np
import os
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
#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(os.path.expanduser("~"), "Desktop")
def apiece_convert_polar(img, polar_thr):
    save_dir = os.path.dirname(polar_thr)

    xy_txt = os.path.join(BASE_DIR, "save_.txt")
    polar_txt = os.path.join(BASE_DIR, "polar_.txt")

    piece_convert_xy(img, xy_txt)
    batch_convert_xy_to_polar(xy_txt, polar_txt, img.shape[1], img.shape[0])
    fill_polar(polar_txt, polar_thr)

    try:
        os.remove(xy_txt)
        os.remove(polar_txt)
    except:
        pass

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

def piece_convert_xy(img, save_txt: str):
    h, w = img.shape[:2]

    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    _, binary = cv2.threshold(
        gray,
        LINE_THRESH,
        255,
        cv2.THRESH_BINARY
    )

    binary = binary // 255

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (2, 2)
    )

    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        kernel
    )

    # 骨架化
    skel = np.zeros_like(binary, np.uint8)

    temp = binary.copy()

    cross = cv2.getStructuringElement(
        cv2.MORPH_CROSS,
        (3, 3)
    )

    while True:
        eroded = cv2.erode(temp, cross)

        temp_dilate = cv2.dilate(
            eroded,
            cross
        )

        skel |= temp - temp_dilate

        temp = eroded

        if np.sum(temp) == 0:
            break

    skeleton = skel.copy()

    contours, _ = cv2.findContours(
        skeleton,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_NONE
    )

    if not contours:
        print("未检测到线条")
        return

    # 转换成点列表
    contour_list = []

    for contour in contours:

        pts = [
            (int(p[0][0]), int(p[0][1]))
            for p in contour
        ]

        if len(pts) > 1:
            contour_list.append(pts)

    if not contour_list:
        print("未检测到有效轮廓")
        return

    center_x = w / 2
    center_y = h / 2

    all_points = []
    total_points = 0

    # 从面积最大的轮廓开始
    start_idx = np.argmax(
        [len(c) for c in contour_list]
    )

    current = contour_list.pop(start_idx)

    last_end = current[-1]

    while True:

        total_points += len(current)

        for x, y in current:

            cx_val = x - center_x
            cy_val = center_y - y

            all_points.append(
                f"{cx_val},{cy_val}"
            )

        if not contour_list:
            break

        best_idx = -1
        best_dist = float("inf")
        best_reverse = False
        best_rotate = 0

        # 从剩余轮廓中寻找最近连接
        for idx, pts in enumerate(contour_list):

            arr = np.asarray(pts)

            dx = arr[:, 0] - last_end[0]
            dy = arr[:, 1] - last_end[1]

            dist2 = dx * dx + dy * dy

            min_pos = np.argmin(dist2)

            d_forward = dist2[min_pos]

            if d_forward < best_dist:
                best_dist = d_forward
                best_idx = idx
                best_reverse = False
                best_rotate = min_pos

            d_reverse = dist2[min_pos]

            if d_reverse < best_dist:
                best_dist = d_reverse
                best_idx = idx
                best_reverse = True
                best_rotate = min_pos

        current = contour_list.pop(best_idx)

        current = (
            current[best_rotate:]
            + current[:best_rotate]
        )

        if best_reverse:
            current.reverse()

        last_end = current[-1]

    with open(
        save_txt,
        "w",
        encoding="utf-8"
    ) as f:
        f.write("\n".join(all_points))

    print(
        f"✅ 完整线条提取完成！共 {len(contours)} 条轮廓，总点数 {total_points}"
    )
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
    if image is None:
        print("图片读取失败")
        return
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

def Get_thr(out_path: str="polar.thr"):#改结果路径
    path = filedialog.askopenfilename()
    if not path:
        return
    save_dir = os.path.join(BASE_DIR, "polar")
    os.makedirs(save_dir,exist_ok=True)
    edge = gray(path)
    list = extract_layers(edge,edge)
    path_list = []
    for i,layer in enumerate(list):
        img = layer
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            img = img.copy()  # 已经是灰度，直接用
        s = os.path.join(save_dir,f"polar_{i}.thr")
        apiece_convert_polar(img,s) 
        path_list.append(s)
    merge_thr(path_list,os.path.join(save_dir,out_path))
    preview_thr(os.path.join(BASE_DIR,"polar/polar.thr"))
    open_folder(os.path.join(BASE_DIR,"polar/polar.thr"))

def preview_thr(thr_path: str, window_name="thr preview"):
    data = []

    # 读取thr
    with open(thr_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                t, r = map(float, line.split())
                data.append((t, r))
            except:
                continue

    if not data:
        print("❌ thr文件为空")
        return

    # 还原为XY（归一化到显示坐标）
    pts = []
    max_r = 400  # 显示缩放（可调）

    for theta, rho in data:
        x = int(rho * max_r * math.cos(theta))
        y = int(rho * max_r * math.sin(theta))
        pts.append([x, y])

    pts = np.array(pts, np.int32)

    # 创建画布
    canvas_size = 900
    canvas = np.zeros((canvas_size, canvas_size, 3), dtype=np.uint8)

    center = canvas_size // 2

    # 平移到中心
    pts[:, 0] += center
    pts[:, 1] += center

    # 画线
    cv2.polylines(canvas, [pts], False, (0, 255, 0), 1)

    # 显示
    cv2.imshow(window_name, canvas)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def open_folder(path):
    folder = os.path.dirname(path)
    if os.path.exists(folder):
        os.startfile(folder)

if __name__ == "__main__":
    # tran.apiece_convert_polar()
    Get_thr()
    
