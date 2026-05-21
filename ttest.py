import tran,cv2

IMG_PATH = "outputs\mao_sand.png"
# IMG_PATH = "jk.webp"
# IMG_PATH = "outputs\xue_preview.png"

IMG_W = 1920
IMG_H = 1080

INPUT_TXT = "xy.txt"
OUTPUT_TXT = "polar.thr"
# 执行批量转换
#tran.batch_convert_xy_to_polar(INPUT_TXT, OUTPUT_TXT, IMG_W, IMG_H)

img = cv2.imread("flr.png")
tran.apiece_convert_polar(img)
img = tran.img_to_spiral(img)
cv2.imshow("abc", img)
cv2.waitKey(0)
# cv2.destroyAllWindows()