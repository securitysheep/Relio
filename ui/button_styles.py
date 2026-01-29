"""统一的按钮样式定义。"""

from PySide6.QtWidgets import QPushButton, QToolButton, QComboBox, QApplication
from PySide6.QtGui import QPalette


def _is_dark_theme() -> bool:
    """检测当前是否为暗黑主题。"""
    app = QApplication.instance()
    if app:
        palette = app.palette()
        window_color = palette.color(QPalette.Window)
        return window_color.lightness() < 128
    return False


# ============ QPushButton 样式 ============

def apply_primary_style(btn: QPushButton, width: int = 90) -> None:
    """主要按钮样式（绿色，用于保存/确认/发送等主要操作）"""
    btn.setFixedWidth(width)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #28a745;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #218838;
        }
        QPushButton:pressed {
            background-color: #1e7e34;
        }
        QPushButton:disabled {
            background-color: #94d3a2;
        }
    """)


def apply_secondary_style(btn: QPushButton, width: int = 90) -> None:
    """次要按钮样式（灰色，用于取消/关闭）"""
    btn.setFixedWidth(width)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #6c757d;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #5a6268;
        }
        QPushButton:pressed {
            background-color: #545b62;
        }
        QPushButton:disabled {
            background-color: #a8adb3;
        }
    """)


def apply_warning_style(btn: QPushButton, width: int = 90) -> None:
    """警告按钮样式（橙色，用于重置/恢复默认）"""
    btn.setFixedWidth(width)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #fd7e14;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #e96b02;
        }
        QPushButton:pressed {
            background-color: #d45d00;
        }
        QPushButton:disabled {
            background-color: #feb573;
        }
    """)


def apply_info_style(btn: QPushButton, width: int = 90) -> None:
    """信息按钮样式（蓝色，用于测试连接/AI操作等）"""
    btn.setFixedWidth(width)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #17a2b8;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #138496;
        }
        QPushButton:pressed {
            background-color: #117a8b;
        }
        QPushButton:disabled {
            background-color: #6dcad9;
        }
    """)


def apply_danger_style(btn: QPushButton, width: int = 90) -> None:
    """危险按钮样式（红色，用于删除/关闭等）"""
    btn.setFixedWidth(width)
    btn.setStyleSheet("""
        QPushButton {
            background-color: #dc3545;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #c82333;
        }
        QPushButton:pressed {
            background-color: #bd2130;
        }
        QPushButton:disabled {
            background-color: #e97983;
        }
    """)


# ============ QToolButton 样式 ============

def apply_toolbar_style(btn: QToolButton) -> None:
    """工具栏按钮样式（⋯ 菜单按钮等）- 自动适配主题"""
    if _is_dark_theme():
        btn.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 14px;
                color: #e0e0e0;
            }
            QToolButton:hover {
                background-color: #3c3c3c;
                border-color: #666;
            }
            QToolButton:pressed {
                background-color: #4a4a4a;
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)
    else:
        btn.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 14px;
                color: #555;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
                border-color: #aaa;
            }
            QToolButton:pressed {
                background-color: #e0e0e0;
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)


def apply_icon_button_style(btn: QToolButton, size: int = 28) -> None:
    """图标按钮样式（复制/喜欢/不喜欢等小按钮）"""
    btn.setFixedSize(size, size)
    btn.setStyleSheet("""
        QToolButton {
            margin: 0px;
            padding: 0px;
            border: none;
            border-radius: 4px;
            background: transparent;
            font-size: 14px;
        }
        QToolButton:hover {
            background: #e8e8e8;
        }
        QToolButton:pressed {
            background: #d0d0d0;
        }
    """)


def apply_icon_button_active_style(btn: QToolButton, size: int = 28) -> None:
    """图标按钮激活样式（已选中状态）"""
    btn.setFixedSize(size, size)
    btn.setStyleSheet("""
        QToolButton {
            margin: 0px;
            padding: 0px;
            border: none;
            border-radius: 4px;
            background: #d0e4ff;
            font-size: 14px;
        }
        QToolButton:hover {
            background: #b8d4ff;
        }
        QToolButton:pressed {
            background: #a0c4ff;
        }
    """)


# ============ QMenu 样式 ============

