"""入口文件：根据命令行参数分流，静默模式或 GUI 模式。"""
import sys

from config import load_config
from core import check_and_repair, show_notify
from logger import log as logger_log
from ota import check_update
from __version__ import __version__


def run_silent_mode(cfg: dict) -> int:
    """静默模式：开机自启时调用，只弹通知，无界面。"""
    logger_log("开始", mode="silent", argv=sys.argv[1:])

    if cfg.get("ota_enabled", True):
        check_update(__version__, cfg.get("ota_repo", ""))

    result = check_and_repair(cfg)

    if result["found_count"] == 0:
        show_notify(
            "异常",
            f"未在桌面找到 {cfg['lnk_name']}（个人/公共桌面均无）",
            sleep_seconds=cfg.get("silent_sleep_after_toast", 2),
        )
    elif result["repaired_count"] > 0 or result.get("created_count", 0) > 0:
        show_notify(
            "修复完成",
            f"检测到 {result['tampered_count']} 个被篡改，已自动恢复官方原始配置",
            sleep_seconds=cfg.get("silent_sleep_after_toast", 2),
        )

    logger_log("退出", mode="silent")
    return 0


def run_gui_mode(cfg: dict) -> int:
    """GUI 模式：启动 tkinter 多标签页窗口。"""
    try:
        from ui.app import run as run_gui
    except ImportError as e:
        print(f"GUI 启动失败: {e}", file=sys.stderr)
        return 1

    logger_log("开始", mode="gui")
    rc = run_gui(cfg)
    logger_log("退出", mode="gui")
    return rc


def main() -> int:
    args = sys.argv[1:]
    cfg = load_config()

    if "--auto" in args or "--silent" in args:
        return run_silent_mode(cfg)
    return run_gui_mode(cfg)


if __name__ == "__main__":
    sys.exit(main())