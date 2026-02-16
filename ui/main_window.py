"""主窗口界面：关系对象列表 + 功能模块切换。"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Optional, List

from PySide6.QtCore import Qt, QSize, Signal, QTimer, QThread
from PySide6.QtGui import QAction, QPixmap, QPalette, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QTabBar,
    QTextEdit,
    QToolButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# matplotlib 嵌入 PySide6
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

from core.system import DialogueDecisionSystem
from core.user_profile import ContactType
from core.memory_extractor import MemoryExtractor
from core.intimacy_manager import IntimacyManager
from .dialogs import (
    PersonDialog, ProfileMemoryDialog, ExperienceMemoryDialog, StrategyMemoryDialog,
    MemoryExtractionDialog, DuplicateMemoryDialog, StrategyMergeDialog,
)
from .store import AppStore, Person, MemoryItem
from .button_styles import (
    apply_primary_style,
    apply_secondary_style,
    apply_info_style,
    apply_toolbar_style,
    apply_icon_button_style,
    apply_icon_button_active_style,
    get_menu_style,
)


RELATIONSHIP_TO_CONTACT = {
    "家人": ContactType.FAMILY,
    "朋友": ContactType.FRIEND,
    "同事": ContactType.COLLEAGUE,
    "领导": ContactType.COLLEAGUE,
    "暧昧": ContactType.OTHER,
    "恋人": ContactType.OTHER,
    "客户": ContactType.OTHER,
}


class PersonItemWidget(QWidget):
    """关系对象列表项。"""

    def __init__(self, person: Person, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.person = person
        self._hovered = False
        self._selected = False

        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.avatar = QLabel()
        self.avatar.setFixedSize(36, 36)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setStyleSheet("background:#f0f0f0;border-radius:6px;")
        if person.avatar_path and os.path.exists(person.avatar_path):
            pixmap = QPixmap(person.avatar_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    36, 36, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
                cropped = self._center_crop(scaled, 36, 36)
                self.avatar.setPixmap(self._rounded_pixmap(cropped, 6))
        else:
            self.avatar.setText("👤")

        self.name_label = QLabel(person.display_name)
        self.name_label.setStyleSheet("font-weight:600;")
        self.meta_label = QLabel(
            f"{person.relationship_type} · 亲密度 {person.intimacy}%"
        )
        self.meta_label.setStyleSheet("color:#666;")

        tags = ", ".join(person.style_tags) if person.style_tags else "-"
        self.tag_label = QLabel(tags)
        self.tag_label.setStyleSheet("color:#999;")

        text_layout = QVBoxLayout()
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.meta_label)
        text_layout.addWidget(self.tag_label)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self.avatar)
        layout.addLayout(text_layout)

        self._update_style()

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._update_style()

    def enterEvent(self, event) -> None:
        self._hovered = True
        self._update_style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self._update_style()
        super().leaveEvent(event)

    def _update_style(self) -> None:
        is_dark = self._is_dark_theme()
        if is_dark:
            if self._selected:
                bg = "#37373d"
                name_color = "#ffffff"
                meta_color = "#d0d0d0"
                tag_color = "#b0b0b0"
            elif self._hovered:
                bg = "#2a2d2e"
                name_color = "#f2f2f2"
                meta_color = "#c8c8c8"
                tag_color = "#a8a8a8"
            else:
                bg = "transparent"
                name_color = "#f2f2f2"
                meta_color = "#c8c8c8"
                tag_color = "#a8a8a8"
        else:
            if self._selected:
                bg = "#eaeaea"
                name_color = "#1f1f1f"
                meta_color = "#555"
                tag_color = "#777"
            elif self._hovered:
                bg = "#efefef"
                name_color = "#2a2a2a"
                meta_color = "#5f5f5f"
                tag_color = "#7f7f7f"
            else:
                bg = "transparent"
                name_color = "#2f2f2f"
                meta_color = "#6b6b6b"
                tag_color = "#8a8a8a"

        self.setStyleSheet(f"PersonItemWidget {{ background-color:{bg}; border-radius:6px; }}")
        self.name_label.setStyleSheet(f"font-weight:600;color:{name_color};background:transparent;")
        self.meta_label.setStyleSheet(f"color:{meta_color};background:transparent;")
        self.tag_label.setStyleSheet(f"color:{tag_color};background:transparent;")

    def update_intimacy(self, intimacy: int) -> None:
        """更新亲密度显示。"""
        self.person.intimacy = intimacy
        self.meta_label.setText(f"{self.person.relationship_type} · 亲密度 {intimacy}%")

    @staticmethod
    def _center_crop(pixmap: QPixmap, target_w: int, target_h: int) -> QPixmap:
        width = pixmap.width()
        height = pixmap.height()
        if width <= target_w and height <= target_h:
            return pixmap
        x = max(0, (width - target_w) // 2)
        y = max(0, (height - target_h) // 2)
        return pixmap.copy(x, y, target_w, target_h)

    @staticmethod
    def _rounded_pixmap(pixmap: QPixmap, radius: int) -> QPixmap:
        target = QPixmap(pixmap.size())
        target.fill(Qt.transparent)
        painter = QPainter(target)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        return target

    def _is_dark_theme(self) -> bool:
        app = QApplication.instance()
        palette = app.palette() if app else self.palette()
        window_color = palette.color(QPalette.Window)
        return window_color.lightness() < 128


class MemoryCardWidget(QWidget):
    """记忆卡片组件 - 显示单条记忆，支持编辑和删除。"""
    
    edit_clicked = Signal(str, str)  # memory_id, memory_type
    delete_clicked = Signal(str, str)  # memory_id, memory_type
    
    def __init__(
        self, 
        memory_id: str, 
        memory_type: str,  # "profile", "experience", "strategy"
        title: str,
        subtitle: str,
        badge_text: str,
        badge_color: str = "#4a90d9",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.memory_id = memory_id
        self.memory_type = memory_type
        
        self.setMinimumHeight(70)
        self.setCursor(Qt.PointingHandCursor)
        
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # 左侧徽章
        badge_label = QLabel(badge_text)
        badge_label.setFixedWidth(60)
        badge_label.setAlignment(Qt.AlignCenter)
        badge_label.setStyleSheet(f"""
            background-color: {badge_color};
            color: white;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 12px;
            font-weight: bold;
        """)
        
        # 中间内容区
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("font-size: 12px; color: #888;")
        
        content_layout.addWidget(title_label)
        content_layout.addWidget(subtitle_label)
        
        # 右侧按钮区
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setToolTip("编辑")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #f5f5f5;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.memory_id, self.memory_type))
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setToolTip("删除")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #f5f5f5;
            }
            QPushButton:hover {
                background: #ffdddd;
            }
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.memory_id, self.memory_type))
        
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        
        layout.addWidget(badge_label)
        layout.addLayout(content_layout, 1)
        layout.addLayout(btn_layout)
        
        # 卡片样式
        self._update_style()
    
    def _update_style(self):
        is_dark = self._is_dark_theme()
        if is_dark:
            self.setStyleSheet("""
                MemoryCardWidget {
                    background-color: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 8px;
                }
                MemoryCardWidget:hover {
                    background-color: #444;
                    border-color: #666;
                }
            """)
        else:
            self.setStyleSheet("""
                MemoryCardWidget {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                }
                MemoryCardWidget:hover {
                    background-color: #f8f8f8;
                    border-color: #ccc;
                }
            """)
    
    def _is_dark_theme(self) -> bool:
        app = QApplication.instance()
        palette = app.palette() if app else self.palette()
        window_color = palette.color(QPalette.Window)
        return window_color.lightness() < 128


class IntimacyTrendChart(FigureCanvas):
    """亲密度变化趋势折线图组件（使用相对时间）。"""
    
    # 中文字体配置
    CHINESE_FONTS = [
        'PingFang SC',           # macOS
        'Heiti SC',              # macOS
        'STHeiti',               # macOS
        'Hiragino Sans GB',      # macOS
        'Microsoft YaHei',       # Windows
        'SimHei',                # Windows
        'WenQuanYi Micro Hei',   # Linux
        'Noto Sans CJK SC',      # Linux
        'sans-serif'             # 后备
    ]
    
    # 时间单位配置：(秒数阈值, 除数, 单位名称)
    TIME_UNITS = [
        (60, 1, '秒'),                    # < 1分钟
        (3600, 60, '分钟'),               # < 1小时
        (86400, 3600, '小时'),            # < 1天
        (604800, 86400, '天'),            # < 1周
        (2592000, 604800, '周'),          # < 30天
        (31536000, 2592000, '月'),        # < 1年
        (float('inf'), 31536000, '年'),   # >= 1年
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        # 创建 Figure 和 Axes
        self.fig = Figure(figsize=(5, 2.2), dpi=100, facecolor='none')
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.setMinimumHeight(160)
        self.setMaximumHeight(200)
        
        # 设置透明背景
        self.fig.patch.set_alpha(0)
        self.ax.patch.set_alpha(0.05)
        
        # 配置中文字体
        self._setup_chinese_font()
        
        # 禁用 FigureCanvas 的滚轮事件，让父容器处理滚动
        self.setFocusPolicy(Qt.NoFocus)
        
        # 初始化空图表
        self._setup_style()
        self._draw_empty()

    def wheelEvent(self, event):
        """将滚轮事件传递给父容器，解决滚动失灵问题。"""
        event.ignore()

    def _setup_chinese_font(self) -> None:
        """配置中文字体支持。"""
        import matplotlib.font_manager as fm
        
        # 尝试找到可用的中文字体
        available_fonts = set(f.name for f in fm.fontManager.ttflist)
        selected_font = None
        
        for font_name in self.CHINESE_FONTS:
            if font_name in available_fonts:
                selected_font = font_name
                break
        
        if selected_font:
            plt.rcParams['font.family'] = selected_font
            plt.rcParams['font.sans-serif'] = [selected_font] + self.CHINESE_FONTS
        else:
            # 使用 sans-serif 并添加中文字体列表
            plt.rcParams['font.sans-serif'] = self.CHINESE_FONTS
        
        # 解决负号显示问题
        plt.rcParams['axes.unicode_minus'] = False

    def _setup_style(self, x_unit: str = '') -> None:
        """设置图表样式。"""
        # 使用现代配色
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#cccccc')
        self.ax.spines['bottom'].set_color('#cccccc')
        self.ax.tick_params(colors='#666666', labelsize=8)
        self.ax.set_ylabel('亲密度 (%)', fontsize=9, color='#666666')
        if x_unit:
            self.ax.set_xlabel(f'相对时间 ({x_unit})', fontsize=9, color='#666666')
        self.ax.set_ylim(0, 105)
        self.ax.grid(True, linestyle='--', alpha=0.3, color='#999999')

    def _draw_empty(self) -> None:
        """绘制空状态提示。"""
        self.ax.clear()
        self._setup_style()
        self.ax.text(0.5, 0.5, '暂无趋势数据', 
                     transform=self.ax.transAxes,
                     ha='center', va='center', 
                     fontsize=11, color='#999999')
        self.fig.tight_layout(pad=1.5)
        self.draw()

    def _select_time_unit(self, max_seconds: float) -> tuple:
        """
        根据最大时间跨度选择合适的时间单位。
        
        返回：(除数, 单位名称)
        """
        for threshold, divisor, unit_name in self.TIME_UNITS:
            if max_seconds < threshold:
                return divisor, unit_name
        return self.TIME_UNITS[-1][1], self.TIME_UNITS[-1][2]

    def _calculate_nice_ticks(self, max_value: float, num_ticks: int = 5) -> List[float]:
        """
        计算规范化的刻度值（整数或简单小数）。
        
        策略：选择 1, 2, 5, 10, 20, 50... 等规整数值作为刻度间隔
        """
        if max_value <= 0:
            return [0]
        
        # 计算合适的刻度间隔
        raw_interval = max_value / num_ticks
        
        # 规范化间隔值
        magnitude = 10 ** int(np.floor(np.log10(raw_interval))) if raw_interval > 0 else 1
        normalized = raw_interval / magnitude
        
        # 选择规整的间隔
        if normalized <= 1:
            nice_interval = 1 * magnitude
        elif normalized <= 2:
            nice_interval = 2 * magnitude
        elif normalized <= 5:
            nice_interval = 5 * magnitude
        else:
            nice_interval = 10 * magnitude
        
        # 生成刻度值
        ticks = []
        current = 0
        while current <= max_value * 1.1:  # 稍微超出一点
            ticks.append(current)
            current += nice_interval
        
        return ticks

    def update_data(self, history: List[dict]) -> None:
        """
        更新折线图数据。
        
        横坐标使用相对时间：
        - 第一个数据点位于 x=0
        - 后续数据点显示相对于第一个数据点的时间差
        - 时间单位根据数据跨度动态选择（分钟/小时/天/周/月/年）
        """
        self.ax.clear()
        
        if not history or len(history) < 1:
            self._setup_style()
            self._draw_empty()
            return
        
        # 解析时间戳和亲密度值
        timestamps = []
        values = []
        for item in history[-15:]:  # 最多显示最近15条记录
            try:
                ts = item.get('timestamp', '')
                if ts:
                    # 支持多种时间格式
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                        try:
                            dt = datetime.strptime(ts, fmt)
                            timestamps.append(dt)
                            values.append(item.get('intimacy_score', 50))
                            break
                        except ValueError:
                            continue
            except Exception:
                continue
        
        if len(timestamps) < 1:
            self._setup_style()
            self._draw_empty()
            return
        
        # 计算相对时间（以第一个时间点为基准，单位：秒）
        base_time = timestamps[0]
        relative_seconds = [(t - base_time).total_seconds() for t in timestamps]
        
        # 根据最大时间跨度选择合适的单位
        max_seconds = max(relative_seconds) if len(relative_seconds) > 1 else 0
        divisor, unit_name = self._select_time_unit(max_seconds)
        
        # 转换为选定单位
        relative_times = [s / divisor for s in relative_seconds]
        max_relative = max(relative_times) if relative_times else 0
        
        # 设置样式（包含X轴单位标签）
        self._setup_style(x_unit=unit_name)
        
        # 绘制折线图
        line_color = '#4A90D9'
        fill_color = '#4A90D9'
        
        # 绘制填充区域
        self.ax.fill_between(relative_times, values, alpha=0.15, color=fill_color)
        
        # 绘制折线
        self.ax.plot(relative_times, values, color=line_color, linewidth=2, 
                     marker='o', markersize=5, markerfacecolor='white',
                     markeredgecolor=line_color, markeredgewidth=2)
        
        # 确定需要标注的关键点：起始值、终止值、最高值、最低值
        # 使用字典记录要标注的点，避免重复（相同位置只标注一次）
        key_points = {}  # {index: [labels]}
        
        n = len(values)
        start_idx = 0
        end_idx = n - 1
        max_val = max(values)
        min_val = min(values)
        max_idx = values.index(max_val)
        min_idx = values.index(min_val)
        
        # 收集各关键点的标签
        def add_label(idx: int, label: str):
            if idx not in key_points:
                key_points[idx] = []
            key_points[idx].append(label)
        
        add_label(start_idx, "起始")
        add_label(end_idx, "终止")
        add_label(max_idx, "最高")
        add_label(min_idx, "最低")
        
        # 绘制标注，合并相同位置的标签
        for idx, labels in key_points.items():
            t = relative_times[idx]
            v = values[idx]
            # 合并标签，去重（如果起始和最高是同一点）
            unique_labels = list(dict.fromkeys(labels))  # 保持顺序去重
            label_text = "/".join(unique_labels)
            annotation = f'{label_text}: {v}%'
            
            # 调整标注位置，避免重叠
            y_offset = 10
            if v == max_val:
                y_offset = 12  # 最高点往上
            elif v == min_val:
                y_offset = -15  # 最低点往下
            
            self.ax.annotate(annotation, (t, v), textcoords='offset points',
                            xytext=(0, y_offset), ha='center', fontsize=8, color='#333333',
                            fontweight='bold')
        
        # 设置 X 轴范围和刻度
        if max_relative > 0:
            # 添加5%边距
            margin = max(max_relative * 0.05, 0.1)
            self.ax.set_xlim(-margin, max_relative + margin)
            
            # 计算规范化刻度
            nice_ticks = self._calculate_nice_ticks(max_relative)
            self.ax.set_xticks(nice_ticks)
            
            # 格式化刻度标签（整数或一位小数）
            tick_labels = []
            for tick in nice_ticks:
                if tick == int(tick):
                    tick_labels.append(str(int(tick)))
                else:
                    tick_labels.append(f'{tick:.1f}')
            self.ax.set_xticklabels(tick_labels)
        else:
            # 单个数据点
            self.ax.set_xlim(-0.5, 0.5)
            self.ax.set_xticks([0])
            self.ax.set_xticklabels(['0'])
        
        # 动态调整 Y 轴范围
        min_val = max(0, min(values) - 10)
        max_val = min(100, max(values) + 10)
        self.ax.set_ylim(min_val, max_val + 5)
        
        self.fig.tight_layout(pad=1.5)
        self.draw()


class MessageGenerationWorker(QThread):
    """后台线程：处理消息生成，避免阻塞主线程。"""
    
    finished = Signal(dict)  # 成功时发送结果
    error = Signal(str)      # 失败时发送错误信息
    
    def __init__(self, system, person_id: str, person_name: str, 
                 composed_message: str, contact_type):
        super().__init__()
        self._system = system
        self._person_id = person_id
        self._person_name = person_name
        self._composed_message = composed_message
        self._contact_type = contact_type
    
    def run(self):
        try:
            result = self._system.process_message(
                contact_id=self._person_id,
                contact_name=self._person_name,
                message_content=self._composed_message,
                contact_type=self._contact_type,
            )
            self._system.save()
            self.finished.emit(result)
        except Exception as err:
            self.error.emit(str(err))


class TypingIndicatorWidget(QWidget):
    """等待输入指示器：三个渐变的点动画，颜色从左到右丝滑循环变化。"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._dots = []
        self._animation_step = 0  # 0-29，用于平滑过渡
        self._base_opacity = [0.3, 0.3, 0.3]  # 三个点的透明度
        
        # 创建布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(6, 2, 6, 2)
        
        # 左对齐（AI消息在左边）
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 气泡容器
        self.bubble = QWidget()
        bubble_layout = QHBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(14, 12, 14, 12)
        bubble_layout.setSpacing(8)
        
        # 创建三个点
        for i in range(3):
            dot = QLabel("●")
            dot.setStyleSheet("color: rgba(128, 128, 128, 0.3); font-size: 12px;")
            self._dots.append(dot)
            bubble_layout.addWidget(dot)
        
        self._update_bubble_style()
        
        content_layout.addWidget(self.bubble)
        main_layout.addLayout(content_layout)
        main_layout.addStretch()
        
        # 动画定时器 - 更快的更新频率实现丝滑效果
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._animate_dots)
        self._animation_timer.start(50)  # 每50ms更新一次，实现丝滑效果
    
    def _update_bubble_style(self) -> None:
        is_dark = self._is_dark_theme()
        if is_dark:
            bg_color = "#303030"
        else:
            bg_color = "#f6f6f6"
        self.bubble.setStyleSheet(
            f"background: {bg_color}; border-radius: 10px;"
        )
    
    def _animate_dots(self) -> None:
        """动画：三个点的颜色从左到右丝滑循环变化。"""
        is_dark = self._is_dark_theme()
        
        # 使用正弦波实现丝滑的亮度变化
        # 每个点的相位偏移 120 度（2π/3）
        import math
        
        for i, dot in enumerate(self._dots):
            # 计算该点的相位（每个点相差 2π/3）
            phase = (self._animation_step / 30.0) * 2 * math.pi - i * (2 * math.pi / 3)
            # 正弦值映射到 0.3 ~ 1.0 的透明度范围
            opacity = 0.3 + 0.7 * (math.sin(phase) + 1) / 2
            
            if is_dark:
                # 深色主题：灰色到白色
                gray_value = int(100 + 155 * opacity)  # 100-255
                color = f"rgb({gray_value}, {gray_value}, {gray_value})"
            else:
                # 浅色主题：浅灰到深灰
                gray_value = int(180 - 130 * opacity)  # 180-50
                color = f"rgb({gray_value}, {gray_value}, {gray_value})"
            
            dot.setStyleSheet(f"color: {color}; font-size: 14px;")
        
        # 更新动画步骤
        self._animation_step = (self._animation_step + 1) % 30
    
    def _is_dark_theme(self) -> bool:
        app = QApplication.instance()
        palette = app.palette() if app else self.palette()
        window_color = palette.color(QPalette.Window)
        return window_color.lightness() < 128
    
    def stop_animation(self) -> None:
        """停止动画。"""
        self._animation_timer.stop()


