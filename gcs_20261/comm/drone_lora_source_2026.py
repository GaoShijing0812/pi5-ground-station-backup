# -*- coding: utf-8 -*-
"""在队友已测通的 LoraSource2026 上,只加无人机 D 帧解析,不改他的文件。
2026-07-31 追加:相对起飞点坐标 -> 场地绝对坐标变换(H=112.5,112.5)。
2026-08-02 追加:覆写 _tick_timer 去掉父类 IDLE mock(状态栏一直闪的根因)。
"""
from PyQt5.QtCore import pyqtSlot
from comm.lora_source_2026 import LoraSource2026
from models.drone_state import DroneState


class DroneLoraSource2026(LoraSource2026):

    _DRONE_STATE_MAP = {
        0: DroneState.IDLE,      1: DroneState.TAKEOFF,  2: DroneState.HOVER,
        3: DroneState.SEARCH,    4: DroneState.FOLLOW,   5: DroneState.DROP,
        6: DroneState.DESCEND,   7: DroneState.ONBOARD,  8: DroneState.RETURN,
        9: DroneState.LANDING_H, 10: DroneState.LANDED,  99: DroneState.ERROR,
    }

    # ---- 坐标标定 2026-07-31 ----
    _HOME_X_CM = 112.5
    _HOME_Y_CM = 112.5
    _SIGN_FWD   = +1.0   # 前进(dx)->场地+Y;若"往前推"标记往下,改 -1.0
    _SIGN_RIGHT = -1.0   # 右移->场地+X;若"往右推"标记往左,改 +1.0

    def _parse_line(self, line, now):
        if line.startswith('D,'):
            parts = line.split(',')
            if len(parts) < 5:
                return
            try:
                state_code = int(parts[1])
                dx = float(parts[2])
                dy = float(parts[3])
                alt_cm = float(parts[4])
            except ValueError:
                return
            st = self._DRONE_STATE_MAP.get(state_code, DroneState.ERROR)
            self.drone_state.emit(st)
            field_x = self._HOME_X_CM + self._SIGN_RIGHT * dy
            field_y = self._HOME_Y_CM + self._SIGN_FWD   * dx
            self.drone_pos.emit(field_x, field_y, 0.0, alt_cm)
            return
        return super()._parse_line(line, now)

    @pyqtSlot()
    def _tick_timer(self):
        # 覆写父类:删掉"elapsed<3s 就发 IDLE"那段 mock。
        # 那段在只测无人机(小车没发P帧)时,_start_ts 恒为0 -> elapsed 恒为0
        # -> 永远 <3s -> 每100ms 灌一个"待命",和真 D 帧的真实状态交替刷 -> 状态栏一直闪。
        # 无人机状态现由真实 D 帧(_parse_line)驱动,不再需要 mock。
        import time
        if not self.running:
            return
        elapsed = time.time() - self._start_ts if self._start_ts else 0.0
        self.timer_tick.emit(elapsed)   # UI 计时器照常,只是不再发 IDLE
