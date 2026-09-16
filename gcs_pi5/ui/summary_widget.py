"""每种动物总数汇总面板"""
from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from models.animal import AnimalType, ANIMAL_NAMES_CN
from models.mission import Mission


class SummaryWidget(QFrame):
    """
    汇总面板 - 5 种动物 + 总数。
    题目要求 4：巡查完成后显示所发现动物的名称及每种动物数量。
    """

    def __init__(self, mission: Mission, parent=None):
        super().__init__(parent)
        self.mission = mission
        self.setFrameShape(QFrame.Box)
        self.setStyleSheet(
            "QFrame { background: #fff; border: 1px solid #ccc; }"
            "QLabel { padding: 4px; }"
        )

        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("识别汇总")
        title.setFont(QFont("", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, 2)

        self.count_labels = {}
        row = 1
        for animal in AnimalType:
            name_lbl = QLabel(ANIMAL_NAMES_CN[animal])
            name_lbl.setFont(QFont("", 13))
            layout.addWidget(name_lbl, row, 0)

            count_lbl = QLabel("0")
            count_lbl.setFont(QFont("", 16, QFont.Bold))
            count_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            count_lbl.setStyleSheet("color: #2196f3;")
            layout.addWidget(count_lbl, row, 1)

            self.count_labels[animal] = count_lbl
            row += 1

        total_name = QLabel("总数")
        total_name.setFont(QFont("", 13, QFont.Bold))
        layout.addWidget(total_name, row, 0)

        self.total_label = QLabel("0")
        self.total_label.setFont(QFont("", 16, QFont.Bold))
        self.total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.total_label.setStyleSheet("color: #f44336;")
        layout.addWidget(self.total_label, row, 1)

    def refresh(self):
        summary = self.mission.summary()
        total = 0
        for animal, lbl in self.count_labels.items():
            count = summary.get(animal, 0)
            lbl.setText(str(count))
            total += count
        self.total_label.setText(str(total))
