import cv2
import numpy as np

def real_sand_art_effect(input_path, output_path="real_sand_art.png"):
    """
    1:1 还原真实沙画质感：暖黄沙底+沙粒堆积明暗+自然颗粒纹理
    :param input_path: 输入线稿/原图路径
    :param output_path: 输出沙画效果路径
    """
    # 1. 读取图像，提取线稿（和之前一致，保证线条干净）
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"无法读取图片: {input_path}")
    h, w = img.shape[:2]

    # ======================
    # 【第一步：提取干净线稿（保证沙画轮廓清晰）】
    # ======================
    # 双边滤波保边去噪
    blurred = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)
    # 转灰度
    gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
    # 双边缘检测融合（Canny+自适应阈值，提取完整轮廓）
    edges_canny = cv2.Canny(gray, threshold1=25, threshold2=90, apertureSize=3, L2gradient=True)
    edges_adaptive = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=11,
        C=2
    )
    edges = cv2.bitwise_or(edges_canny, edges_adaptive)
    # 降噪优化：形态学闭运算+中值滤波，让线条连贯无杂点
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    edges_clean = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=1)
    edges_clean = cv2.medianBlur(edges_clean, 3)

    # ======================
    # 【第二步：生成真实沙画质感背景（核心！1:1匹配示例）】
    # ======================
    # 🔧 1. 生成多层沙粒噪点，模拟真实沙子的粗细混合
    # 细沙（小颗粒）
    noise_fine = np.random.normal(0, 0, (h, w)).astype(np.float32)
    noise_fine_blur = cv2.GaussianBlur(noise_fine, (3, 3), 0.8)
    # 粗沙（大颗粒，模拟沙堆堆积感）
    noise_coarse = np.random.normal(0, 0, (h, w)).astype(np.float32)
    noise_coarse_blur = cv2.GaussianBlur(noise_coarse, (7, 7), 1.8)
    # 融合两层噪点，模拟真实沙粒的自然分布
    noise_final = cv2.addWeighted(noise_fine_blur, 0.6, noise_coarse_blur, 0.4, 0)

    # 🔧 2. 生成沙粒明暗掩码，模拟沙堆堆积的深浅变化
    # 用绝对值+阈值，生成沙粒堆积的明暗区域
    noise_abs = np.abs(noise_final)
    # 生成多层明暗掩码，模拟沙堆的深浅层次
    mask_dark = cv2.threshold(noise_abs, 0.12, 1, cv2.THRESH_BINARY_INV)[1].astype(np.float32)  # 深沙区（堆积厚）
    mask_light = cv2.threshold(noise_abs, 0.06, 1, cv2.THRESH_BINARY)[1].astype(np.float32)   # 浅沙区（堆积薄）

    # 🔧 3. 维度匹配（避免广播报错，cv2原生转换更稳定）
    mask_dark_3ch = cv2.cvtColor(mask_dark, cv2.COLOR_GRAY2BGR)
    mask_light_3ch = cv2.cvtColor(mask_light, cv2.COLOR_GRAY2BGR)

    # 🔧 4. 生成暖黄沙色基底（完全匹配示例的暖黄沙色）
    # BGR顺序：(蓝, 绿, 红) → 暖黄沙色 (100, 160, 220)，偏暖黄，和示例一致
    sand_base_color = np.array([100, 160, 220], dtype=np.float32) / 255.0
    sand_bg = np.full((h, w, 3), sand_base_color, dtype=np.float32)

    # 🔧 5. 融合沙粒明暗层次，模拟真实沙堆的深浅变化
    # 深沙区（堆积厚）：颜色更深，模拟沙堆阴影
    sand_bg = cv2.multiply(sand_bg, 0.7 + mask_dark_3ch * 0.3, dtype=cv2.CV_32F)
    # 浅沙区（堆积薄）：颜色更亮，模拟沙堆高光
    sand_bg = cv2.multiply(sand_bg, 0.9 + mask_light_3ch * 0.2, dtype=cv2.CV_32F)

    # 🔧 6. 转uint8，做沙粒质感强化
    sand_bg = (sand_bg * 255).astype(np.uint8)
    # 轻微锐化，增强沙粒边缘，让颗粒感更真实
    sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], np.float32)
    sand_bg = cv2.filter2D(sand_bg, -1, sharpen_kernel)
    # 轻微高斯模糊，让沙粒过渡更自然，模拟真实沙画的柔和感
    sand_bg = cv2.GaussianBlur(sand_bg, (3, 3), 0.5)

    # ======================
    # 【第三步：线稿叠加，模拟沙画的线条（深沙色线条）】
    # ======================
    # 线稿区域：用深沙色（比背景深很多），模拟沙画中用沙堆出的线条
    line_mask = edges_clean == 255
    # 深沙色BGR：(60, 100, 140)，完全匹配示例中线条的深沙色
    sand_bg[line_mask] = [60, 100, 140]

    # ======================
    # 【第四步：最终质感优化，1:1匹配真实沙画】
    # ======================
    # 整体暖黄调增强，让沙色更统一
    sand_bg = cv2.cvtColor(sand_bg, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(sand_bg)
    # 增强饱和度，让沙色更暖
    s = cv2.add(s, 15)
    # 调整亮度，模拟沙画的暖光感
    v = cv2.add(v, 5)
    sand_bg = cv2.merge((h, s, v))
    sand_bg = cv2.cvtColor(sand_bg, cv2.COLOR_HSV2BGR)

    # ======================
    # 【第五步：保存结果】
    # ======================
    cv2.imwrite(output_path, sand_bg)
    print(f"真实沙画质感效果已保存至: {output_path}")
    return sand_bg

if __name__ == "__main__":
    # 替换为你的图片路径
    real_sand_art_effect("ren.jpg")