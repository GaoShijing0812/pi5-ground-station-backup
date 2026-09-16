#!/usr/bin/env python3
"""Pi5 地面站 - 环境验证 Hello World"""
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton,
    QVBoxLayout, QWidget,
)
from PyQt5.QtCore import Qt

class HelloWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pi5 地面站 - 环境验证")
        self.resize(800, 480)  # 7 寸屏典型分辨率

        w = QWidget()
        layout = QVBoxLayout(w)

        label = QLabel("Hello, Pi5 地面站!\n\n看到这个窗口 = PyQt5 环境 OK")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 24px;")

        btn = QPushButton("点我测试触摸/鼠标")
        btn.setStyleSheet("font-size: 18px; padding: 12px;")
        btn.clicked.connect(
            lambda: label.setText("✓ 交互正常\n\n可以进入 Step 4")
        )

        layout.addWidget(label)
        layout.addWidget(btn)
        self.setCentralWidget(w)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = HelloWindow()
    win.show()
    sys.exit(app.exec_())
