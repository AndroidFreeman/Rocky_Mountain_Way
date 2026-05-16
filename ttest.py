import tran

IMG_PATH = "outputs\mao_sand.png"
IMG_W = 1920
IMG_H = 1080

INPUT_TXT = "xy.txt"
OUTPUT_TXT = "polar.thr"
# 执行批量转换
#tran.batch_convert_xy_to_polar(INPUT_TXT, OUTPUT_TXT, IMG_W, IMG_H)
tran.apiece_convert_polar(IMG_W,IMG_H,IMG_PATH)