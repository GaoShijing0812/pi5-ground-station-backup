#!/usr/bin/env python3
"""地面站入口 - Step 10: 全屏化 + 退出机制"""
import argparse
import os
import sys
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialog, QShortcut,
    QTabWidget,
)
from ui.video_widget import VideoWidget
from PyQt5.QtGui import QKeySequence

import config
from models.mission import Mission
from ui.map_widget import MapWidget
from ui.animal_list_widget import AnimalListWidget
from ui.summary_widget import SummaryWidget
from ui.history_dialog import HistoryDialog
from planning.bfs import plan_bfs_path
from comm.lora_source import LoraSource
from storage.mission_log import save_mission


class MainWindow(QMainWindow):
    def __init__(self, start_fullscreen: bool = True):
        super().__init__()
        self.setWindowTitle("2025 电赛 H 题地面站")
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)

        self.mission = Mission()
        self.source = LoraSource(port_name='/dev/ttyAMA3', parent=self)
        self._start_fullscreen = start_fullscreen

        central = QWidget()
        vlayout = QVBoxLayout(central)
        vlayout.setContentsMargins(8, 8, 8, 8)
        vlayout.setSpacing(6)

        # 顶部按钮条
        btn_bar = QHBoxLayout()

        for text, style, slot, name in [
            ("清除禁飞区", "padding: 8px 12px; font-size: 13px;", self.on_clear, "clear_btn"),
            ("规划航线", "padding: 8px 12px; font-size: 13px; background: #2196f3; color: white;", self.on_plan, "plan_btn"),
            ("▶ 开始巡查", "padding: 8px 12px; font-size: 13px; background: #4caf50; color: white;", self.on_start, "start_btn"),
            ("■ 停止", "padding: 8px 12px; font-size: 13px; background: #f44336; color: white;", self.on_stop, "stop_btn"),
            ("📁 历史", "padding: 8px 12px; font-size: 13px; background: #9c27b0; color: white;", self.on_show_history, "history_btn"),
        ]:
            btn = QPushButton(text)
            btn.setStyleSheet(style)
            btn.clicked.connect(slot)
            btn_bar.addWidget(btn)
            setattr(self, name, btn)

        # 全屏切换按钮（触摸屏无键盘时用）
        fs_text = "⛶ 退出全屏" if start_fullscreen else "⛶ 全屏"
        self.fullscreen_btn = QPushButton(fs_text)
        self.fullscreen_btn.setStyleSheet(
            "padding: 8px 12px; font-size: 13px; background: #607d8b; color: white;"
        )
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        btn_bar.addWidget(self.fullscreen_btn)

        btn_bar.addStretch()
        hint = QLabel("F11 切换全屏 | ESC 退出全屏 | Ctrl+Q 关闭")
        hint.setStyleSheet("color: #666; font-size: 11px;")
        btn_bar.addWidget(hint)
        vlayout.addLayout(btn_bar)

        # ---- 中间 Tab 区域 ----
        self.tabs = QTabWidget()

        # Tab 1: 地图 & 识别 (原样)
        map_tab = QWidget()
        h_main = QHBoxLayout(map_tab)
        h_main.setContentsMargins(0, 0, 0, 0)
        h_main.setSpacing(8)

        self.map_widget = MapWidget(self.mission)
        self.map_widget.forbidden_changed.connect(self.on_forbidden_changed)
        h_main.addWidget(self.map_widget, stretch=3)

        side = QVBoxLayout()
        side.setSpacing(8)
        list_label = QLabel("识别记录")
        list_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        side.addWidget(list_label)
        self.animal_list = AnimalListWidget(self.mission)
        side.addWidget(self.animal_list, stretch=2)
        self.summary = SummaryWidget(self.mission)
        side.addWidget(self.summary, stretch=1)
        h_main.addLayout(side, stretch=1)

        self.tabs.addTab(map_tab, "🗺 地图 & 识别")

        # Tab 2: 图传
        self.video_widget = VideoWidget(config.RTSP_URL, self)
        self.tabs.addTab(self.video_widget, "📹 图传")

        vlayout.addWidget(self.tabs, stretch=1)
        self.setCentralWidget(central)

        # 数据源信号
        self.source.position_updated.connect(self.on_position_updated)
        self.source.animal_sighted.connect(self.on_animal_sighted)
        self.source.mission_started.connect(self.on_mission_started)
        self.source.mission_finished.connect(self.on_mission_finished)
        self.source.log_message.connect(self.on_log)

        # 全屏快捷键
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("Esc"), self, self.exit_fullscreen)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)

        self._update_status()

    # ---- 全屏 ----
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

    # ---- 状态栏 ----
    def _update_status(self):
        n = len(self.mission.forbidden_zones)
        cells = "、".join(c.code() for c in self.mission.forbidden_zones) or "（空）"
        path_n = len(self.mission.planned_path)
        path_info = f"航线: {path_n} 点" if path_n > 0 else "航线: 未规划"
        pos = self.mission.current_position
        pos_info = f"位置: {pos.code()}" if pos else "位置: 待起飞"
        self.statusBar().showMessage(
            f"禁飞区: {n}/{config.FORBIDDEN_COUNT} [{cells}]  |  {path_info}  |  {pos_info}"
        )

    # ---- 按钮回调 ----
    def on_clear(self):
        self.source.stop()
        self.mission.forbidden_zones.clear()
        self.mission.planned_path = []
        self.mission.current_position = None
        self.mission.sightings.clear()
        self.map_widget.update()
        self.animal_list.clear_all()
        self.summary.refresh()
        self._update_status()

    def on_plan(self):
        self.source.stop()
        self.mission.current_position = None
        self.mission.planned_path = plan_bfs_path(self.mission.forbidden_zones)
        self.map_widget.update()
        self._update_status()

    def on_start(self):
        if not self.mission.planned_path:
            self.statusBar().showMessage("先规划航线再开始", 3000)
            return
        # 先把航线告诉飞控,再开始接收动物帧
        if not self.source.send_waypoints(self.mission.planned_path):
            return  # 发送失败,log_message 已报错,不进入接收状态
        self.mission.started_at = datetime.now()
        self.source.start(self.mission)

    def on_stop(self):
        self.source.stop()

    def on_show_history(self):
        dialog = HistoryDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_mission:
            self.source.stop()
            loaded = dialog.selected_mission
            self.mission.forbidden_zones = loaded.forbidden_zones
            self.mission.planned_path = loaded.planned_path
            self.mission.sightings = loaded.sightings
            self.mission.current_position = None
            self.mission.status = loaded.status
            self.mission.started_at = loaded.started_at
            self.mission.finished_at = loaded.finished_at
            self.map_widget.update()
            self.animal_list.rebuild_from_mission()
            self.summary.refresh()
            self._update_status()
            self.statusBar().showMessage("历史任务已加载", 3000)

    def on_forbidden_changed(self):
        self.source.stop()
        self.mission.planned_path = []
        self.mission.current_position = None
        self.map_widget.update()
        self._update_status()

    # ---- 数据源回调 ----
    def on_position_updated(self, cell):
        self.map_widget.update()
        self._update_status()

    def on_animal_sighted(self, sighting):
        self.animal_list.add_sighting(sighting)
        self.summary.refresh()

    def on_mission_started(self):
        self.animal_list.clear_all()
        self.summary.refresh()
        self.map_widget.update()

    def on_mission_finished(self):
        self.map_widget.update()
        self._update_status()
        try:
            self.mission.finished_at = datetime.now()
            path = save_mission(self.mission)
            self.statusBar().showMessage(
                f"任务完成，已保存到 {os.path.basename(path)}", 5000
            )
        except Exception as e:
            self.statusBar().showMessage(f"保存失败: {e}", 5000)

    def on_log(self, msg):
        self.statusBar().showMessage(msg, 3000)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="2025 电赛 H 题地面站")
    parser.add_argument(
        "--windowed", action="store_true",
        help="启动为窗口模式（默认全屏；开发调试用）"
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    win = MainWindow(start_fullscreen=not args.windowed)
    if args.windowed:
        win.show()
    else:
        win.showFullScreen()
    sys.exit(app.exec_())
