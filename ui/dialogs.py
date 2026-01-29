"""对话框：添加/编辑关系对象、编辑记忆。"""

from __future__ import annotations

from typing import List, Optional, Union

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, Signal, QThread

from .store import (
    Person, MemoryItem, 
    ProfileMemory, ExperienceMemory, StrategyMemory
)
from .button_styles import (
    apply_primary_style,
    apply_secondary_style,
    apply_warning_style,
    apply_info_style,
    apply_danger_style,
    apply_combobox_style,
)

from core.intimacy_manager import IntimacyManager

# 从 IntimacyManager 获取统一的关系类型列表
RELATIONSHIP_TYPES = IntimacyManager.get_relationship_types()
RELATIVE_ROLES = ["上级", "平级", "下级"]
AGE_GROUPS = ["年长", "同龄", "年幼"]
GOAL_OPTIONS = ["维持关系", "拉近关系", "保持距离", "提升专业感"]


class PersonDialog(QDialog):
    """添加/编辑关系对象对话框。"""

    def __init__(
        self,
        parent=None,
        person: Optional[Person] = None,
        existing_names: Optional[set[str]] = None,
    ):
        super().__init__(parent)
        self._person = person
        self._existing_names = {name.strip() for name in existing_names or set() if name.strip()}
        self._data: Optional[dict] = None

        self.setWindowTitle("添加关系对象" if person is None else "编辑关系对象")
        self.resize(480, 480)

        layout = QVBoxLayout(self)

        base_group = QGroupBox("基本信息（必填）")
        base_form = QFormLayout(base_group)
        self.name_input = QLineEdit()
        self.avatar_path = ""
        avatar_row = QHBoxLayout()
        self.avatar_path_input = QLineEdit()
        self.avatar_path_input.setReadOnly(True)
        self.avatar_path_input.setPlaceholderText("可选：选择头像文件")
        pick_btn = QPushButton("选择头像")
        apply_info_style(pick_btn)
        pick_btn.clicked.connect(self._pick_avatar)
        avatar_row.addWidget(self.avatar_path_input, 1)
        avatar_row.addWidget(pick_btn)
        self.relationship_box = QComboBox()
        self.relationship_box.addItems(RELATIONSHIP_TYPES)
        apply_combobox_style(self.relationship_box)
        self.relative_box = QComboBox()
        self.relative_box.addItems(RELATIVE_ROLES)
        apply_combobox_style(self.relative_box)
        self.age_box = QComboBox()
        self.age_box.addItems(AGE_GROUPS)
        apply_combobox_style(self.age_box)

        base_form.addRow("姓名/备注名：", self.name_input)
        base_form.addRow("头像（可选）：", avatar_row)
        base_form.addRow("关系类型：", self.relationship_box)
        base_form.addRow("身份相对关系：", self.relative_box)
        base_form.addRow("年龄层：", self.age_box)

        goal_group = QGroupBox("关系目标（多选）")
        goal_layout = QVBoxLayout(goal_group)
        self.goal_checks: List[QCheckBox] = []
        for option in GOAL_OPTIONS:
            check = QCheckBox(option)
            self.goal_checks.append(check)
            goal_layout.addWidget(check)

        style_group = QGroupBox("初始性格标签（可选）")
        style_layout = QVBoxLayout(style_group)
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("使用逗号分隔，例如：不喜欢废话, 情绪稳定, 注重逻辑")
        style_layout.addWidget(QLabel("标签："))
        style_layout.addWidget(self.tags_input)

        notes_group = QGroupBox("补充说明（可选）")
        notes_layout = QVBoxLayout(notes_group)
        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(80)
        notes_layout.addWidget(self.notes_edit)

        layout.addWidget(base_group)
        layout.addWidget(goal_group)
        layout.addWidget(style_group)
        layout.addWidget(notes_group)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("确定")
        apply_primary_style(btn_ok)
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消")
        apply_secondary_style(btn_cancel)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        if person:
            self._load_person(person)

    def _load_person(self, person: Person) -> None:
        self.name_input.setText(person.name)
        self.relationship_box.setCurrentText(person.relationship_type)
        self.relative_box.setCurrentText(person.relative_role)
        self.age_box.setCurrentText(person.age_group)
        self.tags_input.setText(", ".join(person.style_tags))
        self.notes_edit.setPlainText(person.notes)
        self.avatar_path = person.avatar_path
        self.avatar_path_input.setText(person.avatar_path or "")
        for check in self.goal_checks:
            check.setChecked(check.text() in person.goals)

    def _pick_avatar(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择头像",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if not file_path:
            return
        self.avatar_path = file_path
        self.avatar_path_input.setText(file_path)

    def accept(self) -> None:
        data = self._build_data()
        if not data:
            return
        self._data = data
        super().accept()

    def get_data(self) -> Optional[dict]:
        return self._data

    def _build_data(self) -> Optional[dict]:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "姓名/备注名不能为空。")
            return None

        current_name = self._person.name.strip() if self._person else ""
        if name in self._existing_names and name != current_name:
            QMessageBox.warning(self, "提示", "姓名已存在，请更换不重复的姓名后再确定。")
            return None

        relationship_type = self.relationship_box.currentText()
        relative_role = self.relative_box.currentText()
        age_group = self.age_box.currentText()
        goals = [c.text() for c in self.goal_checks if c.isChecked()]
        tags_raw = self.tags_input.text().strip()
        style_tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        notes = self.notes_edit.toPlainText().strip()

        return {
            "name": name,
            "relationship_type": relationship_type,
            "relative_role": relative_role,
            "age_group": age_group,
            "goals": goals,
            "avatar_path": self.avatar_path,
            "style_tags": style_tags,
            "notes": notes,
        }


