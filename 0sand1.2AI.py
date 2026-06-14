import math, cv2
import numpy as np
from shapely.geometry import LineString
from shapely import offset_curve
from tkinter import filedialog
from scipy.spatial import KDTree

# =====================
# 参数区
# =====================
MAX_POINT1 = 20000

LINE_THRESH = 80

MAX_RHO_GAP = 0.1
MAX_THETA_GAP = 0.5

INSERT_CNT = 4

DIST_LIMIT = 60          # 防止跨结构连接
ANGLE_JUMP_LIMIT = 2.0

pi2 = 2 * math.pi


# =====================
# 图像预处理
# =====================
def gray(image_path):
    gray = cv2.imread(image_path, 0)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edge = cv2.Canny(blur, 80, 160)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    edge = cv2.morphologyEx(edge, cv2.MORPH_CLOSE, kernel)
    return edge


# =====================
# 分层（升级：contour + bbox）
# =====================
def extract_layers(edge):
    contours, _ = cv2.findContours(
        edge,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_NONE
    )

    infos = []

    for cnt in contours:
        if len(cnt) < 30:
            continue

        pts = [(p[0][0], p[0][1]) for p in cnt]
        arr = np.array(pts)

        x_min, y_min = arr.min(axis=0)
        x_max, y_max = arr.max(axis=0)

        infos.append({
            "pts": pts,
            "center": arr.mean(axis=0),
            "bbox": (x_min, y_min, x_max, y_max)
        })

    return infos


# =====================
# KDTree
# =====================
def build_tree(infos):
    centers = np.array([i["center"] for i in infos])
    return KDTree(centers)


# =====================
# 稳定轮廓拼接（核心修复）
# =====================
def piece_convert_xy(edge, save_txt):
    infos = extract_layers(edge)

    if not infos:
        print("未检测到轮廓")
        return

    tree = build_tree(infos)

    used = set()

    start_idx = np.argmax([len(i["pts"]) for i in infos])

    current = infos[start_idx]["pts"]
    used.add(start_idx)

    last_pt = np.array(current[-1])

    all_points = []
    total = 0

    while len(used) < len(infos):

        for x, y in current:
            all_points.append(f"{x},{y}")
        total += len(current)

        # KDTree 取候选
        _, idxs = tree.query(last_pt, k=min(6, len(infos)))

        if not isinstance(idxs, np.ndarray):
            idxs = [idxs]

        best_idx = -1
        best_dist = float("inf")
        best_rot = 0

        for idx in idxs:

            if idx in used:
                continue

            pts = infos[idx]["pts"]
            arr = np.array(pts)

            d = np.sum((arr - last_pt) ** 2, axis=1)
            min_pos = np.argmin(d)
            dist = d[min_pos]

            if dist > DIST_LIMIT ** 2:
                continue

            if dist < best_dist:
                best_dist = dist
                best_idx = idx
                best_rot = min_pos

        if best_idx == -1:
            break

        used.add(best_idx)

        next_pts = infos[best_idx]["pts"]

        # rotate
        next_pts = next_pts[best_rot:] + next_pts[:best_rot]

        current = next_pts
        last_pt = np.array(current[-1])

    with open(save_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(all_points))

    print(f"XY提取完成：{total} 点")


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

    # 限制跳变（关键稳定点）
    diff = max(-ANGLE_JUMP_LIMIT, min(ANGLE_JUMP_LIMIT, diff))

    theta = last_theta + diff

    rho = math.hypot(x, y) / (math.hypot(w, h) / 2)
    rho = max(0.0, min(1.0, rho))

    return theta, rho


# =====================
# XY → Polar
# =====================
def batch_convert_xy_to_polar(in_path, out_path, w, h):
    res = []
    last = 0.0

    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            x, y = map(float, line.split(","))

            t, r = deal_point(x, y, w, h, last)
            last = t

            res.append(f"{t:.3f} {r:.3f}")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(res))

    print("极坐标转换完成")


# =====================
# 插值
# =====================
def lerp(a, b, t):
    return a + (b - a) * t


def process_polar_data(raw):
    res = []

    for t, r in raw:
        if not res:
            res.append((t, r))
            continue

        lt, lr = res[-1]

        if abs(t - lt) > MAX_THETA_GAP or abs(r - lr) > MAX_RHO_GAP:
            for i in range(1, INSERT_CNT + 1):
                k = i / (INSERT_CNT + 1)
                res.append((lerp(lt, t, k), lerp(lr, r, k)))

        res.append((t, r))

    return res


def fill_polar(in_path, out_path):
    data = []

    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            t, r = map(float, line.split())
            data.append((t, r))

    final = process_polar_data(data)

    with open(out_path, "w", encoding="utf-8") as f:
        for t, r in final:
            f.write(f"{t:.3f} {r:.3f}\n")

    print(f"完成：{len(final)} 点")


# =====================
# 主入口
# =====================
def Get_thr(out_path="polar.thr"):
    path = filedialog.askopenfilename()

    edge = gray(path)
    h, w = edge.shape[:2]

    xy = "save_.txt"
    polar = "polar_.txt"

    piece_convert_xy(edge, xy)

    batch_convert_xy_to_polar(xy, polar, w, h)

    fill_polar(polar, out_path)


if __name__ == "__main__":
    Get_thr()
