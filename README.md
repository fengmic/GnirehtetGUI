<p align="center">
  <img src="icon.png" alt="Gnirehtet GUI" width="120">
</p>

<h1 align="center">Gnirehtet GUI</h1>

<p align="center">
  Android USB 反向网络共享工具 · 图形界面版<br/>
  让手机通过电脑的 网络 上网（Reverse Tethering）
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows-blue" alt="platform">
  <img src="https://img.shields.io/badge/python-3.10%2B-green" alt="python">
  <img src="https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41CD52" alt="PySide6">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="license">
</p>

---

## 简介

[Gnirehtet](https://github.com/Genymobile/gnirehtet) 是 Genymobile 出品的开源反向网络共享（Reverse Tethering）工具，但官方只提供命令行界面，对普通用户不够友好。本项目为它封装了一个 **Windows 图形界面**：

- 无需记忆任何命令，点一个按钮即可开始共享
- 自动检测并列出已连接的 Android 设备（每 5 秒刷新）
- 多设备场景下可指定目标设备
- 实时彩色运行日志，一目了然
- 退出前自动提醒，防止误断共享

> 反向网络共享：与「手机开热点给电脑」相反——通过 USB 数据线，让 **手机使用电脑的网络** 上网。适合无 Wi-Fi / 无 SIM 卡流量场景下的调试、下载、刷机等需求。

## 界面预览

![Gnirehtet GUI 主界面](img/screenshot.png)

## 功能特性

| 功能 | 说明 |
|------|------|
| 🔄 一键启动 | 自动安装 gnirehtet.apk 到手机并启动 VPN 共享 |
| ■ 一键停止 | 向手机发送停止指令并终止本地进程 |
| 📲 仅安装 | 只推送 APK 到手机，不启动共享 |
| 设备管理 | 自动检测 USB 设备及状态（正常 / 未授权等） |
| 多设备支持 | 选中列表中的设备即可定向操作 |
| 运行日志 | 按级别着色的实时日志输出 |

## 快速开始

### 方式一：直接使用打包版（推荐）

前往 [**Releases**](../../releases) 页面下载 `GnirehtetGUI.exe`（单文件版，开箱即用，无需安装 Python）。

> 首次运行时，如 Windows SmartScreen 提示「已保护你的电脑」，请点击「更多信息」→「仍要运行」。

### 方式二：从源码运行

```bash
git clone https://github.com/fengmic/GnirehtetGUI.git
cd GnirehtetGUI

pip install -r requirements.txt
python gnirehtet_gui.py
```

仓库已随源码附带运行所需的二进制组件（`adb.exe`、`gnirehtet.exe`、`gnirehtet.apk` 等），克隆后即可直接运行，无需额外配置。

## 使用步骤

1. 手机打开 **开发者选项** → 启用 **USB 调试**（通常需在「关于手机」中连点 7 次「版本号」开启开发者选项）
2. 用 USB 数据线连接手机与电脑，手机上如弹出「允许 USB 调试」请选择**允许**
3. 打开 Gnirehtet GUI，等待左侧设备列表出现你的手机（✅ 状态）
4. 点击 **▶ 启动共享**
5. 手机弹出 VPN 授权请求，点击 **确定**
6. 完成——此时手机的网络流量已通过电脑转发

断开时点击 **■ 停止共享** 即可。

## 从源码构建 exe

```powershell
.\build_exe.ps1
```

脚本会自动安装 PyInstaller、由 `icon.png` 生成 `icon.ico`，并将 `gnirehtet.exe`、`adb.exe` 等一并打包为 `dist\GnirehtetGUI.exe`。

## 项目结构

```
├── gnirehtet_gui.py      # 主程序（PySide6 图形界面）
├── demo.py               # 图片转 ICO 小工具（构建图标用）
├── build_exe.ps1         # PyInstaller 打包脚本
├── GnirehtetGUI.spec     # PyInstaller 打包配置
├── requirements.txt      # Python 依赖
├── gnirehtet.exe / .apk  # 反向网络共享核心（Apache-2.0）
├── adb.exe 等            # Android platform-tools 组件（Apache-2.0）
├── icon.png / icon.ico   # 应用图标
└── THIRD_PARTY_NOTICES.md# 第三方组件声明
```

## 常见问题

**Q：提示「未检测到 ADB 设备」？**
检查 USB 线（部分线材仅供电不传数据）、手机是否已开启 USB 调试、是否在手机上确认了调试授权弹窗。

**Q：启动后手机没网？**
确认手机上已允许 VPN 连接请求；部分国产 ROM（MIUI 等）需在后台弹出框中手动确认，请留意通知栏。

**Q：停止后手机还挂着 VPN 图标？**
再次点击 **■ 停止共享**，或在手机系统设置的 VPN 中手动断开。

## 致谢

- [Genymobile / gnirehtet](https://github.com/Genymobile/gnirehtet) — 反向网络共享核心工具（Apache-2.0）
- [Android platform-tools](https://developer.android.com/tools/releases/platform-tools) — ADB 组件（Apache-2.0）
- [PySide6 / Qt](https://www.qt.io/) — 图形界面框架

## 许可证

本项目源代码以 [MIT License](LICENSE) 发布。

仓库内分发的第三方二进制组件（gnirehtet、adb 等）归各自作者所有，遵循 Apache License 2.0，详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 [LICENSE-APACHE-2.0.txt](LICENSE-APACHE-2.0.txt)。
