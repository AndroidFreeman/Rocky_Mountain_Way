import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans


class SandArtGenerator:
    def __init__(self,
                 dot_min=2,
                 dot_max=8,
                 step=6,
                 jitter=0.4,
                 sand_colors=8):
        # 核心参数（和你方案面板完全对应）
        self.dot_min = dot_min
        self.dot_max = dot_max
        self.step = step
        self.jitter = jitter
        self.sand_colors = sand_colors

        # 沙画专用调色板
        self.sand_palette = np.array([
            [210, 240, 250],  # 浅黄
            [180, 210, 240],  # 中黄
            [140, 170, 220],  # 深黄
            [110, 140, 190],  # 浅棕
            [90, 110, 160],   # 棕
            [70, 80, 120],    # 深棕
            [50, 50, 80],     # 暗棕
            [30, 30, 50]      # 近黑
        ], dtype=np.uint8)

    # ==========================
    # 1. 图像预处理模块
    # ==========================
    def preprocess(self, img):
        img = cv2.bilateralFilter(img, 9, 75, 75)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_channel = clahe.apply(l_channel)
        lab = cv2.merge((l_channel, a, b))
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # ==========================
    # 2. 颜色量化模块
    # ==========================
    def quantize_colors(self, img):
        h, w = img.shape[:2]
        pixels = img.reshape(-1, 3)
        kmeans = KMeans(n_clusters=self.sand_colors, random_state=42, n_init='auto')
        labels = kmeans.fit_predict(pixels).reshape(h, w)
        centers = kmeans.cluster_centers_.astype(np.uint8)

        out = np.zeros_like(img)
        for i in range(h):
            for j in range(w):
                c = centers[labels[i, j]]
                dist = np.sum((self.sand_palette - c) ** 2, axis=1)
                out[i, j] = self.sand_palette[np.argmin(dist)]
        return out

    # ==========================
    # 3. 点阵生成核心算法
    # ==========================
    def generate_dots(self, img):
        h, w = img.shape[:2]
        canvas = np.full((h, w, 3), 240, dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        for y in range(0, h, self.step):
            for x in range(0, w, self.step):
                # 随机扰动，避免机械网格
                rx = x + int(np.random.uniform(-self.jitter * self.step, self.jitter * self.step))
                ry = y + int(np.random.uniform(-self.jitter * self.step, self.jitter * self.step))
                rx = np.clip(rx, 0, w - 1)
                ry = np.clip(ry, 0, h - 1)

                # 亮度决定点大小
                val = gray[ry, rx]
                size = int(np.interp(val, [0, 255], [self.dot_max, self.dot_min]))
                color = img[ry, rx].tolist()

                # 画沙粒圆点
                cv2.circle(canvas, (rx, ry), size, color, -1)

        # 轻微羽化，模拟沙粒堆积柔和感
        canvas = cv2.GaussianBlur(canvas, (1, 1), 0.3)
        return canvas

    # ==========================
    # 4. 物理纹理增强
    # ==========================
    def add_sand_texture(self, img):
        h, w = img.shape[:2]
        noise = np.random.normal(243, 3, (h, w)).astype(np.uint8)
        noise_3c = cv2.cvtColor(noise, cv2.COLOR_GRAY2BGR)
        res = cv2.addWeighted(img, 0.93, noise_3c, 0.07, 0)
        res = cv2.GaussianBlur(res, (3, 3), 0.2)
        return res

    # ==========================
    # 主流程（完全对齐方案架构）
    # ==========================
    def process(self, img):
        img = self.preprocess(img)
        img = self.quantize_colors(img)
        img = self.generate_dots(img)
        img = self.add_sand_texture(img)
        return img

    # ==========================
    # 支持 WEBP 输入输出
    # ==========================
    def run(self, input_path, output_path="sand_art.webp"):
        # 用 PIL 打开，兼容 webp / png / jpg 等
        with Image.open(input_path) as im:
            im = im.convert("RGB")
            img = np.array(im)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        result = self.process(img)

        # 保存为 webp
        result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        im_out = Image.fromarray(result_rgb)
        im_out.save(output_path, format="WebP", lossless=False, quality=90)
        print(f"✅ 点阵沙画已保存：{output_path}")


if __name__ == "__main__":
    gen = SandArtGenerator(
        dot_min=2,
        dot_max=10,
        step=6,
        jitter=0.4,
        sand_colors=8
    )
    # 支持传入 .webp / .png / .jpg
    gen.run("jjl.png", "output_sand.png")