class MemoryDialog(QDialog):
    """新增/编辑记忆对话框。（旧版兼容）"""

    def __init__(self, parent=None, memory: Optional[MemoryItem] = None):
        super().__init__(parent)
        self._memory = memory

        self.setWindowTitle("新增记忆" if memory is None else "编辑记忆")
        self.resize(420, 320)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.type_box = QComboBox()
        self.type_box.addItem("性格记忆", "personality")
        self.type_box.addItem("对话偏好", "preference")
        self.type_box.addItem("关键事件", "event")
        self.source_box = QComboBox()
        self.source_box.addItem("手动", "manual")
        self.source_box.addItem("模型", "model")
        self.content_edit = QTextEdit()
        self.content_edit.setFixedHeight(120)

        form.addRow("记忆类型：", self.type_box)
        form.addRow("来源：", self.source_box)
        form.addRow("内容：", self.content_edit)

        layout.addLayout(form)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("确定")
        apply_primary_style(btn_ok)
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消")
        apply_secondary_style(btn_cancel)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        if memory:
            self._set_combo_by_data(self.type_box, memory.memory_type)
            self._set_combo_by_data(self.source_box, memory.source)
            self.content_edit.setPlainText(memory.content)

    def get_data(self) -> Optional[dict]:
        content = self.content_edit.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "提示", "记忆内容不能为空。")
            return None
        return {
            "memory_type": self.type_box.currentData(),
            "source": self.source_box.currentData(),
            "content": content,
        }

    @staticmethod
    def _set_combo_by_data(combo: QComboBox, data: str) -> None:
        for idx in range(combo.count()):
            if combo.itemData(idx) == data:
                combo.setCurrentIndex(idx)
                return


# =====================================================================
# 新版长期记忆对话框 - 三种类型分别对应不同的字段
# =====================================================================

