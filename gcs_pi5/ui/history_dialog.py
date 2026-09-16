"""历史任务对话框"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
    QDialogButtonBox, QLabel
)
from PyQt5.QtCore import Qt

from storage.mission_log import list_missions, load_mission


class HistoryDialog(QDialog):
    """列出历史任务，双击/OK 加载到主窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("历史任务记录")
        self.resize(500, 400)
        self.selected_mission = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("选择一个历史任务查看："))

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_accept)

        files = list_missions()
        if not files:
            empty = QListWidgetItem("(暂无历史记录)")
            empty.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(empty)
        else:
            for f in files:
                try:
                    stem = f.replace("mission_", "").replace(".json", "")
                    d, t = stem.split("_")
                    display = f"{d[:4]}-{d[4:6]}-{d[6:8]} {t[:2]}:{t[2:4]}:{t[4:6]}   ({f})"
                except Exception:
                    display = f
                item = QListWidgetItem(display)
                item.setData(Qt.UserRole, f)
                self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def on_accept(self):
        item = self.list_widget.currentItem()
        if item is None:
            self.reject()
            return
        filename = item.data(Qt.UserRole)
        if not filename:
            self.reject()
            return
        self.selected_mission = load_mission(filename)
        if self.selected_mission is None:
            self.reject()
            return
        self.accept()
