"""Tab 3：快捷方式页（左表 + 右菜单 + 编辑弹窗）。"""
import os
import tkinter as tk
from tkinter import ttk, messagebox

import win32com.client

from core import repair_one, ensure_shortcut


class ShortcutsTab(ttk.Frame):
    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self):
        # 左右分栏
        left = ttk.LabelFrame(self, text="快捷方式列表", padding=6)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
        right = ttk.LabelFrame(self, text="操作", padding=6)
        right.pack(side=tk.LEFT, fill=tk.Y, padx=(6, 0))

        # 左：Treeview
        cols = ("alias", "path", "target", "ok")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=14)
        self.tree.heading("alias", text="标签")
        self.tree.heading("path", text="快捷方式绝对路径")
        self.tree.heading("target", text="目标指向")
        self.tree.heading("ok", text="合规")
        self.tree.column("alias", width=80, anchor=tk.W)
        self.tree.column("path", width=320, anchor=tk.W)
        self.tree.column("target", width=300, anchor=tk.W)
        self.tree.column("ok", width=60, anchor=tk.CENTER)
        ysb = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=ysb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure("ok", foreground="#0a7d27")
        self.tree.tag_configure("bad", foreground="#b00020")
        self.tree.tag_configure("miss", foreground="grey")

        # 右：操作按钮菜单
        ttk.Button(right, text="新建配置", width=18, command=self._on_new).pack(pady=3)
        ttk.Button(right, text="编辑选中", width=18, command=self._on_edit).pack(pady=3)
        ttk.Button(right, text="删除选中", width=18, command=self._on_delete).pack(pady=3)
        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        ttk.Button(right, text="立即修复选中", width=18, command=self._on_repair).pack(pady=3)
        ttk.Button(right, text="全部重新扫描", width=18, command=self.refresh).pack(pady=3)
        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)
        ttk.Button(right, text="返回扫描页", width=18, command=self._goto_scan).pack(pady=3)

        self.hint_var = tk.StringVar(value="提示：选中表格中的一行，点右侧按钮操作")
        ttk.Label(self, textvariable=self.hint_var, foreground="grey").pack(anchor=tk.W, pady=(6, 0))

    # ---------- 数据 ----------
    def load_from(self, cfg: dict):
        self.refresh()

    def refresh(self):
        cfg = self.app.cfg
        self.tree.delete(*self.tree.get_children())
        paths = cfg.get("desktop_paths", [])
        aliases = cfg.get("desktop_aliases", [])
        targets = cfg.get("edge_std_paths") or [cfg.get("edge_std_path", "")] * len(paths)
        names = cfg.get("lnk_names") or [cfg.get("lnk_name", "")] * len(paths)

        for i, p in enumerate(paths):
            alias = aliases[i] if i < len(aliases) else f"桌面{i + 1}"
            lnk_name = names[i] if i < len(names) and names[i] else cfg.get("lnk_name", "Microsoft Edge.lnk")
            full = os.path.join(p, lnk_name)
            target = ""
            ok_mark = "·"
            tag = "miss"
            if os.path.exists(full):
                try:
                    sc = win32com.client.Dispatch("WScript.Shell").CreateShortCut(full)
                    target = sc.TargetPath
                    if target.strip() == targets[i].strip() and sc.Arguments.strip() == "":
                        ok_mark = "✓"
                        tag = "ok"
                    else:
                        ok_mark = "✗"
                        tag = "bad"
                except Exception:
                    target = "[读取失败]"
                    ok_mark = "✗"
                    tag = "bad"
            self.tree.insert("", tk.END, iid=str(i), values=(alias, full, target, ok_mark), tags=(tag,))
        self.app.set_status("就绪")

    # ---------- 选中 ----------
    def _selected_index(self) -> int | None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先在表格中选中一行")
            return None
        return int(sel[0])

    # ---------- 编辑弹窗 ----------
    def _on_new(self):
        cfg = self.app.cfg
        n = len(cfg.get("desktop_paths", []))
        EditDialog(self, self.app, index=None, on_save=self._on_edit_saved)

    def _on_edit(self):
        idx = self._selected_index()
        if idx is None:
            return
        EditDialog(self, self.app, index=idx, on_save=self._on_edit_saved)

    def _on_edit_saved(self, index: int | None, values: dict, write_disk: bool):
        """values: {alias, path, target, lnk_name}; index=None 表示新建。"""
        cfg = self.app.cfg
        paths = cfg.get("desktop_paths", [])
        aliases = cfg.get("desktop_aliases", [])
        targets = cfg.get("edge_std_paths") or [cfg.get("edge_std_path", "")] * len(paths)
        names = cfg.get("lnk_names") or [cfg.get("lnk_name", "")] * len(paths)

        if index is None:
            paths.append(values["path"])
            aliases.append(values["alias"])
            targets.append(values["target"])
            names.append(values["lnk_name"])
        else:
            paths[index] = values["path"]
            aliases[index] = values["alias"]
            targets[index] = values["target"]
            names[index] = values["lnk_name"]

        cfg["desktop_paths"] = paths
        cfg["desktop_aliases"] = aliases
        cfg["edge_std_paths"] = targets
        cfg["lnk_names"] = names

        # 同步全局字段为第一行（向后兼容旧代码）
        if paths:
            cfg["edge_std_path"] = targets[0]
            cfg["lnk_name"] = names[0]

        self.app.cfg = cfg
        self.app.mark_dirty()

        if write_disk:
            full = os.path.join(values["path"], values["lnk_name"])
            if os.path.exists(full):
                res = repair_one(full, values["target"])
            else:
                res = ensure_shortcut(full, values["target"])
            if res.get("error"):
                messagebox.showerror("写入失败", res["error"])
            else:
                self.app.set_status("已写入磁盘")
        else:
            self.app.set_status("配置已更新（未写入磁盘）")

        self.refresh()
        self.hint_var.set("已保存" + ("并写入磁盘" if write_disk else "（仅配置）") + "，去 Tab 2 点击「保存配置」落盘")

    # ---------- 操作 ----------
    def _on_delete(self):
        idx = self._selected_index()
        if idx is None:
            return
        cfg = self.app.cfg
        alias = cfg["desktop_aliases"][idx] if idx < len(cfg["desktop_aliases"]) else f"桌面{idx + 1}"
        if not messagebox.askyesno("确认", f"从配置列表移除「{alias}」？\n（仅移除配置项，不会删除磁盘上的 .lnk 文件）"):
            return
        for key in ("desktop_paths", "desktop_aliases", "edge_std_paths", "lnk_names"):
            lst = cfg.get(key) or []
            if idx < len(lst):
                lst.pop(idx)
                cfg[key] = lst
        self.app.cfg = cfg
        self.app.mark_dirty()
        self.refresh()
        self.hint_var.set(f"已从配置列表移除「{alias}」，记得去 Tab 2 保存")

    def _on_repair(self):
        idx = self._selected_index()
        if idx is None:
            return
        cfg = self.app.cfg
        paths = cfg["desktop_paths"]
        targets = cfg.get("edge_std_paths") or [cfg.get("edge_std_path", "")] * len(paths)
        names = cfg.get("lnk_names") or [cfg.get("lnk_name", "")] * len(paths)
        lnk_name = names[idx] if idx < len(names) else cfg.get("lnk_name", "Microsoft Edge.lnk")
        full = os.path.join(paths[idx], lnk_name)
        target = targets[idx]
        if not os.path.exists(full):
            res = ensure_shortcut(full, target)
        else:
            res = repair_one(full, target)
        if res.get("error"):
            messagebox.showerror("修复失败", res["error"])
        else:
            self.app.set_status("已修复")
            self.refresh()

    def _goto_scan(self):
        self.app._notebook.select(0)