class ProfileMemoryDialog(QDialog):
    """添加或编辑「对象特征」记忆。
    
    字段:
    - content: 特征内容（必填）
    - confidence: 置信度 0~1（滑块 0%~100%）
    - source: 来源 manual/model
    """

    SOURCE_MAP = {"手动录入": "manual", "模型提取": "model"}
    SOURCE_MAP_REV = {v: k for k, v in SOURCE_MAP.items()}

    def __init__(self, parent=None, memory: Optional[ProfileMemory] = None):
        super().__init__(parent)
        self.setWindowTitle("编辑对象特征" if memory else "添加对象特征")
        self._memory = memory
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # 特征内容
        self.content_edit = QTextEdit()
        self.content_edit.setAcceptRichText(False)
        self.content_edit.setPlaceholderText("例如：喜欢篮球、性格外向、不喜欢被打扰...")
        self.content_edit.setMaximumHeight(80)
        if memory:
            self.content_edit.setPlainText(memory.content)
            # 将光标移到开头以避免 Qt 警告
            cursor = self.content_edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.content_edit.setTextCursor(cursor)
        form.addRow("特征内容:", self.content_edit)

        # 置信度滑块
        confidence_widget = QHBoxLayout()
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setRange(0, 100)
        self.confidence_slider.setValue(int((memory.confidence if memory else 0.7) * 100))
        self.confidence_slider.setTickPosition(QSlider.TicksBelow)
        self.confidence_slider.setTickInterval(10)
        self.confidence_label = QLabel(f"{self.confidence_slider.value()}%")
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_label.setText(f"{v}%")
        )
        confidence_widget.addWidget(self.confidence_slider)
        confidence_widget.addWidget(self.confidence_label)
        form.addRow("置信度:", confidence_widget)

        # 来源
        self.source_box = QComboBox()
        self.source_box.addItems(list(self.SOURCE_MAP.keys()))
        if memory:
            idx = list(self.SOURCE_MAP.values()).index(memory.source)
            self.source_box.setCurrentIndex(idx)
        form.addRow("来源:", self.source_box)

        layout.addLayout(form)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("确定")
        apply_primary_style(btn_ok)
        btn_ok.clicked.connect(self._validate_and_accept)
        btn_cancel = QPushButton("取消")
        apply_secondary_style(btn_cancel)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def _validate_and_accept(self):
        if not self.content_edit.toPlainText().strip():
            QMessageBox.warning(self, "提示", "特征内容不能为空")
            return
        self.accept()

    def get_data(self) -> Optional[dict]:
        content = self.content_edit.toPlainText().strip()
        if not content:
            return None
        return {
            "content": content,
            "confidence": self.confidence_slider.value() / 100.0,
            "source": self.SOURCE_MAP[self.source_box.currentText()],
        }


class ExperienceMemoryDialog(QDialog):
    """添加或编辑「关系事件」记忆。
    
    字段:
    - event: 事件描述（必填）
    - impact: 影响 -1~+1（滑块 -100%~+100%）
    - event_time: 发生时间（可选）
    - note: 备注（可选）
    - source: 来源 manual/model
    """

    SOURCE_MAP = {"手动录入": "manual", "模型提取": "model"}
    SOURCE_MAP_REV = {v: k for k, v in SOURCE_MAP.items()}

    def __init__(self, parent=None, memory: Optional[ExperienceMemory] = None):
        super().__init__(parent)
        self.setWindowTitle("编辑关系事件" if memory else "添加关系事件")
        self._memory = memory
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # 事件描述
        self.event_edit = QTextEdit()
        self.event_edit.setAcceptRichText(False)
        self.event_edit.setPlaceholderText("例如：一起看了电影、发生了争吵、帮助解决了问题...")
        self.event_edit.setMaximumHeight(80)
        if memory:
            self.event_edit.setPlainText(memory.event)
            # 将光标移到开头以避免 Qt 警告
            cursor = self.event_edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.event_edit.setTextCursor(cursor)
        form.addRow("事件描述:", self.event_edit)

        # 影响滑块 (-100% ~ +100%)
        impact_widget = QHBoxLayout()
        self.impact_slider = QSlider(Qt.Horizontal)
        self.impact_slider.setRange(-100, 100)
        initial_impact = int((memory.impact if memory else 0.0) * 100)
        self.impact_slider.setValue(initial_impact)
        self.impact_slider.setTickPosition(QSlider.TicksBelow)
        self.impact_slider.setTickInterval(20)
        self.impact_label = QLabel(self._format_impact(initial_impact))
        self.impact_slider.valueChanged.connect(
            lambda v: self.impact_label.setText(self._format_impact(v))
        )
        impact_widget.addWidget(self.impact_slider)
        impact_widget.addWidget(self.impact_label)
        form.addRow("关系影响:", impact_widget)

        # 提示标签
        impact_hint = QLabel("← 负面影响 | 正面影响 →")
        impact_hint.setStyleSheet("color: #888; font-size: 11px;")
        impact_hint.setAlignment(Qt.AlignCenter)
        form.addRow("", impact_hint)

        # 发生时间
        self.time_edit = QLineEdit()
        self.time_edit.setPlaceholderText("例如：2024-01-15 或 上个月")
        if memory and memory.event_time:
            self.time_edit.setText(memory.event_time)
        form.addRow("发生时间:", self.time_edit)

        # 备注
        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("可选的补充说明...")
        if memory and memory.note:
            self.note_edit.setText(memory.note)
        form.addRow("备注:", self.note_edit)

        # 来源
        self.source_box = QComboBox()
        self.source_box.addItems(list(self.SOURCE_MAP.keys()))
        if memory:
            idx = list(self.SOURCE_MAP.values()).index(memory.source)
            self.source_box.setCurrentIndex(idx)
        form.addRow("来源:", self.source_box)

        layout.addLayout(form)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("确定")
        apply_primary_style(btn_ok)
        btn_ok.clicked.connect(self._validate_and_accept)
        btn_cancel = QPushButton("取消")
        apply_secondary_style(btn_cancel)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def _format_impact(self, value: int) -> str:
        if value > 0:
            return f"+{value}%"
        return f"{value}%"

    def _validate_and_accept(self):
        if not self.event_edit.toPlainText().strip():
            QMessageBox.warning(self, "提示", "事件描述不能为空")
            return
        self.accept()

    def get_data(self) -> Optional[dict]:
        event = self.event_edit.toPlainText().strip()
        if not event:
            return None
        return {
            "event": event,
            "impact": self.impact_slider.value() / 100.0,
            "event_time": self.time_edit.text().strip() or None,
            "note": self.note_edit.text().strip() or None,
            "source": self.SOURCE_MAP[self.source_box.currentText()],
        }


