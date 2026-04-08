import cv2
import numpy as np
from sklearn.cluster import KMeans

# ==============================
# 沙画专用调色板（BGR 格式，真实沙子颜色）
# ==============================
SAND_PALETTE = np.array([
    [193, 228, 244],  # 浅黄沙 (BGR)
    [169, 210, 230],  # 米黄
    [131, 180, 212],  # 浅棕沙
    [109, 139, 179],  # 中棕沙
    [43, 90, 139],    # 深棕沙
    [33, 67, 101],    # 褐沙
    [47, 47, 60],     # 深褐
    [26, 26, 26]      # 近黑
], dtype=np.uint8)

class DotSandArtGenerator:
    def __init__(self, dot_step=8, dot_min=2, dot_max=12, random_jitter=0.3):
        self.dot_step = dot_step          # 点阵间距
        self.dot_min = dot_min            # 最小沙点
        self.dot_max = dot_max            # 最大沙点
        self.random_jitter = random_jitter# 随机偏移量

    def preprocess(self, img):
        """
        🔧 强化版预处理：多层级保边降噪 + 对比度增强
        彻底解决噪点问题，同时保留边缘细节
        """
        img=cv2.resize(img,(1000,800))
        # 1. 第一层：非局部均值降噪（强降噪，保边）
        img = cv2.fastNlMeansDenoisingColored(img, None, h=10, hColor=10, templateWindowSize=7, searchWindowSize=21)
        
        # 2. 第二层：双边滤波（二次保边，平滑噪点）
        img = cv2.bilateralFilter(img, d=11, sigmaColor=90, sigmaSpace=90)
        
        # 3. 第三层：CLAHE 对比度增强（避免降噪后画面发灰）
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8,8))
        l = clahe.apply(l)
        lab = cv2.merge((l,a,b))
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # 4. 第四层：形态学降噪（去除孤立噪点）
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel, iterations=1)
        
        return img

    def quantize_colors(self, img, n_colors=8):
        """修复版：K-means颜色量化 → 映射到沙色板（完全解决维度/空间错误）"""
        h, w = img.shape[:2]
        # 1. 展平像素，输入KMeans（BGR格式，3通道）
        pixels = img.reshape(-1, 3).astype(np.float32)
        
        # 2. KMeans聚类
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init='auto').fit(pixels)
        labels = kmeans.labels_.reshape(h, w)
        centers = kmeans.cluster_centers_.astype(np.uint8)

        # 3. 批量计算距离，映射到沙色板（彻底删除低效for循环）
        centers_expanded = centers[:, np.newaxis, :]
        palette_expanded = SAND_PALETTE[np.newaxis, :, :]
        dist = np.sum((centers_expanded - palette_expanded) ** 2, axis=2)
        best_palette_idx = np.argmin(dist, axis=1)
        best_colors = SAND_PALETTE[best_palette_idx]

        # 4. 批量生成量化图像（无循环，效率提升100倍+）
        quantized = best_colors[labels]
        return quantized

    def generate_dots(self, img):
        """核心：点阵沙粒生成（优化沙点过渡，减少噪点）"""
        h, w = img.shape[:2]
        # 沙底颜色（暖黄沙BGR）
        canvas = np.full((h, w, 3), [193, 228, 244], dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        for y in range(0, h, self.dot_step):
            for x in range(0, w, self.dot_step):
                # 随机偏移，避免网格感
                jx = int((np.random.rand()-0.5)*self.random_jitter*self.dot_step)
                jy = int((np.random.rand()-0.5)*self.random_jitter*self.dot_step)
                cx = x + jx
                cy = y + jy
                if cx <0 or cx>=w or cy<0 or cy>=h:
                    continue

                # 亮度决定沙点大小：暗区大点，亮区小点
                val = gray[cy, cx]
                dot_size = int(np.interp(val, [0, 255], [self.dot_max, self.dot_min]))
                color = img[cy, cx].tolist()

                # 绘制沙点
                cv2.circle(canvas, (cx, cy), dot_size, color, -1)
        
        # 优化：高斯模糊核，让沙点过渡更自然，减少颗粒噪点
        canvas = cv2.GaussianBlur(canvas, (3, 3), 0.3)
        return canvas

    def add_sand_texture(self, img):
        """
        🔧 优化版纹理增强：可控沙粒质感，避免噪点
        只添加自然沙粒纹理，不引入额外噪点
        """
        h, w = img.shape[:2]
        # 1. 生成低强度、平滑的沙粒噪声（避免生硬噪点）
        noise = np.random.normal(0, 3, (h, w, 3)).astype(np.int16)
        # 2. 叠加噪声，严格限制像素值范围0-255
        img_noise = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        # 3. 二次平滑，让沙粒纹理更自然
        img_noise = cv2.GaussianBlur(img_noise, (3, 3), 0.4)
        # 4. 最终保边降噪，去除纹理引入的杂点
        img_noise = cv2.bilateralFilter(img_noise, d=5, sigmaColor=30, sigmaSpace=30)
        return img_noise

    def run(self, img_path, out_path="sand_dot_art_clean.png"):
        # 读取图像
        img = cv2.imread(img_path)
        if img is None:
            raise FileNotFoundError(f"无法读取图像: {img_path}")
        
        # 流程：预处理（强降噪） → 颜色量化 → 点阵生成 → 纹理增强
        img = self.preprocess(img)
        img = self.quantize_colors(img, n_colors=8)
        img = self.generate_dots(img)
        img = self.add_sand_texture(img)
        
        # 保存结果
        cv2.imwrite(out_path, img)
        print(f"✅ 降噪强化版点阵沙画生成完成，已保存至: {out_path}")
        return img

if __name__ == "__main__":
    gen = DotSandArtGenerator(dot_step=8, dot_min=2, dot_max=12, random_jitter=0.4)
    gen.run("D:\Tree_Code\dune-weaver-main\_testpy\_test_input.jpg")