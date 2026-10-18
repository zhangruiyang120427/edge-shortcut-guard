"""Tab 1：扫描页。"""
import tkinter as tk
from tkinter import ttk

from core import check_and_repair
from ota import check_update
from __version__ import __version__


class ScanTab(ttk.Frame):
    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app

        # 顶部：OTA 提示条 + 按钮
        top = ttk.Frame(self)
        top.pack(fill=tk.X)
        self.ota_var = tk.StringVar(value="未检查更新")
        ttk.Label(top, textvariable=self.ota_var, foreground="grey").pack(side=tk.LEFT)
        self.btn_scan = ttk.Button(top, text="立即扫描", command=self.refresh)
        self.btn_scan.pack(side=tk.RIGHT)
        self.btn_ota = ttk.Button(top, text="检查更新", command=self._check_update)
        self.btn_ota.pack(side=tk.RIGHT, padx=(0, 6))

        # 中部：Treeview 结果表
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        cols = ("path", "target", "args", "status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        self.tree.heading("path", text="路径")
        self.tree.heading("target", text="目标")
        self.tree.heading("args", text="参数")
        self.tree.heading("status", text="状态")
        self.tree.column("path", width=360, anchor=tk.W)
        self.tree.column("target", width=320, anchor=tk.W)
        self.tree.column("args", width=120, anchor=tk.W)
        self.tree.column("status", width=80, anchor=tk.CENTER)
        ysb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)

        # 状态颜色
        self.tree.tag_configure("ok", foreground="#0a7d27")
        self.tree.tag_configure("fixed", foreground="#b8860b")
        self.tree.tag_configure("created", foreground="#0d6efd")
        self.tree.tag_configure("missing", foreground="#b00020")
        self.tree.tag_configure("error", foreground="#b00020")

        # 底部：摘要
        self.summary_var = tk.StringVar(value="尚未扫描")
        ttk.Label(self, textvariable=self.summary_var, foreground="grey").pack(side=tk.BOTTOM, anchor=tk.W, pady=(6, 0))

    def refresh(self):
        self.app.set_status("扫描中...")
        self.btn_scan.config(state=tk.DISABLED)
        self.tree.delete(*self.tree.get_children())
        try:
            result = check_and_repair(self.app.cfg)
            self._fill_result(result)
            self.app.set_status("就绪")
        finally:
            self.btn_scan.config(state=tk.NORMAL)

    def _check_update(self):
        self.btn_ota.config(state=tk.DISABLED)
        self.ota_var.set("检查中...")
        self.app.set_status("正在检查更新...")
        self.update_idletasks()  # 立即刷新 UI
        try:
            info = check_update(__version__, self.app.cfg.get("ota_repo", ""))
            if info:
                self.ota_var.set(f"🆕 新版本 {info['tag']}  {info['url']}")
                self.app.set_status(f"发现新版本 {info['tag']}")
            else:
                self.ota_var.set("已是最新版本")
                self.app.set_status("就绪")
        finally:
            self.btn_ota.config(state=tk.NORMAL)

    def _fill_result(self, result: dict):
        for item in result["items"]:
            path = item.get("path", "")
            if item.get("error"):
                target = f"[异常] {item['error'][:50]}"
                args = "-"
                status = "异常"
                tag = "error"
            elif not item.get("exists"):
                target = "-"
                args = "-"
                status = "已创建" if item.get("created") else "不存在"
                tag = "created" if item.get("created") else "missing"
            elif item.get("is_tampered") and item.get("repaired"):
                target = item.get("target_path", "")
                args = repr(item.get("arguments", "")) if item.get("arguments") else "-"
                status = "已修复"
                tag = "fixed"
            elif item.get("is_tampered"):
                target = item.get("target_path", "")
                args = repr(item.get("arguments", "")) if item.get("arguments") else "-"
                status = "篡改"
                tag = "fixed"
            else:
                target = item.get("target_path", "")
                args = repr(item.get("arguments", "")) if item.get("arguments") else "-"
                status = "正常"
                tag = "ok"
            self.tree.insert("", tk.END, values=(path, target, args, status), tags=(tag,))

        self.summary_var.set(
            f"找到 {result['found_count']}  篡改 {result['tampered_count']}  "
            f"修复 {result['repaired_count']}  创建 {result['created_count']}"
        )