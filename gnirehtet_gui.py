"""
Gnirehtet GUI - Android USB 反向网络共享工具
基于 PySide6 构建，配合 gnirehtet.exe 使用
"""

import sys
import os
import subprocess
import threading
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QTextEdit,
    QGroupBox, QSplitter, QFrame, QStatusBar, QMessageBox, QToolBar,
    QSizePolicy
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QTimer, QSize
)
from PySide6.QtGui import (
    QFont, QColor, QTextCursor, QPalette, QIcon, QAction
)

# ─── 工具路径（兼容 PyInstaller --onefile 打包后的临时目录）──────
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS          # 打包运行时解压到的临时目录
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ADB_PATH = os.path.join(BASE_DIR, "adb.exe")
GNIREHTET_PATH = os.path.join(BASE_DIR, "gnirehtet.exe")
APK_PATH = os.path.join(BASE_DIR, "gnirehtet.apk")


# ─── 颜色主题（青白简约风）────────────────────────────────────
DARK = {
    "bg":          "#f2fafa",
    "surface":     "#ffffff",
    "surface2":    "#e6f4f6",
    "border":      "#a8d8e0",
    "accent":      "#0b8fa6",
    "accent_dark": "#086f82",
    "green":       "#0f9e60",
    "red":         "#d63050",
    "yellow":      "#c47a00",
    "cyan":        "#0b8fa6",
    "text":        "#13373f",
    "text_dim":    "#5a8a96",
}


# ─── 后台线程：执行命令并实时输出日志 ─────────────────────────
class CommandThread(QThread):
    log_signal   = Signal(str, str)   # (text, level)
    done_signal  = Signal(bool)       # success

    def __init__(self, cmd: list, cwd: str):
        super().__init__()
        self.cmd = cmd
        self.cwd = cwd
        self.process = None
        self._stopped = False

    def run(self):
        try:
            self.process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=self.cwd,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in iter(self.process.stdout.readline, ""):
                if self._stopped:
                    break
                line = line.rstrip()
                if line:
                    lvl = "error" if any(k in line.lower() for k in ("error", "fail", "exception")) \
                        else "warn"  if any(k in line.lower() for k in ("warn", "permission")) \
                        else "ok"    if any(k in line.lower() for k in ("started", "connected", "install")) \
                        else "info"
                    self.log_signal.emit(line, lvl)
            self.process.stdout.close()
            self.process.wait()
            self.done_signal.emit(self.process.returncode == 0)
        except Exception as e:
            self.log_signal.emit(f"执行错误: {e}", "error")
            self.done_signal.emit(False)

    def stop(self):
        self._stopped = True
        if self.process and self.process.poll() is None:
            self.process.terminate()