class ChatMessageWidget(QWidget):
    """会话消息气泡。"""
    
    # 定义反馈信号：参数为 (message_id, feedback_type)
    # feedback_type: "like" | "dislike" | None
    feedback_changed = Signal(str, str)

    def __init__(self, role: str, text: str, message_id: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.role = role
        self.text = text
        self.message_id = message_id
        self._bubble_padding = 28  # 左右 padding 12px * 2 + 额外边距
        self._feedback_state: Optional[str] = None  # "like" | "dislike" | None

        self.bubble = QLabel(text)
        self.bubble.setWordWrap(True)
        self.bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.bubble.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        self.btn_copy = None
        self.btn_like = None
        self.btn_dislike = None
        
        if role == "assistant":
            # 复制按钮
            self.btn_copy = QToolButton()
            self.btn_copy.setText("📋")
            self.btn_copy.setToolTip("复制")
            self.btn_copy.setCursor(Qt.PointingHandCursor)
            apply_icon_button_style(self.btn_copy, 28)
            self.btn_copy.clicked.connect(self._copy_text)
            
            # 喜欢按钮
            self.btn_like = QToolButton()
            self.btn_like.setText("👍")
            self.btn_like.setToolTip("喜欢这个回复")
            self.btn_like.setCursor(Qt.PointingHandCursor)
            self.btn_like.setCheckable(True)
            apply_icon_button_style(self.btn_like, 28)
            self.btn_like.clicked.connect(self._on_like_clicked)
            
            # 不喜欢按钮
            self.btn_dislike = QToolButton()
            self.btn_dislike.setText("👎")
            self.btn_dislike.setToolTip("不喜欢这个回复")
            self.btn_dislike.setCursor(Qt.PointingHandCursor)
            self.btn_dislike.setCheckable(True)
            apply_icon_button_style(self.btn_dislike, 28)
            self.btn_dislike.clicked.connect(self._on_dislike_clicked)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self.bubble)
        if self.btn_copy:
            btn_row = QHBoxLayout()
            btn_row.setContentsMargins(0, 2, 0, 0)
            btn_row.setSpacing(0)  # 无外边距
            btn_row.addWidget(self.btn_copy, 0, Qt.AlignLeft)
            btn_row.addWidget(self.btn_like, 0, Qt.AlignLeft)
            btn_row.addWidget(self.btn_dislike, 0, Qt.AlignLeft)
            btn_row.addStretch()
            content_layout.addLayout(btn_row)

        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        content_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        layout = QHBoxLayout(self)
        if role == "user":
            layout.addStretch()
            layout.addWidget(content_widget)
        else:
            layout.addWidget(content_widget)
            layout.addStretch()
        layout.setContentsMargins(6, 2, 6, 2)

        self._update_style()
    
    def set_feedback_state(self, state: Optional[str]) -> None:
        """设置反馈状态（用于恢复历史状态）。"""
        self._feedback_state = state
        if self.btn_like and self.btn_dislike:
            self.btn_like.setChecked(state == "like")
            self.btn_dislike.setChecked(state == "dislike")
            self._update_feedback_buttons_visibility()
    
    def _update_feedback_buttons_visibility(self) -> None:
        """更新反馈按钮的可见性和样式。"""
        if not self.btn_like or not self.btn_dislike:
            return
        
        if self._feedback_state == "like":
            # 选择了喜欢：隐藏不喜欢按钮
            self.btn_like.setVisible(True)
            apply_icon_button_active_style(self.btn_like, 28)
            self.btn_dislike.setVisible(False)
        elif self._feedback_state == "dislike":
            # 选择了不喜欢：隐藏喜欢按钮
            self.btn_like.setVisible(False)
            self.btn_dislike.setVisible(True)
            apply_icon_button_active_style(self.btn_dislike, 28)
        else:
            # 未选择：显示两个按钮
            self.btn_like.setVisible(True)
            self.btn_dislike.setVisible(True)
            apply_icon_button_style(self.btn_like, 28)
            apply_icon_button_style(self.btn_dislike, 28)
    
    def _on_like_clicked(self) -> None:
        """喜欢按钮点击处理。"""
        if self._feedback_state == "like":
            # 取消选择
            self._feedback_state = None
            self.btn_like.setChecked(False)
        else:
            # 选择喜欢，取消不喜欢
            self._feedback_state = "like"
            self.btn_like.setChecked(True)
            self.btn_dislike.setChecked(False)
        self._update_feedback_buttons_visibility()
        self.feedback_changed.emit(self.message_id, self._feedback_state or "")
    
    def _on_dislike_clicked(self) -> None:
        """不喜欢按钮点击处理。"""
        if self._feedback_state == "dislike":
            # 取消选择
            self._feedback_state = None
            self.btn_dislike.setChecked(False)
        else:
            # 选择不喜欢，取消喜欢
            self._feedback_state = "dislike"
            self.btn_dislike.setChecked(True)
            self.btn_like.setChecked(False)
        self._update_feedback_buttons_visibility()
        self.feedback_changed.emit(self.message_id, self._feedback_state or "")

    def set_max_width(self, max_width: int) -> None:
        if max_width <= 0:
            return
        raw_width = self._measure_text_width_raw()
        if raw_width <= max_width:
            self.bubble.setWordWrap(False)
            desired_width = max(1, raw_width)
        else:
            self.bubble.setWordWrap(True)
            desired_width = max_width
        self.bubble.setMaximumWidth(max_width)
        self.bubble.setFixedWidth(desired_width)
        self.bubble.updateGeometry()

    def _copy_text(self) -> None:
        QApplication.clipboard().setText(self.text)

    def _update_style(self) -> None:
        is_dark = self._is_dark_theme()
        if is_dark:
            bubble_bg = "#303030"
            text_color = "#f2f2f2"
        else:
            bubble_bg = "#e9f5ff" if self.role == "user" else "#f6f6f6"
            text_color = "#222"
        self.bubble.setStyleSheet(
            "padding:8px 12px;border-radius:8px;"
            + f"background:{bubble_bg};color:{text_color};"
        )

    def _measure_text_width_raw(self) -> int:
        lines = self.text.splitlines() or [self.text]
        fm = self.bubble.fontMetrics()
        longest = 0
        for line in lines:
            longest = max(longest, fm.horizontalAdvance(line))
        return longest + self._bubble_padding

    def _is_dark_theme(self) -> bool:
        app = QApplication.instance()
        palette = app.palette() if app else self.palette()
        window_color = palette.color(QPalette.Window)
        return window_color.lightness() < 128


class MessageInput(QTextEdit):
    send_requested = Signal()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)
            else:
                event.accept()
                self.send_requested.emit()
            return
        super().keyPressEvent(event)


