import tran
# 1. 填写图像尺寸
IMG_W = 1920
IMG_H = 1080
# 2. 输入原始坐标文件、输出极坐标文件
INPUT_TXT = "xy.txt"
OUTPUT_TXT = "polar.thr"
# 执行批量转换
tran.batch_convert_xy_to_polar(INPUT_TXT, OUTPUT_TXT, IMG_W, IMG_H)