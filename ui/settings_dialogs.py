"""设置和帮助对话框。"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QTabWidget,
    QWidget,
    QFormLayout,
    QGroupBox,
    QTextEdit,
    QScrollArea,
    QMessageBox,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from core.config import Settings
from core.intimacy_manager import IntimacyManager
from ui.button_styles import (
    apply_primary_style,
    apply_secondary_style,
    apply_warning_style,
    apply_info_style,
    apply_danger_style,
)


# ============ 统一按钮样式（从共享模块导入）============

def _apply_primary_style(btn: QPushButton) -> None:
    """主要按钮样式（绿色，用于保存/确认）"""
    apply_primary_style(btn)


def _apply_secondary_style(btn: QPushButton) -> None:
    """次要按钮样式（灰色，用于取消/关闭）"""
    apply_secondary_style(btn)


def _apply_warning_style(btn: QPushButton) -> None:
    """警告按钮样式（橙色，用于重置/恢复默认）"""
    apply_warning_style(btn)


def _apply_info_style(btn: QPushButton) -> None:
    """信息按钮样式（蓝色，用于测试连接等）"""
    apply_info_style(btn)


def _apply_danger_style(btn: QPushButton) -> None:
    """危险按钮样式（红色，用于关闭等）"""
    apply_danger_style(btn)


class APISettingsDialog(QDialog):
    """模型 API 配置对话框。"""
    
    def __init__(self, parent=None, settings: Settings = None):
        super().__init__(parent)
        self.settings = settings or Settings()
        self.setWindowTitle("模型 API 配置")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # 说明
        hint = QLabel("配置大语言模型的 API 参数")
        font = hint.font()
        font.setPointSize(11)
        font.setBold(True)
        hint.setFont(font)
        layout.addWidget(hint)
        
        # API 配置表单
        form = QFormLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setText(self.settings.api_key)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        form.addRow("API Key:", self.api_key_input)
        
        self.base_url_input = QLineEdit()
        self.base_url_input.setText(self.settings.base_url)
        form.addRow("API 基础 URL:", self.base_url_input)
        
        self.model_input = QLineEdit()
        self.model_input.setText(self.settings.model)
        form.addRow("模型名称:", self.model_input)
        
        # 文本生成参数
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(self.settings.temperature)
        form.addRow("Temperature (0.0-2.0):", self.temperature_spin)
        
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setSingleStep(0.05)
        self.top_p_spin.setValue(self.settings.top_p)
        form.addRow("Top P (0.0-1.0):", self.top_p_spin)
        
        self.frequency_penalty_spin = QDoubleSpinBox()
        self.frequency_penalty_spin.setRange(-2.0, 2.0)
        self.frequency_penalty_spin.setSingleStep(0.1)
        self.frequency_penalty_spin.setValue(self.settings.frequency_penalty)
        form.addRow("Frequency Penalty:", self.frequency_penalty_spin)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(128, 4096)
        self.max_tokens_spin.setValue(self.settings.max_tokens)
        form.addRow("最大 Token 数:", self.max_tokens_spin)
        
        self.max_history_spin = QSpinBox()
        self.max_history_spin.setRange(1, 20)
        self.max_history_spin.setValue(self.settings.max_history)
        form.addRow("对话上下文轮数:", self.max_history_spin)
        
        layout.addLayout(form)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_test = QPushButton("测试连接")
        _apply_info_style(btn_test)
        btn_test.clicked.connect(self._test_connection)
        btn_layout.addWidget(btn_test)
        
        btn_save = QPushButton("保存")
        _apply_primary_style(btn_save)
        btn_save.clicked.connect(self.accept)
        btn_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("取消")
        _apply_secondary_style(btn_cancel)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
    
    def _test_connection(self) -> None:
        """测试 API 连接。"""
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.api_key_input.text(),
                base_url=self.base_url_input.text()
            )
            
            response = client.models.list()
            QMessageBox.information(self, "连接成功", f"✅ 成功连接到 API！\n\n可用模型数：{len(list(response))}")
        except Exception as e:
            QMessageBox.warning(self, "连接失败", f"❌ 连接失败：\n{str(e)}")
    
    def get_settings(self) -> dict:
        """获取配置信息。"""
        return {
            "api_key": self.api_key_input.text(),
            "base_url": self.base_url_input.text(),
            "model": self.model_input.text(),
            "temperature": self.temperature_spin.value(),
            "top_p": self.top_p_spin.value(),
            "frequency_penalty": self.frequency_penalty_spin.value(),
            "max_tokens": self.max_tokens_spin.value(),
            "max_history": self.max_history_spin.value(),
        }


class IntimacyWeightSettingsDialog(QDialog):
    """亲密度计算权重设置对话框。"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("亲密度计算权重设置")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        
        # 说明
        hint = QLabel("配置亲密度增长和衰减的权重参数")
        font = hint.font()
        font.setPointSize(11)
        font.setBold(True)
        hint.setFont(font)
        layout.addWidget(hint)
        
        # 创建标签页
        tabs = QTabWidget()
        
        # 标签页1：衰减配置
        decay_tab = self._build_decay_tab()
        tabs.addTab(decay_tab, "衰减机制")
        
        # 标签页2：增长配置
        growth_tab = self._build_growth_tab()
        tabs.addTab(growth_tab, "增长机制")
        
        # 标签页3：初始亲密度
        base_tab = self._build_base_intimacy_tab()
        tabs.addTab(base_tab, "初始亲密度")
        
        layout.addWidget(tabs)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_reset = QPushButton("恢复默认")
        _apply_warning_style(btn_reset)
        btn_reset.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(btn_reset)
        
        btn_save = QPushButton("保存")
        _apply_primary_style(btn_save)
        btn_save.clicked.connect(self.accept)
        btn_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("取消")
        _apply_secondary_style(btn_cancel)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
    
    def _build_decay_tab(self) -> QWidget:
        """构建衰减配置标签页。"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 使用 Grid 布局实现更美观的表单
        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)
        form_layout.setHorizontalSpacing(16)
        form_layout.setVerticalSpacing(12)
        
        # 设置统一的输入框样式
        spinbox_style = """
            QDoubleSpinBox {
                min-width: 100px;
                padding: 6px 8px;
            }
        """
        label_style = "font-size: 13px;"
        
        # 7-14天衰减率
        lbl_7_14 = QLabel("7-14天的每日衰减率：")
        lbl_7_14.setStyleSheet(label_style)
        self.decay_7_14 = QDoubleSpinBox()
        self.decay_7_14.setRange(0.0, 1.0)
        self.decay_7_14.setSingleStep(0.01)
        self.decay_7_14.setDecimals(2)
        self.decay_7_14.setSuffix(" %")
        self.decay_7_14.setValue(IntimacyManager.DECAY_RATE_7_14)
        self.decay_7_14.setStyleSheet(spinbox_style)
        form_layout.addWidget(lbl_7_14, 0, 0)
        form_layout.addWidget(self.decay_7_14, 0, 1)
        
        # 14-30天衰减率
        lbl_14_30 = QLabel("14-30天的每日衰减率：")
        lbl_14_30.setStyleSheet(label_style)
        self.decay_14_30 = QDoubleSpinBox()
        self.decay_14_30.setRange(0.0, 1.0)
        self.decay_14_30.setSingleStep(0.01)
        self.decay_14_30.setDecimals(2)
        self.decay_14_30.setSuffix(" %")
        self.decay_14_30.setValue(IntimacyManager.DECAY_RATE_14_30)
        self.decay_14_30.setStyleSheet(spinbox_style)
        form_layout.addWidget(lbl_14_30, 1, 0)
        form_layout.addWidget(self.decay_14_30, 1, 1)
        
        # 30-90天衰减率
        lbl_30_90 = QLabel("30-90天的每日衰减率：")
        lbl_30_90.setStyleSheet(label_style)
        self.decay_30_90 = QDoubleSpinBox()
        self.decay_30_90.setRange(0.0, 1.0)
        self.decay_30_90.setSingleStep(0.01)
        self.decay_30_90.setDecimals(2)
        self.decay_30_90.setSuffix(" %")
        self.decay_30_90.setValue(IntimacyManager.DECAY_RATE_30_90)
        self.decay_30_90.setStyleSheet(spinbox_style)
        form_layout.addWidget(lbl_30_90, 2, 0)
        form_layout.addWidget(self.decay_30_90, 2, 1)
        
        # 90天以上衰减率
        lbl_90_plus = QLabel("90天以上的每日衰减率：")
        lbl_90_plus.setStyleSheet(label_style)
        self.decay_90_plus = QDoubleSpinBox()
        self.decay_90_plus.setRange(0.0, 1.0)
        self.decay_90_plus.setSingleStep(0.01)
        self.decay_90_plus.setDecimals(2)
        self.decay_90_plus.setSuffix(" %")
        self.decay_90_plus.setValue(IntimacyManager.DECAY_RATE_90_PLUS)
        self.decay_90_plus.setStyleSheet(spinbox_style)
        form_layout.addWidget(lbl_90_plus, 3, 0)
        form_layout.addWidget(self.decay_90_plus, 3, 1)
        
        # 添加弹性空间
        form_layout.setColumnStretch(2, 1)
        
        layout.addWidget(form_widget)
        layout.addStretch()
        return widget
    
    def _build_growth_tab(self) -> QWidget:
        """构建增长配置标签页。"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 使用 Grid 布局实现更美观的表单
        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)
        form_layout.setHorizontalSpacing(16)
        form_layout.setVerticalSpacing(12)
        
        # 设置统一的输入框样式
        spinbox_style = """
            QSpinBox, QDoubleSpinBox {
                min-width: 100px;
                padding: 6px 8px;
            }
        """
        label_style = "font-size: 13px;"
        
        # 喜欢消息增加值
        lbl_like = QLabel("喜欢消息的亲密度增加值：")
        lbl_like.setStyleSheet(label_style)
        self.like_weight = QSpinBox()
        self.like_weight.setRange(0, 10)
        self.like_weight.setValue(IntimacyManager.LIKE_WEIGHT)
        self.like_weight.setStyleSheet(spinbox_style)
        form_layout.addWidget(lbl_like, 0, 0)
        form_layout.addWidget(self.like_weight, 0, 1)
        
        # 不喜欢消息减少值
        lbl_dislike = QLabel("不喜欢消息的亲密度减少值：")
        lbl_dislike.setStyleSheet(label_style)
        self.dislike_weight = QSpinBox()
        self.dislike_weight.setRange(0, 10)
        self.dislike_weight.setValue(IntimacyManager.DISLIKE_WEIGHT)
        self.dislike_weight.setStyleSheet(spinbox_style)
        form_layout.addWidget(lbl_dislike, 1, 0)
        form_layout.addWidget(self.dislike_weight, 1, 1)
        
        # 接受率增加值
        lbl_accept = QLabel("喜欢消息的接受率增加：")
        lbl_accept.setStyleSheet(label_style)
        self.acceptance_delta = QDoubleSpinBox()
        self.acceptance_delta.setRange(0.0, 1.0)
        self.acceptance_delta.setSingleStep(0.01)
        self.acceptance_delta.setDecimals(2)
        self.acceptance_delta.setValue(IntimacyManager.ACCEPTANCE_DELTA)
        self.acceptance_delta.setStyleSheet(spinbox_style)
        form_layout.addWidget(lbl_accept, 2, 0)
        form_layout.addWidget(self.acceptance_delta, 2, 1)
        
        # 接受率减少值
        lbl_reject = QLabel("不喜欢消息的接受率减少：")
        lbl_reject.setStyleSheet(label_style)
        self.rejection_delta = QDoubleSpinBox()
        self.rejection_delta.setRange(0.0, 1.0)
        self.rejection_delta.setSingleStep(0.01)
        self.rejection_delta.setDecimals(2)
        self.rejection_delta.setValue(IntimacyManager.REJECTION_DELTA)
        self.rejection_delta.setStyleSheet(spinbox_style)
        form_layout.addWidget(lbl_reject, 3, 0)
        form_layout.addWidget(self.rejection_delta, 3, 1)
        
        # 添加弹性空间
        form_layout.setColumnStretch(2, 1)
        
        layout.addWidget(form_widget)
        layout.addStretch()
        return widget
    
    def _build_base_intimacy_tab(self) -> QWidget:
        """构建初始亲密度标签页。"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 使用 Grid 布局实现两列显示
        form_widget = QWidget()
        form_layout = QGridLayout(form_widget)
        form_layout.setHorizontalSpacing(24)
        form_layout.setVerticalSpacing(12)
        
        # 设置统一的输入框样式
        spinbox_style = """
            QSpinBox {
                min-width: 80px;
                padding: 6px 8px;
            }
        """
        label_style = "font-size: 13px;"
        
        self.base_intimacy = {}
        # 从 IntimacyManager 获取统一的关系类型和当前值
        rel_types = list(IntimacyManager.RELATIONSHIP_TYPES)
        
        for idx, rel_type in enumerate(rel_types):
            current_value = IntimacyManager.BASE_INTIMACY_BY_TYPE.get(rel_type, 25)
            
            # 计算行列位置（两列布局）
            row = idx // 2
            col = (idx % 2) * 2  # 0 或 2
            
            lbl = QLabel(f"{rel_type}：")
            lbl.setStyleSheet(label_style)
            
            spin = QSpinBox()
            spin.setRange(0, 100)
            spin.setValue(current_value)
            spin.setStyleSheet(spinbox_style)
            self.base_intimacy[rel_type] = spin
            
            form_layout.addWidget(lbl, row, col)
            form_layout.addWidget(spin, row, col + 1)
        
        # 添加弹性空间
        form_layout.setColumnStretch(4, 1)
        
        layout.addWidget(form_widget)
        layout.addStretch()
        return widget
    
    def _reset_defaults(self) -> None:
        """恢复默认值。"""
        reply = QMessageBox.question(
            self, "确认", "确定要恢复所有参数为默认值吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # 恢复衰减默认值
            self.decay_7_14.setValue(0.1)
            self.decay_14_30.setValue(0.15)
            self.decay_30_90.setValue(0.2)
            self.decay_90_plus.setValue(0.3)
            
            # 恢复增长默认值
            self.like_weight.setValue(2)
            self.dislike_weight.setValue(1)
            self.acceptance_delta.setValue(0.05)
            self.rejection_delta.setValue(0.05)
            
            # 恢复初始亲密度 - 使用默认值映射
            default_values = {
                "家人": 35, "恋人": 45, "伴侣": 45, "亲密朋友": 30,
                "朋友": 25, "同事": 20, "熟人": 15, "陌生人": 10,
            }
            for rel_type, spin in self.base_intimacy.items():
                spin.setValue(default_values.get(rel_type, 25))
    
    def get_settings(self) -> dict:
        """获取设置值。"""
        return {
            "decay": {
                "decay_7_14": self.decay_7_14.value(),
                "decay_14_30": self.decay_14_30.value(),
                "decay_30_90": self.decay_30_90.value(),
                "decay_90_plus": self.decay_90_plus.value(),
            },
            "growth": {
                "like_weight": self.like_weight.value(),
                "dislike_weight": self.dislike_weight.value(),
                "acceptance_delta": self.acceptance_delta.value(),
                "rejection_delta": self.rejection_delta.value(),
            },
            "base_intimacy": {
                rel_type: spin.value() for rel_type, spin in self.base_intimacy.items()
            }
        }


class HelpDialog(QDialog):
    """使用说明对话框。"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("使用说明")
        self.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("对话回复决策系统 - 使用说明")
        font = title.font()
        font.setPointSize(13)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # 内容
        content = QTextEdit()
        content.setReadOnly(True)
        content.setMarkdown("""
# 系统功能介绍

## 1. 关系管理
- **添加/编辑对象**：在左侧列表管理与各个人物的关系数据
- **对象画像**：查看每个对象的详细信息、亲密度变化趋势、关系风险提示
- **关系分类**：支持多种关系类型（家人、朋友、恋人等）

## 2. 对话分析与回复建议
- **消息分析**：自动分析用户消息的情感、深度、亲密度变化
- **智能回复**：基于关系画像和实时亲密度生成个性化回复建议
- **反馈学习**：通过点击"喜欢/不喜欢"让系统学习用户偏好

## 3. 亲密度管理
- **实时更新**：用户反馈实时影响亲密度和关系阶段
- **衰减机制**：长期不交互自动衰减亲密度
- **趋势展示**：折线图显示亲密度变化历史

## 4. 长期记忆与策略
- **自动提取**：AI 自动从对话中提取关键信息（回忆、经验、策略）
- **记忆管理**：手动管理和编辑提取的信息
- **去重合并**：系统自动检测相似内容并提示合并

## 5. 配置与优化
- **API 配置**：在设置中配置 LLM 模型参数
- **权重调整**：自定义亲密度增长/衰减的权重参数
- **数据导入/导出**：备份和恢复关系数据

## 操作提示
- 💬 **对话框内**：输入消息后点击"生成回复"获得建议
- 👍 **反馈机制**：选中生成的回复后，可点击"喜欢"或"不喜欢"进行反馈
- 🧠 **记忆提取**：完成对话后点击"AI 提取"可自动分析提取重要信息
- 📊 **关系画像**：随时切换到此标签页查看亲密度和关系状态
""")
        layout.addWidget(content)
        
        # 关闭按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("关闭")
        _apply_secondary_style(btn_close)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)


