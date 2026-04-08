import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox


class Tooltip:
    def __init__(self, widget, text, delay_ms=350):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip = None

        widget.bind("<Enter>", self._on_enter, add=True)
        widget.bind("<Leave>", self._on_leave, add=True)
        widget.bind("<ButtonPress>", self._on_leave, add=True)

    def _on_enter(self, _event=None):
        self._schedule()

    def _on_leave(self, _event=None):
        self._cancel()
        self._hide()

    def _schedule(self):
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            finally:
                self._after_id = None

    def _show(self):
        if self._tip is not None:
            return
        if not self.text:
            return

        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.attributes("-topmost", True)

        label = tk.Label(
            self._tip,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
        )
        label.pack(ipadx=6, ipady=4)

        x = self.widget.winfo_pointerx() + 12
        y = self.widget.winfo_pointery() + 12
        self._tip.wm_geometry(f"+{x}+{y}")

    def _hide(self):
        if self._tip is not None:
            try:
                self._tip.destroy()
            finally:
                self._tip = None


def repo_root():
    return os.path.dirname(os.path.abspath(__file__))


class DemoLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("算法演示启动器")
        self.geometry("820x520")

        self.image_path_var = tk.StringVar(value="")
        self.output_dir_var = tk.StringVar(value=os.path.join(repo_root(), "outputs"))
        self.status_var = tk.StringVar(value="就绪")

        self._proc = None
        self._last_output_path = None
        self._tooltips = []

        self.mao_show_var = tk.BooleanVar(value=True)
        self.mao_gose_var = tk.StringVar(value="7")
        self.mao_ksize_var = tk.StringVar(value="3")
        self.mao_contrast_var = tk.StringVar(value="1.5")
        self.mao_bright_var = tk.StringVar(value="20")
        self.mao_dilate_var = tk.StringVar(value="3")
        self.mao_dilatetime_var = tk.StringVar(value="1")

        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(top, text="输入图片：").grid(row=0, column=0, sticky="w")
        tk.Entry(top, textvariable=self.image_path_var).grid(row=0, column=1, sticky="we", padx=6)
        tk.Button(top, text="选择", command=self._browse_image).grid(row=0, column=2)

        tk.Label(top, text="输出目录：").grid(row=1, column=0, sticky="w", pady=(8, 0))
        tk.Entry(top, textvariable=self.output_dir_var).grid(row=1, column=1, sticky="we", padx=6, pady=(8, 0))
        tk.Button(top, text="选择", command=self._browse_output_dir).grid(row=1, column=2, pady=(8, 0))

        top.columnconfigure(1, weight=1)

        btns = tk.Frame(self)
        btns.pack(fill=tk.X, padx=10)

        self.btn_hua = tk.Button(btns, text="运行 hua_2（一笔画）", command=self._run_hua)
        self.btn_mao = tk.Button(btns, text="运行 mao（沙画优化）", command=self._run_mao)
        self.btn_xue = tk.Button(btns, text="运行 xue（螺旋thr）", command=self._run_xue)
        self.btn_zhu2 = tk.Button(btns, text="运行 zhu_2（沙画）", command=self._run_zhu2)
        self.btn_open_out = tk.Button(btns, text="打开输出目录", command=self._open_output_dir)
        self.btn_open_last = tk.Button(btns, text="打开最后输出", command=self._open_last_output)

        self.btn_hua.pack(side=tk.LEFT)
        self.btn_mao.pack(side=tk.LEFT, padx=(8, 0))
        self.btn_xue.pack(side=tk.LEFT, padx=(8, 0))
        self.btn_zhu2.pack(side=tk.LEFT, padx=(8, 0))
        self.btn_open_out.pack(side=tk.RIGHT)
        self.btn_open_last.pack(side=tk.RIGHT, padx=(0, 8))

        mao_params = tk.LabelFrame(self, text="mao 参数（相当于原脚本的交互输入）")
        mao_params.pack(fill=tk.X, padx=10, pady=(10, 0))

        cb = tk.Checkbutton(mao_params, text="显示窗口(HC/dilate/sand)", variable=self.mao_show_var)
        cb.grid(row=0, column=0, columnspan=6, sticky="w", padx=8, pady=(6, 0))
        self._tooltips.append(
            Tooltip(
                cb,
                "勾选：会弹出三张图(HC/dilate/sand)用于对比\n"
                "不勾选：仅保存输出文件，演示更快更稳",
            )
        )

        self._add_kv(
            mao_params,
            1,
            "高斯核 gose",
            self.mao_gose_var,
            tooltip="范围：奇数 1~31（建议 7~13）\n影响：越大越模糊，细节更少，边缘更平滑",
        )
        self._add_kv(
            mao_params,
            1,
            "Sobel核 ksize",
            self.mao_ksize_var,
            col=3,
            tooltip="范围：1/3/5/7（最常用 3）\n影响：越大边缘更粗、更不敏感",
        )
        self._add_kv(
            mao_params,
            2,
            "对比度 contrast",
            self.mao_contrast_var,
            tooltip="范围：0.5~3.0（建议 1.0~2.0）\n影响：越大线条更“重”更明显",
        )
        self._add_kv(
            mao_params,
            2,
            "亮度 bright",
            self.mao_bright_var,
            col=3,
            tooltip="范围：-80~80（建议 0~30）\n影响：越大整体越亮，太大会发白",
        )
        self._add_kv(
            mao_params,
            3,
            "膨胀核 dilate",
            self.mao_dilate_var,
            tooltip="范围：1~15（建议 3~7）\n影响：越大线条越粗",
        )
        self._add_kv(
            mao_params,
            3,
            "膨胀次数 dilatetime",
            self.mao_dilatetime_var,
            col=3,
            tooltip="范围：1~10（建议 1~3）\n影响：越大线条越粗更连通",
        )

        tk.Button(mao_params, text="恢复默认", command=self._mao_reset_defaults).grid(
            row=4, column=0, sticky="w", padx=8, pady=(6, 8)
        )

        self.mao_hint = tk.Label(
            mao_params,
            justify="left",
            anchor="w",
            text=(
                "提示：gose/ksize 必须为奇数；ksize 常用 1/3/5/7。"
                " 鼠标移到参数名或输入框上可看范围与影响。"
            ),
        )
        self.mao_hint.grid(row=4, column=1, columnspan=5, sticky="w", padx=(0, 8), pady=(6, 8))

        mao_params.columnconfigure(1, weight=1)
        mao_params.columnconfigure(4, weight=1)

        log_frame = tk.Frame(self)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log = tk.Text(log_frame, wrap=tk.WORD)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = tk.Scrollbar(log_frame, command=self.log.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.configure(yscrollcommand=scroll.set)

        status = tk.Label(self, textvariable=self.status_var, anchor="w")
        status.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _add_kv(self, parent, row, label, var, col=0, tooltip=None):
        lbl = tk.Label(parent, text=label + "：")
        lbl.grid(row=row, column=col, sticky="w", padx=(8, 0), pady=(6, 0))
        ent = tk.Entry(parent, textvariable=var, width=10)
        ent.grid(row=row, column=col + 1, sticky="w", padx=(4, 12), pady=(6, 0))
        if tooltip:
            self._tooltips.append(Tooltip(lbl, tooltip))
            self._tooltips.append(Tooltip(ent, tooltip))

    def _mao_reset_defaults(self):
        self.mao_show_var.set(True)
        self.mao_gose_var.set("7")
        self.mao_ksize_var.set("3")
        self.mao_contrast_var.set("1.5")
        self.mao_bright_var.set("20")
        self.mao_dilate_var.set("3")
        self.mao_dilatetime_var.set("1")

    def _validate_mao_params(self, gose, ksize, contrast, bright, dilate, dilatetime):
        if gose < 1 or gose > 31 or gose % 2 == 0:
            return "gose 需要是 1~31 的奇数（建议 7~13）"
        if ksize not in (1, 3, 5, 7):
            return "ksize 建议用 1/3/5/7（最常用 3）"
        if contrast < 0.5 or contrast > 3.0:
            return "contrast 建议范围 0.5~3.0"
        if bright < -80 or bright > 80:
            return "bright 建议范围 -80~80"
        if dilate < 1 or dilate > 15:
            return "dilate 建议范围 1~15"
        if dilatetime < 1 or dilatetime > 10:
            return "dilatetime 建议范围 1~10"
        return None

    def _browse_image(self):
        path = filedialog.askopenfilename(
            title="选择输入图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.webp"), ("All files", "*.*")],
        )
        if path:
            self.image_path_var.set(path)

    def _browse_output_dir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_dir_var.set(path)

    def _ensure_paths(self, require_image=True):
        out_dir = self.output_dir_var.get().strip()
        if not out_dir:
            messagebox.showerror("错误", "请先选择输出目录")
            return None, None
        os.makedirs(out_dir, exist_ok=True)

        img = self.image_path_var.get().strip()
        if require_image and not img:
            messagebox.showerror("错误", "请先选择输入图片")
            return None, None
        if require_image and not os.path.exists(img):
            messagebox.showerror("错误", f"输入图片不存在：{img}")
            return None, None
        return img, out_dir

    def _set_running(self, running):
        state = tk.DISABLED if running else tk.NORMAL
        for b in [self.btn_hua, self.btn_mao, self.btn_xue, self.btn_zhu2]:
            b.configure(state=state)
        self.status_var.set("运行中..." if running else "就绪")

    def _append_log(self, text):
        self.log.insert(tk.END, text)
        self.log.see(tk.END)

    def _run_process(self, argv, last_output_path=None):
        if self._proc is not None:
            messagebox.showwarning("提示", "已有任务在运行，请等待完成")
            return

        self._last_output_path = last_output_path
        self._set_running(True)
        self._append_log("\n$ " + " ".join(argv) + "\n")

        self._proc = subprocess.Popen(
            argv,
            cwd=repo_root(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        def reader():
            try:
                for line in self._proc.stdout:
                    self.log.after(0, self._append_log, line)
            finally:
                rc = self._proc.wait()
                self._proc = None

                def done():
                    self._append_log(f"\n[exit {rc}]\n")
                    if last_output_path and os.path.exists(last_output_path):
                        self._append_log(f"输出：{last_output_path}\n")
                    self._set_running(False)

                self.log.after(0, done)

        threading.Thread(target=reader, daemon=True).start()

    def _run_hua(self):
        img, _ = self._ensure_paths(require_image=True)
        if not img:
            return
        argv = [sys.executable, os.path.join(repo_root(), "run_hua2.py"), "--input", img]
        self._run_process(argv, last_output_path=None)

    def _run_mao(self):
        img, out_dir = self._ensure_paths(require_image=True)
        if not img:
            return
        out_path = os.path.join(out_dir, "mao_sand.png")

        try:
            gose = int(self.mao_gose_var.get().strip())
            ksize = int(self.mao_ksize_var.get().strip())
            contrast = float(self.mao_contrast_var.get().strip())
            bright = int(self.mao_bright_var.get().strip())
            dilate = int(self.mao_dilate_var.get().strip())
            dilatetime = int(self.mao_dilatetime_var.get().strip())
        except ValueError:
            messagebox.showerror("错误", "mao 参数格式不正确：整数/小数请输入有效数字")
            return

        err = self._validate_mao_params(gose, ksize, contrast, bright, dilate, dilatetime)
        if err:
            messagebox.showerror("参数不合理", err)
            return

        argv = [
            sys.executable,
            os.path.join(repo_root(), "run_mao.py"),
            "--input",
            img,
            "--output",
            out_path,
            "--gose",
            str(gose),
            "--ksize",
            str(ksize),
            "--contrast",
            str(contrast),
            "--bright",
            str(bright),
            "--dilate",
            str(dilate),
            "--dilatetime",
            str(dilatetime),
        ]

        if not self.mao_show_var.get():
            argv.append("--no-show")

        self._run_process(argv, last_output_path=out_path)

    def _run_xue(self):
        img, out_dir = self._ensure_paths(require_image=True)
        if not img:
            return
        thr_path = os.path.join(out_dir, "xue_output.thr")
        preview_path = os.path.join(out_dir, "xue_preview.png")
        argv = [
            sys.executable,
            os.path.join(repo_root(), "run_xue.py"),
            "--input",
            img,
            "--out-dir",
            out_dir,
        ]
        self._run_process(argv, last_output_path=preview_path)

    def _run_zhu2(self):
        img, out_dir = self._ensure_paths(require_image=True)
        if not img:
            return
        out_path = os.path.join(out_dir, "zhu2_sand.png")
        argv = [
            sys.executable,
            os.path.join(repo_root(), "run_zhu2.py"),
            "--input",
            img,
            "--output",
            out_path,
        ]
        self._run_process(argv, last_output_path=out_path)

    def _open_output_dir(self):
        _, out_dir = self._ensure_paths(require_image=False)
        if not out_dir:
            return
        os.startfile(out_dir)

    def _open_last_output(self):
        if not self._last_output_path or not os.path.exists(self._last_output_path):
            messagebox.showinfo("提示", "还没有可打开的输出文件")
            return
        os.startfile(self._last_output_path)


if __name__ == "__main__":
    app = DemoLauncher()
    app.mainloop()

