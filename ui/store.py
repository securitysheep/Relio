"""UI 内存数据模型：关系对象与长期记忆。"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Union
from uuid import uuid4


@dataclass
class Person:
    person_id: str
    name: str
    relationship_type: str
    intimacy: int
    avatar_path: str = ""
    style_tags: List[str] = field(default_factory=list)
    relative_role: str = "平级"
    age_group: str = "同龄"
    goals: List[str] = field(default_factory=list)
    notes: str = ""
    intimacy_history: List[dict] = field(default_factory=list)
    evolution_notes: List[str] = field(default_factory=list)
    style_profile: dict = field(default_factory=dict)
    
    # 新增：亲密度详细指标（用于新的衰减机制）
    last_interaction_date: str = ""  # YYYY-MM-DD，最后交互日期
    last_intimacy_change: int = 0    # 上次亲密度变化量
    last_intimacy_change_date: str = ""  # 上次亲密度变化时间
    intimacy_change_history: List[dict] = field(default_factory=list)  # 近180天内的变化记录
    acceptance_rate: float = 1.0  # 本周接受率 (0-1)
    rejection_count: int = 0  # 本周拒绝次数

    @property
    def display_name(self) -> str:
        return self.name or "未命名"


# ==================== 长期记忆数据模型 ====================

@dataclass
class ProfileMemory:
    """对象稳定特征记忆：描述对方稳定存在的性格、偏好、沟通习惯。"""
    memory_id: str
    person_id: str
    content: str                          # 记忆内容，如"不喜欢被催促"
    confidence: float = 0.5               # 置信度 0.0 ~ 1.0
    source: str = "manual"                # manual | system
    created_at: str = ""
    last_confirmed: str = ""
    is_active: bool = True
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.last_confirmed:
            self.last_confirmed = self.created_at


@dataclass
class ExperienceMemory:
    """关系经验/关键事件记忆：描述双方关系中发生过的关键事件。"""
    memory_id: str
    person_id: str
    event: str                            # 事件描述，如"项目沟通中产生争执"
    impact: float = 0.0                   # 对关系的影响 -1.0 ~ +1.0
    event_time: str = ""                  # 事件发生时间
    note: str = ""                        # 附加说明
    source: str = "manual"                # manual | system
    is_active: bool = True
    
    def __post_init__(self):
        if not self.event_time:
            self.event_time = datetime.now().strftime("%Y-%m-%d")


@dataclass
class StrategyMemory:
    """沟通策略记忆：描述在历史交互中被验证有效/无效的沟通方式。"""
    memory_id: str
    person_id: str
    pattern: str                          # 策略模式，如"直接表达"
    effectiveness: float = 0.5            # 有效性 0.0 ~ 1.0
    evidence_count: int = 1               # 验证次数
    last_updated: str = ""
    source: str = "manual"                # manual | system
    is_active: bool = True
    
    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 兼容旧版本的 MemoryItem（用于迁移）
@dataclass
class MemoryItem:
    memory_id: str
    memory_type: str
    content: str
    source: str
    timestamp: str


# 长期记忆类型别名
LongTermMemory = Union[ProfileMemory, ExperienceMemory, StrategyMemory]


class MemoryService:
    """
    长期记忆服务层。
    
    负责：
    - 存储、管理三种类型的长期记忆
    - 为关系画像和回复建议提供查询接口
    - 记忆生命周期管理
    """
    
    def __init__(self):
        # 按 person_id 组织的记忆存储
        self.profile_memories: Dict[str, List[ProfileMemory]] = {}
        self.experience_memories: Dict[str, List[ExperienceMemory]] = {}
        self.strategy_memories: Dict[str, List[StrategyMemory]] = {}
    
    # ==================== CRUD 操作 ====================
    
    def create_profile_memory(self, person_id: str, content: str, 
                               confidence: float = 0.5, source: str = "manual") -> ProfileMemory:
        """创建对象特征记忆。"""
        memory = ProfileMemory(
            memory_id=str(uuid4()),
            person_id=person_id,
            content=content,
            confidence=confidence,
            source=source,
        )
        self.profile_memories.setdefault(person_id, []).append(memory)
        return memory
    
    def create_experience_memory(self, person_id: str, event: str,
                                  impact: float = 0.0, note: str = "",
                                  event_time: str = "", source: str = "manual") -> ExperienceMemory:
        """创建关系事件记忆。"""
        memory = ExperienceMemory(
            memory_id=str(uuid4()),
            person_id=person_id,
            event=event,
            impact=impact,
            event_time=event_time or datetime.now().strftime("%Y-%m-%d"),
            note=note,
            source=source,
        )
        self.experience_memories.setdefault(person_id, []).append(memory)
        return memory
    
    def create_strategy_memory(self, person_id: str, pattern: str,
                                effectiveness: float = 0.5, source: str = "manual") -> StrategyMemory:
        """创建沟通策略记忆。"""
        memory = StrategyMemory(
            memory_id=str(uuid4()),
            person_id=person_id,
            pattern=pattern,
            effectiveness=effectiveness,
            source=source,
        )
        self.strategy_memories.setdefault(person_id, []).append(memory)
        return memory
    
    def update_profile_memory(self, memory: ProfileMemory) -> None:
        """更新对象特征记忆。"""
        memories = self.profile_memories.get(memory.person_id, [])
        for idx, m in enumerate(memories):
            if m.memory_id == memory.memory_id:
                memories[idx] = memory
                return
    
    def update_experience_memory(self, memory: ExperienceMemory) -> None:
        """更新关系事件记忆。"""
        memories = self.experience_memories.get(memory.person_id, [])
        for idx, m in enumerate(memories):
            if m.memory_id == memory.memory_id:
                memories[idx] = memory
                return
    
    def update_strategy_memory(self, memory: StrategyMemory) -> None:
        """更新沟通策略记忆。"""
        memories = self.strategy_memories.get(memory.person_id, [])
        for idx, m in enumerate(memories):
            if m.memory_id == memory.memory_id:
                memories[idx] = memory
                return
    
    def deactivate_memory(self, person_id: str, memory_id: str, memory_type: str) -> bool:
        """停用记忆（而非删除）。"""
        if memory_type == "profile":
            memories = self.profile_memories.get(person_id, [])
            for m in memories:
                if m.memory_id == memory_id:
                    m.is_active = False
                    return True
        elif memory_type == "experience":
            memories = self.experience_memories.get(person_id, [])
            for m in memories:
                if m.memory_id == memory_id:
                    m.is_active = False
                    return True
        elif memory_type == "strategy":
            memories = self.strategy_memories.get(person_id, [])
            for m in memories:
                if m.memory_id == memory_id:
                    m.is_active = False
                    return True
        return False
    
    def delete_memory(self, person_id: str, memory_id: str, memory_type: str) -> bool:
        """彻底删除记忆。"""
        if memory_type == "profile":
            memories = self.profile_memories.get(person_id, [])
            self.profile_memories[person_id] = [m for m in memories if m.memory_id != memory_id]
            return True
        elif memory_type == "experience":
            memories = self.experience_memories.get(person_id, [])
            self.experience_memories[person_id] = [m for m in memories if m.memory_id != memory_id]
            return True
        elif memory_type == "strategy":
            memories = self.strategy_memories.get(person_id, [])
            self.strategy_memories[person_id] = [m for m in memories if m.memory_id != memory_id]
            return True
        return False
    
    # ==================== 查询接口 ====================
    
    def query_profile_memories(self, person_id: str, active_only: bool = True) -> List[ProfileMemory]:
        """查询对象特征记忆。"""
        memories = self.profile_memories.get(person_id, [])
        if active_only:
            return [m for m in memories if m.is_active]
        return memories
    
    def query_experience_memories(self, person_id: str, active_only: bool = True) -> List[ExperienceMemory]:
        """查询关系事件记忆。"""
        memories = self.experience_memories.get(person_id, [])
        if active_only:
            return [m for m in memories if m.is_active]
        return memories
    
    def query_strategy_memories(self, person_id: str, active_only: bool = True) -> List[StrategyMemory]:
        """查询沟通策略记忆。"""
        memories = self.strategy_memories.get(person_id, [])
        if active_only:
            return [m for m in memories if m.is_active]
        return memories
    
    def get_memory_by_id(self, person_id: str, memory_id: str, memory_type: str) -> Optional[LongTermMemory]:
        """根据ID获取记忆。"""
        if memory_type == "profile":
            for m in self.profile_memories.get(person_id, []):
                if m.memory_id == memory_id:
                    return m
        elif memory_type == "experience":
            for m in self.experience_memories.get(person_id, []):
                if m.memory_id == memory_id:
                    return m
        elif memory_type == "strategy":
            for m in self.strategy_memories.get(person_id, []):
                if m.memory_id == memory_id:
                    return m
        return None
    
    # ==================== 为其他模块提供的接口 ====================
    
    def summarize_for_profile(self, person_id: str) -> dict:
        """
        为关系画像模块提供记忆摘要。
        
        返回：
        - profile_traits: 对象稳定特征列表
        - key_experiences: 关键事件及其影响
        """
        profiles = self.query_profile_memories(person_id)
        experiences = self.query_experience_memories(person_id)
        
        return {
            "profile_traits": [
                {"content": m.content, "confidence": m.confidence}
                for m in profiles if m.confidence >= 0.3
            ],
            "key_experiences": [
                {"event": m.event, "impact": m.impact, "time": m.event_time, "note": m.note}
                for m in experiences
            ],
        }
    
    def summarize_for_reply(self, person_id: str) -> dict:
        """
        为回复建议模块提供记忆摘要（用于构建 Prompt）。
        
        返回：
        - profile_hints: 需要注意的对象特征
        - effective_strategies: 有效的沟通策略
        - avoid_strategies: 应避免的沟通方式
        """
        profiles = self.query_profile_memories(person_id)
        strategies = self.query_strategy_memories(person_id)
        
        # 高置信度的特征
        profile_hints = [m.content for m in profiles if m.confidence >= 0.5]
        
        # 按有效性分类策略
        effective = [m.pattern for m in strategies if m.effectiveness >= 0.6]
        avoid = [m.pattern for m in strategies if m.effectiveness <= 0.3]
        
        return {
            "profile_hints": profile_hints,
            "effective_strategies": effective,
            "avoid_strategies": avoid,
        }
    
    def confirm_profile_memory(self, person_id: str, memory_id: str) -> None:
        """确认/验证对象特征记忆，提升置信度。"""
        for m in self.profile_memories.get(person_id, []):
            if m.memory_id == memory_id:
                m.confidence = min(1.0, m.confidence + 0.1)
                m.last_confirmed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return
    
    def update_strategy_effectiveness(self, person_id: str, memory_id: str, 
                                       success: bool) -> None:
        """根据使用结果更新策略有效性。"""
        for m in self.strategy_memories.get(person_id, []):
            if m.memory_id == memory_id:
                m.evidence_count += 1
                # 渐进式更新有效性
                delta = 0.1 if success else -0.1
                m.effectiveness = max(0.0, min(1.0, m.effectiveness + delta))
                m.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return
    
    # ==================== 持久化 ====================
    
    def to_dict(self) -> dict:
        """序列化为字典。"""
        return {
            "profile_memories": {
                pid: [asdict(m) for m in memories]
                for pid, memories in self.profile_memories.items()
            },
            "experience_memories": {
                pid: [asdict(m) for m in memories]
                for pid, memories in self.experience_memories.items()
            },
            "strategy_memories": {
                pid: [asdict(m) for m in memories]
                for pid, memories in self.strategy_memories.items()
            },
        }
    
    def load_from_dict(self, data: dict) -> None:
        """从字典加载。"""
        self.profile_memories.clear()
        self.experience_memories.clear()
        self.strategy_memories.clear()
        
        for pid, memories in data.get("profile_memories", {}).items():
            self.profile_memories[pid] = [ProfileMemory(**m) for m in memories]
        
        for pid, memories in data.get("experience_memories", {}).items():
            self.experience_memories[pid] = [ExperienceMemory(**m) for m in memories]
        
        for pid, memories in data.get("strategy_memories", {}).items():
            self.strategy_memories[pid] = [StrategyMemory(**m) for m in memories]
    
    def delete_person_memories(self, person_id: str) -> None:
        """删除某人的所有记忆。"""
        self.profile_memories.pop(person_id, None)
        self.experience_memories.pop(person_id, None)
        self.strategy_memories.pop(person_id, None)


class AppStore:
    """简单的数据存储层，负责 UI 侧对象/记忆管理。"""

    def __init__(self) -> None:
        self.people: Dict[str, Person] = {}
        self.memories: Dict[str, List[MemoryItem]] = {}  # 兼容旧版
        self.memory_service = MemoryService()  # 新版长期记忆服务

    def load_from_data_dir(self, data_dir: str) -> None:
        """从 data 目录加载基础联系人数据（profiles.json + relationship_states.json）。"""
        data_path = Path(data_dir)
        profiles_path = data_path / "profiles.json"
        states_path = data_path / "relationship_states.json"
        memories_path = data_path / "long_term_memories.json"

        if not profiles_path.exists():
            return

        try:
            profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
        except Exception:
            return

        states = {}
        if states_path.exists():
            try:
                states = json.loads(states_path.read_text(encoding="utf-8"))
            except Exception:
                states = {}

        self.people.clear()
        self.memories.clear()

        for contact_id, profile_data in profiles.items():
            contact_name = profile_data.get("contact_name") or profile_data.get("contact_id")
            contact_type = profile_data.get("contact_type", "other")
            relationship_type = profile_data.get("relationship_type") or self._relationship_from_contact_type(contact_type)

            state = states.get(contact_id, {})
            closeness = state.get("closeness")
            if isinstance(closeness, (int, float)):
                intimacy = max(0, min(100, int(round(closeness * 100))))
            else:
                # 使用关系类型对应的基础亲密度
                from core.intimacy_manager import IntimacyManager
                intimacy = IntimacyManager.get_base_intimacy(relationship_type)

            notes = profile_data.get("notes") or profile_data.get("description", "")
            goals = profile_data.get("goals", []) or []
            style_tags = profile_data.get("style_tags", []) or []
            relative_role = profile_data.get("relative_role", "平级")
            age_group = profile_data.get("age_group", "同龄")
            avatar_path = profile_data.get("avatar_path", "")
            person = Person(
                person_id=contact_id,
                name=contact_name,
                relationship_type=relationship_type,
                intimacy=intimacy,
                avatar_path=avatar_path,
                style_tags=style_tags,
                relative_role=relative_role,
                age_group=age_group,
                goals=goals,
                notes=notes,
                intimacy_history=profile_data.get("intimacy_history", []),
                evolution_notes=profile_data.get("evolution_notes", []),
                style_profile=profile_data.get("style_profile", {}),
                last_interaction_date=profile_data.get("last_interaction_date", ""),
                last_intimacy_change=profile_data.get("last_intimacy_change", 0),
                last_intimacy_change_date=profile_data.get("last_intimacy_change_date", ""),
                intimacy_change_history=profile_data.get("intimacy_change_history", []),
                acceptance_rate=profile_data.get("acceptance_rate", 1.0),
                rejection_count=profile_data.get("rejection_count", 0),
            )
            self.people[person.person_id] = person
            self.memories[person.person_id] = []
        
        # 加载长期记忆
        if memories_path.exists():
            try:
                memories_data = json.loads(memories_path.read_text(encoding="utf-8"))
                self.memory_service.load_from_dict(memories_data)
            except Exception:
                pass

    def sync_to_data_dir(self, data_dir: str) -> None:
        """将当前对象列表同步写回 data 目录。"""
        data_path = Path(data_dir)
        data_path.mkdir(parents=True, exist_ok=True)
        profiles_path = data_path / "profiles.json"
        states_path = data_path / "relationship_states.json"

        profiles = {}
        if profiles_path.exists():
            try:
                profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
            except Exception:
                profiles = {}

        states = {}
        if states_path.exists():
            try:
                states = json.loads(states_path.read_text(encoding="utf-8"))
            except Exception:
                states = {}

        current_ids = set(self.people.keys())

        for contact_id in list(profiles.keys()):
            if contact_id not in current_ids:
                profiles.pop(contact_id, None)
        for contact_id in list(states.keys()):
            if contact_id not in current_ids:
                states.pop(contact_id, None)

        for person in self.people.values():
            contact_id = person.person_id
            existing_profile = profiles.get(contact_id, {})
            created_at = existing_profile.get("created_at") or datetime.now().isoformat()
            style_params = existing_profile.get("style_params") or {
                "formality": 0.5,
                "initiative": 0.5,
                "emotion": 0.5,
                "humor": 0.5,
                "verbosity": 0.5,
            }
            total_messages = existing_profile.get("total_messages", 0)
            last_interaction = existing_profile.get("last_interaction")

            profiles[contact_id] = {
                "contact_id": contact_id,
                "contact_name": person.display_name,
                "contact_type": self._contact_type_from_relationship(person.relationship_type),
                "relationship_type": person.relationship_type,
                "relative_role": person.relative_role,
                "age_group": person.age_group,
                "goals": person.goals,
                "style_tags": person.style_tags,
                "notes": person.notes,
                "avatar_path": person.avatar_path,
                "intimacy_history": person.intimacy_history,
                "evolution_notes": person.evolution_notes,
                "style_profile": person.style_profile,
                "style_params": style_params,
                "total_messages": total_messages,
                "last_interaction": last_interaction,
                "created_at": created_at,
                "description": person.notes,
                # 新增：亲密度详细指标
                "last_interaction_date": person.last_interaction_date,
                "last_intimacy_change": person.last_intimacy_change,
                "last_intimacy_change_date": person.last_intimacy_change_date,
                "intimacy_change_history": person.intimacy_change_history,
                "acceptance_rate": person.acceptance_rate,
                "rejection_count": person.rejection_count,
            }

            existing_state = states.get(contact_id, {})
            updated_at = datetime.now().isoformat()
            closeness = max(0.0, min(1.0, person.intimacy / 100.0))
            if not existing_state:
                stage_history = {updated_at: "initial"}
                current_stage = "initial"
                interaction_count = 0
                days_since_interaction = 0
                trust_level = 0.5
                interaction_frequency = 0.0
            else:
                stage_history = existing_state.get("stage_history", {})
                current_stage = existing_state.get("current_stage", "initial")
                interaction_count = existing_state.get("interaction_count", 0)
                days_since_interaction = existing_state.get("days_since_interaction", 0)
                trust_level = existing_state.get("trust_level", 0.5)
                interaction_frequency = existing_state.get("interaction_frequency", 0.0)

            states[contact_id] = {
                "contact_id": contact_id,
                "current_stage": current_stage,
                "interaction_count": interaction_count,
                "days_since_interaction": days_since_interaction,
                "stage_history": stage_history,
                "closeness": closeness,
                "trust_level": trust_level,
                "interaction_frequency": interaction_frequency,
                "updated_at": updated_at,
            }

        profiles_path.write_text(
            json.dumps(profiles, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        states_path.write_text(
            json.dumps(states, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        
        # 保存长期记忆
        memories_path = data_path / "long_term_memories.json"
        memories_path.write_text(
            json.dumps(self.memory_service.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _relationship_from_contact_type(contact_type: str) -> str:
        mapping = {
            "friend": "朋友",
            "family": "家人",
            "colleague": "同事",
            "stranger": "客户",
            "other": "客户",
        }
        return mapping.get(contact_type, "朋友")

    @staticmethod
    def _contact_type_from_relationship(relationship_type: str) -> str:
        mapping = {
            "家人": "family",
            "朋友": "friend",
            "同事": "colleague",
            "领导": "colleague",
            "暧昧": "other",
            "恋人": "other",
            "客户": "other",
        }
        return mapping.get(relationship_type, "other")

    def seed_demo(self) -> None:
        if self.people:
            return
        demo_people = [
            Person(
                person_id=str(uuid4()),
                name="张三",
                relationship_type="朋友",
                intimacy=72,
                style_tags=["理性", "简洁"],
                relative_role="平级",
                age_group="同龄",
                goals=["维持关系"],
            ),
            Person(
                person_id=str(uuid4()),
                name="李四",
                relationship_type="家人",
                intimacy=88,
                style_tags=["温和", "关怀"],
                relative_role="上级",
                age_group="年长",
                goals=["拉近关系"],
            ),
            Person(
                person_id=str(uuid4()),
                name="王主管",
                relationship_type="领导",
                intimacy=45,
                style_tags=["专业", "简洁"],
                relative_role="上级",
                age_group="年长",
                goals=["提升专业感"],
            ),
        ]
        for person in demo_people:
            self.people[person.person_id] = person
            self.memories[person.person_id] = []

    def add_person(self, person: Person) -> None:
        self.people[person.person_id] = person
        self.memories.setdefault(person.person_id, [])

    def update_person(self, person: Person) -> None:
        self.people[person.person_id] = person

    def delete_person(self, person_id: str) -> None:
        if person_id in self.people:
            del self.people[person_id]
        self.memories.pop(person_id, None)
        # 删除长期记忆
        self.memory_service.delete_person_memories(person_id)

    def list_people(self) -> List[Person]:
        return list(self.people.values())

    def add_evolution_note(self, person_id: str, note: str) -> None:
        person = self.people.get(person_id)
        if not person:
            return
        person.evolution_notes.append(note)

    def record_intimacy(self, person_id: str, score: int, reason: str = "", round_id: str = None) -> None:
        """记录亲密度变化。
        
        Args:
            person_id: 对象ID
            score: 新的亲密度分数 (0-100)
            reason: 变化原因（用于追踪）
            round_id: 对话轮次ID，若提供则会替换同轮次的之前记录（用于避免临时值）
        """
        person = self.people.get(person_id)
        if not person:
            return
        
        old_score = person.intimacy
        new_score = max(0, min(100, score))
        change = new_score - old_score
        
        person.intimacy = new_score
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        # 如果提供了 round_id，先删除同轮次的之前记录
        if round_id:
            # 删除 intimacy_history 中同轮次的记录
            person.intimacy_history = [
                h for h in person.intimacy_history 
                if h.get("round_id") != round_id
            ]
            # 删除 intimacy_change_history 中同轮次的记录
            person.intimacy_change_history = [
                h for h in person.intimacy_change_history 
                if h.get("round_id") != round_id
            ]
        
        # 更新历史记录
        record = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "intimacy_score": person.intimacy,
            "change": change,
            "reason": reason,
        }
        if round_id:
            record["round_id"] = round_id
        person.intimacy_history.append(record)
        person.intimacy_history = person.intimacy_history[-365:]  # 保留365天（一年）
        
        # 更新变化历史
        if change != 0:
            change_record = {
                "date": today,
                "change": change,
                "reason": reason,
                "new_score": new_score,
            }
            if round_id:
                change_record["round_id"] = round_id
            person.intimacy_change_history.append(change_record)
            person.intimacy_change_history = person.intimacy_change_history[-365:]  # 保留365天（一年）
            person.last_intimacy_change = change
            person.last_intimacy_change_date = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # 更新最后交互日期
        if change != 0 or True:  # 任何操作都更新日期
            person.last_interaction_date = today

    def add_memory(self, person_id: str, memory: MemoryItem) -> None:
        self.memories.setdefault(person_id, []).append(memory)

    def update_memory(self, person_id: str, memory: MemoryItem) -> None:
        items = self.memories.get(person_id, [])
        for idx, item in enumerate(items):
            if item.memory_id == memory.memory_id:
                items[idx] = memory
                return

    def delete_memory(self, person_id: str, memory_id: str) -> None:
        items = self.memories.get(person_id, [])
        self.memories[person_id] = [m for m in items if m.memory_id != memory_id]

    def list_memories(self, person_id: str, memory_type: str) -> List[MemoryItem]:
        items = self.memories.get(person_id, [])
        return [m for m in items if m.memory_type == memory_type]

    @staticmethod
    def new_person(
        name: str,
        relationship_type: str,
        intimacy: int | None = None,  # None 时自动根据关系类型计算
        avatar_path: str = "",
        style_tags: List[str] | None = None,
        relative_role: str = "平级",
        age_group: str = "同龄",
        goals: List[str] | None = None,
        notes: str = "",
    ) -> Person:
        # 导入 IntimacyManager 来计算基础亲密度
        from core.intimacy_manager import IntimacyManager
        
        if intimacy is None:
            intimacy = IntimacyManager.get_base_intimacy(relationship_type)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        return Person(
            person_id=str(uuid4()),
            name=name,
            relationship_type=relationship_type,
            intimacy=intimacy,
            avatar_path=avatar_path,
            style_tags=style_tags or [],
            relative_role=relative_role,
            age_group=age_group,
            goals=goals or [],
            notes=notes,
            last_interaction_date=today,  # 新建对象记录为今天
        )

    @staticmethod
    def new_memory(memory_type: str, content: str, source: str) -> MemoryItem:
        return MemoryItem(
            memory_id=str(uuid4()),
            memory_type=memory_type,
            content=content,
            source=source,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