class AlgorithmDialog(QDialog):
    """算法说明对话框。"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("算法说明")
        self.setMinimumSize(800, 700)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("对话回复决策系统 - 核心算法")
        font = title.font()
        font.setPointSize(13)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # 内容
        content = QTextEdit()
        content.setReadOnly(True)
        content.setMarkdown("""
# 核心算法说明

## 一、亲密度评估模型

### 1.1 亲密度初始化
根据关系类型设置基础亲密度值：
- 家人：35%，恋人/伴侣：45%，亲密朋友：30%
- 朋友：25%，同事：20%，熟人：15%，陌生人：10%

### 1.2 衰减机制
长期不交互时触发衰减：
- 0-7天：无衰减
- 7-14天：每天衰减0.1%
- 14-30天：每天衰减0.15%
- 30-90天：每天衰减0.2%
- 90+天：每天衰减0.3%

### 1.3 增长机制
用户反馈驱动的增长：
- 喜欢消息：+2亲密度，接受率+5%
- 不喜欢消息：-1亲密度，接受率-5%
- 同一对话轮次：去重计算，避免重复计数

## 二、关系阶段划分

```
0-20%    : 陌生人 (Stranger)
20-40%   : 浅认识 (Acquaintance)
40-60%   : 普通朋友 (Friend)
60-75%   : 亲近朋友 (Close Friend)
75-90%   : 亲密朋友 (Very Close)
90-100%  : 知己 (Intimate)
```