class MainWindow(QMainWindow):
    """主窗口。"""

    def __init__(self, system: DialogueDecisionSystem):
        super().__init__()
        self._system = system
        self._store = AppStore()
        self._current_person_id: Optional[str] = None
        self._conversation_cache: dict[str, list[dict]] = {}
        # 跟踪正在进行的消息生成请求：{person_id: context}
        self._pending_requests: dict[str, dict] = {}
        # 当前显示的等待指示器
        self._current_typing_indicator: Optional[QListWidgetItem] = None
        # 对话轮次反馈状态跟踪: {person_id: {round_id: {"like_applied": bool, "dislike_applied": bool}}}
        self._feedback_round_state: dict[str, dict[str, dict]] = {}

        # 加载保存的亲密度权重设置
        from core.intimacy_manager import IntimacyManager
        IntimacyManager.load_saved_settings()

        self.setWindowTitle("对话回复决策系统")
        self.setMinimumSize(1200, 780)
        self.resize(1360, 820)
        
        # 将窗口居中显示
        self._center_on_screen()

        self._build_menu()
        self._build_status_bar()

        container = QWidget(self)
        self.setCentralWidget(container)
        main_layout = QHBoxLayout(container)

        self.left_panel = self._build_left_panel()
        self.right_panel = self._build_right_panel()

        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)

        self._store.load_from_data_dir(self._system.settings.data_dir)
        self._refresh_contact_list()

    # ---------------- Menu/Status ----------------

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("文件")
        import_action = QAction("导入关系数据", self)
        export_action = QAction("导出关系数据", self)
        import_action.triggered.connect(self._import_data)
        export_action.triggered.connect(self._export_data)
        file_menu.addAction(import_action)
        file_menu.addAction(export_action)

        settings_menu = self.menuBar().addMenu("设置")
        api_action = QAction("模型 API 配置", self)
        weight_action = QAction("亲密度计算权重设置", self)
        api_action.triggered.connect(self._show_api_settings)
        weight_action.triggered.connect(self._show_weight_settings)
        settings_menu.addAction(api_action)
        settings_menu.addAction(weight_action)
        
        # 主题切换子菜单
        settings_menu.addSeparator()
        theme_menu = settings_menu.addMenu("主题")
        
        from .theme_manager import ThemeManager, get_theme_display_name
        from core.config import THEME_LIGHT, THEME_DARK, THEME_SYSTEM
        
        theme_manager = ThemeManager.instance()
        current_theme = theme_manager.get_current_setting()
        
        # 创建主题动作组，确保只有一个选中
        self._theme_actions = {}
        for theme_value in (THEME_LIGHT, THEME_DARK, THEME_SYSTEM):
            action = QAction(get_theme_display_name(theme_value), self)
            action.setCheckable(True)
            action.setChecked(theme_value == current_theme)
            action.triggered.connect(lambda checked, t=theme_value: self._switch_theme(t))
            theme_menu.addAction(action)
            self._theme_actions[theme_value] = action

        help_menu = self.menuBar().addMenu("帮助")
        help_action = QAction("使用说明", self)
        algo_action = QAction("算法说明", self)
        help_action.triggered.connect(self._show_help)
        algo_action.triggered.connect(self._show_algorithm)
        help_menu.addAction(help_action)
        help_menu.addAction(algo_action)

    def _show_api_settings(self) -> None:
        """显示 API 设置对话框。"""
        from .settings_dialogs import APISettingsDialog
        from core.config import save_api_settings
        
        dialog = APISettingsDialog(self, self._system.settings)
        if dialog.exec() == QDialog.Accepted:
            settings_dict = dialog.get_settings()
            # 更新系统设置
            for key, value in settings_dict.items():
                if hasattr(self._system.settings, key):
                    setattr(self._system.settings, key, value)
            # 重新创建 LLM 客户端，使新的 API Key/URL 生效
            self._system.llm_client.refresh_client()
            # 持久化保存到文件
            if save_api_settings(self._system.settings):
                QMessageBox.information(self, "成功", "✅ API 设置已保存并生效（重启后仍有效）")
            else:
                QMessageBox.warning(self, "警告", "⚠️ 设置已生效，但保存到文件时出错")

    def _show_weight_settings(self) -> None:
        """显示亲密度权重设置对话框。"""
        from .settings_dialogs import IntimacyWeightSettingsDialog
        from core.intimacy_manager import IntimacyManager
        from core.config import save_intimacy_weight_settings
        
        dialog = IntimacyWeightSettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            settings_dict = dialog.get_settings()
            
            # 应用衰减率设置
            decay = settings_dict.get("decay", {})
            IntimacyManager.update_decay_rates(
                decay_7_14=decay.get("decay_7_14", 0.1),
                decay_14_30=decay.get("decay_14_30", 0.15),
                decay_30_90=decay.get("decay_30_90", 0.2),
                decay_90_plus=decay.get("decay_90_plus", 0.3),
            )
            
            # 应用增长权重设置
            growth = settings_dict.get("growth", {})
            IntimacyManager.update_growth_weights(
                like_weight=growth.get("like_weight", 2),
                dislike_weight=growth.get("dislike_weight", 1),
                acceptance_delta=growth.get("acceptance_delta", 0.05),
                rejection_delta=growth.get("rejection_delta", 0.05),
            )
            
            # 应用初始亲密度设置
            base_intimacy = settings_dict.get("base_intimacy", {})
            IntimacyManager.update_base_intimacy(base_intimacy)
            
            # 持久化保存到文件
            if save_intimacy_weight_settings(decay, growth, base_intimacy):
                QMessageBox.information(self, "成功", "✅ 权重设置已保存并生效（重启后仍有效）")
            else:
                QMessageBox.warning(self, "警告", "⚠️ 设置已生效，但保存到文件时出错")

    def _switch_theme(self, theme: str) -> None:
        """切换应用主题。"""
        from .theme_manager import ThemeManager, get_theme_display_name
        from core.config import THEME_LIGHT, THEME_DARK, THEME_SYSTEM
        
        theme_manager = ThemeManager.instance()
        if theme_manager.set_theme(theme):
            # 更新菜单中的选中状态
            for t, action in self._theme_actions.items():
                action.setChecked(t == theme)
            
            # 刷新联系人列表以更新样式
            self._refresh_contact_list()
            
            # 刷新工具栏按钮和菜单样式
            apply_toolbar_style(self.module_menu_btn)
            self.module_menu.setStyleSheet(get_menu_style())
            
            theme_name = get_theme_display_name(theme)
            self.statusBar().showMessage(f"✅ 已切换至 {theme_name} 主题", 3000)

    def _show_help(self) -> None:
        """显示使用说明。"""
        from .settings_dialogs import HelpDialog
        dialog = HelpDialog(self)
        dialog.exec()

    def _show_algorithm(self) -> None:
        """显示算法说明。"""
        from .settings_dialogs import AlgorithmDialog
        dialog = AlgorithmDialog(self)
        dialog.exec()

    def _build_status_bar(self) -> None:
        self.status_contact = QLabel("当前对象：-")
        self.status_model = QLabel("模型状态：待命")
        self.status_time = QLabel("最近生成：-")
        self.statusBar().addWidget(self.status_contact)
        self.statusBar().addWidget(self.status_model)
        self.statusBar().addPermanentWidget(self.status_time)

    # ---------------- Left Panel ----------------

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(280)
        layout = QVBoxLayout(panel)

        top_row = QHBoxLayout()
        self.btn_add_person = QPushButton("添加对象")
        apply_primary_style(self.btn_add_person, width=100)
        self.btn_add_person.clicked.connect(self._on_add_person)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索对象（姓名/标签）")
        self.search_input.textChanged.connect(self._refresh_contact_list)

        top_row.addWidget(self.btn_add_person)
        layout.addLayout(top_row)
        layout.addWidget(self.search_input)

        self.contact_list = QListWidget()
        self.contact_list.setSpacing(0)
        self.contact_list.setFocusPolicy(Qt.NoFocus)
        self.contact_list.setStyleSheet(
            "QListWidget::item { border: none; margin: 0px; padding: 0px; }"
            "QListWidget::item:selected { background: transparent; outline: none; }"
        )
        self.contact_list.setMouseTracking(True)
        self.contact_list.itemSelectionChanged.connect(self._on_person_selected)
        self.contact_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.contact_list.customContextMenuRequested.connect(self._show_person_context_menu)

        layout.addWidget(self.contact_list)
        return panel

    def _refresh_contact_list(self) -> None:
        keyword = self.search_input.text().strip()
        
        # 保存当前选中的对象ID
        current_id = self._current_person_id
        
        self.contact_list.clear()

        for person in self._store.list_people():
            if keyword:
                haystack = f"{person.name} {' '.join(person.style_tags)}"
                if keyword not in haystack:
                    continue
            item = QListWidgetItem()
            item.setData(Qt.UserRole, person.person_id)
            item.setSizeHint(QSize(220, 70))
            widget = PersonItemWidget(person)
            self.contact_list.addItem(item)
            self.contact_list.setItemWidget(item, widget)

        # 恢复之前选中的对象
        if current_id:
            for idx in range(self.contact_list.count()):
                item = self.contact_list.item(idx)
                if item.data(Qt.UserRole) == current_id:
                    self.contact_list.setCurrentRow(idx)
                    break
        elif self.contact_list.count() > 0:
            self.contact_list.setCurrentRow(0)
        
        self._apply_person_item_styles()

    def _update_contact_item_intimacy(self, person_id: str, intimacy: int) -> None:
        """更新左侧联系人列表中指定对象的亲密度显示。"""
        for idx in range(self.contact_list.count()):
            item = self.contact_list.item(idx)
            if item.data(Qt.UserRole) == person_id:
                widget = self.contact_list.itemWidget(item)
                if isinstance(widget, PersonItemWidget):
                    widget.update_intimacy(intimacy)
                break

    def _on_person_selected(self) -> None:
        items = self.contact_list.selectedItems()
        if not items:
            return
        person_id = items[0].data(Qt.UserRole)
        self._current_person_id = person_id
        person = self._store.people.get(person_id)
        if not person:
            return
        self.status_contact.setText(f"当前对象：{person.display_name}")
        self._render_conversation(person_id)
        
        # 如果该联系人有正在进行的请求，重新显示等待动画
        if person_id in self._pending_requests:
            self._current_typing_indicator = self._show_typing_indicator(person_id)
        
        self._update_profile_panel(person)
        self._update_memory_panel(person)
        self._apply_person_item_styles()

    def _show_person_context_menu(self, pos) -> None:
        item = self.contact_list.itemAt(pos)
        if not item:
            return
        person_id = item.data(Qt.UserRole)
        menu = QMenu(self)
        edit_action = menu.addAction("编辑对象")
        delete_action = menu.addAction("删除对象")
        pin_action = menu.addAction("置顶对象")
        action = menu.exec(self.contact_list.mapToGlobal(pos))
        if action == edit_action:
            self._on_edit_person(person_id)
        elif action == delete_action:
            self._on_delete_person(person_id)
        elif action == pin_action:
            self._on_pin_person(person_id)

    def _on_add_person(self) -> None:
        existing_names = {p.name for p in self._store.list_people()}
        dialog = PersonDialog(self, existing_names=existing_names)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        person = AppStore.new_person(
            name=data["name"],
            relationship_type=data["relationship_type"],
            style_tags=data["style_tags"],
            avatar_path=data["avatar_path"],
            relative_role=data["relative_role"],
            age_group=data["age_group"],
            goals=data["goals"],
            notes=data["notes"],
        )
        self._store.add_person(person)
        self._conversation_cache[person.person_id] = []
        self._store.sync_to_data_dir(self._system.settings.data_dir)
        self._refresh_contact_list()
        self._set_current_person(person.person_id)

    def _on_edit_person(self, person_id: str) -> None:
        person = self._store.people.get(person_id)
        if not person:
            return
        existing_names = {p.name for p in self._store.list_people()}
        dialog = PersonDialog(self, person, existing_names=existing_names)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_data()
        if not data:
            return
        person.name = data["name"]
        person.relationship_type = data["relationship_type"]
        person.relative_role = data["relative_role"]
        person.age_group = data["age_group"]
        person.goals = data["goals"]
        person.style_tags = data["style_tags"]
        person.notes = data["notes"]
        person.avatar_path = data["avatar_path"]
        self._store.update_person(person)
        self._store.sync_to_data_dir(self._system.settings.data_dir)
        self._refresh_contact_list()
        self._set_current_person(person_id)

    def _on_delete_person(self, person_id: str) -> None:
        if QMessageBox.question(self, "确认", "确定要删除该对象吗？") != QMessageBox.Yes:
            return
        self._store.delete_person(person_id)
        self._conversation_cache.pop(person_id, None)
        self._store.sync_to_data_dir(self._system.settings.data_dir)
        self._current_person_id = None
        self._refresh_contact_list()
        self._clear_profile_panel()
        self.status_contact.setText("当前对象：-")

    def _on_pin_person(self, person_id: str) -> None:
        person = self._store.people.get(person_id)
        if not person:
            return
        self._store.delete_person(person_id)
        self._store.people = {person_id: person, **self._store.people}
        self._refresh_contact_list()
        self._set_current_person(person_id)

    def _set_current_person(self, person_id: str) -> None:
        for idx in range(self.contact_list.count()):
            item = self.contact_list.item(idx)
            if item.data(Qt.UserRole) == person_id:
                self.contact_list.setCurrentRow(idx)
                return

    def _apply_person_item_styles(self) -> None:
        for idx in range(self.contact_list.count()):
            item = self.contact_list.item(idx)
            widget = self.contact_list.itemWidget(item)
            if isinstance(widget, PersonItemWidget):
                widget.set_selected(item.isSelected())

    # ---------------- Right Panel ----------------

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # 标题栏容器
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 8)
        
        self.module_title = QLabel("回复建议")
        self.module_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                padding: 4px 0px;
            }
        """)
        
        self.module_menu_btn = QToolButton()
        self.module_menu_btn.setText("⋯")
        self.module_menu_btn.setPopupMode(QToolButton.InstantPopup)
        apply_toolbar_style(self.module_menu_btn)
        self.module_menu = QMenu(self)
        self.module_menu.setStyleSheet(get_menu_style())
        self.action_reply = self.module_menu.addAction("回复建议")
        self.action_profile = self.module_menu.addAction("关系画像")
        self.action_memory = self.module_menu.addAction("长期记忆")
        self.action_reply.triggered.connect(lambda: self._set_module(1))
        self.action_profile.triggered.connect(lambda: self._set_module(0))
        self.action_memory.triggered.connect(lambda: self._set_module(2))
        self.module_menu_btn.setMenu(self.module_menu)

        top_row.addWidget(self.module_title)
        top_row.addStretch()
        top_row.addWidget(self.module_menu_btn)

        self.stack = QStackedWidget()
        self.profile_page = self._build_profile_page()
        self.reply_page = self._build_reply_page()
        self.memory_page = self._build_memory_page()

        self.stack.addWidget(self.profile_page)
        self.stack.addWidget(self.reply_page)
        self.stack.addWidget(self.memory_page)

        layout.addLayout(top_row)
        layout.addWidget(self.stack)
        self._set_module(1)
        return panel

    def _set_module(self, index: int) -> None:
        titles = {0: "关系画像", 1: "回复建议", 2: "长期记忆"}
        self.stack.setCurrentIndex(index)
        self.module_title.setText(titles.get(index, "回复建议"))
        
        # 切换到关系画像时刷新数据
        if index == 0 and self._current_person_id:
            person = self._store.people.get(self._current_person_id)
            if person:
                self._update_profile_panel(person)

    # ---------------- 模块一：关系画像 ----------------

    def _build_profile_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        content = QWidget()
        content_layout = QVBoxLayout(content)

        base_group = QGroupBox("对象基本信息")
        base_layout = QVBoxLayout(base_group)
        self.info_name = QLabel("姓名：-")
        self.info_relation = QLabel("关系类型：-")
        self.info_role = QLabel("身份相对关系：-")
        self.info_age = QLabel("年龄层：-")
        self.info_goals = QLabel("关系目标：-")
        self.info_updated = QLabel("最近更新：-")
        base_layout.addWidget(self.info_name)
        base_layout.addWidget(self.info_relation)
        base_layout.addWidget(self.info_role)
        base_layout.addWidget(self.info_age)
        base_layout.addWidget(self.info_goals)
        base_layout.addWidget(self.info_updated)

        stage_group = QGroupBox("关系阶段 & 亲密度")
        stage_layout = QVBoxLayout(stage_group)
        self.label_stage = QLabel("关系阶段：-")
        self.progress_intimacy = QProgressBar()
        self.progress_intimacy.setRange(0, 100)
        self.label_intimacy = QLabel("亲密度：-")
        self.label_last_updated = QLabel("更新时间：-")
        stage_layout.addWidget(self.label_stage)
        stage_layout.addWidget(self.progress_intimacy)
        stage_layout.addWidget(self.label_intimacy)
        stage_layout.addWidget(self.label_last_updated)

        trend_group = QGroupBox("关系变化趋势")
        trend_layout = QVBoxLayout(trend_group)
        # 使用折线图代替文本显示
        self.trend_chart = IntimacyTrendChart()
        trend_layout.addWidget(self.trend_chart)

        style_group = QGroupBox("对话风格画像（可手动微调）")
        style_layout = QVBoxLayout(style_group)
        self.slider_formality, self.label_formality = self._build_style_slider("正式程度")
        self.slider_warmth, self.label_warmth = self._build_style_slider("情感温度")
        self.slider_direct, self.label_direct = self._build_style_slider("直接程度")
        self.slider_humor, self.label_humor = self._build_style_slider("幽默接受度")
        style_layout.addLayout(self._wrap_slider("正式程度", self.slider_formality, self.label_formality))
        style_layout.addLayout(self._wrap_slider("情感温度", self.slider_warmth, self.label_warmth))
        style_layout.addLayout(self._wrap_slider("直接程度", self.slider_direct, self.label_direct))
        style_layout.addLayout(self._wrap_slider("幽默接受度", self.slider_humor, self.label_humor))

        advice_group = QGroupBox("系统解读 / 建议")
        advice_layout = QVBoxLayout(advice_group)
        self.label_risk = QLabel("关系风险提示：-")
        self.strategy_text = QTextEdit()
        self.strategy_text.setReadOnly(True)
        advice_layout.addWidget(self.label_risk)
        advice_layout.addWidget(self.strategy_text)

        note_group = QGroupBox("关系演化备注（人工）")
        note_layout = QVBoxLayout(note_group)
        note_row = QHBoxLayout()
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("例如：最近吵过一次 / 对方最近压力大")
        self.btn_add_note = QPushButton("记录备注")
        apply_secondary_style(self.btn_add_note)
        self.btn_add_note.clicked.connect(self._on_add_evolution_note)
        note_row.addWidget(self.note_input)
        note_row.addWidget(self.btn_add_note)
        self.note_list = QListWidget()
        note_layout.addLayout(note_row)
        note_layout.addWidget(self.note_list)

        content_layout.addWidget(base_group)
        content_layout.addWidget(stage_group)
        content_layout.addWidget(trend_group)
        content_layout.addWidget(style_group)
        content_layout.addWidget(advice_group)
        content_layout.addWidget(note_group)
        content_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)

        layout.addWidget(scroll)
        return page

    def _update_profile_panel(self, person: Person) -> None:
        if not person.intimacy_history:
            self._store.record_intimacy(person.person_id, person.intimacy, "初始化")
            self._store.sync_to_data_dir(self._system.settings.data_dir)
        stage = self._stage_from_intimacy(person.intimacy)
        risk_text = self._evaluate_risk(person)
        last_updated = self._latest_intimacy_time(person) or "-"
        goals = "、".join(person.goals) if person.goals else "-"
        
        # 获取交互状态
        interaction_status = IntimacyManager.format_interaction_status(
            person.last_interaction_date, person.intimacy
        )
        
        # 计算最近的亲密度变化趋势
        change_trend = self._get_intimacy_trend(person)

        self.info_name.setText(f"姓名：{person.display_name}")
        self.info_relation.setText(f"关系类型：{person.relationship_type}")
        self.info_role.setText(f"身份相对关系：{person.relative_role}")
        self.info_age.setText(f"年龄层：{person.age_group}")
        self.info_goals.setText(f"关系目标：{goals}")
        self.info_updated.setText(f"最近交互：{interaction_status}")

        self.label_stage.setText(f"关系阶段：{stage}")
        self.progress_intimacy.setValue(person.intimacy)
        
        # 显示亲密度和趋势
        trend_text = ""
        if change_trend > 0:
            trend_text = f" ↑{change_trend}"
        elif change_trend < 0:
            trend_text = f" ↓{abs(change_trend)}"
        self.label_intimacy.setText(f"亲密度：{person.intimacy}%{trend_text}")
        self.label_last_updated.setText(f"更新时间：{last_updated}")

        # 更新折线图
        self.trend_chart.update_data(person.intimacy_history)
        self.label_risk.setText(f"关系风险提示：{risk_text}")
        self.strategy_text.setPlainText(self._build_rule_advice(person))

        self._load_style_profile(person)
        self._refresh_notes(person)
    
    def _get_intimacy_trend(self, person: Person) -> int:
        """获取最近一周的亲密度变化趋势。"""
        if not person.intimacy_change_history:
            return 0
        
        # 计算最近7天的变化总和
        from datetime import timedelta
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        total_change = 0
        for record in person.intimacy_change_history:
            try:
                record_date = datetime.strptime(record.get("date", ""), "%Y-%m-%d").date()
                if record_date >= week_ago:
                    total_change += record.get("change", 0)
            except ValueError:
                continue
        
        return total_change
    
    def _update_profile_panel_without_chart(self, person: Person) -> None:
        """轻量级更新画像面板（不刷新折线图，用于反馈变化时）。"""
        stage = self._stage_from_intimacy(person.intimacy)
        change_trend = self._get_intimacy_trend(person)
        
        self.label_stage.setText(f"关系阶段：{stage}")
        self.progress_intimacy.setValue(person.intimacy)
        
        # 显示亲密度和趋势
        trend_text = ""
        if change_trend > 0:
            trend_text = f" ↑{change_trend}"
        elif change_trend < 0:
            trend_text = f" ↓{abs(change_trend)}"
        self.label_intimacy.setText(f"亲密度：{person.intimacy}%{trend_text}")

    def _clear_profile_panel(self) -> None:
        self.info_name.setText("姓名：-")
        self.info_relation.setText("关系类型：-")
        self.info_role.setText("身份相对关系：-")
        self.info_age.setText("年龄层：-")
        self.info_goals.setText("关系目标：-")
        self.info_updated.setText("最近更新：-")
        self.label_stage.setText("关系阶段：-")
        self.progress_intimacy.setValue(0)
        self.label_intimacy.setText("亲密度：-")
        self.label_last_updated.setText("更新时间：-")
        self.trend_chart.update_data([])  # 清空折线图
        self.label_risk.setText("关系风险提示：-")
        self.strategy_text.clear()
        self.note_list.clear()
        self._set_slider(self.slider_formality, self.label_formality, 0)
        self._set_slider(self.slider_warmth, self.label_warmth, 0)
        self._set_slider(self.slider_direct, self.label_direct, 0)
        self._set_slider(self.slider_humor, self.label_humor, 0)

    @staticmethod
    def _stage_from_intimacy(intimacy: int) -> str:
        """获取亲密度对应的关系阶段名称。"""
        stage_cn, _ = IntimacyManager.get_stage(intimacy)
        return stage_cn

    def _build_style_slider(self, name: str) -> tuple[QSlider, QLabel]:
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.valueChanged.connect(self._on_style_changed)
        # 禁用滚轮事件，避免滚动页面时意外调整滑块值
        slider.wheelEvent = lambda event: event.ignore()
        value_label = QLabel("0%")
        value_label.setFixedWidth(48)
        return slider, value_label

    def _wrap_slider(self, title: str, slider: QSlider, value_label: QLabel) -> QHBoxLayout:
        row = QHBoxLayout()
        label = QLabel(title)
        label.setFixedWidth(80)
        row.addWidget(label)
        row.addWidget(slider, 1)
        row.addWidget(value_label)
        return row

    def _load_style_profile(self, person: Person) -> None:
        profile = person.style_profile or {
            "formality": 0.5,
            "warmth": 0.5,
            "directness": 0.5,
            "humor": 0.5,
        }
        person.style_profile = profile
        self._set_slider(self.slider_formality, self.label_formality, profile["formality"])
        self._set_slider(self.slider_warmth, self.label_warmth, profile["warmth"])
        self._set_slider(self.slider_direct, self.label_direct, profile["directness"])
        self._set_slider(self.slider_humor, self.label_humor, profile["humor"])

    def _set_slider(self, slider: QSlider, label: QLabel, value: float) -> None:
        slider.blockSignals(True)
        slider.setValue(int(value * 100))
        slider.blockSignals(False)
        label.setText(f"{int(value * 100)}%")

    def _on_style_changed(self) -> None:
        person = self._get_current_person()
        if not person:
            return
        person.style_profile = {
            "formality": self.slider_formality.value() / 100,
            "warmth": self.slider_warmth.value() / 100,
            "directness": self.slider_direct.value() / 100,
            "humor": self.slider_humor.value() / 100,
        }
        self.label_formality.setText(f"{self.slider_formality.value()}%")
        self.label_warmth.setText(f"{self.slider_warmth.value()}%")
        self.label_direct.setText(f"{self.slider_direct.value()}%")
        self.label_humor.setText(f"{self.slider_humor.value()}%")
        # 保存风格数据到文件
        self._store.sync_to_data_dir(self._system.settings.data_dir)

    def _format_trend(self, person: Person) -> str:
        if not person.intimacy_history:
            return "暂无记录。"
        lines = [f"{item['timestamp']}  亲密度 {item['intimacy_score']}%" for item in person.intimacy_history[-10:]]
        return "\n".join(lines)

    def _latest_intimacy_time(self, person: Person) -> str:
        if not person.intimacy_history:
            return "-"
        return person.intimacy_history[-1]["timestamp"]

    def _build_rule_advice(self, person: Person) -> str:
        stage = self._stage_from_intimacy(person.intimacy)
        warmth = person.style_profile.get("warmth", 0.5)
        formality = person.style_profile.get("formality", 0.5)
        lines = [f"当前关系处于“{stage}期”。"]
        if formality >= 0.7:
            lines.append("建议保持正式、清晰的表达。")
        elif formality <= 0.3:
            lines.append("建议保持轻松自然的语气。")
        else:
            lines.append("建议使用中性、礼貌的语气。")
        if warmth >= 0.6:
            lines.append("可适度使用关怀或鼓励式回应。")
        else:
            lines.append("注意避免过度情感表达。")
        return "\n".join(lines)

    def _evaluate_risk(self, person: Person) -> str:
        """评估关系风险，综合考虑亲密度趋势和交互频率。"""
        risks = []
        
        # 检查亲密度下降趋势
        history = person.intimacy_history[-3:]
        if len(history) >= 3:
            values = [item.get("intimacy_score", 50) for item in history]
            if values[2] < values[1] < values[0]:
                risks.append("亲密度持续下降")
        
        # 检查长期未交互
        if person.last_interaction_date:
            try:
                last_date = datetime.strptime(person.last_interaction_date, "%Y-%m-%d")
                days_since = (datetime.now() - last_date).days
                if days_since >= 30:
                    risks.append(f"已{days_since}天未交互，关系正在淡化")
                elif days_since >= 14:
                    risks.append(f"已{days_since}天未交互")
            except ValueError:
                pass
        
        # 检查亲密度过低
        if person.intimacy < 20:
            risks.append("亲密度较低")
        
        # 检查衰减趋势（本周是否有负变化）
        trend = self._get_intimacy_trend(person)
        if trend < -5:
            risks.append("本周亲密度下降明显")
        
        if not risks:
            return "正常"
        elif len(risks) == 1:
            return f"⚠️ {risks[0]}"
        else:
            return "⚠️ " + "；".join(risks)

    def _refresh_notes(self, person: Person) -> None:
        self.note_list.clear()
        for note in person.evolution_notes[-10:]:
            self.note_list.addItem(note)

    def _on_add_evolution_note(self) -> None:
        person = self._get_current_person()
        if not person:
            QMessageBox.information(self, "提示", "请先选择一个关系对象。")
            return
        note = self.note_input.text().strip()
        if not note:
            return
        self._store.add_evolution_note(person.person_id, note)
        self.note_input.clear()
        self._refresh_notes(person)
        # 保存备注数据到文件
        self._store.sync_to_data_dir(self._system.settings.data_dir)

    # ---------------- 模块二：回复建议 ----------------

    def _build_reply_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        self.conversation_list = QListWidget()
        self.conversation_list.setSpacing(6)
        self.conversation_list.setSelectionMode(QListWidget.NoSelection)
        self.conversation_list.setFocusPolicy(Qt.NoFocus)
        self.conversation_list.setStyleSheet(
            "QListWidget::item { border: none; margin: 0px; padding: 0px; }"
            "QListWidget::item:selected { background: transparent; }"
        )

        strategy_group = QGroupBox("回复策略选择")
        strategy_layout = QHBoxLayout(strategy_group)
        strategy_layout.setSpacing(24)  # 选项之间的间距
        strategy_layout.setContentsMargins(12, 8, 12, 8)
        self.strategy_close = QCheckBox("更亲近")
        self.strategy_formal = QCheckBox("更正式")
        self.strategy_distance = QCheckBox("保持距离")
        self.strategy_humor = QCheckBox("幽默回应")
        # 设置勾选框与文字之间的间距（通过样式表）
        checkbox_style = "QCheckBox { spacing: 4px; }"
        self.strategy_close.setStyleSheet(checkbox_style)
        self.strategy_formal.setStyleSheet(checkbox_style)
        self.strategy_distance.setStyleSheet(checkbox_style)
        self.strategy_humor.setStyleSheet(checkbox_style)
        strategy_layout.addWidget(self.strategy_close)
        strategy_layout.addWidget(self.strategy_formal)
        strategy_layout.addWidget(self.strategy_distance)
        strategy_layout.addWidget(self.strategy_humor)
        strategy_layout.addStretch()

        input_row = QHBoxLayout()
        self.original_input = MessageInput()
        self.original_input.setPlaceholderText("输入消息，回车发送，Shift+回车换行")
        self.original_input.setAcceptRichText(False)
        self.original_input.setLineWrapMode(QTextEdit.WidgetWidth)
        self.original_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        line_height = self.original_input.fontMetrics().lineSpacing()
        margin = int(self.original_input.document().documentMargin())
        self.original_input.setFixedHeight(int(line_height * 2 + margin * 2 + 6))
        self.original_input.send_requested.connect(self._on_send_message)
        self.btn_generate = QPushButton("发送")
        apply_primary_style(self.btn_generate, width=80)
        self.btn_generate.clicked.connect(self._on_send_message)
        input_row.addWidget(self.original_input)
        input_row.addWidget(self.btn_generate)

        layout.addWidget(self.conversation_list, 2)
        layout.addWidget(strategy_group)
        layout.addLayout(input_row)
        return page

    def _on_send_message(self) -> None:
        person = self._get_current_person()
        if not person:
            QMessageBox.information(self, "提示", "请先选择一个关系对象。")
            return
        message = self.original_input.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "提示", "请输入原始消息内容。")
            return

        # 防止重复点击
        self.btn_generate.setEnabled(False)
        self.original_input.setEnabled(False)

        # 保存当前对象ID，防止异步操作期间对象切换导致消息显示到错误的对话框
        target_person_id = person.person_id

        # 1. 立即显示用户消息并清空输入框
        self._append_chat_message("user", message, target_person_id=target_person_id)
        self.original_input.clear()
        
        # 2. 显示等待指示器
        self._current_typing_indicator = self._show_typing_indicator(target_person_id)

        strategy_notes = self._collect_strategy_notes()
        composed_message = message
        if strategy_notes:
            composed_message += f"\n\n[策略倾向]\n{strategy_notes}"

        contact_type = RELATIONSHIP_TO_CONTACT.get(person.relationship_type, ContactType.OTHER)
        self.status_model.setText("模型状态：生成中...")
        
        # 保存上下文信息供回调使用（使用 person_id 作为键，支持多个并发请求）
        self._pending_requests[target_person_id] = {
            "person": person,
            "message": message,
            "target_person_id": target_person_id,
        }
        
        # 3. 在后台线程中处理消息生成
        self._message_worker = MessageGenerationWorker(
            self._system,
            person.person_id,
            person.display_name,
            composed_message,
            contact_type,
        )
        self._message_worker.finished.connect(self._on_message_generated)
        self._message_worker.error.connect(self._on_message_error)
        self._message_worker.start()
    
    def _on_message_generated(self, result: dict) -> None:
        """消息生成完成的回调。"""
        # 获取工作线程中的 person_id
        worker = self.sender()
        if not isinstance(worker, MessageGenerationWorker):
            return
        target_person_id = worker._person_id
        
        # 从待处理请求中获取上下文
        ctx = self._pending_requests.pop(target_person_id, None)
        if ctx is None:
            return
        
        person = ctx["person"]
        message = ctx["message"]
        
        # 恢复输入状态
        self.btn_generate.setEnabled(True)
        self.original_input.setEnabled(True)
        
        self.status_model.setText("模型状态：完成")
        self.status_time.setText(f"最近生成：{datetime.now().strftime('%H:%M:%S')}")
        
        # 只有当目标联系人是当前显示的联系人时才更新 UI
        if target_person_id == self._current_person_id:
            # 移除等待指示器
            self._remove_typing_indicator(self._current_typing_indicator)
            self._current_typing_indicator = None
            
            self._update_intimacy_after_reply(person, result, message)
            self._append_recommendations(result.get("recommendation", {}), target_person_id=target_person_id)
            self._update_profile_panel(person)
        else:
            # 目标联系人不是当前显示的，将回复缓存到对话历史中
            self._update_intimacy_after_reply(person, result, message)
            # 回复建议也需要缓存
            self._cache_recommendations(result.get("recommendation", {}), target_person_id)
    
    def _on_message_error(self, error_msg: str) -> None:
        """消息生成失败的回调。"""
        # 获取工作线程中的 person_id
        worker = self.sender()
        if not isinstance(worker, MessageGenerationWorker):
            return
        target_person_id = worker._person_id
        
        # 从待处理请求中移除
        self._pending_requests.pop(target_person_id, None)
        
        # 恢复输入状态
        self.btn_generate.setEnabled(True)
        self.original_input.setEnabled(True)
        
        # 只有当目标联系人是当前显示的联系人时才移除指示器
        if target_person_id == self._current_person_id:
            self._remove_typing_indicator(self._current_typing_indicator)
            self._current_typing_indicator = None
        
        QMessageBox.critical(self, "错误", f"生成回复失败：{error_msg}")
        self.status_model.setText("模型状态：失败")
    
    def _cache_recommendations(self, recommendation: dict, target_person_id: str) -> None:
        """将回复建议缓存到对话历史中（用于用户切换到其他联系人时）。"""
        replies = recommendation.get("replies", [])
        if not replies:
            return
        
        # 构建回复建议文本
        lines = []
        for i, r in enumerate(replies, 1):
            lines.append(f"【建议{i}】{r.get('text', '')}")
            if r.get("reason"):
                lines.append(f"   理由：{r['reason']}")
        
        combined_text = "\n".join(lines)
        
        # 生成消息ID
        from uuid import uuid4
        message_id = str(uuid4())
        
        # 缓存到对话历史
        if target_person_id not in self._conversation_cache:
            self._conversation_cache[target_person_id] = []
        self._conversation_cache[target_person_id].append({
            "role": "assistant",
            "text": combined_text,
            "message_id": message_id,
            "feedback": None,
        })

    def _collect_strategy_notes(self) -> str:
        notes = []
        if self.strategy_close.isChecked():
            notes.append("语气更亲近")
        if self.strategy_formal.isChecked():
            notes.append("偏正式表达")
        if self.strategy_distance.isChecked():
            notes.append("保持礼貌距离")
        if self.strategy_humor.isChecked():
            notes.append("适当幽默")
        return "\n".join(f"- {note}" for note in notes)

    def _update_intimacy_after_reply(self, person: Person, result: dict, message: str, user_accepted: bool = False) -> None:
        """
        基于对话结果更新亲密度。
        
        新机制：
        1. 仅在用户接受建议时增长亲密度
        2. 考虑对话深度、情感、交互质量等因素
        3. 应用衰减机制（长期不交互会导致亲密度下降）
        
        Args:
            person: 当前对话对象
            result: LLM返回的分析结果
            message: 用户输入的原始消息
            user_accepted: 用户是否接受了建议（目前默认为 True，后续可根据反馈调整）
        """
        analysis = result.get("analysis", {})
        sentiment = analysis.get("sentiment", 0.0)
        
        # 计算距离最后交互的天数
        days_since_last = 0
        if person.last_interaction_date:
            try:
                last_date = datetime.strptime(person.last_interaction_date, "%Y-%m-%d")
                today = datetime.now()
                days_since_last = (today - last_date).days
            except ValueError:
                days_since_last = 0
        
        # 先应用衰减（如果长期未交互）
        current_intimacy = person.intimacy
        decayed_intimacy, decay_reason = IntimacyManager.calculate_decay(
            current_intimacy, 
            person.last_interaction_date
        )
        
        if decayed_intimacy < current_intimacy and decay_reason:
            # 记录衰减
            self._store.record_intimacy(person.person_id, decayed_intimacy, decay_reason)
            current_intimacy = decayed_intimacy
        
        # 分析消息质量
        has_question = "？" in message or "?" in message or "吗" in message
        has_thanks = any(word in message for word in ["谢谢", "感谢", "多谢", "thanks", "thank"])
        has_empathy = any(word in message for word in ["理解", "明白", "懂你", "同感", "也是"])
        
        # 计算增长（只有在用户"接受"建议时才增长）
        # 目前默认为 True，实际应该在用户点击"采纳"时才设置为 True
        new_intimacy, growth_reason, growth = IntimacyManager.calculate_growth(
            current_intimacy=current_intimacy,
            message_length=len(message),
            sentiment_score=sentiment,
            user_accepted=user_accepted,
            has_question=has_question,
            has_thanks=has_thanks,
            has_empathy=has_empathy,
            days_since_last=days_since_last,
        )
        
        # 只有有变化时才记录
        if new_intimacy != current_intimacy:
            self._store.record_intimacy(person.person_id, new_intimacy, growth_reason)
        else:
            # 即使没有增长，也更新最后交互日期
            person.last_interaction_date = datetime.now().strftime("%Y-%m-%d")
        
        # 动态更新对话风格画像
        self._update_style_profile_from_message(person, message, result)
        
        # 保存亲密度和风格数据并刷新联系人列表
        self._store.sync_to_data_dir(self._system.settings.data_dir)
        self._refresh_contact_list()

    def _update_style_profile_from_message(self, person: Person, message: str, result: dict) -> None:
        """
        基于对话内容动态调整风格画像。
        
        策略说明：
        1. 正式程度 (formality)：分析消息中的敬语、称呼、句式等
        2. 情感温度 (warmth)：分析情感词汇、关心类表达、表情符号等
        3. 直接程度 (directness)：分析句子长度、是否有铺垫、是否直接表达观点
        4. 幽默接受度 (humor)：分析是否包含玩笑、俏皮话、表情等轻松内容
        
        采用增量平滑更新：new_value = old_value * (1 - α) + detected_value * α
        α = 0.15，确保渐进式调整，避免单次对话剧烈波动
        """
        if not person.style_profile:
            person.style_profile = {
                "formality": 0.5,
                "warmth": 0.5,
                "directness": 0.5,
                "humor": 0.5,
            }
        
        # 获取当前风格值
        current = person.style_profile
        alpha = 0.15  # 平滑系数
        
        # 分析消息内容
        formality_score = self._analyze_formality(message)
        warmth_score = self._analyze_warmth(message)
        directness_score = self._analyze_directness(message)
        humor_score = self._analyze_humor(message)
        
        # 增量平滑更新
        person.style_profile = {
            "formality": self._smooth_update(current.get("formality", 0.5), formality_score, alpha),
            "warmth": self._smooth_update(current.get("warmth", 0.5), warmth_score, alpha),
            "directness": self._smooth_update(current.get("directness", 0.5), directness_score, alpha),
            "humor": self._smooth_update(current.get("humor", 0.5), humor_score, alpha),
        }

    @staticmethod
    def _smooth_update(old_val: float, new_val: float, alpha: float) -> float:
        """增量平滑更新：避免单次对话导致风格值剧烈波动。"""
        result = old_val * (1 - alpha) + new_val * alpha
        return max(0.0, min(1.0, result))

    def _analyze_formality(self, message: str) -> float:
        """
        分析消息的正式程度。
        
        高正式度指标：敬语、书面用语、完整句式、问候语
        低正式度指标：口语化、省略、网络用语、表情符号
        """
        score = 0.5  # 基础分
        
        # 高正式度词汇
        formal_words = [
            "您", "请", "敬请", "烦请", "尊敬的", "贵", "希望", "建议", "感谢", 
            "打扰", "冒昧", "恳请", "望", "如有", "若", "此", "鉴于", "关于",
            "抱歉", "对不起", "麻烦", "辛苦", "多谢", "致谢", "特此", "敬上"
        ]
        
        # 低正式度词汇（口语化/网络用语）
        informal_words = [
            "哈哈", "嗯嗯", "啊", "呀", "嘛", "呢", "吧", "哦", "噢", "emmm",
            "hhh", "666", "awsl", "牛", "绝了", "真的吗", "咋", "啥", "整",
            "搞", "弄", "咱", "俺", "老", "小", "哥", "姐", "兄弟", "姐妹"
        ]
        
        # 表情符号（降低正式度）
        emoji_pattern = r'[😀-🙏🌀-🗿🚀-🛿☀-⛿✀-➿🤀-🧿😂🤣😊😍🥰😘😭😱😤😡🙄😅🤔🤗👍👎👌✌️🎉🔥💯❤️💕]'
        
        msg_lower = message.lower()
        
        # 统计正式词汇出现次数
        formal_count = sum(1 for word in formal_words if word in message)
        informal_count = sum(1 for word in informal_words if word in msg_lower)
        emoji_count = len(re.findall(emoji_pattern, message))
        
        # 分析句式
        has_complete_punctuation = message.rstrip().endswith(('。', '！', '？', '.', '!', '?'))
        sentence_count = len(re.findall(r'[。！？.!?]', message)) + 1
        avg_sentence_len = len(message) / max(sentence_count, 1)
        
        # 计算得分调整
        score += formal_count * 0.08
        score -= informal_count * 0.06
        score -= emoji_count * 0.04
        
        if has_complete_punctuation:
            score += 0.05
        if avg_sentence_len > 20:  # 较长句子通常更正式
            score += 0.05
        
        return max(0.0, min(1.0, score))

    def _analyze_warmth(self, message: str) -> float:
        """
        分析消息的情感温度。
        
        高温度指标：关心、鼓励、赞美、表达情感
        低温度指标：冷漠、公事公办、无情感词
        """
        score = 0.5
        
        # 温暖/关心类词汇
        warm_words = [
            "关心", "在乎", "想念", "挂念", "担心", "心疼", "辛苦了", "加油",
            "棒", "厉害", "开心", "高兴", "喜欢", "爱", "亲", "宝", "甜",
            "照顾好", "注意身体", "早点休息", "别太累", "有空", "一起",
            "想你", "念你", "好久不见", "期待", "祝", "希望你", "保重",
            "抱抱", "摸摸头", "乖", "宝贝", "亲爱的", "❤️", "💕", "🥰", "😘"
        ]
        
        # 冷淡/公事类词汇
        cold_words = [
            "通知", "告知", "须", "必须", "应当", "不得", "禁止", "按照",
            "根据", "依据", "规定", "要求", "标准", "流程", "提交", "汇报"
        ]
        
        warm_count = sum(1 for word in warm_words if word in message)
        cold_count = sum(1 for word in cold_words if word in message)
        
        # 感叹号和问候语增加温度
        exclamation_count = message.count('！') + message.count('!')
        has_greeting = any(g in message for g in ["早", "晚安", "你好", "嗨", "hi", "hello"])
        
        score += warm_count * 0.1
        score -= cold_count * 0.08
        score += min(exclamation_count * 0.03, 0.15)
        if has_greeting:
            score += 0.05
        
        return max(0.0, min(1.0, score))

    def _analyze_directness(self, message: str) -> float:
        """
        分析消息的直接程度。
        
        高直接度：开门见山、明确表达观点、短句
        低直接度：委婉、铺垫多、条件句多
        """
        score = 0.5
        
        # 直接表达词汇
        direct_words = [
            "我觉得", "我认为", "我想", "我要", "必须", "一定", "肯定",
            "就是", "明确", "直接", "简单说", "总之", "反正", "不行", "可以"
        ]
        
        # 委婉/铺垫词汇
        indirect_words = [
            "可能", "也许", "或许", "大概", "似乎", "好像", "应该", "觉得",
            "不知道", "不太确定", "如果可以的话", "方便的话", "有空的话",
            "能不能", "可不可以", "是否", "是不是", "会不会", "要不要",
            "其实", "说实话", "坦白说", "怎么说呢"
        ]
        
        direct_count = sum(1 for word in direct_words if word in message)
        indirect_count = sum(1 for word in indirect_words if word in message)
        
        # 句子长度分析（短句通常更直接）
        sentences = re.split(r'[。！？.!?，,、；;]', message)
        valid_sentences = [s for s in sentences if len(s.strip()) > 0]
        if valid_sentences:
            avg_len = sum(len(s) for s in valid_sentences) / len(valid_sentences)
            if avg_len < 10:
                score += 0.1
            elif avg_len > 25:
                score -= 0.1
        
        score += direct_count * 0.08
        score -= indirect_count * 0.06
        
        return max(0.0, min(1.0, score))

    def _analyze_humor(self, message: str) -> float:
        """
        分析消息的幽默/轻松程度。
        
        高幽默度：笑声词汇、调侃、表情、轻松用语
        低幽默度：严肃话题、正经表达
        """
        score = 0.5
        
        # 幽默/轻松词汇
        humor_words = [
            "哈哈", "嘿嘿", "呵呵", "hiahia", "233", "笑死", "绝了", "太好笑",
            "搞笑", "有趣", "玩笑", "调侃", "皮", "逗", "段子", "梗",
            "hhh", "xswl", "hhhh", "🤣", "😂", "😆", "🙃", "😏", "😜", "🤪"
        ]
        
        # 严肃话题词汇
        serious_words = [
            "严肃", "认真", "重要", "紧急", "问题", "麻烦", "困难", "危机",
            "严重", "担忧", "焦虑", "压力", "生病", "去世", "抱歉", "道歉"
        ]
        
        humor_count = sum(1 for word in humor_words if word in message.lower())
        serious_count = sum(1 for word in serious_words if word in message)
        
        # 波浪号和省略号增加轻松感
        wave_count = message.count('~') + message.count('～')
        
        score += humor_count * 0.12
        score -= serious_count * 0.08
        score += min(wave_count * 0.05, 0.1)
        
        return max(0.0, min(1.0, score))

    @staticmethod
    def _estimate_conversation_depth(message: str) -> float:
        deep_keywords = ["压力", "焦虑", "难受", "求助", "秘密", "感受", "情绪", "家人", "关系", "问题", "计划"]
        if any(keyword in message for keyword in deep_keywords):
            return 1.0
        if len(message) >= 30:
            return 0.6
        return 0.2

    def _append_recommendations(self, rec: dict, target_person_id: str = None) -> None:
        from uuid import uuid4
        
        replies = []
        primary = rec.get("suggested_reply")
        if primary:
            replies.append(primary)
        replies.extend(rec.get("alternative_replies", []) or [])
        
        # 为这批回复生成一个共同的对话轮次ID
        round_id = str(uuid4())

        for reply in replies:
            self._append_chat_message("assistant", reply, target_person_id=target_person_id, round_id=round_id)

    def _copy_text(self, text: str) -> None:
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "已复制", "回复已复制到剪贴板。")

    def _append_chat_message(self, role: str, text: str, record: bool = True, target_person_id: str = None, feedback: str = None, message_id: str = None, round_id: str = None) -> None:
        """
        添加聊天消息到对话列表。
        
        Args:
            role: 消息角色 ("user" 或 "assistant")
            text: 消息内容
            record: 是否记录到缓存
            target_person_id: 目标对象ID，如果与当前选中对象不同则只记录不显示
            feedback: 反馈状态 ("like" | "dislike" | None)
            message_id: 消息ID，若不传则自动生成
            round_id: 对话轮次ID，用于跟踪同一批回复的反馈状态
        """
        if role == "assistant":
            text = text.lstrip("\n")
        
        # 确定要记录消息的对象ID
        record_person_id = target_person_id or self._current_person_id
        
        # 使用传入的消息ID或生成新的
        from uuid import uuid4
        if message_id is None:
            message_id = str(uuid4())
        
        if record and record_person_id:
            self._conversation_cache.setdefault(record_person_id, []).append({
                "role": role,
                "text": text,
                "message_id": message_id,
                "feedback": feedback,  # "like" | "dislike" | None
                "round_id": round_id,  # 对话轮次ID
            })
        
        # 只有当目标对象是当前选中对象时才显示消息
        if target_person_id and target_person_id != self._current_person_id:
            # 消息属于其他对象，不显示在当前界面
            return
        
        item = QListWidgetItem()
        item.setSizeHint(QSize(520, 70))
        widget = ChatMessageWidget(role, text, message_id)
        
        # 恢复反馈状态
        if feedback:
            widget.set_feedback_state(feedback)
        
        # 连接反馈信号
        if role == "assistant":
            widget.feedback_changed.connect(self._on_message_feedback_changed)
        
        self.conversation_list.addItem(item)
        self.conversation_list.setItemWidget(item, widget)
        self._update_conversation_item_widths()
        self.conversation_list.scrollToBottom()
    
    def _on_message_feedback_changed(self, message_id: str, feedback: str) -> None:
        """处理消息反馈变化。
        
        实现逻辑：
        1. 同一对话轮次内，喜欢/不喜欢各自最多只影响一次亲密度
        2. 同一轮次内的多次反馈变化只保留最终值到折线图
        """
        person_id = self._current_person_id
        if not person_id:
            return
        
        # 获取之前的反馈状态和 round_id
        old_feedback = None
        round_id = None
        cache = self._conversation_cache.get(person_id, [])
        for msg in cache:
            if msg.get("message_id") == message_id:
                old_feedback = msg.get("feedback")
                round_id = msg.get("round_id")
                msg["feedback"] = feedback if feedback else None
                break
        
        # 如果反馈状态没有变化，不处理
        if old_feedback == feedback:
            return
        
        # 获取当前对象
        person = self._store.people.get(person_id)
        if not person:
            return
        
        # 初始化该轮次的反馈状态跟踪
        if person_id not in self._feedback_round_state:
            self._feedback_round_state[person_id] = {}
        if round_id and round_id not in self._feedback_round_state[person_id]:
            self._feedback_round_state[person_id][round_id] = {
                "like_applied": False,
                "dislike_applied": False,
                "base_intimacy": person.intimacy,  # 记录轮次开始时的亲密度基准
            }
        
        round_state = self._feedback_round_state.get(person_id, {}).get(round_id, {}) if round_id else {}
        
        # 统计该轮次内当前所有消息的反馈状态
        has_like = False
        has_dislike = False
        if round_id:
            for msg in cache:
                if msg.get("round_id") == round_id:
                    fb = msg.get("feedback")
                    if fb == "like":
                        has_like = True
                    elif fb == "dislike":
                        has_dislike = True
        
        # 计算亲密度最终值（相对于轮次开始时的基准）
        base_intimacy = round_state.get("base_intimacy", person.intimacy)
        intimacy_delta = 0
        reason_parts = []
        
        if has_like:
            intimacy_delta += 2
            reason_parts.append("用户喜欢回复 (+2)")
        if has_dislike:
            intimacy_delta -= 1
            reason_parts.append("用户不喜欢回复 (-1)")
        
        # 计算最终亲密度
        final_intimacy = max(0, min(100, base_intimacy + intimacy_delta))
        
        # 只有当最终值与当前值不同时才记录（使用 round_id 替换之前的临时值）
        if final_intimacy != person.intimacy or round_id:
            reason = " & ".join(reason_parts) if reason_parts else "反馈已清除"
            if not reason_parts:
                # 如果没有任何反馈，恢复到基准值
                final_intimacy = base_intimacy
                reason = "反馈已清除"
            self._store.record_intimacy(person_id, final_intimacy, reason, round_id=round_id)
        
        # 更新其他指标（基于当前反馈状态）
        acceptance_delta = 0.0
        rejection_delta = 0
        
        # 根据当前消息的反馈变化更新（这些不需要去重，每次反馈都影响）
        if old_feedback == "like":
            acceptance_delta -= 0.05
            rejection_delta += 1
        elif old_feedback == "dislike":
            acceptance_delta += 0.05
            rejection_delta -= 1
        
        if feedback == "like":
            acceptance_delta += 0.05
            rejection_delta -= 1
        elif feedback == "dislike":
            acceptance_delta -= 0.05
            rejection_delta += 1
        
        person.acceptance_rate = max(0.0, min(1.0, person.acceptance_rate + acceptance_delta))
        person.rejection_count = max(0, person.rejection_count + rejection_delta)
        
        # 保存数据（不刷新联系人列表，避免重建对话列表导致其他消息无法操作）
        self._store.sync_to_data_dir(self._system.settings.data_dir)
        
        # 更新左侧联系人列表中的亲密度显示
        self._update_contact_item_intimacy(person_id, person.intimacy)
        
        # 更新当前对象的画像面板（包括折线图，因为亲密度变化了）
        self._update_profile_panel(person)

    def _clear_conversation(self) -> None:
        self.conversation_list.clear()

    def _render_conversation(self, person_id: str) -> None:
        self._clear_conversation()
        history = self._conversation_cache.get(person_id, [])
        for item in history:
            self._append_chat_message(
                item["role"],
                item["text"],
                record=False,
                feedback=item.get("feedback"),
                message_id=item.get("message_id"),
                round_id=item.get("round_id"),
            )

    def _show_typing_indicator(self, target_person_id: str) -> Optional[QListWidgetItem]:
        """显示等待输入指示器。
        
        Returns:
            等待指示器的列表项，用于后续移除
        """
        # 只有当目标对象是当前选中对象时才显示
        if target_person_id != self._current_person_id:
            return None
        
        item = QListWidgetItem()
        item.setSizeHint(QSize(520, 50))
        widget = TypingIndicatorWidget()
        self.conversation_list.addItem(item)
        self.conversation_list.setItemWidget(item, widget)
        self.conversation_list.scrollToBottom()
        return item
    
    def _remove_typing_indicator(self, indicator_item: Optional[QListWidgetItem]) -> None:
        """移除等待输入指示器。"""
        if indicator_item is None:
            return
        
        # 获取并停止动画
        widget = self.conversation_list.itemWidget(indicator_item)
        if isinstance(widget, TypingIndicatorWidget):
            widget.stop_animation()
        
        # 从列表中移除
        row = self.conversation_list.row(indicator_item)
        if row >= 0:
            self.conversation_list.takeItem(row)

    def _update_conversation_item_widths(self) -> None:
        max_width = int(self.conversation_list.viewport().width() * 0.6)
        for idx in range(self.conversation_list.count()):
            item = self.conversation_list.item(idx)
            widget = self.conversation_list.itemWidget(item)
            if isinstance(widget, ChatMessageWidget):
                widget.set_max_width(max_width)
                item.setSizeHint(widget.sizeHint())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_conversation_item_widths()

    # ---------------- 模块三：长期记忆 ----------------

    def _build_memory_page(self) -> QWidget:
        """构建长期记忆页面 - 三种记忆类型。"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Tab切换：对象特征 / 关系事件 / 沟通策略
        self.memory_tabs = QTabBar()
        self.memory_tabs.addTab("对象特征")
        self.memory_tabs.addTab("关系事件")
        self.memory_tabs.addTab("沟通策略")
        self.memory_tabs.currentChanged.connect(self._refresh_memory_lists)

        # 使用滚动区域包裹记忆列表
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.memory_list_container = QWidget()
        self.memory_list_layout = QVBoxLayout(self.memory_list_container)
        self.memory_list_layout.setSpacing(8)
        self.memory_list_layout.setContentsMargins(4, 4, 4, 4)
        self.memory_list_layout.addStretch()
        
        scroll_area.setWidget(self.memory_list_container)

        btn_row = QHBoxLayout()
        self.btn_add_memory = QPushButton("新增")
        apply_primary_style(self.btn_add_memory, width=80)
        self.btn_ai_extract = QPushButton("AI 提取")
        apply_info_style(self.btn_ai_extract, width=90)
        self.btn_ai_extract.setToolTip("从对话记录中自动提取记忆")
        self.btn_summarize = QPushButton("记忆摘要")
        apply_info_style(self.btn_summarize, width=90)
        self.btn_add_memory.clicked.connect(self._on_add_memory)
        self.btn_ai_extract.clicked.connect(self._on_ai_extract_memory)
        self.btn_summarize.clicked.connect(self._on_summarize_memory)

        btn_row.addWidget(self.btn_add_memory)
        btn_row.addWidget(self.btn_ai_extract)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_summarize)

        layout.addWidget(self.memory_tabs)
        layout.addWidget(scroll_area)
        layout.addLayout(btn_row)
        return page

    def _update_memory_panel(self, person: Person) -> None:
        self._refresh_memory_lists()

    def _clear_memory_list(self) -> None:
        """清空记忆列表中的所有卡片。"""
        while self.memory_list_layout.count() > 1:  # 保留最后的 stretch
            item = self.memory_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _refresh_memory_lists(self) -> None:
        """刷新当前Tab对应类型的记忆列表（使用卡片组件）。"""
        self._clear_memory_list()
        
        person = self._get_current_person()
        if not person:
            return
        
        tab_index = self.memory_tabs.currentIndex()
        
        if tab_index == 0:
            # 对象特征 (ProfileMemory)
            items = self._store.memory_service.query_profile_memories(person.person_id)
            for memory in items:
                source_text = "手动录入" if memory.source == "manual" else "模型提取"
                confidence_pct = int(memory.confidence * 100)
                # 根据置信度选择颜色
                if confidence_pct >= 70:
                    badge_color = "#4caf50"  # 绿色
                elif confidence_pct >= 40:
                    badge_color = "#ff9800"  # 橙色
                else:
                    badge_color = "#9e9e9e"  # 灰色
                
                card = MemoryCardWidget(
                    memory_id=memory.memory_id,
                    memory_type="profile",
                    title=memory.content,
                    subtitle=f"来源: {source_text} · 创建于: {memory.created_at[:10] if memory.created_at else '未知'}",
                    badge_text=f"{confidence_pct}%",
                    badge_color=badge_color,
                    parent=self.memory_list_container,
                )
                card.edit_clicked.connect(self._on_edit_memory_card)
                card.delete_clicked.connect(self._on_delete_memory_card)
                self.memory_list_layout.insertWidget(self.memory_list_layout.count() - 1, card)
        
        elif tab_index == 1:
            # 关系事件 (ExperienceMemory)
            items = self._store.memory_service.query_experience_memories(person.person_id)
            for memory in items:
                source_text = "手动录入" if memory.source == "manual" else "模型提取"
                impact_val = int(memory.impact * 100)
                impact_text = f"+{impact_val}%" if impact_val >= 0 else f"{impact_val}%"
                time_text = memory.event_time or "未知时间"
                note_text = f" · {memory.note}" if memory.note else ""
                # 根据影响选择颜色
                if impact_val >= 30:
                    badge_color = "#4caf50"  # 正面 - 绿色
                elif impact_val <= -30:
                    badge_color = "#f44336"  # 负面 - 红色
                else:
                    badge_color = "#2196f3"  # 中性 - 蓝色
                
                card = MemoryCardWidget(
                    memory_id=memory.memory_id,
                    memory_type="experience",
                    title=memory.event,
                    subtitle=f"时间: {time_text} · 来源: {source_text}{note_text}",
                    badge_text=impact_text,
                    badge_color=badge_color,
                    parent=self.memory_list_container,
                )
                card.edit_clicked.connect(self._on_edit_memory_card)
                card.delete_clicked.connect(self._on_delete_memory_card)
                self.memory_list_layout.insertWidget(self.memory_list_layout.count() - 1, card)
        
        elif tab_index == 2:
            # 沟通策略 (StrategyMemory)
            items = self._store.memory_service.query_strategy_memories(person.person_id)
            for memory in items:
                eff_pct = int(memory.effectiveness * 100)
                evidence_text = f"验证 {memory.evidence_count} 次"
                # 根据有效性选择颜色
                if eff_pct >= 60:
                    badge_color = "#4caf50"  # 有效 - 绿色
                elif eff_pct <= 30:
                    badge_color = "#f44336"  # 无效 - 红色
                else:
                    badge_color = "#ff9800"  # 一般 - 橙色
                
                card = MemoryCardWidget(
                    memory_id=memory.memory_id,
                    memory_type="strategy",
                    title=memory.pattern,
                    subtitle=f"有效性: {eff_pct}% · {evidence_text}",
                    badge_text=f"{eff_pct}%",
                    badge_color=badge_color,
                    parent=self.memory_list_container,
                )
                card.edit_clicked.connect(self._on_edit_memory_card)
                card.delete_clicked.connect(self._on_delete_memory_card)
                self.memory_list_layout.insertWidget(self.memory_list_layout.count() - 1, card)

    def _current_memory_type(self) -> str:
        """返回当前Tab对应的记忆类型标识。"""
        index = self.memory_tabs.currentIndex()
        return ["profile", "experience", "strategy"][index]

    def _on_add_memory(self) -> None:
        """新增记忆 - 根据当前Tab类型打开对应对话框。"""
        person = self._get_current_person()
        if not person:
            QMessageBox.information(self, "提示", "请先选择一个关系对象。")
            return
        
        tab_index = self.memory_tabs.currentIndex()
        
        if tab_index == 0:
            # 新增对象特征
            dialog = ProfileMemoryDialog(self)
            if dialog.exec() != QDialog.Accepted:
                return
            data = dialog.get_data()
            if not data:
                return
            
            # 检查是否存在相同特征内容（精确匹配）
            new_content = data["content"].strip()
            existing_profiles = self._store.memory_service.query_profile_memories(person.person_id)
            matched_profile = None
            
            for profile in existing_profiles:
                # 精确匹配特征内容（忽略大小写和首尾空格）
                if profile.content.strip().lower() == new_content.lower():
                    matched_profile = profile
                    break
            
            if matched_profile:
                # 找到相同特征，询问是否替换
                reply = QMessageBox.question(
                    self,
                    "特征已存在",
                    f"发现相同特征内容：\n\n「{matched_profile.content}」\n\n"
                    f"当前置信度: {matched_profile.confidence * 100:.0f}%\n"
                    f"新输入置信度: {data['confidence'] * 100:.0f}%\n\n"
                    f"是否替换？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # 替换：删除旧的，创建新的
                    self._store.memory_service.delete_memory(
                        person.person_id,
                        matched_profile.memory_id,
                        "profile"
                    )
                    self._store.memory_service.create_profile_memory(
                        person_id=person.person_id,
                        content=data["content"],
                        confidence=data["confidence"],
                        source=data["source"],
                    )
                # 用户选择不替换，直接返回不做任何操作
                else:
                    return
            else:
                # 没有相同特征，直接创建
                self._store.memory_service.create_profile_memory(
                    person_id=person.person_id,
                    content=data["content"],
                    confidence=data["confidence"],
                    source=data["source"],
                )
        
        elif tab_index == 1:
            # 新增关系事件
            dialog = ExperienceMemoryDialog(self)
            if dialog.exec() != QDialog.Accepted:
                return
            data = dialog.get_data()
            if not data:
                return
            self._store.memory_service.create_experience_memory(
                person_id=person.person_id,
                event=data["event"],
                impact=data["impact"],
                event_time=data.get("event_time"),
                note=data.get("note"),
                source=data["source"],
            )
        
        elif tab_index == 2:
            # 新增沟通策略
            dialog = StrategyMemoryDialog(self)
            if dialog.exec() != QDialog.Accepted:
                return
            data = dialog.get_data()
            if not data:
                return
            
            # 检查是否存在相同策略模式（精确匹配）
            new_pattern = data["pattern"].strip()
            existing_strategies = self._store.memory_service.query_strategy_memories(person.person_id)
            matched_strategy = None
            
            for strategy in existing_strategies:
                # 精确匹配策略模式（忽略大小写和首尾空格）
                if strategy.pattern.strip().lower() == new_pattern.lower():
                    matched_strategy = strategy
                    break
            
            if matched_strategy:
                # 找到相同策略，融合有效性
                old_eff = matched_strategy.effectiveness
                new_eff = data["effectiveness"]
                old_count = matched_strategy.evidence_count
                
                # 加权平均融合
                merged_eff = (old_eff * old_count + new_eff) / (old_count + 1)
                
                reply = QMessageBox.question(
                    self,
                    "策略已存在",
                    f"发现相同策略模式：\n\n「{matched_strategy.pattern}」\n\n"
                    f"当前有效性: {old_eff * 100:.0f}% (验证 {old_count} 次)\n"
                    f"新输入有效性: {new_eff * 100:.0f}%\n"
                    f"融合后有效性: {merged_eff * 100:.0f}% (验证 {old_count + 1} 次)\n\n"
                    f"是否融合？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # 融合
                    matched_strategy.effectiveness = merged_eff
                    matched_strategy.evidence_count = old_count + 1
                    self._store.memory_service.update_strategy_memory(matched_strategy)
                else:
                    # 用户选择不融合，创建新的
                    self._store.memory_service.create_strategy_memory(
                        person_id=person.person_id,
                        pattern=data["pattern"],
                        effectiveness=data["effectiveness"],
                        source=data["source"],
                    )
            else:
                # 没有相同策略，直接创建
                self._store.memory_service.create_strategy_memory(
                    person_id=person.person_id,
                    pattern=data["pattern"],
                    effectiveness=data["effectiveness"],
                    source=data["source"],
                )
        
        # 保存到文件
        self._store.sync_to_data_dir(self._system.settings.data_dir)
        self._refresh_memory_lists()

    def _on_edit_memory_card(self, memory_id: str, memory_type: str) -> None:
        """编辑记忆卡片 - 根据记忆类型打开对应对话框。"""
        person = self._get_current_person()
        if not person:
            return
        
        memory = self._store.memory_service.get_memory_by_id(person.person_id, memory_id, memory_type)
        if not memory:
            QMessageBox.warning(self, "错误", "未找到该记忆条目。")
            return
        
        if memory_type == "profile":
            dialog = ProfileMemoryDialog(self, memory)
            if dialog.exec() != QDialog.Accepted:
                return
            data = dialog.get_data()
            if not data:
                return
            # 更新 memory 对象的属性
            memory.content = data["content"]
            memory.confidence = data["confidence"]
            self._store.memory_service.update_profile_memory(memory)
        
        elif memory_type == "experience":
            dialog = ExperienceMemoryDialog(self, memory)
            if dialog.exec() != QDialog.Accepted:
                return
            data = dialog.get_data()
            if not data:
                return
            # 更新 memory 对象的属性
            memory.event = data["event"]
            memory.impact = data["impact"]
            memory.event_time = data.get("event_time")
            memory.note = data.get("note")
            self._store.memory_service.update_experience_memory(memory)
        
        elif memory_type == "strategy":
            dialog = StrategyMemoryDialog(self, memory)
            if dialog.exec() != QDialog.Accepted:
                return
            data = dialog.get_data()
            if not data:
                return
            # 更新 memory 对象的属性
            memory.pattern = data["pattern"]
            memory.effectiveness = data["effectiveness"]
            self._store.memory_service.update_strategy_memory(memory)
        
        # 保存到文件
        self._store.sync_to_data_dir(self._system.settings.data_dir)
        self._refresh_memory_lists()

    def _on_delete_memory_card(self, memory_id: str, memory_type: str) -> None:
        """删除记忆卡片 - 弹出确认对话框。"""
        type_names = {
            "profile": "对象特征",
            "experience": "关系事件", 
            "strategy": "沟通策略",
        }
        type_name = type_names.get(memory_type, "记忆")
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除这条{type_name}吗？\n\n此操作无法撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        
        if reply == QMessageBox.Yes:
            person = self._get_current_person()
            if person:
                self._store.memory_service.delete_memory(person.person_id, memory_id, memory_type)
                # 保存到文件
                self._store.sync_to_data_dir(self._system.settings.data_dir)
                self._refresh_memory_lists()

    def _on_summarize_memory(self) -> None:
        """记忆摘要 - 展示当前关系对象的记忆统计和摘要。"""
        person = self._get_current_person()
        if not person:
            QMessageBox.information(self, "提示", "请先选择一个关系对象。")
            return
        
        # 获取完整摘要
        profile_summary = self._store.memory_service.summarize_for_profile(person.person_id)
        reply_summary = self._store.memory_service.summarize_for_reply(person.person_id)
        
        msg_parts = []
        
        # 统计信息
        profile_count = len(profile_summary.get("profile_traits", []))
        experience_count = len(profile_summary.get("key_experiences", []))
        strategy_count = len(self._store.memory_service.query_strategy_memories(person.person_id))
        msg_parts.append(f"📊 记忆统计\n对象特征: {profile_count} 条\n关系事件: {experience_count} 条\n沟通策略: {strategy_count} 条")
        
        # 高置信度特征
        if reply_summary["profile_hints"]:
            hints = reply_summary["profile_hints"][:5]  # 最多显示5条
            msg_parts.append("🎯 高置信度特征（可用于回复建议）\n" + "\n".join(f"• {h}" for h in hints))
        
        # 有效策略
        if reply_summary["effective_strategies"]:
            strategies = reply_summary["effective_strategies"][:3]
            msg_parts.append("✅ 有效沟通策略\n" + "\n".join(f"• {s}" for s in strategies))
        
        # 应避免策略
        if reply_summary["avoid_strategies"]:
            avoids = reply_summary["avoid_strategies"][:3]
            msg_parts.append("⚠️ 应避免的策略\n" + "\n".join(f"• {s}" for s in avoids))
        
        if len(msg_parts) == 1:
            msg_parts.append("\n暂无足够数据生成建议，请添加更多记忆条目。")
        
        QMessageBox.information(self, f"「{person.display_name}」记忆摘要", "\n\n".join(msg_parts))

    def _on_ai_extract_memory(self) -> None:
        """AI 自动提取记忆 - 从对话中分析并提取记忆。
        
        流程：
        1. 提取记忆
        2. 用户选择要保存的条目
        3. 对象特征和关系事件：语义比对，发现重复则询问用户是替换还是保留
        4. 沟通策略：LLM判断策略模式是否一致，一致则询问是否融合
        """
        person = self._get_current_person()
        if not person:
            QMessageBox.information(self, "提示", "请先选择一个关系对象。")
            return
        
        # 获取该联系人的对话记录
        raw_conversation = self._conversation_cache.get(person.person_id, [])
        if not raw_conversation:
            QMessageBox.information(
                self, 
                "提示", 
                "当前联系人没有对话记录。\n\n请先在「回复建议」模块中进行对话，然后再使用 AI 提取功能。"
            )
            return
        
        # 过滤并标记对话记录（优先使用被喜欢的回复，排除被不喜欢的回复）
        conversation = []
        for msg in raw_conversation:
            feedback = msg.get("feedback")
            if feedback == "dislike":
                # 被不喜欢的回复不参与 AI 提取
                continue
            msg_copy = {
                "role": msg["role"],
                "text": msg["text"],
            }
            # 标记被喜欢的回复（AI 可以优先参考）
            if feedback == "like":
                msg_copy["liked"] = True
            conversation.append(msg_copy)
        
        if not conversation:
            QMessageBox.information(
                self, 
                "提示", 
                "当前联系人没有有效的对话记录（所有回复都被标记为不喜欢）。"
            )
            return
        
        # 获取已有记忆（用于去重）
        existing_memories = self._store.memory_service.summarize_for_profile(person.person_id)
        
        # 创建提取器
        extractor = MemoryExtractor(self._system.settings)
        
        # 打开提取对话框
        dialog = MemoryExtractionDialog(self)
        dialog.start_extraction(extractor, person.display_name, conversation, existing_memories)
        
        if dialog.exec() != QDialog.Accepted:
            return
        
        selected = dialog.get_selected_memories()
        saved_count = 0
        replaced_count = 0
        merged_count = 0
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info("=== AI 提取开始保存 ===")
        logger.info("选中的对象特征: %d 条", len(selected.get("profiles", [])))
        logger.info("选中的关系事件: %d 条", len(selected.get("experiences", [])))
        logger.info("选中的沟通策略: %d 条", len(selected.get("strategies", [])))
        
        # ========== 处理对象特征 ==========
        profiles_to_save = selected.get("profiles", [])
        existing_profiles = self._store.memory_service.query_profile_memories(person.person_id)
        
        if profiles_to_save and existing_profiles:
            # 构建比对数据
            items_to_compare = []
            for new_item in profiles_to_save:
                items_to_compare.append({
                    "new_text": new_item.content,
                    "existing_texts": [p.content for p in existing_profiles],
                })
            
            # 调用语义比对
            comparisons = extractor.compare_semantic_similarity(items_to_compare, "profile")
            
            # 找出有重复的项
            duplicates = []
            duplicate_indices = set()
            for comp in comparisons:
                new_idx = comp.get("new_index", 0) - 1
                similar_idx = comp.get("similar_existing_index")
                if similar_idx is not None and 0 <= new_idx < len(profiles_to_save):
                    duplicates.append({
                        "new_item": profiles_to_save[new_idx],
                        "existing_item": existing_profiles[similar_idx - 1],
                        "reason": comp.get("similarity_reason", "语义相似"),
                    })
                    duplicate_indices.add(new_idx)
            
            # 如果有重复，显示确认对话框
            if duplicates:
                dup_dialog = DuplicateMemoryDialog(self, duplicates, "profile")
                if dup_dialog.exec() == QDialog.Accepted:
                    decisions = dup_dialog.get_decisions()
                    # 处理决定
                    for idx, decision in decisions.items():
                        dup = duplicates[idx]
                        if decision == "replace":
                            # 删除旧的，保存新的
                            self._store.memory_service.delete_memory(
                                person.person_id, 
                                dup["existing_item"].memory_id, 
                                "profile"
                            )
                            self._store.memory_service.create_profile_memory(
                                person_id=person.person_id,
                                content=dup["new_item"].content,
                                confidence=dup["new_item"].confidence,
                                source="model",
                            )
                            replaced_count += 1
                        elif decision == "keep_both":
                            # 保留两者
                            self._store.memory_service.create_profile_memory(
                                person_id=person.person_id,
                                content=dup["new_item"].content,
                                confidence=dup["new_item"].confidence,
                                source="model",
                            )
                            saved_count += 1
                        # skip: 不做任何操作
            
            # 保存没有重复的项
            for idx, item in enumerate(profiles_to_save):
                if idx not in duplicate_indices:
                    self._store.memory_service.create_profile_memory(
                        person_id=person.person_id,
                        content=item.content,
                        confidence=item.confidence,
                        source="model",
                    )
                    saved_count += 1
        else:
            # 没有现有记忆，直接保存
            for item in profiles_to_save:
                self._store.memory_service.create_profile_memory(
                    person_id=person.person_id,
                    content=item.content,
                    confidence=item.confidence,
                    source="model",
                )
                saved_count += 1
        
        # ========== 处理关系事件 ==========
        experiences_to_save = selected.get("experiences", [])
        existing_experiences = self._store.memory_service.query_experience_memories(person.person_id)
        
        if experiences_to_save and existing_experiences:
            # 构建比对数据
            items_to_compare = []
            for new_item in experiences_to_save:
                items_to_compare.append({
                    "new_text": new_item.event,
                    "existing_texts": [e.event for e in existing_experiences],
                })
            
            # 调用语义比对
            logger.info("关系事件: 调用语义比对, 新项=%d, 现有=%d", len(experiences_to_save), len(existing_experiences))
            comparisons = extractor.compare_semantic_similarity(items_to_compare, "experience")
            logger.info("关系事件: 语义比对返回 %d 个结果", len(comparisons))
            
            # 找出有重复的项
            duplicates = []
            duplicate_indices = set()
            for comp in comparisons:
                new_idx = comp.get("new_index", 0) - 1
                similar_idx = comp.get("similar_existing_index")
                if similar_idx is not None and 0 <= new_idx < len(experiences_to_save):
                    duplicates.append({
                        "new_item": experiences_to_save[new_idx],
                        "existing_item": existing_experiences[similar_idx - 1],
                        "reason": comp.get("similarity_reason", "语义相似"),
                    })
                    duplicate_indices.add(new_idx)
            
            logger.info("关系事件: 发现 %d 个重复项, duplicate_indices=%s", len(duplicates), duplicate_indices)
            
            # 如果有重复，显示确认对话框
            if duplicates:
                dup_dialog = DuplicateMemoryDialog(self, duplicates, "experience")
                if dup_dialog.exec() == QDialog.Accepted:
                    decisions = dup_dialog.get_decisions()
                    for idx, decision in decisions.items():
                        dup = duplicates[idx]
                        if decision == "replace":
                            self._store.memory_service.delete_memory(
                                person.person_id, 
                                dup["existing_item"].memory_id, 
                                "experience"
                            )
                            self._store.memory_service.create_experience_memory(
                                person_id=person.person_id,
                                event=dup["new_item"].event,
                                impact=dup["new_item"].impact,
                                event_time=dup["new_item"].event_time,
                                source="model",
                            )
                            replaced_count += 1
                        elif decision == "keep_both":
                            self._store.memory_service.create_experience_memory(
                                person_id=person.person_id,
                                event=dup["new_item"].event,
                                impact=dup["new_item"].impact,
                                event_time=dup["new_item"].event_time,
                                source="model",
                            )
                            saved_count += 1
                else:
                    logger.info("关系事件: 用户取消了重复确认对话框")
            
            # 保存没有重复的项
            non_dup_count = 0
            for idx, item in enumerate(experiences_to_save):
                if idx not in duplicate_indices:
                    self._store.memory_service.create_experience_memory(
                        person_id=person.person_id,
                        event=item.event,
                        impact=item.impact,
                        event_time=item.event_time,
                        source="model",
                    )
                    saved_count += 1
                    non_dup_count += 1
            logger.info("关系事件: 保存了 %d 个非重复项", non_dup_count)
        else:
            logger.info("关系事件: 无现有记忆，直接保存 %d 条", len(experiences_to_save))
            for item in experiences_to_save:
                self._store.memory_service.create_experience_memory(
                    person_id=person.person_id,
                    event=item.event,
                    impact=item.impact,
                    event_time=item.event_time,
                    source="model",
                )
                saved_count += 1
        
        logger.info("关系事件处理完成，当前 saved_count=%d", saved_count)
        
        # ========== 处理沟通策略 ==========
        strategies_to_save = selected.get("strategies", [])
        existing_strategies = self._store.memory_service.query_strategy_memories(person.person_id)
        
        for new_strategy in strategies_to_save:
            if existing_strategies:
                # 使用LLM判断策略模式是否一致
                existing_patterns = [s.pattern for s in existing_strategies]
                match_result = extractor.compare_strategy_patterns(
                    new_strategy.pattern, 
                    existing_patterns
                )
                
                if match_result:
                    # 找到相似的策略，询问用户是否融合
                    matched_strategy = existing_strategies[match_result["index"]]
                    merge_dialog = StrategyMergeDialog(
                        self, 
                        new_strategy, 
                        matched_strategy,
                        match_result.get("reason", "")
                    )
                    result = merge_dialog.exec()
                    
                    if result == QDialog.Accepted:
                        # 用户选择融合
                        merged_eff = merge_dialog.get_merged_effectiveness()
                        matched_strategy.effectiveness = merged_eff
                        matched_strategy.evidence_count += 1
                        self._store.memory_service.update_strategy_memory(matched_strategy)
                        merged_count += 1
                    elif result == 2:
                        # 用户选择保留两者
                        self._store.memory_service.create_strategy_memory(
                            person_id=person.person_id,
                            pattern=new_strategy.pattern,
                            effectiveness=new_strategy.effectiveness,
                            source="model",
                        )
                        saved_count += 1
                    # result == QDialog.Rejected: 跳过
                else:
                    # 没有相似的策略，直接保存
                    self._store.memory_service.create_strategy_memory(
                        person_id=person.person_id,
                        pattern=new_strategy.pattern,
                        effectiveness=new_strategy.effectiveness,
                        source="model",
                    )
                    saved_count += 1
            else:
                # 没有现有策略，直接保存
                self._store.memory_service.create_strategy_memory(
                    person_id=person.person_id,
                    pattern=new_strategy.pattern,
                    effectiveness=new_strategy.effectiveness,
                    source="model",
                )
                saved_count += 1
        
        # 保存到文件并刷新UI
        total_changes = saved_count + replaced_count + merged_count
        if total_changes > 0:
            self._store.sync_to_data_dir(self._system.settings.data_dir)
            self._refresh_memory_lists()
            
            # 构建结果消息
            msg_parts = []
            if saved_count > 0:
                msg_parts.append(f"新增 {saved_count} 条")
            if replaced_count > 0:
                msg_parts.append(f"替换 {replaced_count} 条")
            if merged_count > 0:
                msg_parts.append(f"融合 {merged_count} 条策略")
            
            QMessageBox.information(
                self, 
                "提取完成", 
                f"成功处理记忆：{', '.join(msg_parts)}。"
            )

    # ---------------- Utilities ----------------

    def _center_on_screen(self) -> None:
        """将窗口居中显示在屏幕上。"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())

    def _get_current_person(self) -> Optional[Person]:
        if not self._current_person_id:
            return None
        return self._store.people.get(self._current_person_id)

    def _import_data(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "导入关系数据", "", "JSON 文件 (*.json)")
        if not file_path:
            return
        try:
            data = json.loads(open(file_path, "r", encoding="utf-8").read())
        except Exception as err:
            QMessageBox.critical(self, "导入失败", f"无法读取文件：{err}")
            return
        self._store.people.clear()
        self._store.memories.clear()
        for item in data.get("people", []):
            person = Person(**item)
            self._store.add_person(person)
        for pid, memories in data.get("memories", {}).items():
            self._store.memories[pid] = [MemoryItem(**m) for m in memories]
        self._refresh_contact_list()
        QMessageBox.information(self, "导入完成", "关系数据已导入。")

    def _export_data(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "导出关系数据", "relationship_data.json", "JSON 文件 (*.json)")
        if not file_path:
            return
        data = {
            "people": [person.__dict__ for person in self._store.list_people()],
            "memories": {
                pid: [m.__dict__ for m in items]
                for pid, items in self._store.memories.items()
            },
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as err:
            QMessageBox.critical(self, "导出失败", f"无法写入文件：{err}")
            return
        QMessageBox.information(self, "导出完成", "关系数据已导出。")