class StrategyMemoryDialog(QDialog):
    """添加或编辑「沟通策略」记忆。
    
    字段:
    - pattern: 策略模式描述（必填）
    - effectiveness: 有效性 0~1（滑块 0%~100%）
    - source: 来源 manual/model（主要是 model）
    """

    SOURCE_MAP = {"模型提取": "model", "手动录入": "manual"}
    SOURCE_MAP_REV = {v: k for k, v in SOURCE_MAP.items()}

    def __init__(self, parent=None, memory: Optional[StrategyMemory] = None):
        super().__init__(parent)
        self.setWindowTitle("编辑沟通策略" if memory else "添加沟通策略")
        self._memory = memory
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # 策略模式
        self.pattern_edit = QTextEdit()
        self.pattern_edit.setAcceptRichText(False)
        self.pattern_edit.setPlaceholderText(
            "例如：使用幽默语气能获得更好回应、避免在早上发消息..."
        )
        self.pattern_edit.setMaximumHeight(80)
        if memory:
            self.pattern_edit.setPlainText(memory.pattern)
            # 将光标移到开头以避免 Qt 警告
            cursor = self.pattern_edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.pattern_edit.setTextCursor(cursor)
        form.addRow("策略模式:", self.pattern_edit)

        # 有效性滑块
        eff_widget = QHBoxLayout()
        self.effectiveness_slider = QSlider(Qt.Horizontal)
        self.effectiveness_slider.setRange(0, 100)
        self.effectiveness_slider.setValue(
            int((memory.effectiveness if memory else 0.5) * 100)
        )
        self.effectiveness_slider.setTickPosition(QSlider.TicksBelow)
        self.effectiveness_slider.setTickInterval(10)
        self.effectiveness_label = QLabel(f"{self.effectiveness_slider.value()}%")
        self.effectiveness_slider.valueChanged.connect(
            lambda v: self.effectiveness_label.setText(f"{v}%")
        )
        eff_widget.addWidget(self.effectiveness_slider)
        eff_widget.addWidget(self.effectiveness_label)
        form.addRow("有效性:", eff_widget)

        # 提示
        eff_hint = QLabel("0%=无效 | 50%=一般 | 100%=非常有效")
        eff_hint.setStyleSheet("color: #888; font-size: 11px;")
        eff_hint.setAlignment(Qt.AlignCenter)
        form.addRow("", eff_hint)

        # 来源（策略通常由模型提取）
        self.source_box = QComboBox()
        self.source_box.addItems(list(self.SOURCE_MAP.keys()))
        if memory:
            idx = list(self.SOURCE_MAP.values()).index(memory.source)
            self.source_box.setCurrentIndex(idx)
        form.addRow("来源:", self.source_box)

        layout.addLayout(form)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("确定")
        apply_primary_style(btn_ok)
        btn_ok.clicked.connect(self._validate_and_accept)
        btn_cancel = QPushButton("取消")
        apply_secondary_style(btn_cancel)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def _validate_and_accept(self):
        if not self.pattern_edit.toPlainText().strip():
            QMessageBox.warning(self, "提示", "策略模式不能为空")
            return
        self.accept()

    def get_data(self) -> Optional[dict]:
        pattern = self.pattern_edit.toPlainText().strip()
        if not pattern:
            return None
        return {
            "pattern": pattern,
            "effectiveness": self.effectiveness_slider.value() / 100.0,
            "source": self.SOURCE_MAP[self.source_box.currentText()],
        }


