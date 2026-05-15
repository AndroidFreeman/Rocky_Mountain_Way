import math

def deal_point(x: float, y: float, img_w: int, img_h: int) -> tuple[float, float]:
    """
    原点中心XY坐标 转 极坐标
    :param x: 以图像中心为原点的x坐标
    :param y: 以图像中心为原点的y坐标
    :param img_w: 图像总宽度
    :param img_h: 图像总高度
    :return: theta(弧度), rho(0~1)
    """
    # arctan函数
    theta = math.atan2(y, x)
    if theta < 0:
        theta+=2*math.pi
    # 勾股
    raw_rho = math.hypot(x, y)
    # 最长线/画的半径
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
    # 读取原始坐标
    with open(txt_in_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                px, py = map(float, line.split(","))
                t, r = deal_point(px, py, img_width, img_height)
                result_list.append(f"{t} {r}")
            except:
                continue
    # 覆盖写入文件
    with open(txt_out_path, "w", encoding="utf-8") as fw:
        fw.write("\n".join(result_list))
    print(f"批量转换完成！共处理 {len(result_list)} 个坐标，已保存至 {txt_out_path}")


# ====================== 只改这里参数即可运行 ======================
if __name__ == "__main__":
    # 1. 填写图像尺寸
    IMG_W = 1920
    IMG_H = 1080
    # 2. 输入原始坐标文件、输出极坐标文件
    INPUT_TXT = "原始坐标.txt"
    OUTPUT_TXT = "极坐标结果.txt"

    # 执行批量转换
    batch_convert_xy_to_polar(INPUT_TXT, OUTPUT_TXT, IMG_W, IMG_H)