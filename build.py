"""一键打包：分两阶段。

阶段 1: 独立打三个 exe（main / installer / uninstaller）
阶段 2: 把 dist\\Edge快捷方式守护.exe 与 dist\\uninstaller.exe
         base64 注入 installer.py，替换其 _PAYLOAD 字段
阶段 3: 重新打包 installer.py → dist\\installer.exe

最终 dist\\ 只保留 installer.exe（用户只拿这一个）。
其余两个 exe 是阶段 1 的中间产物，会在阶段 2 后被删除。

用法（在 V2.0 目录下）:
    python build.py
"""
import base64
import os
import re
import shutil
import subprocess
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")
BUILD = os.path.join(HERE, "build")


def clean() -> None:
    for sub in ("build", "dist"):
        p = os.path.join(HERE, sub)
        if os.path.isdir(p):
            print(f"[clean] {p}")
            shutil.rmtree(p, ignore_errors=True)
    for spec in ("Edge快捷方式守护.spec", "installer.spec", "uninstaller.spec"):
        p = os.path.join(HERE, spec)
        if os.path.exists(p):
            os.remove(p)


def pyinstaller(cmd: list[str], name: str) -> None:
    print(f"\n=== pyinstaller: {name} ===")
    print(" ".join(cmd))
    pyi_path = shutil.which("pyinstaller") or "pyinstaller"
    if os.name == "nt" and not pyi_path.lower().endswith(".exe"):
        pyi_path = pyi_path + ".exe"
    r = subprocess.run([pyi_path] + cmd, cwd=HERE)
    if r.returncode != 0:
        print(f"[FAIL] {name}")
        sys.exit(r.returncode)


def common_args(name: str) -> list[str]:
    return [
        "--onefile",
        "--noconsole",
        "--name", name,
        "--distpath", DIST,
        "--workpath", BUILD,
    ]


def inject_payload_into_installer(main_path: str, uninst_path: str) -> None:
    """读取 installer.py，替换 _PAYLOAD 字典中两个常量键对应的 b"" 值。"""
    src = os.path.join(HERE, "installer.py")
    with open(src, "r", encoding="utf-8") as f:
        text = f.read()

    main_b64 = base64.b64encode(open(main_path, "rb").read()).decode("ascii")
    uninst_b64 = base64.b64encode(open(uninst_path, "rb").read()).decode("ascii")

    main_const = "MAIN_EXE_NAME"
    uninst_const = "UNINSTALL_EXE_NAME"

    pattern_main = re.compile(
        r'(' + re.escape(main_const) + r'\s*:\s*)b""',
    )
    pattern_uninst = re.compile(
        r'(' + re.escape(uninst_const) + r'\s*:\s*)b""',
    )
    if not pattern_main.search(text) or not pattern_uninst.search(text):
        raise RuntimeError("installer.py 中未找到 _PAYLOAD 占位符")

    def chunked_body(b64: str) -> str:
        """返回完整的 b"..." 字符串字面量内容（含 b" 与闭合 "）。"""
        return f'b"{b64}"'

    new_text = pattern_main.sub(
        lambda m: m.group(1) + chunked_body(main_b64),
        text,
        count=1,
    )
    new_text = pattern_uninst.sub(
        lambda m: m.group(1) + chunked_body(uninst_b64),
        new_text,
        count=1,
    )

    with open(src, "w", encoding="utf-8") as f:
        f.write(new_text)
    print(f"[inject] installer.py 已注入 main={len(main_b64)} B / uninst={len(uninst_b64)} B")


def main() -> int:
    if not shutil.which("pyinstaller"):
        print("未检测到 pyinstaller，先安装: pip install pyinstaller")
        return 1

    clean()
    os.makedirs(DIST, exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)

    # ---- 阶段 1: 打三个独立 exe ----
    pyinstaller(
        common_args("Edge快捷方式守护") + [
            "--hidden-import", "windows_toasts",
            "--collect-all", "winrt",
            "main.py",
        ],
        "Edge快捷方式守护",
    )
    pyinstaller(
        common_args("installer") + ["installer.py"],
        "installer",
    )
    pyinstaller(
        common_args("uninstaller") + ["uninstaller.py"],
        "uninstaller",
    )

    main_exe = os.path.join(DIST, "Edge快捷方式守护.exe")
    uninst_exe = os.path.join(DIST, "uninstaller.exe")
    if not os.path.exists(main_exe) or not os.path.exists(uninst_exe):
        print("[FAIL] 阶段 1 产物缺失")
        return 1

    # ---- 阶段 2: 注入 payload ----
    inject_payload_into_installer(main_exe, uninst_exe)

    # ---- 阶段 3: 重打 installer.py（此时已含 payload）----
    pyinstaller(
        common_args("installer") + ["installer.py"],
        "installer (with payload)",
    )

    # ---- 清理中间产物 ----
    # 删除主程序与卸载器的独立 exe（用户只拿 installer.exe）
    for p in (main_exe, uninst_exe):
        try:
            os.remove(p)
            print(f"[clean] {p}")
        except OSError:
            pass

    print("\n[done] 最终产物:")
    for name in os.listdir(DIST):
        p = os.path.join(DIST, name)
        if os.path.isfile(p):
            sz = os.path.getsize(p)
            print(f"  - {p}  ({sz / 1024 / 1024:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())