def get_menu_style() -> str:
    """获取下拉菜单样式 - 自动适配主题"""
    if _is_dark_theme():
        return """
            QMenu {
                background-color: #2d2d30;
                border: 1px solid #505050;
                border-radius: 6px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 8px 20px;
                color: #e0e0e0;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #3e3e42;
                color: #ffffff;
            }
            QMenu::item:pressed {
                background-color: #094771;
            }
            QMenu::separator {
                height: 1px;
                background: #505050;
                margin: 4px 8px;
            }
        """
    else:
        return """
            QMenu {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 8px 20px;
                color: #333;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #f0f7ff;
                color: #1a73e8;
            }
            QMenu::item:pressed {
                background-color: #e3effd;
            }
            QMenu::separator {
                height: 1px;
                background: #eee;
                margin: 4px 8px;
            }
        """


# ============ QComboBox 样式 ============

def _get_assets_path() -> str:
    """获取 assets 目录的路径"""
    import sys
    from pathlib import Path
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        base_path = Path(sys._MEIPASS)
    else:
        # 开发模式
        base_path = Path(__file__).parent.parent
    return str(base_path / "assets").replace("\\", "/")


def apply_combobox_style(combo: QComboBox) -> None:
    """下拉框样式 - 自动适配主题，带清晰的向下箭头 SVG"""
    assets_path = _get_assets_path()
    
    if _is_dark_theme():
        arrow_svg = f"{assets_path}/arrow-down-dark.svg"
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 6px 12px;
                padding-right: 30px;
                font-size: 13px;
                min-height: 20px;
            }}
            QComboBox:hover {{
                border-color: #666;
                background-color: #454545;
            }}
            QComboBox:focus {{
                border-color: #0078d4;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 24px;
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                image: url({arrow_svg});
                width: 10px;
                height: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #2d2d30;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 2px;
                selection-background-color: #094771;
                selection-color: #ffffff;
                outline: none;
                margin: 0px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 12px;
                min-height: 24px;
                color: #e0e0e0;
                border: none;
                background: transparent;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: #3e3e42;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: #094771;
            }}
        """)
    else:
        arrow_svg = f"{assets_path}/arrow-down-light.svg"
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #c0c0c0;
                border-radius: 6px;
                padding: 6px 12px;
                padding-right: 30px;
                font-size: 13px;
                min-height: 20px;
            }}
            QComboBox:hover {{
                border-color: #a0a0a0;
                background-color: #fafafa;
            }}
            QComboBox:focus {{
                border-color: #0078d4;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 24px;
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                image: url({arrow_svg});
                width: 10px;
                height: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 2px;
                selection-background-color: #e3effd;
                selection-color: #1a73e8;
                outline: none;
                margin: 0px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 12px;
                min-height: 24px;
                color: #333333;
                border: none;
                background: transparent;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: #f0f7ff;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: #e3effd;
            }}
        """)


def get_combobox_style() -> str:
    """获取下拉框样式字符串 - 自动适配主题"""
    if _is_dark_theme():
        return """
            QComboBox {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 6px 12px;
                padding-right: 30px;
                font-size: 13px;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #666;
                background-color: #454545;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 28px;
                border-left: 1px solid #555;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: #454545;
            }
            QComboBox::drop-down:hover {
                background-color: #505050;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #b0b0b0;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #e0e0e0;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d30;
                border: 1px solid #505050;
                border-radius: 6px;
                padding: 4px;
                selection-background-color: #094771;
                selection-color: #ffffff;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 12px;
                min-height: 24px;
                color: #e0e0e0;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #3e3e42;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #094771;
            }
        """
    else:
        return """
            QComboBox {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #c0c0c0;
                border-radius: 6px;
                padding: 6px 12px;
                padding-right: 30px;
                font-size: 13px;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #a0a0a0;
                background-color: #fafafa;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 28px;
                border-left: 1px solid #c0c0c0;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: #f5f5f5;
            }
            QComboBox::drop-down:hover {
                background-color: #e8e8e8;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #666666;
            }
            QComboBox::down-arrow:hover {
                border-top-color: #333333;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 4px;
                selection-background-color: #e3effd;
                selection-color: #1a73e8;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 12px;
                min-height: 24px;
                color: #333333;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #f0f7ff;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #e3effd;
            }
        """