# ─── 后台线程：一次性运行并返回结果（用于 adb devices）────────
class QueryThread(QThread):
    result_signal = Signal(list)

    def __init__(self, cmd: list, cwd: str):
        super().__init__()
        self.cmd = cmd
        self.cwd = cwd

    def run(self):
        try:
            r = subprocess.run(
                self.cmd, capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                cwd=self.cwd,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
            lines = r.stdout.strip().splitlines()
            devices = []
            for line in lines[1:]:          # 跳过 "List of devices attached"
                if "\t" in line:
                    serial, state = line.split("\t", 1)
                    devices.append((serial.strip(), state.strip()))
            self.result_signal.emit(devices)
        except Exception:
            self.result_signal.emit([])


# ─── 主窗口 ────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.gnirehtet_thread: CommandThread | None = None
        self.query_thread:     QueryThread   | None = None
        self.stop_thread:      CommandThread | None = None
        self.install_thread:   CommandThread | None = None
        self.is_running = False
        self._init_ui()
        self._apply_style()
        self._refresh_devices()

        # 定时自动刷新设备列表
        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self._refresh_devices)
        self.auto_timer.start(5000)

    # ── 构建界面 ────────────────────────────────────────────────
    def _init_ui(self):
        self.setWindowTitle("Gnirehtet — Android USB 反向网络共享")
        self.setMinimumSize(900, 620)
        self.resize(960, 680)

        central = QWidget()
        central.setObjectName("central_widget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        # ── 顶部 Banner ─────────────────────────────────────────
        banner = QFrame()
        banner.setObjectName("banner")
        banner.setFixedHeight(80)
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(20, 12, 20, 12)
        b_layout.setSpacing(10)

        title_lbl = QLabel("Gnirehtet")
        title_lbl.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        title_lbl.setObjectName("title")

        subtitle_lbl = QLabel("Android USB 反向网络共享")
        subtitle_lbl.setFont(QFont("Segoe UI", 9))
        subtitle_lbl.setObjectName("subtitle")

        self.status_dot = QLabel("●")
        self.status_dot.setFont(QFont("Segoe UI", 14))
        self.status_dot.setObjectName("dot_stopped")
        self.status_dot.setToolTip("运行状态指示")

        self.status_lbl = QLabel("未运行")
        self.status_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.status_lbl.setObjectName("status_stopped")

        # 右侧状态区域用半透明胶囊容器包裹
        status_frame = QFrame()
        status_frame.setObjectName("status_badge")
        sf_layout = QHBoxLayout(status_frame)
        sf_layout.setContentsMargins(10, 4, 14, 4)
        sf_layout.setSpacing(6)
        sf_layout.addWidget(self.status_dot)
        sf_layout.addWidget(self.status_lbl)

        v = QVBoxLayout()
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)
        v.addWidget(title_lbl)
        v.addWidget(subtitle_lbl)
        b_layout.addLayout(v)
        b_layout.addStretch()
        b_layout.addWidget(status_frame)
        root.addWidget(banner)

        # ── 主体分割面板 ────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)

        # ── 左侧：设备面板 + 控制按钮 ───────────────────────────
        left = QWidget()
        left.setMaximumWidth(260)
        left.setMinimumWidth(220)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # 设备列表
        dev_group = QGroupBox("已连接设备")
        dev_group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        dev_inner = QVBoxLayout(dev_group)
        dev_inner.setSpacing(6)

        self.device_list = QListWidget()
        self.device_list.setFont(QFont("Consolas", 9))
        self.device_list.setAlternatingRowColors(True)
        self.device_list.setFixedHeight(160)
        dev_inner.addWidget(self.device_list)

        self.refresh_btn = QPushButton("🔄  刷新设备")
        self.refresh_btn.setObjectName("btn_secondary")
        self.refresh_btn.clicked.connect(self._refresh_devices)
        dev_inner.addWidget(self.refresh_btn)

        self.dev_hint = QLabel("每 5 秒自动刷新")
        self.dev_hint.setObjectName("hint")
        self.dev_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_inner.addWidget(self.dev_hint)

        left_layout.addWidget(dev_group)

        # 控制按钮
        ctrl_group = QGroupBox("操作控制")
        ctrl_group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        ctrl_inner = QVBoxLayout(ctrl_group)
        ctrl_inner.setSpacing(8)

        self.run_btn = QPushButton("▶  启动共享")
        self.run_btn.setObjectName("btn_green")
        self.run_btn.setFixedHeight(42)
        self.run_btn.clicked.connect(self._on_run)

        self.stop_btn = QPushButton("■  停止共享")
        self.stop_btn.setObjectName("btn_red")
        self.stop_btn.setFixedHeight(42)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)

        self.install_btn = QPushButton("📲  仅安装 APK")
        self.install_btn.setObjectName("btn_secondary")
        self.install_btn.setFixedHeight(36)
        self.install_btn.clicked.connect(self._on_install)

        ctrl_inner.addWidget(self.run_btn)
        ctrl_inner.addWidget(self.stop_btn)
        ctrl_inner.addWidget(self.install_btn)

        # 说明文字
        tip = QLabel(
            "<span style='color:#0b8fa6;font-weight:bold;'>▶ 启动共享</span>：自动安装 APK 并开始共享<br>"
            "<span style='color:#d63050;font-weight:bold;'>■ 停止共享</span>：断开网络共享<br>"
            "<span style='color:#0b8fa6;font-weight:bold;'>📲 仅安装</span>：只推送 APK 不启动"
        )
        tip.setObjectName("tip")
        tip.setWordWrap(True)
        tip.setFont(QFont("Segoe UI", 8))
        ctrl_inner.addWidget(tip)

        left_layout.addWidget(ctrl_group)
        left_layout.addStretch()

        splitter.addWidget(left)

        # ── 右侧：日志输出 ──────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        log_header = QHBoxLayout()
        log_title = QLabel("运行日志")
        log_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.clear_btn = QPushButton("清空日志")
        self.clear_btn.setObjectName("btn_tiny")
        self.clear_btn.setFixedHeight(26)
        self.clear_btn.clicked.connect(self._clear_log)
        log_header.addWidget(log_title)
        log_header.addStretch()
        log_header.addWidget(self.clear_btn)
        right_layout.addLayout(log_header)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("Consolas", 9))
        self.log_box.setObjectName("log_box")
        right_layout.addWidget(self.log_box)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter)

        # ── 底部状态栏 ──────────────────────────────────────────
        self.statusBar().setFont(QFont("Segoe UI", 9))
        self.statusBar().showMessage("就绪  |  gnirehtet v2.x + platform-tools 36.0.2")

    # ── 样式表 ──────────────────────────────────────────────────
    def _apply_style(self):
        c = DARK
        self.setStyleSheet(f"""
        QMainWindow {{
            background-color: {c['bg']};
        }}
        QWidget {{
            color: {c['text']};
            font-family: "Segoe UI";
        }}
        /* 所有 Label 默认透明底，防止遮挡父容器背景 */
        QLabel {{
            background: transparent;
        }}
        /* 主背景容器 */
        QWidget#central_widget {{
            background-color: {c['bg']};
        }}
        /* Banner */
        QFrame#banner {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {c['accent']}, stop:1 #12b8d4);
            border-radius: 10px;
            border: none;
        }}
        QLabel#title    {{ color: #ffffff; background: transparent; }}
        QLabel#subtitle {{ color: #d0f4fa; background: transparent; }}
        /* 状态胶囊 */
        QFrame#status_badge {{
            background-color: #097d96;
            border-radius: 14px;
            border: 1px solid #5dd4e8;
        }}
        QLabel#dot_stopped {{ color: #9de8f2; background: transparent; }}
        QLabel#dot_running {{ color: #ffffff; background: transparent; }}
        QLabel#status_stopped {{ color: #c8f0f8; background: transparent; }}
        QLabel#status_running {{ color: #ffffff; font-weight: bold; background: transparent; }}

        /* GroupBox */
        QGroupBox {{
            background-color: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            margin-top: 14px;
            padding: 8px 6px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            color: {c['accent']};
            font-weight: bold;
        }}

        /* List */
        QListWidget {{
            background-color: {c['surface2']};
            border: 1px solid {c['border']};
            border-radius: 6px;
            color: {c['text']};
            selection-background-color: {c['accent']};
            selection-color: #ffffff;
            outline: none;
        }}
        QListWidget::alternate-row {{
            background-color: {c['surface']};
        }}
        QListWidget::item:hover {{
            background-color: #cceef4;
        }}

        /* Buttons */
        QPushButton {{
            border-radius: 6px;
            font-family: "Segoe UI";
            font-size: 10pt;
            padding: 4px 12px;
            border: none;
        }}
        QPushButton#btn_green {{
            background-color: {c['green']};
            color: #ffffff;
            font-weight: bold;
        }}
        QPushButton#btn_green:hover  {{ background-color: #12b86a; }}
        QPushButton#btn_green:pressed{{ background-color: #0c8a4e; }}
        QPushButton#btn_green:disabled{{ background-color: #b0d9c4; color: #8ab8a4; }}

        QPushButton#btn_red {{
            background-color: {c['red']};
            color: #ffffff;
            font-weight: bold;
        }}
        QPushButton#btn_red:hover  {{ background-color: #e8405e; }}
        QPushButton#btn_red:pressed{{ background-color: #b02040; }}
        QPushButton#btn_red:disabled{{ background-color: #eabac4; color: #c08898; }}

        QPushButton#btn_secondary {{
            background-color: {c['surface2']};
            color: {c['accent']};
            border: 1px solid {c['border']};
        }}
        QPushButton#btn_secondary:hover  {{ background-color: #cdedf4; border-color: {c['accent']}; }}
        QPushButton#btn_secondary:pressed{{ background-color: {c['border']}; }}

        QPushButton#btn_tiny {{
            background-color: transparent;
            color: {c['text_dim']};
            border: 1px solid {c['border']};
            font-size: 8pt;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        QPushButton#btn_tiny:hover{{ color: {c['accent']}; border-color: {c['accent']}; }}

        /* 日志 */
        QTextEdit#log_box {{
            background-color: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            color: {c['text']};
        }}

        /* Splitter */
        QSplitter::handle {{
            background-color: {c['border']};
        }}

        /* 提示文字 */
        QLabel#hint {{ color: {c['text_dim']}; font-size: 8pt; }}
        QLabel#tip  {{ color: {c['text_dim']}; padding: 4px; line-height: 1.6; }}

        /* 状态栏 */
        QStatusBar {{ background-color: {c['surface']}; color: {c['text_dim']}; border-top: 1px solid {c['border']}; }}

        /* 滚动条 */
        QScrollBar:vertical {{
            background: {c['surface2']};
            width: 8px; border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {c['border']}; border-radius: 4px; min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {c['accent']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

    # ── 日志追加 ────────────────────────────────────────────────
    def _log(self, text: str, level: str = "info"):
        # info 级别不输出
        if level == "info":
            return
        colors = {
            "info":  DARK["text"],
            "ok":    DARK["green"],
            "warn":  DARK["yellow"],
            "error": DARK["red"],
            "cyan":  DARK["accent"],
            "dim":   DARK["text_dim"],
        }
        color = colors.get(level, DARK["text"])
        ts = datetime.now().strftime("%H:%M:%S")
        html = (
            f'<span style="color:{DARK["text_dim"]};">[{ts}]</span> '
            f'<span style="color:{color};">{text}</span>'
        )
        self.log_box.append(html)
        self.log_box.moveCursor(QTextCursor.MoveOperation.End)

    def _clear_log(self):
        self.log_box.clear()
        self._log("日志已清空", "dim")

    # ── 刷新设备列表 ────────────────────────────────────────────
    def _refresh_devices(self):
        if not os.path.exists(ADB_PATH):
            self._update_device_list([])
            return
        if self.query_thread and self.query_thread.isRunning():
            return
        self.query_thread = QueryThread([ADB_PATH, "devices"], BASE_DIR)
        self.query_thread.result_signal.connect(self._update_device_list)
        self.query_thread.start()

    def _update_device_list(self, devices: list):
        self.device_list.clear()
        if not devices:
            item = QListWidgetItem("  暂无设备连接")
            item.setForeground(QColor(DARK["text_dim"]))
            self.device_list.addItem(item)
            self.statusBar().showMessage("未检测到 ADB 设备，请检查 USB 连接和调试模式")
        else:
            for serial, state in devices:
                icon = "✅" if state == "device" else "⚠️"
                item = QListWidgetItem(f"  {icon}  {serial}  [{state}]")
                if state == "device":
                    item.setForeground(QColor(DARK["green"]))
                else:
                    item.setForeground(QColor(DARK["yellow"]))
                item.setData(Qt.ItemDataRole.UserRole, serial)
                self.device_list.addItem(item)
            self.statusBar().showMessage(f"检测到 {len(devices)} 台设备  |  gnirehtet 36.0.2")

    def _get_selected_serial(self) -> str | None:
        """返回当前选中设备序列号，若未选则返回 None（使用默认）"""
        item = self.device_list.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    # ── 按钮事件 ────────────────────────────────────────────────
    def _on_run(self):
        if not os.path.exists(GNIREHTET_PATH):
            QMessageBox.critical(self, "错误", f"找不到 gnirehtet.exe:\n{GNIREHTET_PATH}")
            return

        serial = self._get_selected_serial()
        cmd = [GNIREHTET_PATH, "run"]
        if serial:
            cmd.append(serial)

        self._log("━" * 50, "dim")
        self._log(f"启动命令: {' '.join(cmd)}", "dim")
        self._log("正在安装 APK 并启动反向网络共享...", "cyan")
        self._log("手机会弹出 VPN 授权请求，请点击【确定】", "warn")

        self._set_running(True)
        self.gnirehtet_thread = CommandThread(cmd, BASE_DIR)
        self.gnirehtet_thread.log_signal.connect(self._log)
        self.gnirehtet_thread.done_signal.connect(self._on_done)
        self.gnirehtet_thread.start()

    def _on_stop(self):
        serial = self._get_selected_serial()
        cmd = [GNIREHTET_PATH, "stop"]
        if serial:
            cmd.append(serial)

        self._log("━" * 50, "dim")
        self._log("正在向手机发送停止指令...", "warn")

        # 停止期间禁用按鈕，防止重复点击
        self.stop_btn.setEnabled(False)
        self.stop_btn.setText("⏳  停止中...")

        # 存为实例变量防止被 GC 销毁
        self.stop_thread = CommandThread(cmd, BASE_DIR)
        self.stop_thread.log_signal.connect(self._log)
        self.stop_thread.done_signal.connect(self._on_stop_done)
        self.stop_thread.start()

    def _on_stop_done(self, ok: bool):
        """gnirehtet stop 指令执行完毕后，再终止本地进程"""
        if ok:
            self._log("手机 VPN 已断开 ✓", "ok")
        else:
            self._log("停止指令已发送（手机可能需手动关闭 VPN）", "warn")

        # 终止本地 gnirehtet run 进程
        if self.gnirehtet_thread and self.gnirehtet_thread.isRunning():
            self.gnirehtet_thread.stop()
            self.gnirehtet_thread.wait(3000)

        self.stop_btn.setText("■  停止共享")
        self._set_running(False)

    def _on_install(self):
        if not os.path.exists(APK_PATH):
            QMessageBox.warning(self, "提示", f"找不到 APK 文件:\n{APK_PATH}")
            return

        serial = self._get_selected_serial()
        cmd = [GNIREHTET_PATH, "install"]
        if serial:
            cmd.append(serial)

        self._log("━" * 50, "dim")
        self._log(f"安装 gnirehtet.apk → {serial or '默认设备'}", "cyan")

        self.install_thread = CommandThread(cmd, BASE_DIR)
        self.install_thread.log_signal.connect(self._log)
        self.install_thread.done_signal.connect(lambda ok: self._log(
            "APK 安装成功 ✓" if ok else "APK 安装失败 ✗", "ok" if ok else "error"))
        self.install_thread.start()

    def _on_done(self, success: bool):
        if self.is_running:
            self._set_running(False)
            self._log("共享进程已退出", "warn")

    # ── 状态切换 ────────────────────────────────────────────────
    def _set_running(self, running: bool):
        self.is_running = running
        self.run_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.install_btn.setEnabled(not running)

        if running:
            self.status_dot.setObjectName("dot_running")
            self.status_lbl.setObjectName("status_running")
            self.status_dot.setText("●")
            self.status_lbl.setText("共享中")
        else:
            self.status_dot.setObjectName("dot_stopped")
            self.status_lbl.setObjectName("status_stopped")
            self.status_dot.setText("●")
            self.status_lbl.setText("未运行")

        # 强制刷新样式
        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)

    # ── 关闭事件 ────────────────────────────────────────────────
    def closeEvent(self, event):
        if self.is_running:
            reply = QMessageBox.question(
                self, "确认退出",
                "网络共享正在运行中，退出将中断共享。\n确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        if self.stop_thread and self.stop_thread.isRunning():
            self.stop_thread.wait(3000)
        if self.gnirehtet_thread and self.gnirehtet_thread.isRunning():
            self.gnirehtet_thread.stop()
            self.gnirehtet_thread.wait(2000)
        event.accept()


# ─── 入口 ──────────────────────────────────────────────────────
def main():
    # PySide6 默认已支持高 DPI，无需手动开启
    app = QApplication(sys.argv)
    app.setApplicationName("Gnirehtet GUI")
    app.setStyle("Fusion")

    # 设置应用图标（优先 .png，fallback .ico）
    for _icon_name in ("icon.png", "icon.ico"):
        icon_path = os.path.join(BASE_DIR, _icon_name)
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            break

    win = MainWindow()
    win._log("欢迎使用 Gnirehtet GUI", "cyan")
    win._log("步骤 1：手机打开【USB 调试模式】（开发者选项）", "info")
    win._log("步骤 2：用 USB 数据线连接手机", "info")
    win._log("步骤 3：点击【▶ 启动共享】，手机弹窗点确定即可上网", "info")
    win._log("━" * 50, "dim")
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
