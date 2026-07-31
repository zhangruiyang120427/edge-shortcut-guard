# Edge快捷方式守护

监控并修复桌面 Edge 快捷方式被篡改的情况。

## 功能

- 检测个人桌面与公共桌面上的 `Microsoft Edge.lnk`
- 判定标准：目标路径必须是 `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`，且不带任何启动参数
- 不符合时自动重置为官方配置，并弹 25 秒通知
- 正常时静默退出，不打扰

## 使用

直接运行打包好的 exe：

```
dist\Edge快捷方式守护.exe
```

## 开机自启动

通过 Windows 任务计划程序设置，触发条件为用户登录。手动命令：

```cmd
schtasks /create /tn "EdgeShortcutGuard" /tr "\"dist\Edge快捷方式守护.exe\"" /sc onlogon /rl limited /f
```

卸载：

```cmd
schtasks /delete /tn "EdgeShortcutGuard" /f
```

## 项目结构

```
├── main.py      # 主程序源码
├── dist/
│   └── Edge快捷方式守护.exe  # 打包产物
└── README.md
```

## 依赖

- `pywin32` —— 读取/修改 `.lnk` 快捷方式
- `windows-toasts` —— Windows 10/11 原生通知（25 秒长持续）

安装：

```cmd
pip install pywin32 windows-toasts
```

## 重新打包

```cmd
pyinstaller --onefile --noconsole --name "Edge快捷方式守护" --hidden-import windows_toasts --collect-all winrt main.py
```

打包产物在 `dist\` 目录。