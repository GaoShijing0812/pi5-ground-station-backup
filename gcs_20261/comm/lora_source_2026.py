# -*- coding: utf-8 -*-
"""
LoraSource2026 —— 真实 LoRa 数据源（替换 MockSource2026）。

从 Pi5 串口接收小车发来的位置帧，解析后 emit 对应信号。
无人机坐标目前留空（待接入飞控遥测后再补）。

帧格式（小车 → 地面站，200ms 一包）：
    P,task,dist_cm,x_cm,y_cm\r\n
例: P,1,385.2,225.0,350.0\r\n
"""
from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtSerialPort import QSerialPort

import config_2026 as C
from comm.source_interface_2026 import MissionSource2026
from models.drone_state import DroneState


class LoraSource2026(MissionSource2026):
    def __init__(self, port_name='/dev/ttyAMA8', parent=None):
        super().__init__(parent)
        self.port_name = port_name
        self.baudrate = C.LORA_BAUDRATE
        self.running = False
        self._task = 1                # 当前任务 1/2
        self._start_ts = 0.0          # wall-clock start time (秒)
        self._car_prog = 0.0          # 小车进度 0~1
        self._rx_buf = bytearray()

        # 串口
        self._serial = QSerialPort(self)
        self._serial.setPortName(self.port_name)
        self._serial.setBaudRate(self.baudrate)
        self._serial.setDataBits(QSerialPort.Data8)
        self._serial.setParity(QSerialPort.NoParity)
        self._serial.setStopBits(QSerialPort.OneStop)
        self._serial.setFlowControl(QSerialPort.NoFlowControl)
        self._serial.readyRead.connect(self._on_ready_read)

        # 100ms 计时器 tick
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._tick_timer)

    # ---- MissionSource2026 接口 ----
    def start(self):
        if not self._serial.isOpen():
            if not self._serial.open(QSerialPort.ReadWrite):
                err = self._serial.errorString()
                self.log_message.emit(f"[LoRa] 串口打开失败: {err}")
                return
            self.log_message.emit(
                f"[LoRa] 串口已开: {self.port_name} @ {self.baudrate}"
            )

        self._rx_buf.clear()
        self._car_prog = 0.0
        self.running = True
        self._start_ts = 0.0  # 第一帧到达时才校准

        self._timer.start()
        self.mission_started.emit()
        self.log_message.emit("LoRa 接收就绪，等待小车发车...")

    def set_task(self, n):
        self._task = 2 if int(n) == 2 else 1
        self.log_message.emit(f"已切到任务{self._task}")

    def stop(self):
        self.running = False
        self._timer.stop()
        self._car_prog = 0.0
        self.log_message.emit("任务停止")
        self.mission_finished.emit()

    # ---- 计时器 ----
    @pyqtSlot()
    def _tick_timer(self):
        """100ms tick，用于 UI 计时器 + 无人机状态 mock"""
        import time
        if not self.running:
            return
        elapsed = time.time() - self._start_ts if self._start_ts else 0.0
        self.timer_tick.emit(elapsed)

        # 无人机状态 mock（待接飞控数据后替换）
        if elapsed < 3.0:
            self.drone_state.emit(DroneState.IDLE)

    # ---- 串口接收 ----
    @pyqtSlot()
    def _on_ready_read(self):
        import time
        data = bytes(self._serial.readAll())
        if not data:
            return
        self._rx_buf.extend(data)

        while True:
            idx = self._rx_buf.find(b'\n')
            if idx < 0:
                break
            line = bytes(self._rx_buf[:idx]).decode('ascii', errors='ignore').strip()
            del self._rx_buf[:idx + 1]
            self._parse_line(line, time.time())

    def _parse_line(self, line: str, now: float):
        """解析 "P,task,dist,x,y" 或 "P,task,dist,x,y\\r" """
        if not line.startswith('P,'):
            self.log_message.emit(f"[DEBUG] 非P帧: {line[:40]}")
            return
        parts = line.split(',')
        if len(parts) < 5:
            self.log_message.emit(f"[DEBUG] P帧字段不足: {line}")
            return
        try:
            task   = int(parts[1])       # 1 or 2
            dist   = float(parts[2])     # cm
            x_cm   = float(parts[3])
            y_cm   = float(parts[4])
        except ValueError:
            return

        # 第一帧到达时校准计时器起点
        if self._start_ts == 0.0:
            self._start_ts = now
            self.log_message.emit(f"收到首帧: 任务{task} {dist:.0f}cm ({x_cm:.0f},{y_cm:.0f})")

        self._car_prog = min(dist / C.FIELD_H_CM, 1.0)  # rough, real prog from track total
        self._car_prog = min(dist / 771.0, 1.0)          # track perimeter ~771cm

        self.car_pos.emit(x_cm, y_cm, self._car_prog)