## 三、消息分析算法

### 3.1 情感分析
- 积极词汇识别：喜悦、感谢、期待等
- 消极词汇识别：失望、愤怒、疲惫等
- 中性评判：无明显情绪倾向

### 3.2 对话深度评估
基于关键词和内容长度判断：
- 深度话题：涉及情感、计划、问题、关系等
- 轻度话题：日常闲聊、普通信息
- 深度评分 0.0-1.0，影响亲密度权重

### 3.3 幽默/轻松程度
- 幽默词汇和表情符号识别
- 严肃话题关键词检测
- 评分 0.0-1.0，影响回复风格选择

## 四、记忆提取与去重

### 4.1 记忆分类
- **回忆 (Profile)**：关于对象的基本信息和特征
- **经验 (Experience)**：互动过程中发生的具体事件
- **策略 (Strategy)**：有效的沟通和互动方式

### 4.2 相似度计算
使用语义相似性模型（向量化 + 余弦相似度）：
- 相似度阈值：0.7+为相似
- 合并后有效性：加权平均 = (现有有效性×验证次数 + 新有效性) / (验证次数+1)

### 4.3 去重策略
- 新提取与现有记忆对比
- 识别模式相似内容
- 用户确认后自动合并

## 五、回复生成策略

### 5.1 提示词构建
包含以下信息：
- 对象的完整画像（名字、关系、性格等）
- 当前亲密度和关系阶段
- 历史策略和有效反馈
- 消息分析结果（情感、深度、幽默度）

### 5.2 多样性生成
生成3条不同风格的回复建议：
- 主要建议（基于历史最有效的策略）
- 备选建议1（温暖友好风格）
- 备选建议2（幽默轻松或正式专业风格）

### 5.3 质量控制
- 长度限制：50-200字
- 语义连贯性检查
- 敏感词过滤

## 六、系统改进机制

### 6.1 反馈学习
- 用户喜欢反馈：增加该风格策略的权重
- 用户不喜欢反馈：降低该风格策略的权重
- 反馈积累影响后续消息生成

### 6.2 长期优化
- 记录每个策略的有效性评分（0-1）
- 定期评估亲密度变化趋势
- 根据数据调整权重参数

## 七、隐私与安全

- 所有数据存储在本地 JSON 文件
- 支持数据导入/导出
- 不上传用户隐私信息到云端
- 模型调用通过配置的 API 完成

---
本系统的核心创新在于：
1. **动态亲密度模型**：反映真实关系变化
2. **多维度分析**：情感、深度、幽默等综合考虑
3. **用户反馈闭环**：持续学习改进
4. **记忆管理系统**：建立持久知识库
""")
        layout.addWidget(content)
        
        # 关闭按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("关闭")
        _apply_secondary_style(btn_close)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