# =====================================================================
# 语义重复确认对话框
# =====================================================================

class DuplicateMemoryDialog(QDialog):
    """显示语义重复的记忆，让用户决定是替换还是保留两者。"""
    
    def __init__(self, parent=None, duplicates: list = None, memory_type: str = "profile"):
        """
        Args:
            duplicates: 重复项列表，每项包含:
                - new_item: 新记忆
                - existing_item: 现有记忆
                - reason: 相似原因
            memory_type: "profile" | "experience" | "strategy"
        """
        super().__init__(parent)
        self._duplicates = duplicates or []
        self._memory_type = memory_type
        self._decisions = {}  # {index: "replace" | "keep_both" | "skip"}
        
        type_names = {
            "profile": "对象特征",
            "experience": "关系事件",
            "strategy": "沟通策略",
        }
        self.setWindowTitle(f"发现重复的{type_names.get(memory_type, '记忆')}")
        self.setMinimumSize(550, 400)
        
        layout = QVBoxLayout(self)
        
        # 说明
        hint = QLabel("以下新记忆与现有记忆语义相似，请选择处理方式：")
        hint.setStyleSheet("font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(hint)
        
        # 滚动区域包含所有重复项
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        for idx, dup in enumerate(self._duplicates):
            group = self._create_duplicate_group(idx, dup)
            scroll_layout.addWidget(group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_confirm = QPushButton("确认")
        apply_primary_style(btn_confirm)
        btn_confirm.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消")
        apply_secondary_style(btn_cancel)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_confirm)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def _create_duplicate_group(self, idx: int, dup: dict) -> QGroupBox:
        """创建单个重复项的选择组。"""
        new_item = dup["new_item"]
        existing_item = dup["existing_item"]
        reason = dup.get("reason", "语义相似")
        
        # 获取显示文本
        if self._memory_type == "profile":
            new_text = getattr(new_item, "content", str(new_item))
            existing_text = getattr(existing_item, "content", str(existing_item))
        elif self._memory_type == "experience":
            new_text = getattr(new_item, "event", str(new_item))
            existing_text = getattr(existing_item, "event", str(existing_item))
        else:
            new_text = getattr(new_item, "pattern", str(new_item))
            existing_text = getattr(existing_item, "pattern", str(existing_item))
        
        group = QGroupBox(f"重复项 {idx + 1}")
        group_layout = QVBoxLayout(group)
        
        # 新记忆
        new_label = QLabel(f"🆕 新记忆: {new_text}")
        new_label.setWordWrap(True)
        new_label.setStyleSheet("color: #2196f3;")
        group_layout.addWidget(new_label)
        
        # 现有记忆
        existing_label = QLabel(f"📌 现有记忆: {existing_text}")
        existing_label.setWordWrap(True)
        existing_label.setStyleSheet("color: #4caf50;")
        group_layout.addWidget(existing_label)
        
        # 相似原因
        reason_label = QLabel(f"💡 相似原因: {reason}")
        reason_label.setWordWrap(True)
        reason_label.setStyleSheet("color: #888; font-size: 11px;")
        group_layout.addWidget(reason_label)
        
        # 选项
        from PySide6.QtWidgets import QButtonGroup, QRadioButton
        btn_group = QButtonGroup(self)
        
        radio_replace = QRadioButton("替换现有记忆（用新记忆覆盖）")
        radio_keep = QRadioButton("保留两者（同时保留新旧记忆）")
        radio_skip = QRadioButton("跳过（不保存新记忆）")
        
        radio_replace.setChecked(True)  # 默认选择替换
        self._decisions[idx] = "replace"
        
        btn_group.addButton(radio_replace, 0)
        btn_group.addButton(radio_keep, 1)
        btn_group.addButton(radio_skip, 2)
        
        def on_selection_changed(button_id):
            if button_id == 0:
                self._decisions[idx] = "replace"
            elif button_id == 1:
                self._decisions[idx] = "keep_both"
            else:
                self._decisions[idx] = "skip"
        
        btn_group.idClicked.connect(on_selection_changed)
        
        group_layout.addWidget(radio_replace)
        group_layout.addWidget(radio_keep)
        group_layout.addWidget(radio_skip)
        
        return group
    
    def get_decisions(self) -> dict:
        """获取用户的决定。
        
        Returns:
            {index: "replace" | "keep_both" | "skip"}
        """
        return self._decisions


class StrategyMergeDialog(QDialog):
    """沟通策略融合确认对话框。"""
    
    def __init__(self, parent=None, new_strategy=None, existing_strategy=None, reason: str = ""):
        super().__init__(parent)
        self._new_strategy = new_strategy
        self._existing_strategy = existing_strategy
        
        self.setWindowTitle("策略模式相似")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # 说明
        hint = QLabel("发现新策略与现有策略模式基本一致，是否合并？")
        hint.setStyleSheet("font-size: 13px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(hint)
        
        # 新策略
        new_text = getattr(new_strategy, "pattern", str(new_strategy))
        new_eff = getattr(new_strategy, "effectiveness", 0.5) * 100
        new_label = QLabel(f"🆕 新策略: {new_text}\n   有效性: {new_eff:.0f}%")
        new_label.setWordWrap(True)
        new_label.setStyleSheet("color: #2196f3; margin: 5px 0;")
        layout.addWidget(new_label)
        
        # 现有策略
        existing_text = getattr(existing_strategy, "pattern", str(existing_strategy))
        existing_eff = getattr(existing_strategy, "effectiveness", 0.5) * 100
        existing_count = getattr(existing_strategy, "evidence_count", 1)
        existing_label = QLabel(
            f"📌 现有策略: {existing_text}\n"
            f"   有效性: {existing_eff:.0f}% | 验证次数: {existing_count}"
        )
        existing_label.setWordWrap(True)
        existing_label.setStyleSheet("color: #4caf50; margin: 5px 0;")
        layout.addWidget(existing_label)
        
        # 相似原因
        if reason:
            reason_label = QLabel(f"💡 相似原因: {reason}")
            reason_label.setWordWrap(True)
            reason_label.setStyleSheet("color: #888; font-size: 11px; margin: 5px 0;")
            layout.addWidget(reason_label)
        
        # 合并预览
        merged_eff = self._calculate_merged_effectiveness()
        preview_label = QLabel(
            f"📊 合并后: 有效性 {merged_eff:.0f}% | 验证次数 {existing_count + 1}"
        )
        # 根据主题选择合适的背景和文字颜色
        if self._is_dark_theme():
            preview_style = (
                "background: #1e3a5f; color: #e3f2fd; padding: 8px; border-radius: 4px; "
                "font-weight: bold; margin: 10px 0;"
            )
        else:
            preview_style = (
                "background: #e3f2fd; color: #1a237e; padding: 8px; border-radius: 4px; "
                "font-weight: bold; margin: 10px 0;"
            )
        preview_label.setStyleSheet(preview_style)
        layout.addWidget(preview_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_merge = QPushButton("合并")
        apply_primary_style(btn_merge)
        btn_merge.clicked.connect(self.accept)
        
        btn_keep_both = QPushButton("保留两者")
        apply_info_style(btn_keep_both)
        btn_keep_both.clicked.connect(lambda: self.done(2))  # 自定义返回值
        
        btn_cancel = QPushButton("跳过")
        apply_secondary_style(btn_cancel)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_merge)
        btn_layout.addWidget(btn_keep_both)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def _is_dark_theme(self) -> bool:
        """检测当前是否为暗色主题。"""
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPalette
        app = QApplication.instance()
        palette = app.palette() if app else self.palette()
        window_color = palette.color(QPalette.Window)
        return window_color.lightness() < 128
    
    def _calculate_merged_effectiveness(self) -> float:
        """计算合并后的有效性（加权平均）。"""
        new_eff = getattr(self._new_strategy, "effectiveness", 0.5)
        existing_eff = getattr(self._existing_strategy, "effectiveness", 0.5)
        existing_count = getattr(self._existing_strategy, "evidence_count", 1)
        
        # 加权平均：现有策略权重为验证次数，新策略权重为1
        merged = (existing_eff * existing_count + new_eff) / (existing_count + 1)
        return merged * 100
    
    def get_merged_effectiveness(self) -> float:
        """获取合并后的有效性值（0~1）。"""
        new_eff = getattr(self._new_strategy, "effectiveness", 0.5)
        existing_eff = getattr(self._existing_strategy, "effectiveness", 0.5)
        existing_count = getattr(self._existing_strategy, "evidence_count", 1)
        return (existing_eff * existing_count + new_eff) / (existing_count + 1)


# =====================================================================
# AI 提取记忆预览对话框
# =====================================================================

class MemoryExtractionWorker(QThread):
    """后台线程执行记忆提取。"""
    
    finished = Signal(object)  # ExtractionResult
    error = Signal(str)
    
    def __init__(self, extractor, contact_name: str, conversation: list, existing_memories: dict):
        super().__init__()
        self._extractor = extractor
        self._contact_name = contact_name
        self._conversation = conversation
        self._existing_memories = existing_memories
    
    def run(self):
        try:
            result = self._extractor.extract_from_conversation(
                self._contact_name,
                self._conversation,
                self._existing_memories,
            )
            self.finished.emit(result)
        except Exception as err:
            self.error.emit(str(err))


class MemoryExtractionDialog(QDialog):
    """AI 记忆提取结果预览对话框。
    
    显示 AI 从对话中提取的记忆条目，让用户选择要保存的内容。
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI 记忆提取")
        self.setMinimumSize(600, 500)
        self.resize(650, 550)
        
        self._selected_profiles = []
        self._selected_experiences = []
        self._selected_strategies = []
        
        layout = QVBoxLayout(self)
        
        # 状态区域
        self.status_label = QLabel("正在分析对话内容...")
        self.status_label.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 不确定进度模式
        layout.addWidget(self.progress_bar)
        
        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setVisible(False)
        
        # 对象特征标签页
        self.profile_list = QListWidget()
        self.tab_widget.addTab(self.profile_list, "对象特征")
        
        # 关系事件标签页
        self.experience_list = QListWidget()
        self.tab_widget.addTab(self.experience_list, "关系事件")
        
        # 沟通策略标签页
        self.strategy_list = QListWidget()
        self.tab_widget.addTab(self.strategy_list, "沟通策略")
        
        layout.addWidget(self.tab_widget)
        
        # 提示信息
        self.hint_label = QLabel("✅ 勾选要保存的条目，然后点击「保存选中」")
        self.hint_label.setStyleSheet("color: #888; font-size: 12px;")
        self.hint_label.setVisible(False)
        layout.addWidget(self.hint_label)
        
        # 按钮区域
        self.btn_layout = QHBoxLayout()
        
        self.btn_select_all = QPushButton("全选")
        apply_info_style(self.btn_select_all, width=80)
        self.btn_select_all.clicked.connect(self._select_all)
        self.btn_select_all.setVisible(False)
        
        self.btn_deselect_all = QPushButton("取消全选")
        apply_secondary_style(self.btn_deselect_all)
        self.btn_deselect_all.clicked.connect(self._deselect_all)
        self.btn_deselect_all.setVisible(False)
        
        self.btn_layout.addWidget(self.btn_select_all)
        self.btn_layout.addWidget(self.btn_deselect_all)
        self.btn_layout.addStretch()
        
        self.btn_save = QPushButton("保存选中")
        apply_primary_style(self.btn_save)
        self.btn_save.clicked.connect(self.accept)
        self.btn_save.setVisible(False)
        
        self.btn_cancel = QPushButton("取消")
        apply_secondary_style(self.btn_cancel)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_layout.addWidget(self.btn_save)
        self.btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(self.btn_layout)
        
        self._extraction_result = None
        self._worker = None
    
    def start_extraction(self, extractor, contact_name: str, conversation: list, existing_memories: dict):
        """开始后台提取。"""
        self._worker = MemoryExtractionWorker(extractor, contact_name, conversation, existing_memories)
        self._worker.finished.connect(self._on_extraction_finished)
        self._worker.error.connect(self._on_extraction_error)
        self._worker.start()
    
    def _on_extraction_finished(self, result):
        """提取完成。"""
        self._extraction_result = result
        
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 填充列表
        total_count = 0
        
        # 对象特征
        for item in result.profiles:
            list_item = QListWidgetItem()
            confidence_pct = int(item.confidence * 100)
            list_item.setText(f"[置信度 {confidence_pct}%] {item.content}")
            list_item.setData(Qt.UserRole, item)
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            list_item.setCheckState(Qt.Checked)  # 默认勾选
            self.profile_list.addItem(list_item)
            total_count += 1
        
        # 关系事件
        for item in result.experiences:
            list_item = QListWidgetItem()
            impact_pct = int(item.impact * 100)
            impact_text = f"+{impact_pct}%" if impact_pct >= 0 else f"{impact_pct}%"
            time_text = f" ({item.event_time})" if item.event_time else ""
            list_item.setText(f"[影响 {impact_text}] {item.event}{time_text}")
            list_item.setData(Qt.UserRole, item)
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            list_item.setCheckState(Qt.Checked)  # 默认勾选
            self.experience_list.addItem(list_item)
            total_count += 1
        
        # 沟通策略
        for item in result.strategies:
            list_item = QListWidgetItem()
            eff_pct = int(item.effectiveness * 100)
            list_item.setText(f"[有效性 {eff_pct}%] {item.pattern}")
            list_item.setData(Qt.UserRole, item)
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            list_item.setCheckState(Qt.Checked)  # 默认勾选
            self.strategy_list.addItem(list_item)
            total_count += 1
        
        # 更新 UI
        if total_count > 0:
            self.status_label.setText(f"✅ 共发现 {total_count} 条记忆")
            self.status_label.setStyleSheet("font-size: 14px; color: #4caf50;")
            self.tab_widget.setVisible(True)
            self.hint_label.setVisible(True)
            self.btn_select_all.setVisible(True)
            self.btn_deselect_all.setVisible(True)
            self.btn_save.setVisible(True)
            
            # 更新标签页标题显示数量
            self.tab_widget.setTabText(0, f"对象特征 ({len(result.profiles)})")
            self.tab_widget.setTabText(1, f"关系事件 ({len(result.experiences)})")
            self.tab_widget.setTabText(2, f"沟通策略 ({len(result.strategies)})")
        else:
            self.status_label.setText("未从对话中发现新的记忆信息")
            self.status_label.setStyleSheet("font-size: 14px; color: #ff9800;")
    
    def _on_extraction_error(self, error_msg: str):
        """提取失败。"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"❌ 提取失败: {error_msg}")
        self.status_label.setStyleSheet("font-size: 14px; color: #f44336;")
    
    def _select_all(self):
        """全选当前标签页。"""
        current_list = self._get_current_list()
        for i in range(current_list.count()):
            current_list.item(i).setCheckState(Qt.Checked)
    
    def _deselect_all(self):
        """取消全选当前标签页。"""
        current_list = self._get_current_list()
        for i in range(current_list.count()):
            current_list.item(i).setCheckState(Qt.Unchecked)
    
    def _get_current_list(self) -> QListWidget:
        """获取当前标签页的列表。"""
        idx = self.tab_widget.currentIndex()
        if idx == 0:
            return self.profile_list
        elif idx == 1:
            return self.experience_list
        else:
            return self.strategy_list
    
    def get_selected_memories(self) -> dict:
        """获取用户勾选的记忆条目。"""
        profiles = []
        for i in range(self.profile_list.count()):
            item = self.profile_list.item(i)
            if item.checkState() == Qt.Checked:
                profiles.append(item.data(Qt.UserRole))
        
        experiences = []
        for i in range(self.experience_list.count()):
            item = self.experience_list.item(i)
            if item.checkState() == Qt.Checked:
                experiences.append(item.data(Qt.UserRole))
        
        strategies = []
        for i in range(self.strategy_list.count()):
            item = self.strategy_list.item(i)
            if item.checkState() == Qt.Checked:
                strategies.append(item.data(Qt.UserRole))
        
        return {
            "profiles": profiles,
            "experiences": experiences,
            "strategies": strategies,
        }
        
        strategies = []
        for i in range(self.strategy_list.count()):
            item = self.strategy_list.item(i)
            if item.isSelected():
                strategies.append(item.data(Qt.UserRole))
        
        return {
            "profiles": profiles,
            "experiences": experiences,
            "strategies": strategies,
        }

