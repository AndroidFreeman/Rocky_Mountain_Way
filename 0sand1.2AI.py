import math, cv2
import numpy as np
from shapely.geometry import LineString
from shapely import offset_curve
from tkinter import filedialog

MAX_POINT1 = 20000

pi2 = 2 * math.pi
LINE_THRESH = 80
MAX_POINT = 3000

MAX_RHO_GAP = 0.1
MAX_THETA_GAP = 0.5
INSERT_CNT = 4

P = -7

ANGLE_JUMP_LIMIT = 2.0


def apiece_convert_polar(img, polar_thr="polar.thr"):
    h, w = img.shape[:2]
    xy_txt = "polar/save_.txt"
    polar_txt = "polar/polar_.txt"
    piece_convert_xy(img, xy_txt)
    batch_convert_xy_to_polar(xy_txt, polar_txt, w, h)
    fill_polar(polar_txt, polar_thr)


def img_to_spiral(img, offset=P):
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
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
            l = offset_curve(line, offset * i)
            p = np.array(l.coords, np.int32)
            if i % 2:
                p = p[::-1]
            pts_list.extend(p)
        except:
            break
    if pts_list:
        cv2.polylines(res, [np.array(pts_list)], False, 255, 2)
    return res


def piece_convert_xy(img, save_txt: str):
    h, w = img.shape[:2]

    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    _, binary = cv2.threshold(gray, LINE_THRESH, 255, cv2.THRESH_BINARY)
    binary = binary // 255

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    skel = np.zeros_like(binary, np.uint8)
    temp = binary.copy()
    cross = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))

    while True:
        eroded = cv2.erode(temp, cross)
        temp_dilate = cv2.dilate(eroded, cross)
        skel |= temp - temp_dilate
        temp = eroded
        if np.sum(temp) == 0:
            break

    skeleton = skel.copy()

    contours, _ = cv2.findContours(skeleton, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    if not contours:
        print("未检测到线条")
        return

    contour_list = []

    for contour in contours:
        pts = [(int(p[0][0]), int(p[0][1])) for p in contour]
        if len(pts) > 1:
            contour_list.append(pts)

    if not contour_list:
        print("未检测到有效轮廓")
        return

    center_x = w / 2
    center_y = h / 2

    all_points = []
    total_points = 0

    start_idx = np.argmax([len(c) for c in contour_list])

    current = contour_list.pop(start_idx)

    last_end = current[-1]

    while True:

        total_points += len(current)

        for x, y in current:
            cx_val = x - center_x
            cy_val = center_y - y
            all_points.append(f"{cx_val},{cy_val}")

        if not contour_list:
            break

        best_idx = -1
        best_dist = float("inf")
        best_reverse = False
        best_rotate = 0

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

        current = current[best_rotate:] + current[:best_rotate]

        if best_reverse:
            current.reverse()

        last_end = current[-1]

    with open(save_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(all_points))

    print(f"✅ 完整线条提取完成！共 {len(contours)} 条轮廓，总点数 {total_points}")


# =====================
# 极坐标连续映射
# =====================
def deal_point(x, y, w, h, last_theta=0.0):
    arc = math.atan2(y, x)

    last_ang = last_theta % pi2
    if last_ang > math.pi:
        last_ang -= pi2

    diff = arc - last_ang

    if diff > math.pi:
        diff -= pi2
    elif diff < -math.pi:
        diff += pi2

    theta = last_theta + diff

    raw_rho = math.hypot(x, y)
    max_r = math.hypot(w, h) / 2
    rho = raw_rho / max_r
    rho = max(0.0, min(1.0, rho))

    return theta, rho


def batch_convert_xy_to_polar(txt_in_path, txt_out_path, img_width, img_height):
    result_list = []
    last_angle = 0.0

    with open(txt_in_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                px, py = map(float, line.split(","))
                t, r = deal_point(px, py, img_width, img_height, last_angle)
                last_angle = t
                result_list.append(f"{t:.3f} {r:.3f}")
            except:
                continue

    with open(txt_out_path, "w", encoding="utf-8") as fw:
        fw.write("\n".join(result_list))

    print(f"批量转换完成！共处理 {len(result_list)} 个坐标，已保存至 {txt_out_path}")


def lerp(a, b, t):
    return a + (b - a) * t


def process_polar_data(raw_points):
    res = []

    for tar_theta, tar_rho in raw_points:
        if not res:
            res.append((tar_theta, tar_rho))
            continue

        last_theta, last_rho = res[-1]

        theta_diff = abs(tar_theta - last_theta)
        rho_diff = abs(tar_rho - last_rho)

        if theta_diff > MAX_THETA_GAP or rho_diff > MAX_RHO_GAP:
            for i in range(1, INSERT_CNT + 1):
                ratio = i / (INSERT_CNT + 1)
                mid_t = lerp(last_theta, tar_theta, ratio)
                mid_r = lerp(last_rho, tar_rho, ratio)
                res.append((mid_t, mid_r))

        res.append((tar_theta, tar_rho))

    return res


def fill_polar(txt_in_path, thr_out_path):
    origin_data = []

    with open(txt_in_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            t, r = map(float, line.split())
            origin_data.append((t, r))

    final_points = process_polar_data(origin_data)

    with open(thr_out_path, "w", encoding="utf-8") as fw:
        for th, rh in final_points:
            fw.write(f"{th:.3f} {rh:.3f}\n")

    print(f"处理完成！")
    print(f"原始点数：{len(origin_data)}")
    print(f"处理后总点数：{len(final_points)}")
    print(f"已保存至 {thr_out_path}")


def gray(image):
    gray = cv2.imread(image, 0)
    gray_blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edge = cv2.Canny(gray_blur, 80, 160)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    edge = cv2.morphologyEx(edge, cv2.MORPH_CLOSE, kernel)
    return edge


def extract_layers(edge, gray_img, min_area=100):
    num_labels, labels = cv2.connectedComponents(edge)
    layers = []
    for i in range(1, num_labels):
        mask = (labels == i).astype(np.uint8) * 255
        if cv2.countNonZero(mask) < min_area:
            continue
        layer = cv2.bitwise_and(gray_img, gray_img, mask=mask)
        layers.append(layer)
    return layers


def merge_thr(thr_path_list, save_merge_path):
    all_lines = []
    for path in thr_path_list:
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                all_lines.extend(lines)
        except Exception as e:
            print(f"跳过异常文件 {path}: {e}")

    if len(all_lines) > MAX_POINT1:
        step = len(all_lines) // MAX_POINT1
        all_lines = all_lines[::step]

    with open(save_merge_path, "w", encoding="utf-8") as fw:
        fw.writelines(all_lines)
    print(f"合并完成，共 {len(all_lines)} 个点位")


def Get_thr(out_path="polar.thr"):
    import os
    os.makedirs("polar", exist_ok=True)

    path = filedialog.askopenfilename()
    edge = gray(path)
    list = extract_layers(edge, edge)
    path_list = []
    for i, layer in enumerate(list):
        img = layer
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            img = img.copy()
        s = "polar/polar_" + str(i) + ".thr"
        apiece_convert_polar(img, s)
        path_list.append(s)
    merge_thr(path_list, out_path)


if __name__ == "__main__":
    Get_thr()
