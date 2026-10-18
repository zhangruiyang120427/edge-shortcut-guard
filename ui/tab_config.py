"""Tab 2：基本配置页（桌面路径 / 通知 / OTA）。Edge 相关信息由 Tab 3 管理。"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from config import DEFAULT_CONFIG, save_config
from logger import log as logger_log
from logger import STATE_CONFIG


class ConfigTab(ttk.Frame):
    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self):
        # 左右两列
        left = ttk.LabelFrame(self, text="通知 & 桌面路径", padding=10)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
        right = ttk.LabelFrame(self, text="OTA", padding=10)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))

        # ---- 左列 ----
        self.duration_var = tk.IntVar()
        self.sleep_var = tk.IntVar()

        ttk.Label(left, text="通知 duration (秒):").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Spinbox(left, from_=5, to=60, textvariable=self.duration_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=4)
        ttk.Label(left, text="通知后等待 (秒):").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Spinbox(left, from_=0, to=10, textvariable=self.sleep_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=4)
        left.columnconfigure(1, weight=1)

        # 桌面路径列表
        list_frame = ttk.LabelFrame(left, text="桌面路径列表", padding=8)
        list_frame.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW, pady=(8, 0))
        left.rowconfigure(2, weight=1)
        left.columnconfigure(0, weight=1)

        self.path_listbox = tk.Listbox(list_frame, height=6, exportselection=False)
        self.path_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ysb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.path_listbox.yview)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)
        self.path_listbox.config(yscrollcommand=ysb.set)

        btn_col = ttk.Frame(list_frame)
        btn_col.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))
        ttk.Button(btn_col, text="添加", command=self._on_add_path, width=10).pack(pady=2)
        ttk.Button(btn_col, text="删除选中", command=self._on_remove_path, width=10).pack(pady=2)

        # ---- 右列 ----
        self.ota_enabled_var = tk.BooleanVar()
        self.ota_repo_var = tk.StringVar()

        ttk.Checkbutton(right, text="启用 OTA 检测", variable=self.ota_enabled_var).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=4)
        ttk.Label(right, text="GitHub 仓库:").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Entry(right, textvariable=self.ota_repo_var, width=40).grid(row=1, column=1, sticky=tk.EW, pady=4)
        right.columnconfigure(1, weight=1)
        ttk.Label(right, text="格式: owner/repo", foreground="grey").grid(row=2, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(right, text="Edge 相关信息请在「快捷方式」Tab 中编辑", foreground="grey").grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=(12, 0)
        )

        # ---- 底部按钮 ----
        bottom = ttk.Frame(self)
        bottom.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(bottom, text="保存配置", command=self.save).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(bottom, text="恢复默认", command=self.restore_defaults).pack(side=tk.RIGHT)
        ttk.Button(bottom, text="重新载入", command=self._reload).pack(side=tk.RIGHT, padx=(0, 6))

        self.load_from(self.app.cfg)

    def load_from(self, cfg: dict):
        self.duration_var.set(int(cfg.get("toast_duration_seconds", DEFAULT_CONFIG["toast_duration_seconds"])))
        self.sleep_var.set(int(cfg.get("silent_sleep_after_toast", DEFAULT_CONFIG["silent_sleep_after_toast"])))
        self.ota_enabled_var.set(bool(cfg.get("ota_enabled", DEFAULT_CONFIG["ota_enabled"])))
        self.ota_repo_var.set(cfg.get("ota_repo", DEFAULT_CONFIG["ota_repo"]))
        self._refresh_listbox(cfg)

    def _refresh_listbox(self, cfg: dict):
        self.path_listbox.delete(0, tk.END)
        for p in cfg.get("desktop_paths", []):
            self.path_listbox.insert(tk.END, p)

    def _collect(self) -> dict:
        cfg = {
            "toast_duration_seconds": int(self.duration_var.get()),
            "silent_sleep_after_toast": int(self.sleep_var.get()),
            "ota_enabled": bool(self.ota_enabled_var.get()),
            "ota_repo": self.ota_repo_var.get().strip(),
            "desktop_paths": list(self.path_listbox.get(0, tk.END)),
        }
        # 保留其它字段（edge_std_path / lnk_name / aliases）
        for k in ("edge_std_path", "lnk_name", "desktop_aliases"):
            if k in self.app.cfg:
                cfg[k] = self.app.cfg[k]
        cfg["desktop_aliases"] = cfg.get("desktop_aliases", [])[: len(cfg["desktop_paths"])]
        while len(cfg["desktop_aliases"]) < len(cfg["desktop_paths"]):
            cfg["desktop_aliases"].append(f"桌面{len(cfg['desktop_aliases']) + 1}")
        return cfg

    def save(self):
        try:
            cfg = self._collect()
            if not cfg["desktop_paths"]:
                messagebox.showwarning("配置错误", "至少需要一个桌面路径")
                return
            save_config(cfg)
            self.app.cfg = cfg
            self.app.set_status("配置已保存")
            self.app._dirty = False
            logger_log(STATE_CONFIG, fields="toast,duration,ota,desktop_paths")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def restore_defaults(self):
        if not messagebox.askyesno("确认", "恢复默认配置？当前未保存的修改将丢失。"):
            return
        self.load_from(dict(DEFAULT_CONFIG))
        self.app.mark_dirty()

    def _reload(self):
        self.app.reload_config()
        self.app.set_status("已重新载入")

    def _on_add_path(self):
        text = simpledialog.askstring("添加桌面路径", "输入桌面路径 (例如 C:\\Users\\Public\\Desktop):")
        if text and text.strip():
            existing = list(self.path_listbox.get(0, tk.END))
            if text.strip() in existing:
                messagebox.showinfo("提示", "该路径已在列表中")
                return
            self.path_listbox.insert(tk.END, text.strip())
            self.app.mark_dirty()

    def _on_remove_path(self):
        sel = self.path_listbox.curselection()
        if sel:
            self.path_listbox.delete(sel[0])
            self.app.mark_dirty()