import argparse
import cv2
import os
import zhu_3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True)
    parser.add_argument("--output", "-o", default=os.path.join("outputs", "zhu3_sand.png"))
    parser.add_argument("--no-show", action="store_true")
    args = parser.parse_args()

    img = cv2.imread(args.input, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise SystemExit("Failed to read image")

    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    hui = zhu_3.sand_c(zhu_3.pre(img))
    cv2.imwrite(out_path, hui)

    if not args.no_show:
        zhu_3.show_img("Real Sand Art", hui, zhu_3.max_width, zhu_3.max_height)

    print(f"output: {out_path}")


if __name__ == "__main__":
    main()

