import math
import cv2
import numpy as np

pi2=2*math.pi

def apiece_convert_polar(img_width: int, img_height: int,img_path: str,polar_thr :str = "polar.thr"):
    xy_txt = "save_.txt"
    piece_convert_xy(img_path,xy_txt)
    batch_convert_xy_to_polar(xy_txt,polar_thr,img_width,img_height)


def piece_convert_xy(img_path: str,save_txt: str):

    # 2. 读取图像+灰度化
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. 二值化提取线条（黑线条白背景/白线条黑背景自行调换）
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    # 4. 以图像中心为原点计算坐标
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

    # 5. 写入TXT
    with open(save_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(points))

    print(f"提取完成！共{len(points)}个坐标点，已保存至 {save_txt}")



def deal_point(x: float, y: float, img_w: int, img_h: int, last_theta: float = 0.0) -> tuple[float, float]:
    """
    中心原点XY转**连续递增/递减弧度角度**
    转圈时角度持续增大/减小，不会跳变，范围可远超±2π
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


# ====================== 只改这里参数即可运行 ======================
if __name__ == "__main__":
    # 1. 填写图像尺寸
    IMG_W = 1920
    IMG_H = 1080
    # 2. 输入原始坐标文件、输出极坐标文件
    INPUT_TXT = "原始坐标.txt"
    OUTPUT_TXT = "极坐标结果.thr"

    # 执行批量转换
    batch_convert_xy_to_polar(INPUT_TXT, OUTPUT_TXT, IMG_W, IMG_H)