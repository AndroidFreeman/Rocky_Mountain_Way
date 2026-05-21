import argparse
import hua_2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True)
    args = parser.parse_args()
    hua_2.generate_one_stroke_animation(args.input)


if __name__ == "__main__":
    main()

