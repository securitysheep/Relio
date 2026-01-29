"""关系状态管理：维护社交关系阶段与动态演化。"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Optional
from datetime import datetime


class RelationshipStage(str, Enum):
    """关系阶段定义。"""
    INITIAL = "initial"        # 初识阶段
    BUILDING = "building"      # 关系建立阶段
    STABLE = "stable"          # 稳定阶段
    CLOSE = "close"            # 亲密阶段
    DISTANT = "distant"        # 疏远阶段
    ARCHIVED = "archived"      # 归档（历史关系）


@dataclass
class RelationshipState:
    """关系状态模型：描述与某一联系人的关系所处的阶段。"""
    contact_id: str
    current_stage: RelationshipStage = RelationshipStage.INITIAL
    
    # 阶段统计
    interaction_count: int = 0      # 交互次数
    days_since_interaction: int = 0 # 距离最后交互的天数
    
    # 关系演化轨迹
    stage_history: Dict[str, str] = None  # {timestamp: stage}
    
    # 阶段特征参数
    closeness: float = 0.0          # 亲密度 (0=陌生, 1=非常亲密)
    trust_level: float = 0.5        # 信任度 (0=无信任, 1=完全信任)
    interaction_frequency: float = 0.0  # 交互频率 (0=极少, 1=非常频繁)
    
    # 更新时间
    updated_at: str = None

    def __post_init__(self):
        if self.stage_history is None:
            self.stage_history = {datetime.now().isoformat(): self.current_stage.value}
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """转换为字典。"""
        data = asdict(self)
        data['current_stage'] = self.current_stage.value
        return data


class RelationshipStateManager:
    """关系状态管理器：维护所有联系人的关系阶段。"""

    def __init__(self):
        self._states: Dict[str, RelationshipState] = {}

    def get_state(self, contact_id: str) -> RelationshipState:
        """获取或初始化联系人的关系状态。"""
        if contact_id not in self._states:
            self._states[contact_id] = RelationshipState(contact_id=contact_id)
        return self._states[contact_id]

    def update_stage(
        self,
        contact_id: str,
        new_stage: RelationshipStage,
    ) -> RelationshipState:
        """更新关系阶段。"""
        state = self.get_state(contact_id)
        old_stage = state.current_stage
        
        if old_stage != new_stage:
            state.current_stage = new_stage
            timestamp = datetime.now().isoformat()
            state.stage_history[timestamp] = new_stage.value
            state.updated_at = timestamp
        
        return state

    def record_interaction(self, contact_id: str) -> RelationshipState:
        """记录一次交互，自动更新相关统计。"""
        state = self.get_state(contact_id)
        state.interaction_count += 1
        state.days_since_interaction = 0
        state.updated_at = datetime.now().isoformat()
        
        # 根据交互次数自动进阶关系阶段（可选策略）
        self._auto_evolve_stage(state)
        
        return state

    def _auto_evolve_stage(self, state: RelationshipState) -> None:
        """根据交互统计自动演化关系阶段（可选的启发式规则）。"""
        # 这是一个简单的启发式规则，实际应用中可根据具体需求调整
        if state.current_stage == RelationshipStage.INITIAL and state.interaction_count >= 3:
            self.update_stage(state.contact_id, RelationshipStage.BUILDING)
        elif state.current_stage == RelationshipStage.BUILDING and state.interaction_count >= 10:
            self.update_stage(state.contact_id, RelationshipStage.STABLE)

    def update_metrics(
        self,
        contact_id: str,
        closeness: Optional[float] = None,
        trust_level: Optional[float] = None,
        interaction_frequency: Optional[float] = None,
    ) -> RelationshipState:
        """更新关系指标。"""
        state = self.get_state(contact_id)
        
        if closeness is not None:
            state.closeness = max(0.0, min(1.0, closeness))
        if trust_level is not None:
            state.trust_level = max(0.0, min(1.0, trust_level))
        if interaction_frequency is not None:
            state.interaction_frequency = max(0.0, min(1.0, interaction_frequency))
        
        state.updated_at = datetime.now().isoformat()
        return state

    def list_states(self) -> Dict[str, RelationshipState]:
        """列出所有关系状态。"""
        return dict(self._states)

    def get_stage_timeline(self, contact_id: str) -> Dict[str, str]:
        """获取指定联系人的阶段演化历史。"""
        state = self.get_state(contact_id)
        return dict(state.stage_history)
