"""任务模型 - 承载禁飞区、航线、动物记录、状态"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from models.animal import AnimalType
from models.grid import GridCell


class MissionStatus(Enum):
    """任务状态机（简化版，够阶段 1 用）"""
    IDLE        = "idle"         # 就绪，等禁飞区输入
    PLANNED     = "planned"      # 已规划航线，未发送
    TRANSMITTED = "transmitted"  # 航线已发给飞控
    FLYING      = "flying"       # 飞机巡查中
    LANDED      = "landed"       # 飞机已降落
    ABORTED     = "aborted"      # 中断（超时/人为终止）


@dataclass
class AnimalSighting:
    """一次动物识别记录"""
    cell: GridCell
    animal: AnimalType
    count: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Mission:
    """一次完整任务的状态容器 - UI 组件共享的数据源"""
    # 输入
    forbidden_zones: list[GridCell] = field(default_factory=list)

    # 规划
    planned_path: list[GridCell] = field(default_factory=list)

    # 运行时
    current_position: Optional[GridCell] = None
    sightings: list[AnimalSighting] = field(default_factory=list)

    # 状态
    status: MissionStatus = MissionStatus.IDLE
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    # ---- 禁飞区 ----
    def toggle_forbidden(self, cell: GridCell) -> bool:
        """切换禁飞区：不在→加上，在→移除。返回操作后是否为禁飞。"""
        if cell in self.forbidden_zones:
            self.forbidden_zones.remove(cell)
            return False
        self.forbidden_zones.append(cell)
        return True

    def is_forbidden(self, cell: GridCell) -> bool:
        return cell in self.forbidden_zones

    # ---- 动物记录 ----
    def add_sighting(self, sighting: AnimalSighting) -> None:
        self.sightings.append(sighting)

    def summary(self) -> dict[AnimalType, int]:
        """按种类汇总动物数量（用于 UI 底部汇总面板）"""
        result: dict[AnimalType, int] = {}
        for s in self.sightings:
            result[s.animal] = result.get(s.animal, 0) + s.count
        return result
