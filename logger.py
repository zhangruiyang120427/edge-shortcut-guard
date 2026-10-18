"""日志模块：JSON dict 单行格式，自动追加时间戳与级别。"""
import json
import os
import sys
import threading
from datetime import datetime

LOG_NAME = "edge_guard.log"
BACKUP_NAME = "edge_guard.log.bak"
MAX_BYTES = 1 * 1024 * 1024  # 1MB

_LOCK = threading.Lock()

# 状态枚举常量（与 UI 颜色 / 筛选对应）
STATE_START = "开始"
STATE_EXIT = "退出"
STATE_NORMAL = "正常"
STATE_REPAIR = "已修复"
STATE_CREATE = "已创建"
STATE_MISSING = "不存在"
STATE_ERROR = "异常"
STATE_UPDATE = "新版本"
STATE_CONFIG = "配置变更"


def _log_path() -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, LOG_NAME)


def _rotate_if_needed(path: str) -> None:
    if not os.path.exists(path):
        return
    try:
        if os.path.getsize(path) >= MAX_BYTES:
            bak = os.path.join(os.path.dirname(path), BACKUP_NAME)
            if os.path.exists(bak):
                os.remove(bak)
            os.rename(path, bak)
    except OSError:
        pass


def log(state: str, level: str = "INFO", **fields) -> None:
    """追加一条日志。fields 内的值必须可 JSON 序列化。"""
    path = _log_path()
    with _LOCK:
        _rotate_if_needed(path)
        record = {
            "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "level": level,
            "state": state,
        }
        record.update(fields)
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError:
            pass


def read_all() -> list[dict]:
    """全量读取日志，按时间倒序。容错：跳过解析失败的行。"""
    path = _log_path()
    if not os.path.exists(path):
        return []
    out: list[dict] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        out.append(obj)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    out.sort(key=lambda r: r.get("ts", ""), reverse=True)
    return out


def filter_by_state(records: list[dict], states: set[str] | None) -> list[dict]:
    """按状态集合过滤。states 为 None 或空集表示不过滤。"""
    if not states:
        return records
    return [r for r in records if r.get("state") in states]


def clear_screen_only() -> None:
    """占位：UI 调用，仅清屏，不删磁盘日志。由 UI 层实现。"""
    pass


def clear_log_file() -> bool:
    """清空磁盘日志文件。返回是否成功。"""
    path = _log_path()
    with _LOCK:
        try:
            if os.path.exists(path):
                with open(path, "w", encoding="utf-8"):
                    pass
            return True
        except OSError:
            return False