import math
import matplotlib.pyplot as plt

def read_polar_thr(file_path):
    points_xy = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # 顺序：弧度θ , 半径r
            theta_rad, r = map(float, line.split())
            x = r * math.cos(theta_rad)
            y = r * math.sin(theta_rad)
            points_xy.append((x, y))
    return points_xy

if __name__ == "__main__":
    thr_path = "polar.thr"
    xy_data = read_polar_thr(thr_path)
    
    xs = [p[0] for p in xy_data]
    ys = [p[1] for p in xy_data]

    plt.figure(figsize=(7,7))
    plt.plot(xs, ys, c="#1f77b4", linewidth=2, marker=".", markersize=3)
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.title("THR")
    plt.show()