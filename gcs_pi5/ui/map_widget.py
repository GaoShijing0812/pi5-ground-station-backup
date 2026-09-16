"""9x7 网格地图组件 - Step 8c: 加飞机位置绘制"""
from typing import Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt5.QtCore import Qt, QPoint, pyqtSignal

import config
from models.grid import GridCell
from models.mission import Mission


class MapWidget(QWidget):
    forbidden_changed = pyqtSignal()

    COLOR_NORMAL     = QColor("#ffffff")
    COLOR_FORBIDDEN  = QColor("#b4b4b4")
    COLOR_HOME       = QColor("#ff6b6b")
    COLOR_BORDER     = QColor("#888888")
    COLOR_TEXT       = QColor("#333333")
    COLOR_LABEL      = QColor("#000000")
    COLOR_PATH       = QColor("#2196f3")
    COLOR_START_MARK = QColor("#4caf50")
    COLOR_DRONE      = QColor("#ff5722")   # 飞机 橙红

    MARGIN = 40

    def __init__(self, mission: Mission, parent=None):
        super().__init__(parent)
        self.mission = mission
        self.setMinimumSize(600, 400)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cell_w = (w - 2 * self.MARGIN) // config.GRID_COLS
        cell_h = (h - 2 * self.MARGIN) // config.GRID_ROWS

        for a in range(1, config.GRID_COLS + 1):
            for b in range(1, config.GRID_ROWS + 1):
                x = self.MARGIN + (a - 1) * cell_w
                y = self.MARGIN + (config.GRID_ROWS - b) * cell_h

                cell = GridCell(a, b)
                if a == config.HOME_A and b == config.HOME_B:
                    color = self.COLOR_HOME
                elif self.mission.is_forbidden(cell):
                    color = self.COLOR_FORBIDDEN
                else:
                    color = self.COLOR_NORMAL

                painter.fillRect(x, y, cell_w, cell_h, color)
                painter.setPen(QPen(self.COLOR_BORDER, 1))
                painter.drawRect(x, y, cell_w, cell_h)

                painter.setPen(self.COLOR_TEXT)
                painter.drawText(x, y, cell_w, cell_h, Qt.AlignCenter, cell.code())

        self._draw_path(painter, cell_w, cell_h)
        self._draw_drone(painter, cell_w, cell_h)

        painter.setPen(self.COLOR_LABEL)
        painter.setFont(QFont("", 12, QFont.Bold))
        for a in range(1, config.GRID_COLS + 1):
            x = self.MARGIN + (a - 1) * cell_w
            y = self.MARGIN + config.GRID_ROWS * cell_h
            painter.drawText(x, y, cell_w, 30, Qt.AlignCenter, f"A{a}")
        for b in range(1, config.GRID_ROWS + 1):
            x = 0
            y = self.MARGIN + (config.GRID_ROWS - b) * cell_h
            painter.drawText(x, y, self.MARGIN - 5, cell_h, Qt.AlignCenter, f"B{b}")

    def _draw_path(self, painter, cell_w, cell_h):
        path = self.mission.planned_path
        if len(path) < 2:
            return

        def cell_center(cell):
            x = self.MARGIN + (cell.a - 1) * cell_w + cell_w // 2
            y = self.MARGIN + (config.GRID_ROWS - cell.b) * cell_h + cell_h // 2
            return QPoint(x, y)

        points = [cell_center(c) for c in path]

        painter.setPen(QPen(self.COLOR_PATH, 3))
        painter.setBrush(Qt.NoBrush)
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        start = points[0]
        painter.setBrush(QBrush(self.COLOR_START_MARK))
        painter.setPen(QPen(self.COLOR_START_MARK, 2))
        painter.drawEllipse(start.x() - 10, start.y() - 10, 20, 20)

    def _draw_drone(self, painter, cell_w, cell_h):
        """画飞机当前位置（红色圆 + 白色十字）"""
        if not self.mission.current_position:
            return
        cur = self.mission.current_position
        x = self.MARGIN + (cur.a - 1) * cell_w + cell_w // 2
        y = self.MARGIN + (config.GRID_ROWS - cur.b) * cell_h + cell_h // 2
        painter.setBrush(QBrush(self.COLOR_DRONE))
        painter.setPen(QPen(QColor("#d32f2f"), 2))
        painter.drawEllipse(x - 12, y - 12, 24, 24)
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.drawLine(x - 6, y, x + 6, y)
        painter.drawLine(x, y - 6, x, y + 6)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        cell = self._point_to_cell(event.pos().x(), event.pos().y())
        if cell is None:
            return
        if cell.a == config.HOME_A and cell.b == config.HOME_B:
            return
        self.mission.toggle_forbidden(cell)
        self.forbidden_changed.emit()
        self.update()

    def _point_to_cell(self, x, y):
        w = self.width()
        h = self.height()
        cell_w = (w - 2 * self.MARGIN) // config.GRID_COLS
        cell_h = (h - 2 * self.MARGIN) // config.GRID_ROWS
        if x < self.MARGIN or x >= self.MARGIN + config.GRID_COLS * cell_w:
            return None
        if y < self.MARGIN or y >= self.MARGIN + config.GRID_ROWS * cell_h:
            return None
        a = (x - self.MARGIN) // cell_w + 1
        b = config.GRID_ROWS - (y - self.MARGIN) // cell_h
        try:
            return GridCell(a, b)
        except ValueError:
            return None
