class Styles:
    global_style = """
        /* ===== 全局 ===== */
        QMainWindow {
            background-color: #0a1628;
        }

        /* ===== 数据源卡片（原 QGroupBox：圆角 + ::title 在 Windows 上易裁切子控件，
              露出背后渐变，像透明条挡住标题下方；改为 QFrame + QLabel 标题） ===== */
        QFrame#dataSourceCard {
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(0, 198, 255, 0.28);
            border-radius: 14px;
        }
        QLabel#dataSourceCardTitle {
            font-size: 14px;
            font-weight: bold;
            color: #00e8ff;
            padding: 2px 0 10px 0;
            background: transparent;
        }

        /* ===== 通用按钮 ===== */
        QPushButton {
            background: rgba(0, 114, 255, 0.25);
            color: #c8e0ff;
            border: 1px solid rgba(0, 198, 255, 0.35);
            border-radius: 8px;
            padding: 10px 24px;
            font-size: 14px;
            font-weight: bold;
            min-height: 24px;
        }
        QPushButton:hover {
            background: rgba(0, 150, 255, 0.40);
            border: 1px solid rgba(0, 255, 255, 0.65);
            color: #ffffff;
        }
        QPushButton:pressed {
            background: rgba(0, 80, 180, 0.45);
        }
        QPushButton:disabled {
            background: rgba(60, 60, 60, 0.35);
            border: 1px solid rgba(80, 80, 80, 0.3);
            color: #555;
        }

        /* ===== 浏览按钮（渐变 + 悬停加亮边，近似外发光） ===== */
        QPushButton#btnBrowse {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #00c6ff, stop:1 #0072ff
            );
            border: 1px solid rgba(0, 255, 255, 0.55);
            border-radius: 8px;
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            padding: 10px 20px;
        }
        QPushButton#btnBrowse:hover {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #33d4ff, stop:1 #2980ff
            );
            border: 2px solid rgba(0, 255, 220, 0.95);
            color: #ffffff;
        }
        QPushButton#btnBrowse:pressed {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #0099cc, stop:1 #0058cc
            );
        }

        /* ===== 启动按钮（主 CTA：绿→蓝渐变，字距收紧） ===== */
        QPushButton#btnLaunch {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #00f260, stop:1 #0575e6
            );
            border: 2px solid rgba(0, 230, 255, 0.55);
            border-radius: 14px;
            color: #ffffff;
            font-size: 19px;
            font-weight: bold;
            letter-spacing: 2px;
            padding: 14px 28px;
            min-height: 56px;
        }
        QPushButton#btnLaunch:hover {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #33ff88, stop:1 #1a8fff
            );
            border: 2px solid rgba(0, 255, 200, 0.95);
            color: #ffffff;
        }
        QPushButton#btnLaunch:pressed {
            padding: 15px 28px 13px 28px;
        }
        QPushButton#btnLaunch:disabled {
            background: rgba(60, 60, 60, 0.35);
            border: 1px solid rgba(80, 80, 80, 0.3);
            color: #555;
            letter-spacing: 2px;
            padding: 14px 28px;
        }

        /* ===== 标签 ===== */
        QLabel {
            font-size: 14px;
            color: #b0bec5;
        }

        QLabel#lblHint {
            font-size: 13px;
            color: #8fa3b0;
        }

        /* ===== 路径标签（默认态由代码覆盖；此处为兜底） ===== */
        QLabel#lblPath {
            font-size: 13px;
            padding: 8px 12px;
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.58);
            border: 1px solid rgba(0, 198, 255, 0.22);
        }
        QLabel#lblPath:hover {
            border: 1px solid rgba(0, 255, 255, 0.45);
        }
    """
