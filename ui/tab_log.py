"""Tab 4：日志页（复选框筛选 + 列表）。"""
import tkinter as tk
from tkinter import ttk

from logger import read_all, filter_by_state, STATE_START, STATE_EXIT


ALL_STATES = ["开始", "退出", "正常", "已修复", "已创建", "不存在", "异常", "新版本", "配置变更"]


class LogTab(ttk.Frame):
    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._selected = set()
        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.X)
        ttk.Button(top, text="刷新", command=self.refresh).pack(side=tk.RIGHT)
        ttk.Button(top, text="全选", command=self._select_all).pack(side=tk.RIGHT, padx=6)
        ttk.Button(top, text="全不选", command=self._select_none).pack(side=tk.RIGHT)

        chips = ttk.LabelFrame(self, text="状态筛选（多选）", padding=6)
        chips.pack(fill=tk.X, pady=(8, 6))

        self._state_vars: dict[str, tk.BooleanVar] = {}
        cols = 5
        for i, s in enumerate(ALL_STATES):
            var = tk.BooleanVar(value=False)
            self._state_vars[s] = var
            ttk.Checkbutton(
                chips, text=s, variable=var, command=self._on_filter_change,
            ).grid(row=i // cols, column=i % cols, sticky=tk.W, padx=6, pady=2)

        # 日志表
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True)
        cols_t = ("ts", "state", "detail")
        self.tree = ttk.Treeview(table_frame, columns=cols_t, show="headings")
        self.tree.heading("ts", text="时间")
        self.tree.heading("state", text="状态")
        self.tree.heading("detail", text="详情")
        self.tree.column("ts", width=170, anchor=tk.W)
        self.tree.column("state", width=100, anchor=tk.W)
        self.tree.column("detail", width=500, anchor=tk.W)
        ysb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)

        for st, color in [
            ("正常", "#0a7d27"), ("已修复", "#b8860b"), ("已创建", "#0d6efd"),
            ("不存在", "#b00020"), ("异常", "#b00020"), ("新版本", "#0d6efd"),
            ("配置变更", "purple"), ("开始", "grey"), ("退出", "grey"),
        ]:
            self.tree.tag_configure(st, foreground=color)

        self.count_var = tk.StringVar(value="0 条")
        ttk.Label(self, textvariable=self.count_var, foreground="grey").pack(anchor=tk.W, pady=(6, 0))

    # ---------- 操作 ----------
    def refresh(self):
        # 当前选中的状态集合
        sel = {s for s, v in self._state_vars.items() if v.get()}
        self._selected = sel
        records = read_all()
        filtered = filter_by_state(records, sel)

        self.tree.delete(*self.tree.get_children())
        for r in filtered[:500]:
            ts = r.get("ts", "")
            state = r.get("state", "")
            detail_parts = []
            for k, v in r.items():
                if k in ("ts", "level", "state"):
                    continue
                detail_parts.append(f"{k}={v}")
            detail = " ".join(detail_parts) or "-"
            tags = (state,) if state in [
                "正常", "已修复", "已创建", "不存在", "异常", "新版本", "配置变更", "开始", "退出"
            ] else ()
            self.tree.insert("", tk.END, values=(ts, state, detail), tags=tags)

        self.count_var.set(f"{len(filtered)} 条（总计 {len(records)} 条）")
        self.app.set_status("就绪")

    def _on_filter_change(self):
        self.refresh()

    def _select_all(self):
        for v in self._state_vars.values():
            v.set(True)
        self.refresh()

    def _select_none(self):
        for v in self._state_vars.values():
            v.set(False)
        self.refresh()