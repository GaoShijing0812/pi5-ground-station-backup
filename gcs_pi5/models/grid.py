"""9×7 网格模型 - 2025 H 题坐标系统"""
from dataclasses import dataclass
from typing import Optional
import re
import config


@dataclass(frozen=True)
class GridCell:
    """一个方格，用 A/B 坐标标识。
    - a: 1..9 (横向 A1..A9)
    - b: 1..7 (纵向 B1..B7)
    frozen=True → 不可变 → 可作 dict key / set 元素
    """
    a: int
    b: int

    def __post_init__(self):
        if not self.is_valid():
            raise ValueError(f"Invalid cell: A{self.a}B{self.b}")

    def is_valid(self) -> bool:
        """是否在 9×7 场地内"""
        return 1 <= self.a <= config.GRID_COLS and 1 <= self.b <= config.GRID_ROWS

    def code(self) -> str:
        """返回代码字符串，如 'A3B5'"""
        return f"A{self.a}B{self.b}"

    def to_flight_cm(self) -> tuple[int, int]:
        """转成飞控坐标（cm），依据 drone-setup memory 第七节：
             x = (B-1) * 50    # x 方向 = B 方向
             y = (9-A) * 50    # y 方向 = A 方向反向
           返回 (x_cm, y_cm)
        """
        x_cm = (self.b - 1) * config.GRID_CM
        y_cm = (config.GRID_COLS - self.a) * config.GRID_CM
        return (x_cm, y_cm)


# ---- 解析工具 ----
_CELL_RE = re.compile(r'^A(\d+)B(\d+)$', re.IGNORECASE)


def parse_cell(code: str) -> Optional[GridCell]:
    """从字符串解析 GridCell，如 'A3B5' → GridCell(3, 5)。失败返回 None。"""
    m = _CELL_RE.match(code.strip())
    if not m:
        return None
    try:
        return GridCell(int(m.group(1)), int(m.group(2)))
    except ValueError:
        return None