class EditDialog(tk.Toplevel):
    """编辑/新建 配置项的弹窗。"""

    def __init__(self, parent, app, index: int | None, on_save):
        super().__init__(parent)
        self.app = app
        self.index = index
        self.on_save = on_save

        self.title("新建配置" if index is None else f"编辑第 {index + 1} 项")
        self.geometry("560x320")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        cfg = app.cfg
        paths = cfg.get("desktop_paths", [])
        aliases = cfg.get("desktop_aliases", [])
        targets = cfg.get("edge_std_paths") or [cfg.get("edge_std_path", "")] * len(paths)
        names = cfg.get("lnk_names") or [cfg.get("lnk_name", "")] * len(paths)

        if index is None:
            # 新建：四个输入框全部留空
            init_alias = ""
            init_path = ""
            init_target = ""
            init_name = ""
        else:
            init_alias = aliases[index] if index < len(aliases) else f"桌面{index + 1}"
            init_path = paths[index]
            init_target = targets[index]
            init_name = names[index] if index < len(names) else cfg.get("lnk_name", "")

        body = ttk.Frame(self, padding=12)
        body.pack(fill=tk.BOTH, expand=True)

        self.alias_var = tk.StringVar(value=init_alias)
        self.path_var = tk.StringVar(value=init_path)
        self.target_var = tk.StringVar(value=init_target)
        self.lnk_name_var = tk.StringVar(value=init_name)

        rows = [
            ("标签:", self.alias_var),
            ("桌面路径:", self.path_var),
            ("目标 (exe 路径):", self.target_var),
            ("快捷方式文件名:", self.lnk_name_var),
        ]
        for i, (label, var) in enumerate(rows):
            ttk.Label(body, text=label).grid(row=i, column=0, sticky=tk.W, padx=(0, 8), pady=6)
            ttk.Entry(body, textvariable=var, width=60).grid(row=i, column=1, sticky=tk.EW, pady=6)

        body.columnconfigure(1, weight=1)

        btns = ttk.Frame(self, padding=(12, 0, 12, 12))
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="取消", command=self.destroy).pack(side=tk.RIGHT)
        ttk.Button(btns, text="保存", command=self._on_save_click).pack(side=tk.RIGHT, padx=(0, 6))

    def _on_save_click(self):
        values = {
            "alias": self.alias_var.get().strip(),
            "path": self.path_var.get().strip(),
            "target": self.target_var.get().strip(),
            "lnk_name": self.lnk_name_var.get().strip(),
        }
        if not values["path"] or not values["target"] or not values["lnk_name"]:
            messagebox.showwarning("输入错误", "桌面路径、目标、快捷方式文件名均不能为空", parent=self)
            return

        write_disk = messagebox.askyesno(
            "写入磁盘",
            "是否同时将磁盘上的 .lnk 创建/修复为该目标？\n点「否」只更新内存配置（最后去 Tab 2 保存）",
            parent=self,
        )
        self.on_save(self.index, values, write_disk)
        self.destroy()