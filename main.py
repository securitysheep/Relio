"""程序入口：启动 PySide6 桌面 GUI。"""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from core.system import DialogueDecisionSystem
from ui.main_window import MainWindow
from ui.theme_manager import ThemeManager


def main() -> None:
    """主程序入口。"""
    app = QApplication(sys.argv)
    
    # 初始化主题管理器并应用保存的主题
    theme_manager = ThemeManager(app)
    theme_manager.initialize()
    
    try:
        system = DialogueDecisionSystem()
    except Exception as err:
        QMessageBox.critical(None, "启动失败", f"系统初始化失败：{err}")
        sys.exit(1)

    window = MainWindow(system)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
