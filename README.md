# Edge 快捷方式守护 / Edge Shortcut Guard

> 监控并修复桌面 Edge 快捷方式被篡改的情况（捆绑导航、推广进程劫持等）。

## 特性

- **多模式启动**：`--silent` 静默检查；默认启动 4 Tab GUI（扫描 / 配置 / 快捷方式 / 日志）
- **自动修复**：检测到目标不是 `msedge.exe` 或带启动参数 → 自动重置
- **自动创建**：公共桌面快捷方式缺失时自动建立官方配置
- **每行独立配置**：Tab 3 可给每个桌面独立设置目标 / 快捷方式文件名
- **OTA 更新检测**：启动时检查 GitHub Releases，发现新版本提示
- **JSON 日志**：每次操作落 `edge_guard.log`（1MB 自动轮转）
- **独立安装器 / 卸载器**：单一 `installer.exe` 内嵌主程序与卸载器，双击即可

## 截图

```
┌─ 1 扫描 ──────────────────────────┐
│ 检查中...    [立即扫描] [检查更新] │
│ 路径            目标        状态   │
│ C:\...\Public\...\Edge.lnk  ✓正常  │
│ C:\...\Administrator\...     ✗篡改  │
└──────────────────────────────────┘
```

## 快速开始

### 用户（无 Python 环境）

1. 从 [Releases](https://github.com/zhangruiyang120427/edge-shortcut-guard/releases) 下载 `installer.exe`
2. 双击运行 → 选择安装目录 → 勾选「开机启动」「桌面快捷方式」→ 安装
3. 卸载：双击安装目录下的 `uninstaller.exe`，或在「设置 > 应用」中点卸载

默认安装到 `%LOCALAPPDATA%\Programs\Edge快捷方式守护\`。

### 开发者

```cmd
pip install -r requirements.txt
python main.py             # 启动 GUI
python main.py --silent    # 静默扫描一次
python build.py            # 打包出 dist\installer.exe
```

## 依赖

```
pywin32
windows-toasts
```

`tkinter` 与 `urllib` 为 Python 内置。

## 项目结构

```
V2.0/
├── main.py              # 入口：--auto/--silent 静默；默认 GUI
├── config.py            # 默认配置 + OTA/别名扩展
├── core.py              # 检测/修复/自动创建核心逻辑
├── ota.py               # GitHub Releases 检测
├── logger.py            # JSON dict 日志
├── installer.py         # 安装器（资源嵌入主程序与卸载器）
├── uninstaller.py       # 独立卸载器
├── build.py             # 三阶段打包
├── ui/                  # tkinter 多 Tab GUI
│   ├── app.py
│   ├── tab_scan.py
│   ├── tab_config.py
│   ├── tab_shortcuts.py
│   └── tab_log.py
├── README.md
└── .gitignore
```

## 自启动

安装器自动通过 `schtasks` 注册：

```cmd
schtasks /create /tn "EdgeShortcutGuard" /tr "\"...Edge快捷方式守护.exe\" --silent" /sc onlogon /rl limited /f
```

卸载时自动删除。

## 版本

- **V2.0**：tkinter 多 Tab GUI / 独立安装器卸载器 / OTA / 日志筛选
- V1.0：PyQt6 单窗体（保留在仓库 [V1.0 分支](https://github.com/zhangruiyang120427/edge-shortcut-guard/tree/v1.0)）

## 许可

MIT
