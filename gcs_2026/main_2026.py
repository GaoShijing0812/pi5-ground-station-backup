# -*- coding: utf-8 -*-
"""
gcs_2026 主窗口 —— 2026 电赛 D 题地面站入口。

布局：
  ┌─ 工具栏: [▶开始] [■停止] [🧹清尾迹]   ⏱右侧计时 ─┐
  ├── 场地地图(左, 大) ── | ── 状态面板(右) ──┤
  └─ 状态栏(底部日志) ───────────────────────┘

运行：
  python3 main_2026.py            # 默认全屏(比赛现场)
  python3 main_2026.py --windowed # 窗口模式(开发调试)
"""
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout,
                             QVBoxLayout, QPushButton, QLabel, QStatusBar,
                             QShortcut)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

import config_2026 as C
from ui.field_widget import FieldWidget
from ui.status_widget import StatusWidget
from comm.mock_source_2026 import MockSource2026


class MainWindow(QMainWindow):
    def __init__(self, start_fullscreen: bool = True):
        super().__init__()
        self.setWindowTitle("2026 电赛 D 题 · 陆空协同地面站")
        self.resize(C.WINDOW_WIDTH, C.WINDOW_HEIGHT)
        self._start_fullscreen = start_fullscreen

        # 数据源（现在是 Mock；接 LoRa 时换 LoraSource2026 即可）
        self.source = MockSource2026(self)

        self._build_ui()
        self._wire_signals()
        self._setup_shortcuts()

    def _build_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(6, 6, 6, 6)

        # 工具栏
        bar = QHBoxLayout()
        # 任务切换（互斥）
        self.btn_task1 = QPushButton("任务1 抛投")
        self.btn_task2 = QPushButton("任务2 动态起降")
        for b in (self.btn_task1, self.btn_task2):
            b.setCheckable(True); b.setMinimumHeight(34); bar.addWidget(b)
        self.btn_task1.setChecked(True)
        bar.addSpacing(16)
        self.btn_start = QPushButton("▶ 开始")
        self.btn_stop = QPushButton("■ 停止")
        self.btn_clear = QPushButton("🧹 清尾迹")
        for b in (self.btn_start, self.btn_stop, self.btn_clear):
            b.setMinimumHeight(34); bar.addWidget(b)
        bar.addStretch(1)
        self.hint = QLabel("就绪"); self.hint.setStyleSheet("color:#888;")
        bar.addWidget(self.hint)
        bar.addSpacing(16)
        # 全屏切换按钮（初始文字随启动模式而定，和 2025 一致）
        fs_text = "⛶ 退出全屏" if self._start_fullscreen else "⛶ 全屏"
        self.fullscreen_btn = QPushButton(fs_text)
        self.fullscreen_btn.setMinimumHeight(34)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        bar.addWidget(self.fullscreen_btn)
        root.addLayout(bar)

        # 主区：地图 + 状态面板
        body = QHBoxLayout()
        self.field = FieldWidget()
        self.status = StatusWidget()
        self.status.setFixedWidth(240)
        body.addWidget(self.field, 1)
        body.addWidget(self.status)
        root.addLayout(body, 1)

        # 状态栏
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("等待开始  |  F11 切换全屏 · ESC 退出全屏 · Ctrl+Q 关闭")

    def _wire_signals(self):
        self.btn_start.clicked.connect(self.source.start)
        self.btn_stop.clicked.connect(self.source.stop)
        self.btn_clear.clicked.connect(self.field.clear_trail)
        self.btn_task1.clicked.connect(lambda: self._select_task(1))
        self.btn_task2.clicked.connect(lambda: self._select_task(2))

        self.source.drone_pos.connect(self._on_drone_pos)
        self.source.car_pos.connect(self._on_car_pos)
        self.source.drone_state.connect(self.status.set_state)
        self.source.timer_tick.connect(self.status.set_timer)
        self.source.log_message.connect(self.statusBar().showMessage)
        self.source.mission_started.connect(lambda: self.hint.setText("任务进行中"))
        self.source.mission_finished.connect(lambda: self.hint.setText("任务完成"))

    def _setup_shortcuts(self):
        """键盘快捷键：F11 切换全屏 / Esc 退出全屏 / Ctrl+Q 关闭（和 2025 一致）。"""
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("Esc"), self, self.exit_fullscreen)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setText("⛶ 全屏")
        else:
            self.showFullScreen()
            self.fullscreen_btn.setText("⛶ 退出全屏")

    def exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setText("⛶ 全屏")

    def _select_task(self, n):
        """任务1/2 互斥切换：切前先停+清尾迹，两按钮保持互斥。"""
        self.btn_task1.setChecked(n == 1)
        self.btn_task2.setChecked(n == 2)
        self.source.set_task(n)
        self.field.clear_trail()
        self.hint.setText(f"已选 任务{n}")

    def _on_drone_pos(self, x, y, yaw, alt):
        self.field.set_drone(x, y, yaw)
        self.status.set_drone_info(x, y, alt)

    def _on_car_pos(self, x, y, prog):
        self.field.set_car(x, y)
        self.status.set_car_info(x, y, prog)


def main():
    app = QApplication(sys.argv)
    windowed = "--windowed" in sys.argv
    win = MainWindow(start_fullscreen=not windowed)
    if windowed:
        win.show()
    else:
        win.showFullScreen()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
