import argparse
import os
import cv2
import numpy as np


def high_contrast_edge(image_path, gose=7, ksize_s=3, contrast=1.5, bright=20):
    gray = cv2.imread(image_path, 0)
    if gray is None:
        return None
    gray_blur = cv2.GaussianBlur(gray, (gose, gose), 0)
    sobel_x = cv2.Sobel(gray_blur, cv2.CV_64F, 1, 0, ksize=ksize_s)
    sobel_y = cv2.Sobel(gray_blur, cv2.CV_64F, 0, 1, ksize=ksize_s)
    edge = cv2.magnitude(sobel_x, sobel_y)
    edge = cv2.convertScaleAbs(edge)
    hc_image = cv2.convertScaleAbs(edge, alpha=contrast, beta=bright)
    return hc_image


def color_change(gray_1):
    gray = 255 - gray_1
    sand = np.zeros((gray.shape[0], gray.shape[1], 3), dtype=np.uint8)
    sand[:, :, 0] = gray * 0.4
    sand[:, :, 1] = gray * 0.6
    sand[:, :, 2] = gray * 0.8
    return sand


def dilate(image, dilate_s=3, dilatetime_s=1):
    core = np.ones((dilate_s, dilate_s), np.uint8)
    after = cv2.dilate(image, core, iterations=dilatetime_s)
    return after


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True)
    parser.add_argument("--output", "-o", default=os.path.join("outputs", "mao_sand.png"))
    parser.add_argument("--no-show", action="store_true")
    parser.add_argument("--gose", type=int, default=7)
    parser.add_argument("--ksize", type=int, default=3)
    parser.add_argument("--contrast", type=float, default=1.5)
    parser.add_argument("--bright", type=int, default=20)
    parser.add_argument("--dilate", type=int, default=3)
    parser.add_argument("--dilatetime", type=int, default=1)
    args = parser.parse_args()

    hc = high_contrast_edge(args.input, gose=args.gose, ksize_s=args.ksize, contrast=args.contrast, bright=args.bright)
    if hc is None:
        raise SystemExit("Failed to read image")

    dilated = dilate(hc, dilate_s=args.dilate, dilatetime_s=args.dilatetime)
    sand = color_change(dilated)

    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cv2.imwrite(out_path, sand)

    if not args.no_show:
        cv2.imshow("HC", hc)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        cv2.imshow("dilate", dilated)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        cv2.imshow("sand", sand)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    print(f"output: {out_path}")


if __name__ == "__main__":
    main()

