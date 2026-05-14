"""与主界面一致的深色科技风消息框（替代系统 QMessageBox）。"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

_PANEL_QSS = """
QFrame#TechDialogPanel {
    background-color: #0d1420;
    border: 1px solid rgba(103, 120, 146, 0.52);
    border-radius: 12px;
}
QFrame#TechDialogBadge {
    background: rgba(26, 34, 49, 0.95);
    border: 1px solid rgba(161, 177, 205, 0.42);
    border-radius: 24px;
}
QLabel#TechDialogTitle {
    color: #edf2fb;
    font-size: 17px;
    font-weight: 700;
}
QLabel#TechDialogSubTitle {
    color: #94a5bc;
    font-size: 12px;
}
QLabel#TechDialogBody {
    color: #d7e0ee;
    font-size: 14px;
    line-height: 1.45;
}
QPushButton#TechDialogOk {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #b49053, stop:0.1 #d1b172, stop:0.55 #658de1, stop:1 #4267a9
    );
    border: 1px solid rgba(209, 223, 248, 0.48);
    border-radius: 8px;
    color: #ffffff;
    padding: 8px 28px;
    font-size: 14px;
    font-weight: 600;
    min-width: 100px;
    min-height: 34px;
}
QPushButton#TechDialogOk:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #c6a362, stop:0.1 #e0c17f, stop:0.55 #77a0f2, stop:1 #537bc0
    );
    border: 1px solid rgba(236, 242, 255, 0.82);
}
QPushButton#TechDialogOk:pressed {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #a48248, stop:0.1 #b99b62, stop:0.55 #4d76c5, stop:1 #3b5c95
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
        inner.setSpacing(16)

        title_bar = _DialogTitleBar(self)
        head = QHBoxLayout(title_bar)
        head.setContentsMargins(0, 0, 0, 0)
        title_wrap = QVBoxLayout()
        title_wrap.setContentsMargins(0, 0, 0, 0)
        title_wrap.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("TechDialogTitle")
        if error:
            title_lbl.setStyleSheet(
                "color: #ffd6d1; font-size: 17px; font-weight: 700;"
            )
        title_wrap.addWidget(title_lbl)
        sub_lbl = QLabel("启动状态")
        sub_lbl.setObjectName("TechDialogSubTitle")
        title_wrap.addWidget(sub_lbl)
        head.addLayout(title_wrap)
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
            "stop:0 transparent, stop:0.25 rgba(180,144,83,0.85), stop:0.65 rgba(108,140,210,0.85), stop:1 transparent);"
            "border: none; border-radius: 1px;"
        )
        inner.addWidget(accent)

        content_row = QHBoxLayout()
        content_row.setSpacing(14)

        badge = QFrame()
        badge.setObjectName("TechDialogBadge")
        badge.setFixedSize(48, 48)
        badge_layout = QVBoxLayout(badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_icon = QLabel("!")
        badge_icon.setAlignment(Qt.AlignCenter)
        badge_icon.setStyleSheet(
            "color: %s; font-size: 22px; font-weight: 700; background: transparent;"
            % ("#ffb4ab" if error else "#f4efe4")
        )
        badge_layout.addWidget(badge_icon)
        content_row.addWidget(badge, 0, Qt.AlignTop)

        body = QLabel(message)
        body.setObjectName("TechDialogBody")
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_row.addWidget(body, 1)
        inner.addLayout(content_row)

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
