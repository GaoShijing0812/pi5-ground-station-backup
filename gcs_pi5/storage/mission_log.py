"""任务日志保存/加载 - JSON 格式"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import config
from models.animal import AnimalType
from models.grid import GridCell
from models.mission import Mission, AnimalSighting, MissionStatus


def _ensure_data_dir():
    Path(config.DATA_DIR).mkdir(parents=True, exist_ok=True)


def mission_to_dict(mission: Mission) -> dict:
    return {
        "forbidden_zones": [[c.a, c.b] for c in mission.forbidden_zones],
        "planned_path": [[c.a, c.b] for c in mission.planned_path],
        "sightings": [
            {
                "cell": [s.cell.a, s.cell.b],
                "animal": int(s.animal),
                "count": s.count,
                "timestamp": s.timestamp.isoformat(),
            }
            for s in mission.sightings
        ],
        "status": mission.status.value,
        "started_at": mission.started_at.isoformat() if mission.started_at else None,
        "finished_at": mission.finished_at.isoformat() if mission.finished_at else None,
    }


def dict_to_mission(data: dict) -> Mission:
    mission = Mission()
    mission.forbidden_zones = [GridCell(*c) for c in data.get("forbidden_zones", [])]
    mission.planned_path = [GridCell(*c) for c in data.get("planned_path", [])]
    for s in data.get("sightings", []):
        cell = GridCell(*s["cell"])
        animal = AnimalType(s["animal"])
        ts = datetime.fromisoformat(s["timestamp"])
        mission.sightings.append(AnimalSighting(cell, animal, s["count"], ts))
    mission.status = MissionStatus(data.get("status", "landed"))
    if data.get("started_at"):
        mission.started_at = datetime.fromisoformat(data["started_at"])
    if data.get("finished_at"):
        mission.finished_at = datetime.fromisoformat(data["finished_at"])
    return mission


def save_mission(mission: Mission) -> str:
    """保存 mission 到 JSON，返回文件绝对路径"""
    _ensure_data_dir()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mission_{ts}.json"
    path = os.path.join(config.DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mission_to_dict(mission), f, ensure_ascii=False, indent=2)
    return path


def list_missions() -> List[str]:
    """列出所有历史任务文件名（按时间倒序）"""
    _ensure_data_dir()
    files = [f for f in os.listdir(config.DATA_DIR)
             if f.startswith("mission_") and f.endswith(".json")]
    files.sort(reverse=True)
    return files


def load_mission(filename: str) -> Optional[Mission]:
    path = os.path.join(config.DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return dict_to_mission(data)
