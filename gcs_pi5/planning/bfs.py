"""路径规划 - 翻译自 2025 队友2 bfs.c

算法：贪心 + BFS 逃脱
  - 从 A9B1 出发
  - 每步优先按 [下、左、上、右] 顺序走相邻未覆盖格
  - 走不通时 BFS 找最近未覆盖格（沿途所有格标记为已覆盖）
  - 覆盖完毕后 BFS 回 A9B1

对应 bfs.c 的 move_x[]={0,-1,0,1}, move_y[]={-1,0,1,0}
   在 (A, B) 坐标系下 = (dA, dB): [(0,-1), (-1,0), (0,1), (1,0)]
"""
from collections import deque
from typing import List, Optional

import config
from models.grid import GridCell


# 方向优先级：下 (B-1)、左 (A-1)、上 (B+1)、右 (A+1)
MOVES = [(0, -1), (-1, 0), (0, 1), (1, 0)]


def _in_bounds(a: int, b: int) -> bool:
    return 1 <= a <= config.GRID_COLS and 1 <= b <= config.GRID_ROWS


def _bfs_shortest(start: GridCell, goal: GridCell,
                  obstacles: set) -> Optional[List[GridCell]]:
    """BFS 找 start -> goal 最短路径。返回不含 start、含 goal。"""
    if start == goal:
        return []
    queue = deque([start])
    parent = {start: None}
    while queue:
        cur = queue.popleft()
        if cur == goal:
            break
        for da, db in MOVES:
            na, nb = cur.a + da, cur.b + db
            if not _in_bounds(na, nb):
                continue
            nxt = GridCell(na, nb)
            if nxt in obstacles or nxt in parent:
                continue
            parent[nxt] = cur
            queue.append(nxt)
    if goal not in parent:
        return None
    path = []
    node = goal
    while node != start:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def _bfs_nearest_uncovered(start: GridCell, uncovered: set,
                           obstacles: set) -> Optional[List[GridCell]]:
    """BFS 找最近的 uncovered 格，返回 start 到那格的路径（不含 start）。"""
    queue = deque([start])
    parent = {start: None}
    target = None
    while queue:
        cur = queue.popleft()
        if cur in uncovered:
            target = cur
            break
        for da, db in MOVES:
            na, nb = cur.a + da, cur.b + db
            if not _in_bounds(na, nb):
                continue
            nxt = GridCell(na, nb)
            if nxt in obstacles or nxt in parent:
                continue
            parent[nxt] = cur
            queue.append(nxt)
    if target is None:
        return None
    path = []
    node = target
    while node != start:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def plan_bfs_path(forbidden: List[GridCell]) -> List[GridCell]:
    """贪心 + BFS 逃脱 + 返程回家"""
    obstacles = set(forbidden)
    home = GridCell(config.HOME_A, config.HOME_B)

    # HOME 是禁飞（异常）→ 返回空
    if home in obstacles:
        return []

    # 收集所有需要覆盖的格
    uncovered = set()
    for a in range(1, config.GRID_COLS + 1):
        for b in range(1, config.GRID_ROWS + 1):
            cell = GridCell(a, b)
            if cell not in obstacles:
                uncovered.add(cell)

    # 起点标记为已覆盖
    uncovered.discard(home)
    path: List[GridCell] = [home]
    current = home

    # 主循环：贪心 + BFS 逃脱
    while uncovered:
        # 1) 贪心：按方向优先级找相邻未覆盖格
        moved = False
        for da, db in MOVES:
            na, nb = current.a + da, current.b + db
            if not _in_bounds(na, nb):
                continue
            nxt = GridCell(na, nb)
            if nxt in uncovered:
                current = nxt
                path.append(current)
                uncovered.discard(current)
                moved = True
                break

        if moved:
            continue

        # 2) 贪心走不通：BFS 逃脱到最近未覆盖格
        escape = _bfs_nearest_uncovered(current, uncovered, obstacles)
        if escape is None:
            break  # 无未覆盖可到达（不应发生）
        for cell in escape:
            current = cell
            path.append(current)
            uncovered.discard(current)

    # 返程：BFS 回 HOME
    if current != home:
        back = _bfs_shortest(current, home, obstacles)
        if back:
            path.extend(back)

    return path
