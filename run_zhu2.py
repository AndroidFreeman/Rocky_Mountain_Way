import argparse
import cv2
import os
import zhu_2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True)
    parser.add_argument("--output", "-o", default=os.path.join("outputs", "zhu2_sand.png"))
    parser.add_argument("--no-show", action="store_true")
    args = parser.parse_args()

    img = cv2.imread(args.input)
    if img is None:
        raise SystemExit("Failed to read image")

    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    hui = zhu_2.sand_c(zhu_2.pre(img))
    cv2.imwrite(out_path, hui)

    if not args.no_show:
        zhu_2.show_img("Real Sand Art", hui, zhu_2.max_width, zhu_2.max_height)

    print(f"output: {out_path}")


if __name__ == "__main__":
    main()

