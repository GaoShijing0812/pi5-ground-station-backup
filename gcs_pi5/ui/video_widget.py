"""RTSP 视频显示 widget (阶段 3 图传练手, 2026-07-24)

用 python-vlc 拉 rtsp 流,嵌入 Qt widget。
默认不自动播,点▶按钮才开始拉流(避免 UI 打开就阻塞)。

跨平台渲染:
- Linux X11: set_xwindow
- macOS:     set_nsobject
- Windows:   set_hwnd

比赛现场换 IP:改 config.RTSP_URL 一处即可,本文件不用动。
"""
import sys

import vlc
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame,
)


class VideoWidget(QWidget):
    """图传 Tab 里的视频区。点▶开始拉流,点■停止。"""

    def __init__(self, rtsp_url: str, parent=None):
        super().__init__(parent)
        self.rtsp_url = rtsp_url
        self._vlc_instance = None
        self._player = None

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(4, 4, 4, 4)
        vlayout.setSpacing(4)

        # ---- 顶部工具条 ----
        top_bar = QHBoxLayout()
        self.url_label = QLabel(f"📡 {rtsp_url}")
        self.url_label.setStyleSheet("color: #666; font-size: 12px;")
        top_bar.addWidget(self.url_label)
        top_bar.addStretch()

        self.play_btn = QPushButton("▶ 连接图传")
        self.play_btn.setStyleSheet(
            "padding: 6px 12px; background: #4caf50; color: white; font-size: 13px;"
        )
        self.play_btn.clicked.connect(self.play)
        top_bar.addWidget(self.play_btn)

        self.stop_btn = QPushButton("■ 停止图传")
        self.stop_btn.setStyleSheet(
            "padding: 6px 12px; background: #f44336; color: white; font-size: 13px;"
        )
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        top_bar.addWidget(self.stop_btn)

        vlayout.addLayout(top_bar)

        # ---- 视频渲染区(黑底) ----
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background: #111;")
        self.video_frame.setMinimumHeight(300)
        vlayout.addWidget(self.video_frame, stretch=1)

        # ---- 状态栏 ----
        self.status_label = QLabel("就绪。点 ▶ 连接图传 开始拉流。")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        vlayout.addWidget(self.status_label)

    def play(self):
        """开始拉 RTSP 流,渲染到 video_frame"""
        if self._player is None:
            self._vlc_instance = vlc.Instance('--quiet')
            self._player = self._vlc_instance.media_player_new()

        media = self._vlc_instance.media_new(self.rtsp_url)
        media.add_option(':network-caching=500')
        self._player.set_media(media)

        wid = int(self.video_frame.winId())
        if sys.platform.startswith('linux'):
            self._player.set_xwindow(wid)
        elif sys.platform == 'darwin':
            self._player.set_nsobject(wid)
        elif sys.platform == 'win32':
            self._player.set_hwnd(wid)

        result = self._player.play()
        if result == 0:
            self.status_label.setText(f"连接中: {self.rtsp_url}")
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        else:
            self.status_label.setText(f"[错误] libvlc play() 返回 {result}")

    def stop(self):
        """停止拉流(不销毁 player,下次 play 复用)"""
        if self._player is not None:
            self._player.stop()
        self.status_label.setText("已停止")
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def closeEvent(self, event):
        """窗口关闭时确保 stop,不然子进程会残留"""
        self.stop()
        super().closeEvent(event)
