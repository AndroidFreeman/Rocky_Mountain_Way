import argparse
import os
import shutil
import tempfile
import xue


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True)
    parser.add_argument("--out-dir", "-o", default="outputs")
    args = parser.parse_args()

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="xue_run_") as work_dir:
        work_dir = os.path.abspath(work_dir)
        test_input = os.path.join(work_dir, "test_input.jpg")
        shutil.copyfile(args.input, test_input)

        prev_cwd = os.getcwd()
        try:
            os.chdir(work_dir)
            xue.generate_correct_orientation_spiral()
        finally:
            os.chdir(prev_cwd)

        thr_src = os.path.join(work_dir, "rocky_mountain_way.thr")
        preview_src = os.path.join(work_dir, "rocky_mountain_way_preview.png")

        thr_dst = os.path.join(out_dir, "xue_output.thr")
        preview_dst = os.path.join(out_dir, "xue_preview.png")

        if os.path.exists(thr_src):
            shutil.copyfile(thr_src, thr_dst)
        if os.path.exists(preview_src):
            shutil.copyfile(preview_src, preview_dst)

        print(f"thr: {thr_dst}")
        print(f"preview: {preview_dst}")


if __name__ == "__main__":
    main()

