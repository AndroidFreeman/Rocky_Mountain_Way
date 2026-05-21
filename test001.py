import tran,sanddraw,cv2
from tkinter import filedialog

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
    # 写入合并文件
    with open(save_merge_path, "w", encoding="utf-8") as fw:
        fw.writelines(all_lines)
    print(f"合并完成，共 {len(all_lines)} 个点位")

def Get_thr(out_path: str="polar.thr"):
    path = filedialog.askopenfilename()
    edge = sanddraw.gray(path)
    list = sanddraw.extract_layers(edge,edge)
    path_list = []
    for i,layer in enumerate(list):
        img = layer
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            img = img.copy()  # 已经是灰度，直接用
        s = "polar_" + str(i) + ".thr"
        tran.apiece_convert_polar(img,s) 
        path_list.append(s)
        # img = tran.img_to_spiral(img)
        # cv2.imshow("abc", img)
        # cv2.waitKey(0)
    merge_thr(path_list,out_path)

if __name__ == "__main__":
    # tran.apiece_convert_polar()
    Get_thr()