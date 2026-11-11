#
"""
场地地图组件 —— 按真实比例画 400×500cm 场地 + 跑道轨迹 + A/B/C/D/H，
并把无人机和小车两个对象按 cm 坐标实时定位。

坐标转换：场地物理坐标(cm, 原点左下, Y向上) → 屏幕像素(原点左上, Y向下)。
"""
import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPolygonF

import config_2026 as C


class FieldWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 450)
        # 实时对象状态（场地 cm 坐标）；None = 不显示
        self.drone_xy = None      # (x_cm, y_cm)
        self.drone_yaw = 0.0      # 航向角(度)，用于画机头朝向
        self.car_xy = None        # (x_cm, y_cm)
        self.drone_trail = []     # 无人机轨迹尾迹 [(x,y), ...]
        self._trail_max = 120

    # ---------- 对外更新接口 ----------
    def set_drone(self, x_cm, y_cm, yaw=0.0):
        self.drone_xy = (x_cm, y_cm)
        self.drone_yaw = yaw
        self.drone_trail.append((x_cm, y_cm))
        if len(self.drone_trail) > self._trail_max:
            self.drone_trail.pop(0)
        self.update()

    def set_car(self, x_cm, y_cm):
        self.car_xy = (x_cm, y_cm)
        self.update()

    def clear_trail(self):
        self.drone_trail = []
        self.update()

    # ---------- 坐标转换 ----------
    def _scale_offset(self):
        """等比缩放 + 居中。返回 (scale, ox, oy, draw_w, draw_h)。"""
        margin = 18
        avail_w = self.width() - 2 * margin
        avail_h = self.height() - 2 * margin
        sx = avail_w / C.FIELD_W_CM
        sy = avail_h / C.FIELD_H_CM
        scale = min(sx, sy)
        draw_w = C.FIELD_W_CM * scale
        draw_h = C.FIELD_H_CM * scale
        ox = (self.width() - draw_w) / 2.0
        oy = (self.height() - draw_h) / 2.0
        return scale, ox, oy, draw_w, draw_h

    def cm_to_px(self, x_cm, y_cm):
        """场地(cm, 左下原点, Y上) → 屏幕(px, 左上原点, Y下)。"""
        scale, ox, oy, dw, dh = self._scale_offset()
        px = ox + x_cm * scale
        py = oy + (C.FIELD_H_CM - y_cm) * scale   # Y 翻转
        return QPointF(px, py)

    def cm_len(self, cm):
        scale, *_ = self._scale_offset()
        return cm * scale

    # ---------- 绘制 ----------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.fillRect(self.rect(), QColor(245, 245, 245))
        self._draw_field(p)
        self._draw_track(p)
        self._draw_points(p)
        self._draw_trail(p)
        self._draw_car(p)
        self._draw_drone(p)
        p.end()

    def _draw_field(self, p):
        # 场地边框
        tl = self.cm_to_px(0, C.FIELD_H_CM)
        br = self.cm_to_px(C.FIELD_W_CM, 0)
        rect = QRectF(tl, br)
        p.fillRect(rect, QColor(255, 255, 255))
        p.setPen(QPen(QColor(40, 40, 40), 2))
        p.drawRect(rect)

    def _draw_track(self, p):
        # 采样跑道轨迹连成折线
        p.setPen(QPen(QColor(20, 20, 20), 2))
        poly = QPolygonF()
        for i in range(201):
            x, y = C.track_point(i / 200.0)
            poly.append(self.cm_to_px(x, y))
        p.drawPolyline(poly)

    def _draw_points(self, p):
        f = QFont(); f.setPointSize(10); f.setBold(True); p.setFont(f)
        # A 出发点 40cm 横线（从 A 向左伸，绿）
        ax, ay = C.POINT_A
        p.setPen(QPen(QColor(0, 150, 0), 3))
        p.drawLine(self.cm_to_px(ax - C.A_MARK_LEN_CM, ay),
                   self.cm_to_px(ax, ay))
        # A/B/C/D 蓝点 + 标注
        for name, pt in [("A", C.POINT_A), ("B", C.POINT_B),
                         ("C", C.POINT_C), ("D", C.POINT_D)]:
            c = self.cm_to_px(*pt)
            p.setPen(QPen(QColor(30, 80, 200), 1))
            p.setBrush(QBrush(QColor(30, 80, 200)))
            p.drawEllipse(c, 4, 4)
            p.setPen(QColor(30, 80, 200))
            p.drawText(QPointF(c.x() + 6, c.y() - 6), name)
        # H 点：两个同心圆（甜甜圈，红）
        hc = self.cm_to_px(*C.POINT_H)
        r_out = self.cm_len(C.H_RING_CM / 2)
        r_in = self.cm_len(C.H_INNER_CM / 2)
        p.setPen(QPen(QColor(210, 40, 40), 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(hc, r_out, r_out)
        p.drawEllipse(hc, r_in, r_in)
        p.setPen(QColor(210, 40, 40))
        p.drawText(QPointF(hc.x() + r_out + 2, hc.y() - 2), "H")

    def _draw_trail(self, p):
        if len(self.drone_trail) < 2:
            return
        p.setPen(QPen(QColor(255, 140, 0, 120), 1, Qt.DotLine))
        poly = QPolygonF()
        for (x, y) in self.drone_trail:
            poly.append(self.cm_to_px(x, y))
        p.drawPolyline(poly)

    def _draw_car(self, p):
        if self.car_xy is None:
            return
        c = self.cm_to_px(*self.car_xy)
        # 小车用方块 + 平台同心圆示意
        half = self.cm_len(30)   # 平台约 60cm → 半边 30
        p.setPen(QPen(QColor(120, 80, 20), 2))
        p.setBrush(QBrush(QColor(200, 160, 90, 180)))
        p.drawRect(QRectF(c.x()-half, c.y()-half, 2*half, 2*half))
        # 平台靶标：同心圆(外50/内30) + 十字准星（图2）
        p.setPen(QPen(QColor(60, 40, 10), 1))
        p.setBrush(Qt.NoBrush)
        r_out = self.cm_len(C.PLATFORM_OUTER_CM/2)
        r_in = self.cm_len(C.PLATFORM_INNER_CM/2)
        p.drawEllipse(c, r_out, r_out)
        p.drawEllipse(c, r_in, r_in)
        # 十字准星（贯穿外圈）
        p.drawLine(QPointF(c.x()-r_out, c.y()), QPointF(c.x()+r_out, c.y()))
        p.drawLine(QPointF(c.x(), c.y()-r_out), QPointF(c.x(), c.y()+r_out))
        p.setPen(QColor(90, 60, 10))
        p.drawText(QPointF(c.x()+half+2, c.y()+4), "车")

    def _draw_drone(self, p):
        if self.drone_xy is None:
            return
        c = self.cm_to_px(*self.drone_xy)
        r = self.cm_len(22)   # 轴距≤45cm → 半径约 22
        # 机身圆
        p.setPen(QPen(QColor(200, 30, 30), 2))
        p.setBrush(QBrush(QColor(255, 60, 60, 140)))
        p.drawEllipse(c, r, r)
        # 机头朝向（yaw，0°=+X 向右，逆时针为正）
        ang = math.radians(self.drone_yaw)
        nose = QPointF(c.x() + r*math.cos(-ang), c.y() + r*math.sin(-ang))
        p.setPen(QPen(QColor(150, 0, 0), 2))
        p.drawLine(c, nose)
        p.setPen(QColor(200, 30, 30))
        p.drawText(QPointF(c.x()+r+2, c.y()-2), "机")
