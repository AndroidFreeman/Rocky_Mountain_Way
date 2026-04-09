import cv2
import numpy as np
import math

def generate_correct_orientation_spiral():
    img = cv2.imread('test_input.jpg', cv2.IMREAD_GRAYSCALE)
    if img is None:
        return

    h, w = img.shape
    size = min(h, w)
    start_y = (h - size) // 2
    start_x = (w - size) // 2
    img = img[start_y:start_y+size, start_x:start_x+size]

    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
    _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    img = cv2.GaussianBlur(img, (5, 5), 0)

    num_spirals = 80
    steps_per_spiral = 4000
    total_steps = num_spirals * steps_per_spiral
    max_theta = num_spirals * 2 * math.pi

    i_array = np.arange(total_steps)
    thetas = (i_array / total_steps) * max_theta
    base_rhos = i_array / total_steps

    r_pixels = base_rhos * (size / 2.0 - 1)
    xs = np.clip(size / 2.0 + r_pixels * np.cos(thetas), 0, size - 1).astype(int)
    ys = np.clip(size / 2.0 - r_pixels * np.sin(thetas), 0, size - 1).astype(int)

    darkness = 1.0 - (img[ys, xs] / 255.0)

    fixed_freq = 120
    track_distance = 1.0 / num_spirals
    max_amplitude = track_distance * 0.8

    wobbles = np.where(darkness > 0.1, max_amplitude * darkness * np.sin(fixed_freq * thetas), 0.0)
    final_rhos = np.clip(base_rhos + wobbles, 0.0, 1.0)

    data_to_save = np.column_stack((thetas, final_rhos))
    np.savetxt('rocky_mountain_way.thr', data_to_save, fmt='%.4f %.4f')

    draw_rs = final_rhos * (size / 2.0 - 1)
    draw_xs = np.clip(size / 2.0 + draw_rs * np.cos(thetas), 0, size - 1).astype(np.int32)
    draw_ys = np.clip(size / 2.0 - draw_rs * np.sin(thetas), 0, size - 1).astype(np.int32)

    preview_img = np.full((size, size), 255, dtype=np.uint8)
    points = np.column_stack((draw_xs, draw_ys)).reshape((-1, 1, 2))
    cv2.polylines(preview_img, [points], isClosed=False, color=0, thickness=1, lineType=cv2.LINE_AA)

    cv2.imwrite('rocky_mountain_way_preview.png', preview_img)

if __name__ == '__main__':
    generate_correct_orientation_spiral()
