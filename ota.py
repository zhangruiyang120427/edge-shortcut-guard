"""OTA 检测：从 GitHub Releases 拉取最新版本信息并比较。"""
import json
import re
import urllib.request
from typing import Optional

from logger import log as logger_log
from logger import STATE_UPDATE


def _parse_version(ver: str) -> tuple[int, ...]:
    """'v1.2.3' / '1.2.3' → (1,2,3)。无法解析时返回 ()。"""
    m = re.match(r"^v?(\d+(?:\.\d+)*)$", ver.strip())
    if not m:
        return ()
    return tuple(int(x) for x in m.group(1).split("."))


def check_update(current_version: str, repo: str, timeout: int = 5) -> Optional[dict]:
    """命中比 current_version 新的发布则返回 dict，否则 None。"""
    if not repo:
        return None
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "edge-shortcut-guard", "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    tag = (data.get("tag_name") or "").strip()
    if not tag:
        return None

    latest = _parse_version(tag)
    current = _parse_version(current_version)
    if not latest or not current:
        return None
    if latest <= current:
        return None

    info = {
        "tag": tag,
        "url": data.get("html_url", ""),
        "name": data.get("name", tag),
        "body": (data.get("body") or "").strip(),
        "current": current_version,
    }
    logger_log(STATE_UPDATE, tag=tag, url=info["url"], current=current_version, latest=tag)
    return info