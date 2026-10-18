"""配置管理：加载/保存 config.json，未设置项使用默认。"""
import os
import json

DEFAULT_CONFIG = {
    "edge_std_path": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "desktop_paths": [
        os.path.expanduser("~/Desktop"),
        r"C:\Users\Public\Desktop",
    ],
    "desktop_aliases": ["个人桌面", "公共桌面"],
    "lnk_name": "Microsoft Edge.lnk",
    # 每行快捷方式独立的目标与文件名（与 desktop_paths 等长）
    "edge_std_paths": None,
    "lnk_names": None,
    "toast_duration_seconds": 25,
    "silent_sleep_after_toast": 2,
    "ota_enabled": True,
    "ota_repo": "zhangruiyang120427/edge-shortcut-guard",
}


def get_config_path() -> str:
    """获取 config.json 路径：exe 同目录 / 开发时脚本同目录。"""
    if getattr(__import__("sys"), "frozen", False):
        base_dir = os.path.dirname(__import__("sys").executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "config.json")


def _align_aliases(cfg: dict) -> dict:
    """保证 desktop_aliases、edge_std_paths、lnk_names 与 desktop_paths 长度一致。"""
    paths = cfg.get("desktop_paths", [])
    n = len(paths)

    aliases = list(cfg.get("desktop_aliases", []))
    if len(aliases) < n:
        for i in range(len(aliases), n):
            aliases.append(f"桌面{i + 1}")
    aliases = aliases[:n]
    cfg["desktop_aliases"] = aliases

    # 每行目标：缺则用全局 edge_std_path
    targets = list(cfg.get("edge_std_paths") or [])
    default_target = cfg.get("edge_std_path", DEFAULT_CONFIG["edge_std_path"])
    if len(targets) < n:
        for i in range(len(targets), n):
            targets.append(default_target)
    targets = targets[:n]
    cfg["edge_std_paths"] = targets

    # 每行快捷方式文件名：缺则用全局 lnk_name
    names = list(cfg.get("lnk_names") or [])
    default_name = cfg.get("lnk_name", DEFAULT_CONFIG["lnk_name"])
    if len(names) < n:
        for i in range(len(names), n):
            names.append(default_name)
    names = names[:n]
    cfg["lnk_names"] = names

    return cfg


def load_config() -> dict:
    """加载配置，缺失字段用默认值补齐。"""
    path = get_config_path()
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            if isinstance(user_cfg, dict):
                cfg.update({k: v for k, v in user_cfg.items() if k in DEFAULT_CONFIG})
        except (json.JSONDecodeError, OSError):
            pass
    return _align_aliases(cfg)


def save_config(cfg: dict) -> None:
    """保存配置到 config.json。"""
    path = get_config_path()
    cfg = _align_aliases(cfg)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)