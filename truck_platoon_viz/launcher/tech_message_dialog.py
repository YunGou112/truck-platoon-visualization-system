"""与主界面一致的深色科技风消息框（替代系统 QMessageBox）。"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

_PANEL_QSS = """
QFrame#TechDialogPanel {
    background-color: #0f1c2e;
    border: 1px solid rgba(0, 198, 255, 0.45);
    border-radius: 10px;
}
QLabel#TechDialogTitle {
    color: #00d4ff;
    font-size: 16px;
    font-weight: bold;
}
QLabel#TechDialogBody {
    color: #e6f7ff;
    font-size: 14px;
    line-height: 1.45;
}
QPushButton#TechDialogOk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #00c6ff, stop:1 #0072ff
    );
    border: 1px solid rgba(0, 255, 255, 0.55);
    border-radius: 8px;
    color: #ffffff;
    padding: 8px 28px;
    font-size: 14px;
    font-weight: bold;
    min-width: 100px;
    min-height: 34px;
}
QPushButton#TechDialogOk:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #33d4ff, stop:1 #2980ff
    );
    border: 1px solid rgba(0, 255, 220, 0.95);
}
QPushButton#TechDialogOk:pressed {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #0099cc, stop:1 #0058cc
    );
}
"""


class _DialogTitleBar(QWidget):
    """无边框对话框标题栏：可拖动窗口，子控件（关闭按钮）仍单独响应点击。"""

    def __init__(self, dialog):
        super().__init__()
        self._dlg = dialog
        self._anchor = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._anchor = event.globalPos() - self._dlg.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._anchor is not None and event.buttons() & Qt.LeftButton:
            self._dlg.move(event.globalPos() - self._anchor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._anchor = None
        super().mouseReleaseEvent(event)


class TechMessageDialog(QDialog):
    def __init__(self, parent, title, message, *, error=False):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(True)

        panel = QFrame()
        shadow = QGraphicsDropShadowEffect(panel)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 80, 120, 120))
        shadow.setOffset(0, 6)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)

        panel.setObjectName("TechDialogPanel")
        panel.setGraphicsEffect(shadow)
        panel.setStyleSheet(_PANEL_QSS)
        outer.addWidget(panel)

        inner = QVBoxLayout(panel)
        inner.setContentsMargins(22, 18, 22, 18)
        inner.setSpacing(14)

        title_bar = _DialogTitleBar(self)
        head = QHBoxLayout(title_bar)
        head.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("TechDialogTitle")
        if error:
            title_lbl.setStyleSheet(
                "color: #ff8a80; font-size: 16px; font-weight: bold;"
            )
        head.addWidget(title_lbl)
        head.addStretch()
        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(0,198,255,0.25);
                border-radius: 6px;
                color: #9ec4d6;
                font-size: 18px;
            }
            QPushButton:hover {
                background: rgba(255,80,80,0.25);
                border: 1px solid rgba(255,120,120,0.5);
                color: #ffcccc;
            }
        """)
        close_btn.clicked.connect(self.reject)
        head.addWidget(close_btn)
        inner.addWidget(title_bar)

        accent = QFrame()
        accent.setFixedHeight(2)
        accent.setStyleSheet(
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 transparent, stop:0.35 rgba(0,198,255,0.85), stop:1 transparent);"
            "border: none; border-radius: 1px;"
        )
        inner.addWidget(accent)

        body = QLabel(message)
        body.setObjectName("TechDialogBody")
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        inner.addWidget(body)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok = QPushButton("确定")
        ok.setObjectName("TechDialogOk")
        ok.setDefault(True)
        ok.setCursor(Qt.PointingHandCursor)
        ok.clicked.connect(self.accept)
        btn_row.addWidget(ok)
        btn_row.addStretch()
        inner.addLayout(btn_row)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter):
            self.accept()
            return
        super().keyPressEvent(event)


def tech_information(parent, title, message):
    dlg = TechMessageDialog(parent, title, message, error=False)
    dlg.exec_()


def tech_critical(parent, title, message):
    dlg = TechMessageDialog(parent, title, message, error=True)
    dlg.exec_()
