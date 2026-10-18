"""核心检测/修复/创建逻辑：纯函数，便于 TUI 调用。"""
import os
import time
from typing import TypedDict

import win32com.client

from logger import log as logger_log
from logger import STATE_NORMAL, STATE_REPAIR, STATE_CREATE, STATE_MISSING, STATE_ERROR


class LnkResult(TypedDict, total=False):
    path: str
    exists: bool
    target_path: str
    arguments: str
    is_tampered: bool
    repaired: bool
    created: bool
    error: str


class CheckResult(TypedDict):
    found_count: int
    tampered_count: int
    repaired_count: int
    created_count: int
    items: list[LnkResult]


def _shell():
    return win32com.client.Dispatch("WScript.Shell")


def ensure_shortcut(lnk_path: str, target: str) -> LnkResult:
    """在指定路径创建 Edge 快捷方式（默认参数为空、最大化窗口、icon 取自 msedge.exe）。"""
    try:
        os.makedirs(os.path.dirname(lnk_path), exist_ok=True)
        shell = _shell()
        sc = shell.CreateShortCut(lnk_path)
        sc.TargetPath = target
        sc.Arguments = ""
        sc.WindowStyle = 1
        icon = f"{target},0"
        sc.IconLocation = icon
        sc.Save()
        logger_log(STATE_CREATE, path=lnk_path, target=target)
        return LnkResult(
            path=lnk_path, exists=True, target_path=target, arguments="",
            is_tampered=False, repaired=False, created=True, error="",
        )
    except Exception as e:
        err = str(e)
        logger_log(STATE_ERROR, level="ERROR", path=lnk_path, detail=err)
        return LnkResult(
            path=lnk_path, exists=False, target_path="", arguments="",
            is_tampered=False, repaired=False, created=False, error=err,
        )


def repair_one(lnk_path: str, target: str) -> LnkResult:
    """修复单条快捷方式。"""
    try:
        shell = _shell()
        sc = shell.CreateShortCut(lnk_path)
        old_target = sc.TargetPath.strip()
        old_args = sc.Arguments.strip()
        sc.TargetPath = target
        sc.Arguments = ""
        sc.Save()
        logger_log(STATE_REPAIR, path=lnk_path, target=target,
                    old_target=old_target, old_arguments=old_args)
        return LnkResult(
            path=lnk_path, exists=True, target_path=target, arguments="",
            is_tampered=True, repaired=True, created=False, error="",
        )
    except Exception as e:
        err = str(e)
        logger_log(STATE_ERROR, level="ERROR", path=lnk_path, detail=err)
        return LnkResult(
            path=lnk_path, exists=False, target_path="", arguments="",
            is_tampered=False, repaired=False, created=False, error=err,
        )


def check_and_repair(cfg: dict) -> CheckResult:
    """检测并修复桌面快捷方式。

    规则：
      - TargetPath 必须等于该行对应的 edge_std（edge_std_paths[i]）
      - Arguments 必须为空
    所有桌面都不存在时，自动创建第一项对应的快捷方式。
    """
    desktop_paths = cfg["desktop_paths"]
    n = len(desktop_paths)

    # 每行独立 target / lnk_name，缺失时回退到全局
    default_target = cfg.get("edge_std_path", "").strip()
    default_name = cfg.get("lnk_name", "Microsoft Edge.lnk")
    targets = cfg.get("edge_std_paths") or [default_target] * n
    names = cfg.get("lnk_names") or [default_name] * n
    if len(targets) < n:
        targets = targets + [default_target] * (n - len(targets))
    if len(names) < n:
        names = names + [default_name] * (n - len(names))

    # (path, target, lnk_name) 三元组对齐
    rows = list(zip(desktop_paths, targets[:n], names[:n]))
    candidate_lnks = [os.path.join(p, lnk) for p, _, lnk in rows]
    existing_idx = [i for i, lnk in enumerate(candidate_lnks) if os.path.exists(lnk)]
    existing_lnks = [candidate_lnks[i] for i in existing_idx]

    items: list[LnkResult] = []

    for i, lnk_path in enumerate(candidate_lnks):
        if not os.path.exists(lnk_path):
            items.append(LnkResult(
                path=lnk_path, exists=False, target_path="", arguments="",
                is_tampered=False, repaired=False, created=False, error="",
            ))
            logger_log(STATE_MISSING, path=lnk_path)

    if not existing_lnks:
        # 全部不存在 → 自动创建第一项对应的快捷方式（按 Tab 3 的设定）
        created_count = 0
        if rows:
            p0, t0, lnk0 = rows[0]
            public_path = os.path.join(p0, lnk0)
            created = ensure_shortcut(public_path, t0)
            for i, it in enumerate(items):
                if it["path"] == public_path and not it.get("exists"):
                    items[i] = created
                    if created.get("created"):
                        created_count += 1
                    break
        return CheckResult(
            found_count=0, tampered_count=0, repaired_count=0,
            created_count=created_count, items=items,
        )

    try:
        shell = _shell()
    except Exception as e:
        err = f"WScript.Shell 初始化失败: {e}"
        logger_log(STATE_ERROR, level="ERROR", detail=err)
        for lnk_path in existing_lnks:
            items.append(LnkResult(
                path=lnk_path, exists=True, target_path="", arguments="",
                is_tampered=False, repaired=False, created=False, error=err,
            ))
        return CheckResult(
            found_count=len(existing_lnks), tampered_count=0, repaired_count=0,
            created_count=0, items=items,
        )

    tampered_count = 0
    repaired_count = 0

    for idx in existing_idx:
        lnk_path = candidate_lnks[idx]
        target_std = rows[idx][1].strip()
        result = LnkResult(
            path=lnk_path, exists=True, target_path="", arguments="",
            is_tampered=False, repaired=False, created=False, error="",
        )
        try:
            sc = shell.CreateShortCut(lnk_path)
            target_path = sc.TargetPath.strip()
            arguments = sc.Arguments.strip()
            result["target_path"] = target_path
            result["arguments"] = arguments

            is_tampered = (target_path != target_std) or (arguments != "")
            result["is_tampered"] = is_tampered

            if is_tampered:
                tampered_count += 1
                sc.TargetPath = target_std
                sc.Arguments = ""
                sc.Save()
                result["repaired"] = True
                repaired_count += 1
                logger_log(STATE_REPAIR, path=lnk_path, target=target_std,
                            old_target=target_path, old_arguments=arguments)
            else:
                logger_log(STATE_NORMAL, path=lnk_path, target=target_path)
        except Exception as e:
            result["error"] = str(e)
            logger_log(STATE_ERROR, level="ERROR", path=lnk_path, detail=str(e))

        replaced = False
        for i, it in enumerate(items):
            if it["path"] == lnk_path:
                items[i] = result
                replaced = True
                break
        if not replaced:
            items.append(result)

    return CheckResult(
        found_count=len(existing_lnks),
        tampered_count=tampered_count,
        repaired_count=repaired_count,
        created_count=0,
        items=items,
    )


def show_notify(title: str, msg: str, sleep_seconds: int = 2) -> None:
    """弹出 Windows 系统通知。"""
    try:
        from windows_toasts import InteractableWindowsToaster, Toast, ToastDuration
        toaster = InteractableWindowsToaster("Edge快捷方式守护")
        toast = Toast()
        toast.text_fields = [title, msg]
        toast.duration = ToastDuration.Long
        toaster.show_toast(toast)
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
    except Exception:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, title, 0x40)