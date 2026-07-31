import os
import sys
import win32com.client
from windows_toasts import Toast, ToastDuration

# ===================== 配置常量 =====================
# Edge官方标准程序路径
EDGE_STD_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
# 桌面路径：同时检查个人桌面与公共桌面
DESKTOP_PATHS = [
    os.path.expanduser("~/Desktop"),
    r"C:\Users\Public\Desktop",
]
# Edge快捷方式文件名
EDGE_LNK_NAME = "Microsoft Edge.lnk"
# 拼接所有候选快捷方式路径
EDGE_LNK_FULLS = [os.path.join(p, EDGE_LNK_NAME) for p in DESKTOP_PATHS]
# ====================================================

# 通知停留时长由 windows-toasts 的 ToastDuration.Long 控制，
# Windows 系统最长支持 25 秒持续显示。

def show_notify(title: str, msg: str):
    """弹出Windows系统通知，使用 windows-toasts 长持续模式（最长25秒）"""
    try:
        from windows_toasts import InteractableWindowsToaster
        toaster = InteractableWindowsToaster("Edge快捷方式守护")
        toast = Toast()
        toast.text_fields = [title, msg]
        # 长持续模式（最长25秒）
        toast.duration = ToastDuration.Long
        toaster.show_toast(toast)
        # 缓冲2秒防止进程退出导致通知闪现
        import time
        time.sleep(2)
    except Exception:
        # 通知组件异常兜底弹窗
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, title, 0x40)

def check_and_repair_edge_shortcut():
    # 收集所有实际存在的 Edge 快捷方式
    existing_lnks = [p for p in EDGE_LNK_FULLS if os.path.exists(p)]

    # 校验快捷方式文件是否存在
    if not existing_lnks:
        show_notify("异常", f"未在桌面找到 {EDGE_LNK_NAME}（个人/公共桌面均无）")
        return

    try:
        # Windows Shell 读取快捷方式
        shell = win32com.client.Dispatch("WScript.Shell")

        any_tampered = False
        for lnk_path in existing_lnks:
            shortcut = shell.CreateShortCut(lnk_path)
            target_path = shortcut.TargetPath.strip()
            arguments = shortcut.Arguments.strip()

            # 判断规则：目标不是标准路径 或者 附带启动参数（拼接网址）
            is_tampered = False
            if target_path != EDGE_STD_PATH:
                is_tampered = True
            if arguments.strip() != "":
                is_tampered = True

            if is_tampered:
                # 重置快捷方式为原始状态
                shortcut.TargetPath = EDGE_STD_PATH
                shortcut.Arguments = ""
                shortcut.Save()
                any_tampered = True
        # 未篡改：无任何提示，直接结束程序

        if any_tampered:
            show_notify("修复完成", "检测到Edge快捷方式被篡改，已自动恢复官方原始配置")

    except Exception as err:
        err_info = f"处理快捷方式失败：{str(err)}"
        show_notify("程序运行错误", err_info)

if __name__ == "__main__":
    check_and_repair_edge_shortcut()
    sys.exit(0)