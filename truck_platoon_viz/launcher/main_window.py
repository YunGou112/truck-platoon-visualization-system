import os

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QFileDialog,
                             QHBoxLayout, QGraphicsDropShadowEffect,
                             QSizePolicy, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import (QPixmap, QPainter, QColor, QFont, QFontMetrics,
                         QPen, QLinearGradient, QRadialGradient, QBrush)
from .process_manager import ProcessManager
from .tech_message_dialog import tech_information, tech_critical


# ── 校徽生成 ───────────────────────────────────────────
# 若 `school_logo.png` 为「左侧校徽 + 右侧校名」横长图，只截取左侧一段再缩放。
# 按实际图片调节：偏小则裁掉右侧文字偏多，偏大则可能带入一点字边，一般 0.32～0.48。
LOGO_LEFT_ONLY_WIDTH_RATIO = 0.3


def _make_logo_pixmap(size=80):
    """尝试加载校徽图片，失败则绘制文字徽章兜底。"""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_paths = [
        os.path.join(base, 'assets', 'school_logo.png'),
        os.path.join(base, '..', 'assets', 'school_logo.png'),
    ]
    for p in logo_paths:
        if os.path.isfile(p):
            pm = QPixmap(p)
            if not pm.isNull():
                w, h = pm.width(), pm.height()
                if w > 0 and h > 0:
                    ratio = max(0.15, min(0.85, float(LOGO_LEFT_ONLY_WIDTH_RATIO)))
                    cw = max(1, int(w * ratio))
                    pm = pm.copy(QRect(0, 0, cw, h))
                return pm.scaled(size, size, Qt.KeepAspectRatio,
                                 Qt.SmoothTransformation)

    # 兜底：绘制圆形文字徽章
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    cx, cy, r = size // 2, size // 2, size // 2 - 4
    painter.setPen(QPen(QColor("#00c6ff"), 2))
    painter.setBrush(QColor("#0d2540"))
    painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
    font = QFont("Microsoft YaHei", size // 3)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor("#80e8ff"))
    painter.drawText(pm.rect(), Qt.AlignCenter, "交")
    painter.end()
    return pm


# ── 渐变发光校名（Qt QSS 无法做文字渐变，用手绘） ───────────
class GradientSchoolLabel(QWidget):
    def __init__(self, text="兰州交通大学", parent=None):
        super().__init__(parent)
        self._text = text
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        base = QFont("Microsoft YaHei", 34)
        base.setBold(True)
        fm = QFontMetrics(base)
        self.setMinimumHeight(fm.height() + 8)
        self.setMinimumWidth(120)

    def sizeHint(self):
        return QSize(280, self.minimumHeight())

    def _font_for_width(self, w):
        px = max(16, min(44, max(int(w), 120) // 11))
        f = QFont("Microsoft YaHei")
        f.setPixelSize(px)
        f.setBold(True)
        f.setLetterSpacing(QFont.AbsoluteSpacing, max(1, px // 12))
        return f

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        font = self._font_for_width(self.width())
        painter.setFont(font)
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, QColor("#00c6ff"))
        grad.setColorAt(0.55, QColor("#5eb3ff"))
        grad.setColorAt(1.0, QColor("#7f7fd5"))
        pen = QPen()
        pen.setBrush(QBrush(grad))
        painter.setPen(pen)
        painter.drawText(self.rect(), Qt.AlignLeft | Qt.AlignVCenter, self._text)


# ── 渐变背景容器 ────────────────────────────────────────
class GradientWidget(QWidget):
    """绘制深色渐变背景 + 轻网格 + 中心微光。"""
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0.0, QColor("#0a1628"))
        grad.setColorAt(0.45, QColor("#112240"))
        grad.setColorAt(1.0, QColor("#0d1f38"))
        painter.fillRect(self.rect(), QBrush(grad))

        # 中心轻微径向提亮（叠在渐变上）
        rad = QRadialGradient(self.width() * 0.5, self.height() * 0.35,
                              max(self.width(), self.height()) * 0.55)
        rad.setColorAt(0.0, QColor(0, 120, 180, 38))
        rad.setColorAt(0.5, QColor(0, 60, 90, 12))
        rad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), QBrush(rad))

        # 细网格
        painter.setPen(QPen(QColor(0, 198, 255, 18), 1))
        step = 48
        for x in range(0, self.width() + 1, step):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height() + 1, step):
            painter.drawLine(0, y, self.width(), y)


