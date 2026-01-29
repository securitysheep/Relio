"""亲密度管理器：新的衰减机制与合理的增长逻辑。"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, List
import math
import logging

logger = logging.getLogger(__name__)


class IntimacyManager:
    """管理亲密度的增长和衰减。"""
    
    # 可配置的衰减率（百分比）
    DECAY_RATE_7_14 = 0.1    # 7-14天每日衰减率
    DECAY_RATE_14_30 = 0.15  # 14-30天每日衰减率
    DECAY_RATE_30_90 = 0.2   # 30-90天每日衰减率
    DECAY_RATE_90_PLUS = 0.3 # 90天以上每日衰减率
    
    # 可配置的增长/惩罚权重
    LIKE_WEIGHT = 2      # 喜欢消息增加的亲密度
    DISLIKE_WEIGHT = 1   # 不喜欢消息减少的亲密度
    
    # 可配置的接受率变化
    ACCEPTANCE_DELTA = 0.05  # 喜欢消息的接受率增加
    REJECTION_DELTA = 0.05   # 不喜欢消息的接受率减少
    
    # 基于关系类型的初始亲密度（可动态更新）
    BASE_INTIMACY_BY_TYPE = {
        "家人": 35,
        "恋人": 45,
        "伴侣": 45,
        "亲密朋友": 30,
        "朋友": 25,
        "同事": 20,
        "熟人": 15,
        "陌生人": 10,
    }
    
    # 系统支持的所有关系类型（单一来源）
    RELATIONSHIP_TYPES: List[str] = [
        "家人", "恋人", "伴侣", "亲密朋友", "朋友", "同事", "熟人", "陌生人"
    ]
    
    # 亲密度阶段定义
    STAGES = {
        (0, 20): ("陌生人", "Stranger"),
        (20, 40): ("浅认识", "Acquaintance"),
        (40, 60): ("普通朋友", "Friend"),
        (60, 75): ("亲近朋友", "Close Friend"),
        (75, 90): ("亲密朋友", "Very Close"),
        (90, 101): ("知己", "Intimate"),
    }
    
    # 是否已加载保存的设置
    _settings_loaded = False
    
    @classmethod
    def load_saved_settings(cls) -> None:
        """从配置文件加载保存的亲密度权重设置。"""
        if cls._settings_loaded:
            return
        
        try:
            from .config import load_intimacy_weight_settings
            settings = load_intimacy_weight_settings()
            
            # 应用衰减率
            cls.DECAY_RATE_7_14 = settings.decay_7_14
            cls.DECAY_RATE_14_30 = settings.decay_14_30
            cls.DECAY_RATE_30_90 = settings.decay_30_90
            cls.DECAY_RATE_90_PLUS = settings.decay_90_plus
            
            # 应用增长权重
            cls.LIKE_WEIGHT = settings.like_weight
            cls.DISLIKE_WEIGHT = settings.dislike_weight
            
            # 应用接受率变化
            cls.ACCEPTANCE_DELTA = settings.acceptance_delta
            cls.REJECTION_DELTA = settings.rejection_delta
            
            # 应用初始亲密度
            for rel_type, value in settings.base_intimacy.items():
                if rel_type in cls.BASE_INTIMACY_BY_TYPE:
                    cls.BASE_INTIMACY_BY_TYPE[rel_type] = value
            
            cls._settings_loaded = True
            logger.info("Loaded saved intimacy weight settings")
        except Exception as e:
            logger.warning(f"Failed to load intimacy weight settings: {e}")
    
    @classmethod
    def update_decay_rates(
        cls,
        decay_7_14: float,
        decay_14_30: float,
        decay_30_90: float,
        decay_90_plus: float,
    ) -> None:
        """更新衰减率配置。"""
        cls.DECAY_RATE_7_14 = decay_7_14
        cls.DECAY_RATE_14_30 = decay_14_30
        cls.DECAY_RATE_30_90 = decay_30_90
        cls.DECAY_RATE_90_PLUS = decay_90_plus
    
    @classmethod
    def update_growth_weights(
        cls,
        like_weight: int,
        dislike_weight: int,
        acceptance_delta: float = None,
        rejection_delta: float = None,
    ) -> None:
        """更新增长权重配置。"""
        cls.LIKE_WEIGHT = like_weight
        cls.DISLIKE_WEIGHT = dislike_weight
        if acceptance_delta is not None:
            cls.ACCEPTANCE_DELTA = acceptance_delta
        if rejection_delta is not None:
            cls.REJECTION_DELTA = rejection_delta
    
    @classmethod
    def update_base_intimacy(
        cls,
        base_intimacy_map: Dict[str, int],
    ) -> None:
        """更新各关系类型的初始亲密度。"""
        for rel_type, value in base_intimacy_map.items():
            if rel_type in cls.BASE_INTIMACY_BY_TYPE:
                cls.BASE_INTIMACY_BY_TYPE[rel_type] = value
    
    @classmethod
    def get_relationship_types(cls) -> List[str]:
        """获取系统支持的所有关系类型。"""
        return cls.RELATIONSHIP_TYPES.copy()
    
    @staticmethod
    def get_base_intimacy(relationship_type: str) -> int:
        """获取基于关系类型的基础亲密度。"""
        return IntimacyManager.BASE_INTIMACY_BY_TYPE.get(relationship_type, 25)
    
    @staticmethod
    def get_stage(intimacy: int) -> Tuple[str, str]:
        """获取当前亲密度对应的阶段。"""
        for (min_val, max_val), (cn, en) in IntimacyManager.STAGES.items():
            if min_val <= intimacy < max_val:
                return (cn, en)
        return ("未知", "Unknown")
    
    @staticmethod
    def calculate_decay(
        current_intimacy: int,
        last_interaction_date: Optional[str],
        today: Optional[str] = None,
    ) -> Tuple[int, str]:
        """
        计算应该衰减的亲密度。
        
        Args:
            current_intimacy: 当前亲密度 (0-100)
            last_interaction_date: 最后交互日期 (YYYY-MM-DD)
            today: 当前日期 (YYYY-MM-DD)，默认为系统日期
        
        Returns:
            (衰减后的亲密度, 衰减原因)
        """
        if today is None:
            today = datetime.now().strftime("%Y-%m-%d")
        
        if not last_interaction_date:
            # 新对象，无衰减
            return current_intimacy, ""
        
        try:
            last_date = datetime.strptime(last_interaction_date, "%Y-%m-%d")
            today_date = datetime.strptime(today, "%Y-%m-%d")
            days_since = (today_date - last_date).days
        except ValueError:
            return current_intimacy, ""
        
        if days_since < 7:
            # 7天内有交互，无衰减
            return current_intimacy, ""
        elif days_since < 14:
            # 7-14天
            decay = int(math.ceil((days_since - 7) * IntimacyManager.DECAY_RATE_7_14))
        elif days_since < 30:
            # 14-30天
            decay_phase1 = int(math.ceil(7 * IntimacyManager.DECAY_RATE_7_14))
            decay = decay_phase1 + int(math.ceil((days_since - 14) * IntimacyManager.DECAY_RATE_14_30))
        elif days_since < 90:
            # 30-90天
            decay_phase1 = int(math.ceil(7 * IntimacyManager.DECAY_RATE_7_14))
            decay_phase2 = int(math.ceil(16 * IntimacyManager.DECAY_RATE_14_30))
            decay = decay_phase1 + decay_phase2 + int(math.ceil((days_since - 30) * IntimacyManager.DECAY_RATE_30_90))
        else:
            # 90天以上
            decay_phase1 = int(math.ceil(7 * IntimacyManager.DECAY_RATE_7_14))
            decay_phase2 = int(math.ceil(16 * IntimacyManager.DECAY_RATE_14_30))
            decay_phase3 = int(math.ceil(60 * IntimacyManager.DECAY_RATE_30_90))
            decay = decay_phase1 + decay_phase2 + decay_phase3 + int(math.ceil((days_since - 90) * IntimacyManager.DECAY_RATE_90_PLUS))
        
        new_intimacy = max(IntimacyManager.get_base_intimacy("陌生人"), current_intimacy - decay)
        reason = f"长期不联系（{days_since}天未交互）"
        
        return new_intimacy, reason
    
    @staticmethod
    def calculate_growth(
        current_intimacy: int,
        message_length: int,
        sentiment_score: float,  # -1 ~ 1
        user_accepted: bool,
        has_question: bool = False,
        has_thanks: bool = False,
        has_empathy: bool = False,
        days_since_last: int = 0,
    ) -> Tuple[int, str, int]:
        """
        计算应该增加的亲密度。
        
        Args:
            current_intimacy: 当前亲密度
            message_length: 消息长度（字符数）
            sentiment_score: 情感评分 (-1=非常负面, 0=中立, 1=非常正面)
            user_accepted: 用户是否接受了建议
            has_question: 消息中是否包含问题
            has_thanks: 消息中是否包含感谢
            has_empathy: 消息中是否包含共鸣表达
            days_since_last: 距离最后交互的天数
        
        Returns:
            (新亲密度, 变化原因, 原始增长值)
        """
        # 只有接受建议才能增长
        if not user_accepted:
            return current_intimacy, "建议未被接受", 0
        
        # 周期性限制：超过30天未交互不增长
        if days_since_last > 30:
            return current_intimacy, "长期不交互，暂停增长", 0
        
        # 基础分
        base_score = 2
        
        # 深度乘数（根据消息长度）
        if message_length > 200:
            depth_multiplier = 1.3
        elif message_length > 100:
            depth_multiplier = 1.2
        elif message_length > 50:
            depth_multiplier = 1.1
        else:
            depth_multiplier = 1.0
        
        # 情感调整
        if sentiment_score >= 0.3:
            sentiment_bonus = 2
        elif sentiment_score >= 0.0:
            sentiment_bonus = 1
        elif sentiment_score >= -0.3:
            sentiment_bonus = 0
        else:
            sentiment_bonus = -2
        
        # 质量加分
        quality_bonus = 0
        if has_question:
            quality_bonus += 1
        if has_thanks:
            quality_bonus += 1
        if has_empathy:
            quality_bonus += 1
        
        # 频率加成
        if days_since_last <= 3:
            frequency_multiplier = 1.0
        elif days_since_last <= 7:
            frequency_multiplier = 0.95
        elif days_since_last <= 14:
            frequency_multiplier = 0.90
        else:
            frequency_multiplier = 0.80
        
        # 计算最终增长
        growth = int(round(
            (base_score * depth_multiplier + sentiment_bonus + quality_bonus) * frequency_multiplier
        ))
        
        # 周增长限制：最多 +15 分
        growth = min(15, growth)
        growth = max(1, growth)  # 最少 +1 分
        
        new_intimacy = min(100, current_intimacy + growth)
        reason = f"正常交互 (+{growth}分)"
        
        return new_intimacy, reason, growth
    
    @staticmethod
    def apply_rejection_penalty(
        current_intimacy: int,
        rejection_count: int,
    ) -> Tuple[int, str]:
        """
        应用拒绝建议的惩罚。
        
        Args:
            current_intimacy: 当前亲密度
            rejection_count: 本周拒绝次数
        
        Returns:
            (惩罚后的亲密度, 惩罚原因)
        """
        if rejection_count == 0:
            return current_intimacy, ""
        
        # 每次拒绝 -2 分
        penalty = rejection_count * 2
        
        # 如果多次拒绝 (>3次)，额外惩罚
        if rejection_count > 3:
            penalty += 2
        
        new_intimacy = max(0, current_intimacy - penalty)
        reason = f"多次拒绝建议 (-{penalty}分)"
        
        return new_intimacy, reason
    
    @staticmethod
    def format_interaction_status(
        last_interaction_date: Optional[str],
        current_intimacy: int,
        today: Optional[str] = None,
    ) -> str:
        """格式化最后交互状态的显示文本。"""
        if not last_interaction_date:
            return "未曾交互"
        
        if today is None:
            today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            last_date = datetime.strptime(last_interaction_date, "%Y-%m-%d")
            today_date = datetime.strptime(today, "%Y-%m-%d")
            days_since = (today_date - last_date).days
        except ValueError:
            return "未知"
        
        if days_since == 0:
            return "刚刚交互"
        elif days_since == 1:
            return "昨天交互"
        elif days_since < 7:
            return f"{days_since}天前交互"
        elif days_since < 30:
            weeks = days_since // 7
            return f"{weeks}周前交互" if weeks > 0 else "最近交互"
        else:
            months = days_since // 30
            return f"{months}个月前交互"
