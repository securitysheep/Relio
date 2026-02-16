"""主题管理器：支持明亮、暗黑和跟随系统三种主题模式。"""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication

from core.config import (
    load_theme_setting,
    save_theme_setting,
    THEME_LIGHT,
    THEME_DARK,
    THEME_SYSTEM,
)

# 获取 assets 目录路径
ASSETS_DIR = Path(__file__).parent.parent / "assets"


class ThemeManager(QObject):
    """主题管理器，负责应用和切换应用程序主题。"""
    
    # 主题变更信号
    theme_changed = Signal(str)  # 参数: 实际应用的主题 ('light' 或 'dark')
    
    _instance: Optional["ThemeManager"] = None
    
    def __new__(cls, app: Optional[QApplication] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, app: Optional[QApplication] = None):
        if self._initialized:
            return
        
        super().__init__()
        self._app = app or QApplication.instance()
        self._current_setting = THEME_SYSTEM  # 用户选择的设置
        self._current_theme = THEME_LIGHT  # 实际应用的主题
        self._initialized = True
    
    @classmethod
    def instance(cls) -> "ThemeManager":
        """获取单例实例。"""
        if cls._instance is None:
            raise RuntimeError("ThemeManager not initialized. Call ThemeManager(app) first.")
        return cls._instance
    
    def initialize(self) -> None:
        """初始化主题管理器，加载保存的设置并应用。"""
        self._current_setting = load_theme_setting()
        self.apply_theme(self._current_setting)
    
    def get_current_setting(self) -> str:
        """获取当前的主题设置。"""
        return self._current_setting
    
    def get_actual_theme(self) -> str:
        """获取实际应用的主题（light 或 dark）。"""
        return self._current_theme
    
    def is_dark_mode(self) -> bool:
        """当前是否为暗黑模式。"""
        return self._current_theme == THEME_DARK
    
    def set_theme(self, theme: str) -> bool:
        """设置并应用主题。
        
        Args:
            theme: 'light', 'dark', 或 'system'
        
        Returns:
            是否设置成功
        """
        if theme not in (THEME_LIGHT, THEME_DARK, THEME_SYSTEM):
            return False
        
        self._current_setting = theme
        self.apply_theme(theme)
        save_theme_setting(theme)
        return True
    
    def apply_theme(self, theme: str) -> None:
        """应用指定的主题。"""
        if theme == THEME_SYSTEM:
            actual_theme = self._detect_system_theme()
        else:
            actual_theme = theme
        
        self._current_theme = actual_theme
        
        if actual_theme == THEME_DARK:
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
        
        self.theme_changed.emit(actual_theme)
    
    def _detect_system_theme(self) -> str:
        """检测系统主题设置。"""
        if sys.platform == "darwin":
            # macOS: 使用 subprocess 运行 defaults 命令
            try:
                import subprocess
                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and "Dark" in result.stdout:
                    return THEME_DARK
                return THEME_LIGHT
            except Exception:
                pass
        
        # 通用方法：检查系统调色板
        if self._app:
            palette = self._app.palette()
            window_color = palette.color(QPalette.Window)
            if window_color.lightness() < 128:
                return THEME_DARK
        
        return THEME_LIGHT
    
    def _apply_light_theme(self) -> None:
        """应用明亮主题。"""
        if not self._app:
            return
        
        palette = QPalette()
        
        # 基础颜色
        palette.setColor(QPalette.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.WindowText, QColor(30, 30, 30))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.Text, QColor(30, 30, 30))
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ButtonText, QColor(30, 30, 30))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(0, 102, 204))
        palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # 禁用状态
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(150, 150, 150))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(150, 150, 150))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(150, 150, 150))
        
        self._app.setPalette(palette)
        self._app.setStyleSheet(self._get_light_stylesheet())
    
    def _apply_dark_theme(self) -> None:
        """应用暗黑主题。"""
        if not self._app:
            return
        
        palette = QPalette()
        
        # 基础颜色
        palette.setColor(QPalette.Window, QColor(45, 45, 48))
        palette.setColor(QPalette.WindowText, QColor(240, 240, 240))
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.AlternateBase, QColor(45, 45, 48))
        palette.setColor(QPalette.ToolTipBase, QColor(60, 60, 60))
        palette.setColor(QPalette.ToolTipText, QColor(240, 240, 240))
        palette.setColor(QPalette.Text, QColor(240, 240, 240))
        palette.setColor(QPalette.Button, QColor(55, 55, 58))
        palette.setColor(QPalette.ButtonText, QColor(240, 240, 240))
        palette.setColor(QPalette.BrightText, QColor(255, 100, 100))
        palette.setColor(QPalette.Link, QColor(86, 156, 214))
        palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # 禁用状态
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(100, 100, 100))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(100, 100, 100))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100, 100, 100))
        
        self._app.setPalette(palette)
        self._app.setStyleSheet(self._get_dark_stylesheet())
    
    def _get_light_stylesheet(self) -> str:
        """获取明亮主题的样式表。"""
        checkmark_path = (ASSETS_DIR / "checkmark-white.svg").as_posix()
        return """
            QMainWindow, QDialog {
                background-color: #f5f5f5;
            }
            
            QMenuBar {
                background-color: #f0f0f0;
                border-bottom: 1px solid #d0d0d0;
            }
            
            QMenuBar::item {
                padding: 6px 10px;
                background: transparent;
            }
            
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
            
            QMenu {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
            }
            
            QMenu::item {
                padding: 6px 30px 6px 20px;
            }
            
            QMenu::item:selected {
                background-color: #e8f0fe;
            }
            
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 5px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            
            QScrollBar:horizontal {
                background: #f0f0f0;
                height: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background: #c0c0c0;
                border-radius: 5px;
                min-width: 30px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: #a0a0a0;
            }
            
            QScrollBar::add-line, QScrollBar::sub-line {
                height: 0px;
                width: 0px;
            }
            
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            
            QListWidget::item {
                padding: 4px;
            }
            
            QListWidget::item:selected {
                background-color: #e8f0fe;
            }
            
            QTextEdit, QLineEdit {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 4px;
            }
            
            QTextEdit:focus, QLineEdit:focus {
                border-color: #0078d4;
            }
            
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: #ffffff;
            }
            
            QTabBar::tab {
                background-color: #e8e8e8;
                padding: 8px 16px;
                border: 1px solid #d0d0d0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: #ffffff;
            }
            
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            
            QToolTip {
                background-color: #ffffdc;
                color: #000000;
                border: 1px solid #c0c0c0;
                padding: 4px;
            }
            
            QSlider::groove:horizontal {
                background: #d0d0d0;
                height: 6px;
                border-radius: 3px;
            }
            
            QSlider::sub-page:horizontal {
                background: #0078d4;
                height: 6px;
                border-radius: 3px;
            }
            
            QSlider::add-page:horizontal {
                background: #d0d0d0;
                height: 6px;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                background: #0078d4;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            
            QSlider::handle:horizontal:hover {
                background: #106ebe;
            }
            
            /* QCheckBox 美化样式 */
            QCheckBox {
                spacing: 8px;
                color: #1e1e1e;
                font-size: 13px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 2px solid #b0b0b0;
                background-color: #ffffff;
            }
            
            QCheckBox::indicator:unchecked:hover {
                border: 2px solid #0078d4;
                background-color: #e8f4fc;
            }
            
            QCheckBox::indicator:checked {
                border: 2px solid #0078d4;
                background-color: #0078d4;
                image: url(""" + checkmark_path + """);
            }
            
            QCheckBox::indicator:checked:hover {
                border: 2px solid #106ebe;
                background-color: #106ebe;
            }
            
            QCheckBox:disabled {
                color: #a0a0a0;
            }
            
            QCheckBox::indicator:disabled {
                border: 2px solid #d0d0d0;
                background-color: #f0f0f0;
            }
            
            /* QSpinBox 和 QDoubleSpinBox 样式 */
            QSpinBox, QDoubleSpinBox {
                background-color: #ffffff;
                border: 1px solid #b0b0b0;
                border-radius: 4px;
                padding: 4px 8px;
                padding-right: 24px;
                color: #1e1e1e;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
            }
            
            QSpinBox:hover, QDoubleSpinBox:hover {
                border-color: #808080;
            }
            
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #0078d4;
            }
            
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                height: 12px;
                border: none;
                border-left: 1px solid #d0d0d0;
                border-bottom: 1px solid #d0d0d0;
                border-top-right-radius: 3px;
                background-color: #f5f5f5;
                image: url(""" + (ASSETS_DIR / "arrow-up-light.svg").as_posix() + """);
            }
            
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
                background-color: #e8e8e8;
            }
            
            QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {
                background-color: #d0d0d0;
            }
            
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                height: 12px;
                border: none;
                border-left: 1px solid #d0d0d0;
                border-bottom-right-radius: 3px;
                background-color: #f5f5f5;
                image: url(""" + (ASSETS_DIR / "arrow-down-light.svg").as_posix() + """);
            }
            
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #e8e8e8;
            }
            
            QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {
                background-color: #d0d0d0;
            }
        """
    
    def _get_dark_stylesheet(self) -> str:
        """获取暗黑主题的样式表。"""
        checkmark_path = (ASSETS_DIR / "checkmark-white.svg").as_posix()
        return """
            QMainWindow, QDialog {
                background-color: #2d2d30;
            }
            
            QMenuBar {
                background-color: #3c3c3c;
                border-bottom: 1px solid #505050;
            }
            
            QMenuBar::item {
                padding: 6px 10px;
                background: transparent;
                color: #e0e0e0;
            }
            
            QMenuBar::item:selected {
                background-color: #505050;
            }
            
            QMenu {
                background-color: #2d2d30;
                border: 1px solid #505050;
                color: #e0e0e0;
            }
            
            QMenu::item {
                padding: 6px 30px 6px 20px;
            }
            
            QMenu::item:selected {
                background-color: #3e3e42;
            }
            
            QScrollBar:vertical {
                background: #2d2d30;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background: #686868;
                border-radius: 5px;
                min-height: 30px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #888888;
            }
            
            QScrollBar:horizontal {
                background: #2d2d30;
                height: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background: #686868;
                border-radius: 5px;
                min-width: 30px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: #888888;
            }
            
            QScrollBar::add-line, QScrollBar::sub-line {
                height: 0px;
                width: 0px;
            }
            
            QListWidget {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                color: #e0e0e0;
            }
            
            QListWidget::item {
                padding: 4px;
            }
            
            QListWidget::item:selected {
                background-color: #094771;
            }
            
            QTextEdit, QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 4px;
                color: #e0e0e0;
            }
            
            QTextEdit:focus, QLineEdit:focus {
                border-color: #0078d4;
            }
            
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background-color: #252526;
            }
            
            QTabBar::tab {
                background-color: #2d2d30;
                padding: 8px 16px;
                border: 1px solid #3c3c3c;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                color: #b0b0b0;
            }
            
            QTabBar::tab:selected {
                background-color: #252526;
                color: #e0e0e0;
            }
            
            QGroupBox {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
                color: #e0e0e0;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            
            QLabel {
                color: #e0e0e0;
            }
            
            /* QCheckBox 美化样式 */
            QCheckBox {
                spacing: 8px;
                color: #e0e0e0;
                font-size: 13px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 2px solid #6a6a6a;
                background-color: #2d2d30;
            }
            
            QCheckBox::indicator:unchecked:hover {
                border: 2px solid #3794ff;
                background-color: #1e3a5f;
            }
            
            QCheckBox::indicator:checked {
                border: 2px solid #3794ff;
                background-color: #3794ff;
                image: url(""" + checkmark_path + """);
            }
            
            QCheckBox::indicator:checked:hover {
                border: 2px solid #4ba3ff;
                background-color: #4ba3ff;
            }
            
            QCheckBox:disabled {
                color: #6a6a6a;
            }
            
            QCheckBox::indicator:disabled {
                border: 2px solid #4a4a4a;
                background-color: #3c3c3c;
            }
            
            QRadioButton {
                color: #e0e0e0;
            }
            
            /* QSpinBox 和 QDoubleSpinBox 样式 */
            QSpinBox, QDoubleSpinBox {
                background-color: #1e1e1e;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 4px 8px;
                padding-right: 24px;
                color: #e0e0e0;
                selection-background-color: #094771;
                selection-color: #ffffff;
            }
            
            QSpinBox:hover, QDoubleSpinBox:hover {
                border-color: #606060;
            }
            
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #3794ff;
            }
            
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                height: 12px;
                border: none;
                border-left: 1px solid #4a4a4a;
                border-bottom: 1px solid #4a4a4a;
                border-top-right-radius: 3px;
                background-color: #333337;
                image: url(""" + (ASSETS_DIR / "arrow-up-dark.svg").as_posix() + """);
            }
            
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
                background-color: #3e3e42;
            }
            
            QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {
                background-color: #4a4a4e;
            }
            
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                height: 12px;
                border: none;
                border-left: 1px solid #4a4a4a;
                border-bottom-right-radius: 3px;
                background-color: #333337;
                image: url(""" + (ASSETS_DIR / "arrow-down-dark.svg").as_posix() + """);
            }
            
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #3e3e42;
            }
            
            QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {
                background-color: #4a4a4e;
            }
            
            QComboBox {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 4px;
                color: #e0e0e0;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2d2d30;
                border: 1px solid #3c3c3c;
                color: #e0e0e0;
                selection-background-color: #094771;
            }
            
            QSlider::groove:horizontal {
                background: #4a4a4a;
                height: 6px;
                border-radius: 3px;
            }
            
            QSlider::sub-page:horizontal {
                background: #0078d4;
                height: 6px;
                border-radius: 3px;
            }
            
            QSlider::add-page:horizontal {
                background: #4a4a4a;
                height: 6px;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                background: #0078d4;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            
            QSlider::handle:horizontal:hover {
                background: #1a8cff;
            }
            
            QProgressBar {
                background-color: #3c3c3c;
                border: none;
                border-radius: 4px;
                text-align: center;
                color: #e0e0e0;
            }
            
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 4px;
            }
            
            QToolTip {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #505050;
                padding: 4px;
            }
            
            QStatusBar {
                background-color: #007acc;
                color: #ffffff;
            }
        """


def get_theme_display_name(theme: str) -> str:
    """获取主题的显示名称。"""
    names = {
        THEME_LIGHT: "明亮",
        THEME_DARK: "暗黑",
        THEME_SYSTEM: "跟随系统",
    }
    return names.get(theme, theme)
