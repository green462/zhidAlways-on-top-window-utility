# Windows 任意窗口置顶工具

一个轻量的 Windows 托盘小工具，可以像微信聊天框那样把任意普通窗口置顶，不被其他窗口遮挡。

## 下载打包版

- [下载 exe](https://github.com/green462/zhidAlways-on-top-window-utility/releases/download/v1.0.0/AlwaysOnTopTool.exe)
- [下载 zip](https://github.com/green462/zhidAlways-on-top-window-utility/releases/download/v1.0.0/AlwaysOnTopTool.zip)

## 使用方法

1. 如果已下载打包版，双击 `窗口置顶工具.exe`；如果运行源码版，双击 `启动置顶工具.bat`。
2. 点一下要置顶的窗口。
3. 按 `Ctrl+Space` 置顶或取消置顶。
4. 按 `Ctrl+Alt+Q` 关闭工具。

也可以右键托盘图标，使用菜单里的“置顶/取消当前窗口”“开机启动”“退出”。

## 说明

- 使用 Python 标准库 `ctypes` 调用 Win32 API，不需要安装第三方依赖。
- `Ctrl+Space` 可能被中文输入法占用，遇到冲突时可以使用托盘菜单。
- 管理员权限窗口、UAC 弹窗、独占全屏游戏可能无法被普通权限程序置顶。

## 运行环境

- Windows
- Python 3.10 或更新版本
