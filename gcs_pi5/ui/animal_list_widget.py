"""动物识别结果实时列表"""
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtGui import QFont

from models.animal import name_of
from models.mission import Mission, AnimalSighting


class AnimalListWidget(QListWidget):
    """
    滚动列表，每行：HH:MM:SS   A3B5   老虎   x1
    """

    def __init__(self, mission: Mission, parent=None):
        super().__init__(parent)
        self.mission = mission
        self.setFont(QFont("", 11))
        self.setStyleSheet(
            "QListWidget { background: #fafafa; border: 1px solid #ccc; }"
            "QListWidget::item { padding: 6px 8px; border-bottom: 1px solid #eee; }"
        )

    def add_sighting(self, sighting: AnimalSighting):
        ts = sighting.timestamp.strftime("%H:%M:%S")
        text = f"{ts}   {sighting.cell.code()}   {name_of(sighting.animal)}   x{sighting.count}"
        self.addItem(QListWidgetItem(text))
        self.scrollToBottom()

    def clear_all(self):
        self.clear()

    def rebuild_from_mission(self):
        self.clear()
        for s in self.mission.sightings:
            self.add_sighting(s)
