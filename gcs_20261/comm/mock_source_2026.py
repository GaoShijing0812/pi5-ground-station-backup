# -*- coding: utf-8 -*-
"""
MockSource2026 —— 假数据源，演示任务1(伴飞抛投) / 任务2(动态起降) 两条流程。

QTimer 每 100ms tick 一次，按脚本时间线推进：
  小车从 A 沿轨迹跑（约 60s 一圈），无人机走状态链。
  任务1：起飞→悬停3s→伴飞→抛投→返航→降落H。
  任务2：起飞→悬停→搜索→飞到上方→降落到运动平台→停留5s→起飞→返航→降落H。
用 set_task(1/2) 切换；接真实 LoRa 时换成 LoraSource2026（实现同接口），此文件可整个不要。
"""
from PyQt5.QtCore import QTimer
import config_2026 as C
from comm.source_interface_2026 import MissionSource2026
from models.drone_state import DroneState

TICK_MS = 100
CAR_LAP_S = 60.0          # 小车跑完一圈的模拟用时(演示值，实际≤90s)
PLATFORM_ALT_CM = 15.0    # 小车平台离地高度(演示值，无人机落上去时的高度)


class MockSource2026(MissionSource2026):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.setInterval(TICK_MS)
        self.timer.timeout.connect(self._tick)
        self.t = 0.0
        self.running = False
        self.task = 1          # 当前演示任务(1=抛投, 2=动态起降)

    def set_task(self, n):
        """切换要演示的任务(1/2)。运行中切换会先停。"""
        if self.running:
            self.stop()
        self.task = 2 if int(n) == 2 else 1
        self.log_message.emit(f"已切到任务{self.task}演示")

    def start(self):
        self.t = 0.0
        self.running = True
        self.timer.start()
        self.mission_started.emit()
        self.log_message.emit(f"任务{self.task}开始：小车发车 + 无人机起飞")

    def stop(self):
        self.running = False
        self.timer.stop()
        self.log_message.emit("任务停止")

    def _tick(self):
        self.t += TICK_MS / 1000.0
        self.timer_tick.emit(self.t)
        self._update_car()
        self._update_drone()

    def _update_car(self):
        # 小车启动即匀速循线；到 A(t满一圈)后停
        prog = min(self.t / CAR_LAP_S, 1.0)
        x, y = C.track_point(prog)
        self.car_pos.emit(x, y, prog)
        if prog >= 1.0 and self.running:
            self.log_message.emit("小车回到 A 点停车")
            self.running = False
            self.timer.stop()
            self.mission_finished.emit()

    def _update_drone(self):
        """按当前任务分派到对应时间线。"""
        if self.task == 2:
            self._update_drone_task2()
        else:
            self._update_drone_task1()

    def _update_drone_task1(self):
        """任务1 脚本时间线（秒）。位置用简单插值，只为演示 UI。"""
        t = self.t
        hx, hy = C.POINT_H
        car_prog = min(t / CAR_LAP_S, 1.0)
        cx, cy = C.track_point(car_prog)

        if t < 5.0:
            # 起飞：H 点原地升高（地图上位置不变，高度爬升）
            self._set(DroneState.TAKEOFF, hx, hy, 0.0, alt=C.CRUISE_ALT_CM * (t/5.0))
        elif t < 8.0:
            # 悬停 3s
            self._set(DroneState.HOVER, hx, hy, 0.0, alt=C.CRUISE_ALT_CM)
        elif t < 16.0:
            # 飞向小车上方（H → 小车当前位置线性插值），形成伴飞
            k = (t - 8.0) / 8.0
            x = hx + (cx - hx) * k
            y = hy + (cy - hy) * k
            self._set(DroneState.FOLLOW, x, y, 0.0, alt=C.CRUISE_ALT_CM)
        elif t < 26.0:
            # 伴飞跟随小车
            self._set(DroneState.FOLLOW, cx, cy, 0.0, alt=C.CRUISE_ALT_CM)
        elif t < 27.5:
            # 抛投（在小车上方松爪）
            if abs(t - 26.0) < TICK_MS/1000.0 + 1e-6:
                self.log_message.emit("抛投：舵机松爪，物资投向平台中心")
            self._set(DroneState.DROP, cx, cy, 0.0, alt=C.CRUISE_ALT_CM)
        elif t < 40.0:
            # 返航：小车位置 → H 线性插值
            k = min((t - 27.5) / 10.0, 1.0)
            x = cx + (hx - cx) * k
            y = cy + (hy - cy) * k
            self._set(DroneState.RETURN, x, y, 0.0, alt=C.CRUISE_ALT_CM)
        elif t < 45.0:
            # 视觉落桩回 H，高度下降
            k = (t - 40.0) / 5.0
            self._set(DroneState.LANDING_H, hx, hy, 0.0, alt=C.CRUISE_ALT_CM * (1-k))
        else:
            self._set(DroneState.LANDED, hx, hy, 0.0, alt=0.0)

    def _update_drone_task2(self):
        """任务2 动态起降脚本时间线（秒）。
        起飞→悬停→搜索→飞到小车上方→降落到运动平台→停留5s→起飞→返航→降落H。
        关键：ONBOARD 那 5s 无人机位置=小车位置(跟着车一起动)。"""
        t = self.t
        hx, hy = C.POINT_H
        car_prog = min(t / CAR_LAP_S, 1.0)
        cx, cy = C.track_point(car_prog)

        if t < 5.0:
            # 起飞：H 点原地升高
            self._set(DroneState.TAKEOFF, hx, hy, 0.0, alt=C.CRUISE_ALT_CM * (t/5.0))
        elif t < 8.0:
            # 悬停 3s @150
            self._set(DroneState.HOVER, hx, hy, 0.0, alt=C.CRUISE_ALT_CM)
        elif t < 14.0:
            # 搜索：雷达光流粗定位飞向航迹上方（H → 小车当前位置插值）
            k = (t - 8.0) / 6.0
            x = hx + (cx - hx) * k
            y = hy + (cy - hy) * k
            self._set(DroneState.SEARCH, x, y, 0.0, alt=C.CRUISE_ALT_CM)
        elif t < 20.0:
            # 飞到小车正上方，定高对准（保持巡航高度跟随）
            self._set(DroneState.FOLLOW, cx, cy, 0.0, alt=C.CRUISE_ALT_CM)
        elif t < 28.0:
            # 降落到运动平台：高度从 150 降到平台高度，XY 始终跟着车
            if abs(t - 20.0) < TICK_MS/1000.0 + 1e-6:
                self.log_message.emit("开始降落到运动中的小车平台")
            k = (t - 20.0) / 8.0
            alt = C.CRUISE_ALT_CM + (PLATFORM_ALT_CM - C.CRUISE_ALT_CM) * k
            self._set(DroneState.DESCEND, cx, cy, 0.0, alt=alt)
        elif t < 33.0:
            # 平台停留 5s：位置=小车位置(跟车一起动)，停在平台高度
            if abs(t - 28.0) < TICK_MS/1000.0 + 1e-6:
                self.log_message.emit("已停稳在平台上，停留 5s")
            self._set(DroneState.ONBOARD, cx, cy, 0.0, alt=PLATFORM_ALT_CM)
        elif t < 39.0:
            # 自主起飞：从平台升回巡航高度，刚起飞仍在车上方
            if abs(t - 33.0) < TICK_MS/1000.0 + 1e-6:
                self.log_message.emit("从平台自主起飞，回巡航高度")
            k = (t - 33.0) / 6.0
            alt = PLATFORM_ALT_CM + (C.CRUISE_ALT_CM - PLATFORM_ALT_CM) * k
            self._set(DroneState.TAKEOFF, cx, cy, 0.0, alt=alt)
        elif t < 50.0:
            # 返航：小车位置 → H 线性插值
            k = min((t - 39.0) / 8.0, 1.0)
            x = cx + (hx - cx) * k
            y = cy + (hy - cy) * k
            self._set(DroneState.RETURN, x, y, 0.0, alt=C.CRUISE_ALT_CM)
        elif t < 55.0:
            # 视觉落桩回 H，高度下降
            k = (t - 50.0) / 5.0
            self._set(DroneState.LANDING_H, hx, hy, 0.0, alt=C.CRUISE_ALT_CM * (1-k))
        else:
            self._set(DroneState.LANDED, hx, hy, 0.0, alt=0.0)

    def _set(self, state, x, y, yaw, alt):
        if getattr(self, "_last_state", None) != state:
            self._last_state = state
            self.log_message.emit(f"无人机状态 → {state.label}")
        self.drone_state.emit(state)
        self.drone_pos.emit(x, y, yaw, alt)
