class Styles:
    global_style = """
        /* ===== 全局 ===== */
        QMainWindow {
            background-color: #09111b;
            color: #d7e1ef;
        }

        QWidget {
            color: #c7d1df;
            selection-background-color: rgba(88, 132, 255, 0.35);
            selection-color: #f4f7fb;
        }

        /* ===== 区块卡片 ===== */
        QFrame#heroPanel,
        QFrame#dataSourceCard,
        QFrame#launcherHintPanel {
            background: rgba(14, 20, 32, 0.82);
            border: 1px solid rgba(87, 100, 124, 0.48);
            border-radius: 12px;
        }

        QFrame#headerRule {
            background: rgba(103, 124, 158, 0.38);
            border: none;
            min-height: 1px;
            max-height: 1px;
        }

        QFrame#dataSourceCard {
            background: rgba(15, 20, 30, 0.92);
        }
        QFrame#heroPanel {
            background: rgba(13, 19, 30, 0.76);
        }
        QFrame#launcherHintPanel {
            background: rgba(11, 16, 26, 0.7);
        }
        QLabel#dataSourceCardTitle {
            font-size: 14px;
            font-weight: bold;
            color: #ecf2fb;
            padding: 0 0 6px 0;
            background: transparent;
        }
        QLabel#heroEyebrow {
            color: #8ea1bb;
            font-size: 12px;
            font-weight: 600;
            padding: 0;
        }
        QLabel#heroMeta {
            color: #95a7c0;
            font-size: 13px;
            padding: 0;
        }
        QLabel#statChip {
            color: #dbe7f5;
            font-size: 12px;
            padding: 6px 10px;
            background: rgba(24, 31, 46, 0.95);
            border: 1px solid rgba(94, 108, 130, 0.52);
            border-radius: 8px;
        }

        /* ===== 通用按钮 ===== */
        QPushButton {
            background: rgba(35, 46, 68, 0.95);
            color: #dce6f4;
            border: 1px solid rgba(101, 118, 146, 0.56);
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
            min-height: 24px;
        }
        QPushButton:hover {
            background: rgba(48, 61, 86, 0.98);
            border: 1px solid rgba(135, 154, 186, 0.82);
            color: #ffffff;
        }
        QPushButton:pressed {
            background: rgba(25, 34, 52, 0.98);
        }
        QPushButton:disabled {
            background: rgba(27, 31, 39, 0.78);
            border: 1px solid rgba(69, 77, 92, 0.34);
            color: #69758a;
        }

        /* ===== 浏览按钮 ===== */
        QPushButton#btnBrowse {
            background: rgba(28, 37, 56, 0.98);
            border: 1px solid rgba(118, 132, 160, 0.62);
            border-radius: 8px;
            color: #edf3ff;
            font-size: 14px;
            font-weight: 600;
            padding: 10px 16px;
        }
        QPushButton#btnBrowse:hover {
            background: rgba(41, 52, 76, 1.0);
            border: 1px solid rgba(164, 181, 212, 0.84);
            color: #ffffff;
        }
        QPushButton#btnBrowse:pressed {
            background: rgba(22, 30, 46, 1.0);
        }

        /* ===== 启动按钮 ===== */
        QPushButton#btnLaunch {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #b49053, stop:0.08 #d1b172, stop:0.5 #5a83d5, stop:1 #3c5f9c
            );
            border: 1px solid rgba(194, 213, 248, 0.5);
            border-radius: 12px;
            color: #ffffff;
            font-size: 18px;
            font-weight: 700;
            padding: 14px 24px;
            min-height: 56px;
        }
        QPushButton#btnLaunch:hover {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #c6a362, stop:0.08 #e1c485, stop:0.5 #6f97ea, stop:1 #4a72b5
            );
            border: 1px solid rgba(225, 236, 255, 0.82);
            color: #ffffff;
        }
        QPushButton#btnLaunch:pressed {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #a68449, stop:0.08 #bc9d63, stop:0.5 #4a70be, stop:1 #37568f
            );
        }
        QPushButton#btnLaunch:disabled {
            background: rgba(35, 40, 49, 0.94);
            border: 1px solid rgba(73, 81, 95, 0.42);
            color: #6b7687;
            padding: 14px 24px;
        }

        /* ===== 标签 ===== */
        QLabel {
            font-size: 14px;
            color: #b7c3d4;
        }

        QLabel#lblHint {
            font-size: 13px;
            color: #90a0b6;
        }

        /* ===== 路径标签 ===== */
        QLabel#lblPath {
            font-size: 13px;
            padding: 10px 12px;
            border-radius: 8px;
            background: rgba(10, 14, 22, 0.9);
            border: 1px solid rgba(88, 102, 126, 0.42);
            color: #8d9bae;
        }
        QLabel#lblPath:hover {
            border: 1px solid rgba(138, 154, 182, 0.62);
        }

        QScrollArea#launcherScroll {
            background: transparent;
            border: none;
        }
        QScrollBar:vertical {
            width: 10px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 5px;
            margin: 2px;
        }
        QScrollBar::handle:vertical {
            background: rgba(102, 122, 152, 0.55);
            border-radius: 5px;
            min-height: 28px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(134, 156, 192, 0.75);
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
    """
