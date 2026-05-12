import sys
from PyQt5.QtWidgets import QApplication

try:
    from .launcher.main_window import LauncherWindow
    from .launcher.styles import Styles
except ImportError:
    from launcher.main_window import LauncherWindow
    from launcher.styles import Styles


def main():
    app = QApplication(sys.argv)

    # 应用全局样式（可选，也可以在 main_window 中应用）
    app.setStyleSheet(Styles.global_style)

    window = LauncherWindow()
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
