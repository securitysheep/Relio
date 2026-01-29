"""用户画像管理：为不同社交对象建立和维护对应的用户画像。"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Optional
from datetime import datetime


class ContactType(str, Enum):
    """对话对象类型。"""
    FRIEND = "friend"          # 好友
    FAMILY = "family"          # 家人
    COLLEAGUE = "colleague"    # 同事
    STRANGER = "stranger"      # 陌生人
    OTHER = "other"            # 其他


@dataclass
class StyleParams:
    """对话风格参数。"""
    formality: float = 0.5      # 正式程度 (0=非常随意, 1=非常正式)
    initiative: float = 0.5     # 主动性 (0=被动, 1=主动)
    emotion: float = 0.5        # 情绪表达倾向 (0=冷静, 1=热情)
    humor: float = 0.5          # 幽默倾向 (0=严肃, 1=幽默)
    verbosity: float = 0.5      # 冗长程度 (0=简洁, 1=详细)


@dataclass
class UserProfile:
    """用户画像：为单个联系人维护的个性化配置。"""
    contact_id: str             # 联系人唯一标识
    contact_name: str           # 联系人昵称
    contact_type: ContactType   # 对话对象类型
    style_params: StyleParams = field(default_factory=StyleParams)
    
    # 统计信息
    total_messages: int = 0     # 总消息数
    last_interaction: Optional[str] = None  # 最后交互时间 (ISO format)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 用户自定义描述
    description: str = ""       # 用户对该联系人的自定义描述

    def to_dict(self) -> dict:
        """转换为字典，便于序列化。"""
        return asdict(self)

    def update_interaction(self) -> None:
        """更新最后交互时间和消息计数。"""
        self.last_interaction = datetime.now().isoformat()
        self.total_messages += 1


class UserProfileManager:
    """用户画像管理器：维护所有联系人的画像。"""

    def __init__(self):
        self._profiles: Dict[str, UserProfile] = {}

    def create_profile(
        self,
        contact_id: str,
        contact_name: str,
        contact_type: ContactType = ContactType.FRIEND,
        description: str = "",
    ) -> UserProfile:
        """为新联系人创建用户画像。"""
        if contact_id in self._profiles:
            raise ValueError(f"Profile for {contact_id} already exists")
        
        profile = UserProfile(
            contact_id=contact_id,
            contact_name=contact_name,
            contact_type=contact_type,
            description=description,
        )
        self._profiles[contact_id] = profile
        return profile

    def get_profile(self, contact_id: str) -> Optional[UserProfile]:
        """获取指定联系人的画像，若不存在则返回 None。"""
        return self._profiles.get(contact_id)

    def get_or_create_profile(
        self,
        contact_id: str,
        contact_name: str = "",
        contact_type: ContactType = ContactType.FRIEND,
    ) -> UserProfile:
        """获取或创建用户画像。"""
        if contact_id not in self._profiles:
            self.create_profile(contact_id, contact_name or contact_id, contact_type)
        return self._profiles[contact_id]

    def update_profile(self, contact_id: str, **kwargs) -> UserProfile:
        """更新指定联系人的画像属性。"""
        profile = self.get_profile(contact_id)
        if not profile:
            raise ValueError(f"Profile for {contact_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
            elif hasattr(profile.style_params, key):
                setattr(profile.style_params, key, value)
        
        return profile

    def update_style_params(
        self, contact_id: str, **params
    ) -> StyleParams:
        """更新指定联系人的风格参数。"""
        profile = self.get_profile(contact_id)
        if not profile:
            raise ValueError(f"Profile for {contact_id} not found")
        
        for key, value in params.items():
            if hasattr(profile.style_params, key):
                setattr(profile.style_params, key, value)
        
        return profile.style_params

    def record_interaction(self, contact_id: str) -> None:
        """记录一次交互。"""
        profile = self.get_or_create_profile(contact_id)
        profile.update_interaction()

    def list_profiles(self) -> Dict[str, UserProfile]:
        """列出所有用户画像。"""
        return dict(self._profiles)

    def delete_profile(self, contact_id: str) -> bool:
        """删除指定联系人的画像。"""
        if contact_id in self._profiles:
            del self._profiles[contact_id]
            return True
        return False
