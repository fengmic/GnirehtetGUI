# 第三方组件声明（Third-Party Notices）

本项目（源代码部分）以 MIT 许可证发布（见 [LICENSE](LICENSE)）。
为方便使用，仓库内随源码分发了以下第三方二进制组件，它们的著作权归各自作者所有，分别遵循 Apache License 2.0：

## 1. gnirehtet（gnirehtet.exe、gnirehtet.apk、libwinpthread-1.dll）

- 上游项目：https://github.com/Genymobile/gnirehtet
- 作者：Genymobile
- 许可证：Apache License 2.0
- 用途：反向网络共享（Reverse Tethering）核心工具，通过 adb 在 Android 设备上建立 VPN 通道，使手机经由电脑的网络上网。

## 2. Android platform-tools（adb.exe、AdbWinApi.dll、AdbWinUsbApi.dll）

- 来源：Android SDK platform-tools r36.0.2（见 `source.properties`）
- 作者：Google / The Android Open Source Project
- 许可证：Apache License 2.0（部分组件含 BSD 条款）
- 官方下载：https://developer.android.com/tools/releases/platform-tools
- 用途：ADB 通信，用于检测和连接 Android 设备。

## 许可证全文

Apache License 2.0 全文见 [LICENSE-APACHE-2.0.txt](LICENSE-APACHE-2.0.txt)。

---

其余未列出的 platform-tools 工具（fastboot、sqlite3 等）仅为本机日常使用保留在本地，不在本仓库中分发。
