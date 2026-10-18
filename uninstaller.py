"""卸载器（独立脚本，与 installer.py 解耦）。

用法:
    python uninstaller.py
    或双击 uninstaller.exe

行为:
    1. 读注册表 InstallLocation 定位安装目录
    2. 删除任务计划 EdgeShortcutGuard
    3. 删除个人桌面 Edge快捷方式守护.lnk
    4. 清理注册表 Uninstall 键与 APP 键
    5. 删除安装目录（含自身 uninstaller.exe）
"""
import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox

APP_NAME = "Edge快捷方式守护"
APP_DIR_NAME = "Edge快捷方式守护"
TASK_NAME = "EdgeShortcutGuard"
REG_UNINSTALL = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\EdgeShortcutGuard"
REG_APP = r"Software\EdgeShortcutGuard"
DEFAULT_DESKTOP_LNK = "Edge快捷方式守护.lnk"


# ---------- 路径 ----------
def default_install_dir() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "Programs", APP_DIR_NAME)


def desktop_dir() -> str:
    return os.path.join(os.path.expanduser("~"), "Desktop")


def current_exe_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# ---------- 任务计划 ----------
def delete_task() -> tuple[bool, str]:
    try:
        r = subprocess.run(
            ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            return True, ""
        msg = (r.stderr or r.stdout or "").strip()
        if "找不到" in msg or "not found" in msg.lower():
            return True, ""
        return False, msg
    except Exception as e:
        return False, str(e)


# ---------- 桌面快捷方式 ----------
def delete_desktop_shortcut() -> tuple[bool, str]:
    lnk = os.path.join(desktop_dir(), DEFAULT_DESKTOP_LNK)
    if not os.path.exists(lnk):
        return True, ""
    try:
        os.remove(lnk)
        return True, ""
    except Exception as e:
        return False, str(e)


# ---------- 注册表 ----------
def _reg_delete_tree(key: str) -> None:
    subprocess.run(["reg", "delete", key, "/f"], capture_output=True, shell=False)


def clean_registry() -> tuple[bool, str]:
    try:
        _reg_delete_tree(r"HKCU\\" + REG_UNINSTALL)
        _reg_delete_tree(r"HKCU\\" + REG_APP)
        return True, ""
    except Exception as e:
        return False, str(e)


def query_install_dir() -> str | None:
    try:
        r = subprocess.run(
            ["reg", "query", r"HKCU\\" + REG_UNINSTALL, "/v", "InstallLocation"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            return None
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if line.startswith("InstallLocation"):
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    return parts[2]
    except Exception:
        return None
    return None


# ---------- 文件删除 ----------
def remove_dir_silent(install_dir: str) -> tuple[bool, str]:
    """删除安装目录；允许失败（如自身正在被使用）。"""
    try:
        if not os.path.isdir(install_dir):
            return True, ""
        # 先尝试删文件（含 uninstaller.exe 自身）
        for name in os.listdir(install_dir):
            full = os.path.join(install_dir, name)
            try:
                if os.path.isfile(full):
                    os.remove(full)
                elif os.path.isdir(full):
                    shutil.rmtree(full, ignore_errors=True)
            except OSError:
                pass
        try:
            os.rmdir(install_dir)
        except OSError:
            pass
        return True, ""
    except Exception as e:
        return False, str(e)


# ---------- 卸载主流程 ----------
def do_uninstall(log) -> int:
    log("开始卸载")
    install_dir = query_install_dir() or current_exe_dir()
    log(f"安装目录: {install_dir}")

    ok, err = delete_task()
    log("已删除任务计划" if ok else f"删除任务计划失败: {err}")

    ok, err = delete_desktop_shortcut()
    log("已删除桌面快捷方式" if ok else f"删除桌面快捷方式失败: {err}")

    ok, err = clean_registry()
    log("已清理注册表" if ok else f"清理注册表失败: {err}")

    ok, err = remove_dir_silent(install_dir)
    log("已删除安装目录" if ok else f"删除安装目录失败: {err}")

    log("卸载完成")
    return 0


# ---------- UI ----------
class UninstallWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - 卸载")
        self.geometry("520x340")
        self.resizable(False, False)

        body = ttk.Frame(self, padding=14)
        body.pack(fill=tk.BOTH, expand=True)

        install_dir = query_install_dir() or current_exe_dir()
        ttk.Label(body, text=f"卸载 {APP_NAME}", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W)
        ttk.Label(body, text=f"检测到安装目录:\n{install_dir}", foreground="grey").pack(anchor=tk.W, pady=(8, 8))

        note = ttk.LabelFrame(body, text="将执行以下操作", padding=8)
        note.pack(fill=tk.X, pady=4)
        for txt in [
            "• 删除开机启动任务计划",
            "• 删除桌面快捷方式",
            "• 清理注册表卸载项",
            "• 删除整个安装目录（含本卸载程序）",
        ]:
            ttk.Label(note, text=txt).pack(anchor=tk.W)

        self.log_text = tk.Text(body, height=6, font=("Consolas", 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        btns = ttk.Frame(self, padding=(14, 0, 14, 14))
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="取消", command=self.destroy).pack(side=tk.RIGHT)
        ttk.Button(btns, text="卸载", command=self._on_uninstall).pack(side=tk.RIGHT, padx=(0, 6))

    def _log(self, msg: str, error: bool = False):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n", "err" if error else "info")
        self.log_text.tag_config("err", foreground="#b00020")
        self.log_text.tag_config("info", foreground="black")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.update_idletasks()

    def _on_uninstall(self):
        if not messagebox.askyesno("确认", "确定要卸载吗？此操作不可撤销。"):
            return
        self._log("...")
        do_uninstall(self._log)
        messagebox.showinfo("完成", "卸载完成")
        self.destroy()


def main():
    UninstallWindow().mainloop()


if __name__ == "__main__":
    main()