# ── 主窗口 ──────────────────────────────────────────────
class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("卡车编队可视化系统 — 兰州交通大学")
        self.setMinimumSize(520, 420)
        self.resize(960, 640)

        self.selected_folder = None
        self._last_logo_px = 0
        self._hero_meta_label = None
        self._init_ui()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
            return
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
            return
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_responsive_layout()

    def _apply_responsive_layout(self):
        w, h = self.width(), self.height()
        if w < 1 or h < 1:
            return

        hm = max(20, min(64, w // 12))
        vm = max(16, min(48, h // 16))
        self._root_layout.setContentsMargins(hm, vm, hm, vm)

        d = min(w, h)
        logo_px = max(48, min(120, int(d * 0.11)))
        if abs(logo_px - self._last_logo_px) >= 2:
            self._last_logo_px = logo_px
            pm = _make_logo_pixmap(logo_px)
            self._logo_label.setPixmap(pm)
            self._logo_label.setFixedSize(logo_px, logo_px)

        title_px = max(16, min(34, int(w * 0.034)))
        sub_px = max(10, min(16, int(w * 0.018)))
        self._title_cn.setStyleSheet(
            f"font-size: {title_px}px; font-weight: bold;"
            "color: #2ad4ff;"
            "padding: 4px 0;"
            f"letter-spacing: {max(0, title_px // 24)}px;"
        )
        self._title_en.setStyleSheet(
            f"font-size: {sub_px}px; color: #4a6577; font-style: italic;"
            "padding: 0 0 4px 0;"
            f"letter-spacing: {max(0, sub_px // 18)}px;"
        )

        college_px = max(11, min(15, int(w * 0.019)))
        self._college_label.setStyleSheet(
            f"font-size: {college_px}px; color: #5a7088; letter-spacing: 1px;"
        )

        hint_px = max(11, min(14, int(w * 0.017)))
        # 右下角提示：略放宽宽度，减少自动折行；断行由文案内 \n 控制
        hint_max = min(640, max(260, int(w * 0.52)))
        if hasattr(self, "_right_hint_panel"):
            self._right_hint_panel.setMaximumWidth(hint_max + 32)
        if hasattr(self, "_hints_label"):
            self._hints_label.setMaximumWidth(hint_max)
            self._hints_label.setStyleSheet(
                f"font-size: {hint_px}px; color: #9eb4c4;"
                "padding: 2px 0 2px 8px;"
            )
        if self._hero_meta_label is not None:
            hero_meta_px = max(12, min(15, int(w * 0.017)))
            self._hero_meta_label.setStyleSheet(
                f"font-size: {hero_meta_px}px; color: #95a7c0;"
            )

    def _init_ui(self):
        # 使用渐变背景容器
        central = GradientWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        self._root_layout = root
        root.setContentsMargins(48, 30, 48, 24)
        root.setSpacing(0)

        # 细线（顶部分隔）
        line1 = QFrame()
        line1.setObjectName("headerRule")
        line1.setFixedHeight(1)
        root.addWidget(line1)
        root.addSpacing(14)

        hero = QFrame()
        hero.setObjectName("heroPanel")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(22, 18, 22, 18)
        hero_layout.setSpacing(10)

        eyebrow = QLabel("TRUCK PLATOON TOOL")
        eyebrow.setObjectName("heroEyebrow")
        eyebrow.setAlignment(Qt.AlignCenter)
        hero_layout.addWidget(eyebrow)

        self._title_cn = QLabel("数据驱动的卡车队列可视化系统")
        self._title_cn.setAlignment(Qt.AlignCenter)
        self._title_cn.setWordWrap(True)
        self._title_cn.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
            "color: #2ad4ff;"
            "padding: 4px 0;"
            "letter-spacing: 1px;"
        )
        hero_layout.addWidget(self._title_cn)

        self._title_en = QLabel(
            "Data-Driven Truck Platooning Visualization System"
        )
        self._title_en.setAlignment(Qt.AlignCenter)
        self._title_en.setWordWrap(True)
        self._title_en.setStyleSheet(
            "font-size: 12px; color: #4a6577; font-style: italic;"
            "padding: 0 0 4px 0;"
            "letter-spacing: 0.5px;"
        )
        hero_layout.addWidget(self._title_en)

        self._hero_meta_label = QLabel("选择编队数据后启动，Pygame 可视化窗口将独立弹出。")
        self._hero_meta_label.setObjectName("heroMeta")
        self._hero_meta_label.setAlignment(Qt.AlignCenter)
        self._hero_meta_label.setWordWrap(True)
        hero_layout.addWidget(self._hero_meta_label)

        chip_row = QHBoxLayout()
        chip_row.setSpacing(10)
        chip_row.addStretch(1)
        for text in ("深色监控台", "本地数据启动", "独立可视化窗口"):
            chip = QLabel(text)
            chip.setObjectName("statChip")
            chip_row.addWidget(chip)
        chip_row.addStretch(1)
        hero_layout.addLayout(chip_row)

        root.addWidget(hero)
        root.addSpacing(16)

        # ── 中间可滚动区：数据源 + 启动 ──
        scroll = QScrollArea()
        scroll.setObjectName("launcherScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        mid = QWidget()
        mid.setObjectName("launcherMid")
        mid.setStyleSheet("QWidget#launcherMid { background: transparent; }")
        mid.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        mid_layout = QVBoxLayout(mid)
        mid_layout.setContentsMargins(0, 0, 0, 16)
        mid_layout.setSpacing(0)

        # ── 数据源卡片（不用 QGroupBox：Win + 圆角 QSS 常错误裁切子控件，
        #    标题下会像被透明层挡住；改用 QFrame + 标题标签布局更稳） ──
        card = QFrame()
        card.setObjectName("dataSourceCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)
        card_layout.setContentsMargins(18, 18, 18, 20)

        title_ds = QLabel("选择数据源")
        title_ds.setObjectName("dataSourceCardTitle")
        title_ds.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        subtitle_ds = QLabel("选择包含 `platoon_data.csv` 的编队数据文件夹。")
        subtitle_ds.setStyleSheet("color: #92a2b8; font-size: 13px; padding: 0 0 2px 0;")

        # 路径独占一行全宽，按钮下一行右对齐，避免窄窗口横向挤压遮挡
        path_col = QVBoxLayout()
        path_col.setSpacing(12)
        self.lbl_path = QLabel("当前路径：未选择")
        self.lbl_path.setObjectName("lblPath")
        self.lbl_path.setWordWrap(True)
        self.lbl_path.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.lbl_path.setMinimumHeight(72)
        self.lbl_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.lbl_path.setStyleSheet(
            "color: #98a7bb; font-size: 13px; padding: 10px 14px;"
            "background: rgba(10, 14, 22, 0.9);"
            "border: 1px solid rgba(88, 102, 126, 0.42);"
            "border-radius: 8px;"
        )

        btn_browse = QPushButton("浏览文件夹")
        btn_browse.setObjectName("btnBrowse")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.setMinimumWidth(140)
        btn_browse.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        btn_browse.clicked.connect(self._on_browse_clicked)

        path_col.addWidget(self.lbl_path)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(btn_browse)
        path_col.addLayout(btn_row)
        card_layout.addWidget(title_ds)
        card_layout.addWidget(subtitle_ds)
        card_layout.addLayout(path_col)

        mid_layout.addWidget(card)
        mid_layout.addSpacing(18)

        self.btn_launch = QPushButton("启动可视化系统")
        self.btn_launch.setObjectName("btnLaunch")
        self.btn_launch.setEnabled(False)
        self.btn_launch.setMinimumHeight(52)
        self.btn_launch.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_launch.setCursor(Qt.PointingHandCursor)
        self.btn_launch.clicked.connect(self._on_launch_clicked)
        mid_layout.addWidget(self.btn_launch)
        mid_layout.addStretch(0)

        scroll.setWidget(mid)
        root.addWidget(scroll, 1)

        # ── 底栏：左下角校徽+校名 / 右下角提示 ──
        bottom_bar = QWidget()
        bottom_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        bb = QHBoxLayout(bottom_bar)
        bb.setContentsMargins(0, 10, 0, 2)
        bb.setSpacing(16)

        left_corner = QWidget()
        left_corner.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        left_h = QHBoxLayout(left_corner)
        left_h.setContentsMargins(0, 0, 0, 0)
        left_h.setSpacing(10)

        self._logo_label = QLabel()
        logo_pm = _make_logo_pixmap(76)
        self._logo_label.setPixmap(logo_pm)
        self._logo_label.setFixedSize(76, 76)
        self._logo_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        left_h.addWidget(self._logo_label, 0, Qt.AlignBottom)

        school_col = QVBoxLayout()
        school_col.setSpacing(2)
        school_col.setAlignment(Qt.AlignBottom)
        uni = GradientSchoolLabel("兰州交通大学")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(22)
        glow.setColor(QColor(0, 198, 255, 140))
        glow.setOffset(0, 0)
        uni.setGraphicsEffect(glow)
        school_col.addWidget(uni, 0, Qt.AlignLeft | Qt.AlignBottom)

        self._college_label = QLabel("交通运输学院")
        self._college_label.setWordWrap(True)
        self._college_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        self._college_label.setStyleSheet(
            "font-size: 13px; color: #5a7088; letter-spacing: 1px;"
        )
        school_col.addWidget(self._college_label, 0, Qt.AlignLeft | Qt.AlignBottom)
        left_h.addLayout(school_col)

        bb.addWidget(left_corner, 0, Qt.AlignLeft | Qt.AlignBottom)
        bb.addStretch(1)

        right_corner = QWidget()
        right_corner.setObjectName("launcherHintPanel")
        self._right_hint_panel = right_corner
        right_corner.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        right_v = QVBoxLayout(right_corner)
        right_v.setContentsMargins(0, 0, 4, 0)
        right_v.setSpacing(5)
        right_v.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        hint_title = QLabel("操作提示")
        hint_title.setStyleSheet("color: #e7edf8; font-size: 13px; font-weight: 600;")
        right_v.addWidget(hint_title, 0, Qt.AlignRight)

        self._hints_label = QLabel(
            "Pygame 独立弹窗\n"
            "Space 暂停 · 滚轮缩放\n"
            "左键拖拽地图\n"
            "↑↓ 调速 · ←→ 跳转\n"
            "F11 全屏 · Esc 退出"
        )
        self._hints_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        # 已手动断行；关闭自动换行，避免在标点或词中间再折一行
        self._hints_label.setWordWrap(False)
        self._hints_label.setObjectName("lblHint")
        right_v.addWidget(self._hints_label, 0, Qt.AlignRight)

        bb.addWidget(right_corner, 0, Qt.AlignRight | Qt.AlignBottom)

        root.addWidget(bottom_bar, 0)

        self._apply_responsive_layout()

    # ── 交互逻辑 ──
    def _on_browse_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, "选择数据文件夹")
        if folder:
            self.selected_folder = folder
            self.lbl_path.setText(f"已选择：{folder}")
            self.lbl_path.setStyleSheet(
                "color: #dbe7f5; font-size: 13px; padding: 10px 14px;"
                "background: rgba(14, 22, 30, 0.95);"
                "border: 1px solid rgba(179, 148, 86, 0.56);"
                "border-radius: 8px;"
            )
            self.btn_launch.setEnabled(True)
        else:
            self.selected_folder = None
            self.lbl_path.setText("当前路径：未选择")
            self.lbl_path.setStyleSheet(
                "color: #98a7bb; font-size: 13px; padding: 10px 14px;"
                "background: rgba(10, 14, 22, 0.9);"
                "border: 1px solid rgba(88, 102, 126, 0.42);"
                "border-radius: 8px;"
            )
            self.btn_launch.setEnabled(False)

    def _on_launch_clicked(self):
        if not self.selected_folder:
            return
        success, message = ProcessManager.run_visualization(self.selected_folder)
        if success:
            tech_information(
                self,
                "提示",
                "可视化程序已启动。\n请切换到新弹出的 Pygame 窗口进行操作。",
            )
        else:
            tech_critical(self, "启动失败", message)
