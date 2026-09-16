# -*- coding: utf-8 -*-
"""
数据源抽象接口 —— 沿用 2025 gcs_pi5 的"可替换数据源"设计。

UI 只认这些信号，不关心数据从哪来。
- 现在：MockSource2026（QTimer 假数据，演示用）
- 将来：LoraSource2026（读 LoRa 真机遥测），实现同一套信号，UI 一行不改。

⚠️ 小车位置数据源未定（回传/时间推算/无人机视觉估计三选一），
   等定了只需新增一个 Source 子类，car_pos 信号照样发。
"""
from PyQt5.QtCore import QObject, pyqtSignal


class MissionSource2026(QObject):
    # 无人机位置：x_cm, y_cm, yaw_deg, alt_cm
    drone_pos = pyqtSignal(float, float, float, float)
    # 小车位置：x_cm, y_cm, progress(0~1)
    car_pos = pyqtSignal(float, float, float)
    # 无人机状态：DroneState 枚举
    drone_state = pyqtSignal(object)
    # 任务计时：seconds
    timer_tick = pyqtSignal(float)
    # 日志/事件文字
    log_message = pyqtSignal(str)
    # 任务开始/结束
    mission_started = pyqtSignal()
    mission_finished = pyqtSignal()

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def set_task(self, n):
        raise NotImplementedError
