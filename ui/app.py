"""主窗口：tkinter ttk Notebook + 4 个 Tab。"""
import tkinter as tk
from tkinter import ttk, messagebox

from __version__ import __version__
from config import load_config, save_config, DEFAULT_CONFIG
from ui.tab_scan import ScanTab
from ui.tab_config import ConfigTab
from ui.tab_shortcuts import ShortcutsTab
from ui.tab_log import LogTab


class App(tk.Tk):
    def __init__(self, cfg: dict):
        super().__init__()
        self.title(f"Edge 快捷方式守护 v{__version__}")
        self.geometry("900x620")
        self.minsize(720, 480)

        self.cfg = dict(cfg)
        self._dirty = False

        # 顶部信息条
        top = ttk.Frame(self, padding=(10, 6))
        top.pack(fill=tk.X)
        ttk.Label(top, text=f"Edge 快捷方式守护 v{__version__}", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(top, textvariable=self.status_var, foreground="grey").pack(side=tk.RIGHT)

        # Notebook
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.scan_tab = ScanTab(nb, self)
        self.config_tab = ConfigTab(nb, self)
        self.shortcuts_tab = ShortcutsTab(nb, self)
        self.log_tab = LogTab(nb, self)

        nb.add(self.scan_tab, text="  1 扫描  ")
        nb.add(self.config_tab, text="  2 配置  ")
        nb.add(self.shortcuts_tab, text="  3 快捷方式  ")
        nb.add(self.log_tab, text="  4 日志  ")

        nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._notebook = nb

        # 底部状态条
        self._status_bar = ttk.Frame(self, relief=tk.SUNKEN, padding=(6, 2))
        self._status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # 首次进入扫描页时自动跑一次
        self.after(150, self.scan_tab.refresh)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- 状态 ----------
    def set_status(self, text: str) -> None:
        self.status_var.set(text)

    def mark_dirty(self) -> None:
        self._dirty = True

    def reload_config(self) -> None:
        """重新从磁盘读 config（其它 Tab 修改保存后调用）。"""
        self.cfg = load_config()
        self.config_tab.load_from(self.cfg)
        self.shortcuts_tab.load_from(self.cfg)

    # ---------- 事件 ----------
    def _on_tab_changed(self, event):
        idx = self._notebook.index("current")
        # 进入日志页自动刷新
        if idx == 3:
            self.log_tab.refresh()
        # 进入快捷方式页自动刷新一次
        elif idx == 2:
            self.shortcuts_tab.refresh()

    def _on_close(self):
        if self._dirty:
            if messagebox.askyesnocancel("退出", "有未保存的修改，是否保存？"):
                self.config_tab.save()
        self.destroy()


def run(cfg: dict) -> int:
    app = App(cfg)
    app.mainloop()
    return 0