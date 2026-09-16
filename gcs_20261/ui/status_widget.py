# -*- coding: utf-8 -*-
"""
无人机状态面板 —— 任务3 要求的"文字显示无人机状态"。
包含：大字状态、90s 任务计时器、无人机/小车数值信息。
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout)
from PyQt5.QtCore import Qt

import config_2026 as C
from models.drone_state import DroneState


class StatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.set_state(DroneState.IDLE)
        self.set_timer(0.0)
        self.set_drone_info(None, None, None)
        self.set_car_info(None, None, None)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # ---- 大字状态 ----
        cap = QLabel("无人机状态")
        cap.setStyleSheet("color:#666; font-size:12px;")
        root.addWidget(cap)

        self.state_lbl = QLabel("待命")
        self.state_lbl.setAlignment(Qt.AlignCenter)
        self.state_lbl.setMinimumHeight(70)
        root.addWidget(self.state_lbl)

        # ---- 90s 计时器 ----
        line = QFrame(); line.setFrameShape(QFrame.HLine); root.addWidget(line)
        self.timer_lbl = QLabel("00.0 s")
        self.timer_lbl.setAlignment(Qt.AlignCenter)
        self.timer_lbl.setStyleSheet(
            "font-size:30px; font-weight:bold; color:#222; font-family:monospace;")
        root.addWidget(self.timer_lbl)
        self.timer_cap = QLabel(f"任务限时 {int(C.TASK_TIME_LIMIT_S)}s")
        self.timer_cap.setAlignment(Qt.AlignCenter)
        self.timer_cap.setStyleSheet("color:#888; font-size:11px;")
        root.addWidget(self.timer_cap)

        # ---- 数值信息 ----
        line2 = QFrame(); line2.setFrameShape(QFrame.HLine); root.addWidget(line2)
        grid = QGridLayout(); grid.setSpacing(4)
        self.d_pos = QLabel("--"); self.d_alt = QLabel("--")
        self.c_pos = QLabel("--"); self.c_prog = QLabel("--")
        rows = [("无人机 X/Y", self.d_pos), ("无人机 高度", self.d_alt),
                ("小车 X/Y", self.c_pos), ("小车 进度", self.c_prog)]
        for i, (name, val) in enumerate(rows):
            k = QLabel(name); k.setStyleSheet("color:#666; font-size:12px;")
            val.setStyleSheet("font-size:13px; font-weight:bold; color:#222;")
            grid.addWidget(k, i, 0); grid.addWidget(val, i, 1)
        root.addLayout(grid)
        root.addStretch(1)

    # ---------- 对外接口 ----------
    def set_state(self, state: DroneState):
        r, g, b = state.color
        self.state_lbl.setText(state.label)
        self.state_lbl.setStyleSheet(
            f"background:rgb({r},{g},{b}); color:white; "
            f"font-size:30px; font-weight:bold; border-radius:8px;")

    def set_timer(self, seconds: float):
        self.timer_lbl.setText(f"{seconds:04.1f} s")
        # 超 90s 变红
        over = seconds > C.TASK_TIME_LIMIT_S
        self.timer_lbl.setStyleSheet(
            "font-size:30px; font-weight:bold; font-family:monospace; "
            + ("color:#d02020;" if over else "color:#222;"))

    def set_drone_info(self, x, y, alt):
        self.d_pos.setText("--" if x is None else f"{x:.0f}, {y:.0f} cm")
        self.d_alt.setText("--" if alt is None else f"{alt:.0f} cm")

    def set_car_info(self, x, y, progress):
        self.c_pos.setText("--" if x is None else f"{x:.0f}, {y:.0f} cm")
        self.c_prog.setText("--" if progress is None else f"{progress*100:.0f} %")
