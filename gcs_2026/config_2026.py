# -*- coding: utf-8 -*-
"""
gcs_2026 全局配置 —— 2026 电赛 D 题《陆空协同无人机系统》地面站

坐标系约定（重要）
------------------
- 采用「场地物理坐标系」，单位 cm。
- 原点 (0,0) = 场地【左下角】。X 轴向右（0~400），Y 轴向上（0~500）。
- 这样定义是为了跟无人机飞控/雷达的物理坐标好对齐（接真实数据时只需一次平移/缩放标定）。
- 屏幕绘制时 Y 轴要翻转（屏幕 y 向下），翻转逻辑放在地图组件里，config 只管物理量。

 几何数字说明
--------------
下面跑道轨迹的具体数字是【从赛题附图渲染读出的近似值】，
拿到赛区打印附图后必须实测校准。改这里的常量，整张地图会自动重绘，
不用动其它代码。拓扑（跑道形闭环 + A/B/C/D 顺序 + H 在环外左下）是确定的。
"""

import math

# ============ 场地边框 ============
FIELD_W_CM = 400.0   # 场地宽 (X)
FIELD_H_CM = 500.0   # 场地高 (Y)
LINE_W_CM  = 2.0     # 黑线/边框线宽 (2cm ± 0.2)

# ============ 跑道形循线轨迹（stadium：竖向 —— 左右直线 + 上下半圆）============
# 真实地图是【竖着的】跑道：两条竖直线在左右两侧，两个半圆在上下。
# 用「上下半圆的圆心 Y + 左右直线的 X + 半径」参数化整条跑道。
# 以下均为照附图比例目测的近似值，拿到卷尺实测后校准这几个数即可，整图自动重绘。
# 以下数字来自赛题图1实测标注（2026 官方尺寸），非目测。
TRACK_R_CM      = 75.0            # 半圆半径（图1标注 75cm，上下半圆共用）
LEFT_CX_CM      = 150.0          # 左竖直线的 X（图1：左竖线距左框 150cm）
RIGHT_CX_CM     = 300.0         # 右竖直线的 X（LEFT + 2R = 300）
TOP_CY_CM       = 350.0         # 上半圆圆心 Y = B/C 的 Y（竖线长 150cm → 200+150）
BOT_CY_CM       = 200.0         # 下半圆圆心 Y = A/D 的 Y（下半圆底距下框 125cm → 125+75）

# 由上面几个量派生（顺时针顶点 A/B/C/D）
# A=左下(出发/终点)  B=左上  C=右上  D=右下
POINT_A = (LEFT_CX_CM,  BOT_CY_CM)
POINT_B = (LEFT_CX_CM,  TOP_CY_CM)
POINT_C = (RIGHT_CX_CM, TOP_CY_CM)
POINT_D = (RIGHT_CX_CM, BOT_CY_CM)

# A 点出发标识：一根 40cm 黑色横线（画在 A 点前）
A_MARK_LEN_CM = 40.0

# ============ H 点：无人机起降点（环外左下角，两个同心圆）============
# 图1实测：外圈直径75，左/下边缘各距框75 → 圆心=(75+37.5, 75+37.5)=(112.5,112.5)
POINT_H     = (112.5, 112.5)
H_RING_CM   = 75.0    # H 点外圈直径（图1标注 75cm）
H_INNER_CM  = 50.0    # H 点内圈直径（图1标注 50cm）

# ============ 小车平台靶标（图2：同心圆 外50/内30 + 十字）============
PLATFORM_OUTER_CM = 50.0
PLATFORM_INNER_CM = 30.0
PLATFORM_MAX_CM   = 60.0   # 平台边长上限 60×60

# ============ 任务参数 ============
TASK_TIME_LIMIT_S = 90.0   # 两个任务小车全程都 ≤90s（计时器上限）
CRUISE_ALT_CM     = 150.0  # 巡航/初始悬停高度 150±10cm
ALT_TOL_CM        = 10.0

# ============ UI 尺寸 ============
WINDOW_WIDTH  = 1024   # 贴合轮趣 7 寸屏
WINDOW_HEIGHT = 600


def track_point(t):
    """
    竖向跑道参数化：t ∈ [0,1]，返回轨迹上一点的场地坐标 (x_cm, y_cm)。
    行进方向 A(t=0) → B → C → D → A(t=1)，顺时针。
    段序：① A→B 左竖线(上行)  ② B→C 上半圆(经顶)  ③ C→D 右竖线(下行)  ④ D→A 下半圆(经底)
    """
    t = t % 1.0
    straight = TOP_CY_CM - BOT_CY_CM      # 竖直线段长
    arc = math.pi * TRACK_R_CM            # 半圆弧长
    total = 2 * straight + 2 * arc
    d = t * total

    # ① A→B：左竖直线，向上
    if d <= straight:
        return (LEFT_CX_CM, BOT_CY_CM + d)
    d -= straight
    # ② B→C：上半圆，圆心 (中点X, TOP_CY)，从左(180°)经顶(90°)到右(0°)
    if d <= arc:
        ang = math.pi - (d / TRACK_R_CM)         # 180° → 90° → 0°
        x = (LEFT_CX_CM + RIGHT_CX_CM) / 2 + TRACK_R_CM * math.cos(ang)
        y = TOP_CY_CM + TRACK_R_CM * math.sin(ang)
        return (x, y)
    d -= arc
    # ③ C→D：右竖直线，向下
    if d <= straight:
        return (RIGHT_CX_CM, TOP_CY_CM - d)
    d -= straight
    # ④ D→A：下半圆，圆心 (中点X, BOT_CY)，从右(0°)经底(-90°)到左(-180°)
    ang = -(d / TRACK_R_CM)                       # 0° → -90° → -180°
    x = (LEFT_CX_CM + RIGHT_CX_CM) / 2 + TRACK_R_CM * math.cos(ang)
    y = BOT_CY_CM + TRACK_R_CM * math.sin(ang)
    return (x, y)
