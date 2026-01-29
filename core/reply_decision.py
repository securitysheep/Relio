"""回复决策模块：根据分析结果生成回复建议。"""

from dataclasses import dataclass, asdict
from typing import List, Optional
from enum import Enum
from datetime import datetime

from .conversation_analyzer import InteractionContext
from .llm_client import LLMClient
from .history_store import Message


class ReplyStrategy(str, Enum):
    """回复策略类型。"""
    FORMAL = "formal"              # 正式风格
    CASUAL = "casual"              # 随意风格
    WARM = "warm"                  # 温暖友好
    PROFESSIONAL = "professional"  # 专业
    HUMOROUS = "humorous"          # 幽默


@dataclass
class ReplyRecommendation:
    """回复建议。"""
    recommendation_id: str          # 推荐唯一标识
    contact_id: str                 # 联系人 ID
    suggested_reply: str            # 建议回复内容
    
    # 策略信息
    strategy: ReplyStrategy         # 采用的回复策略
    confidence_score: float         # 置信度 (0-1)
    matching_score: float           # 与用户画像的匹配度
    
    # 多样性选项
    alternative_replies: List[str] = None  # 替代方案（多样化建议）
    
    # 元信息
    generated_at: str = None
    based_on_context: Optional[str] = None  # 基于的上下文类型

    def __post_init__(self):
        if self.alternative_replies is None:
            self.alternative_replies = []
        if self.generated_at is None:
            self.generated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """转换为字典。"""
        data = asdict(self)
        data['strategy'] = self.strategy.value
        return data


class ReplyDecisionEngine:
    """回复决策引擎：根据交互语境生成个性化回复建议。"""

    def __init__(self, llm_client: LLMClient):
        self._llm = llm_client
        self._recommendation_counter = 0

    def generate_reply(
        self,
        context: InteractionContext,
        conversation_history: List[Message],
    ) -> ReplyRecommendation:
        """
        根据交互语境生成回复建议。
        
        Args:
            context: 交互语境（包含分析结果、用户画像、关系状态）
            conversation_history: 对话历史
        
        Returns:
            ReplyRecommendation 对象
        """
        self._recommendation_counter += 1
        rec_id = f"rec_{context.user_profile.contact_id}_{self._recommendation_counter}"
        
        # 选择合适的回复策略
        strategy = self._select_strategy(context)
        
        # 构建 LLM 提示词
        system_prompt = self._build_system_prompt(context, strategy)
        
        # 调用 LLM 生成回复
        suggested_reply = self._llm.generate_reply(
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_history,
            ]
        )
        
        # 生成替代方案（多样化）
        alternative_replies = self._generate_alternatives(
            context, strategy, suggested_reply
        )
        
        # 创建推荐对象
        recommendation = ReplyRecommendation(
            recommendation_id=rec_id,
            contact_id=context.user_profile.contact_id,
            suggested_reply=suggested_reply,
            strategy=strategy,
            confidence_score=context.recommendation_confidence,
            matching_score=context.matching_score,
            alternative_replies=alternative_replies,
            based_on_context=context.dialogue_analysis.intent,
        )
        
        return recommendation

    # ========== 私有方法 ==========

    def _select_strategy(self, context: InteractionContext) -> ReplyStrategy:
        """
        根据用户画像和关系状态选择回复策略。
        
        Returns:
            选定的 ReplyStrategy
        """
        profile = context.user_profile
        state = context.relationship_state
        analysis = context.dialogue_analysis
        
        # 基于形式程度参数
        formality = profile.style_params.formality
        if formality > 0.7:
            return ReplyStrategy.FORMAL
        elif formality > 0.55:
            return ReplyStrategy.PROFESSIONAL
        
        # 基于情绪表达倾向
        emotion = profile.style_params.emotion
        if emotion > 0.7:
            return ReplyStrategy.WARM
        
        # 基于幽默倾向
        humor = profile.style_params.humor
        if humor > 0.6:
            return ReplyStrategy.HUMOROUS
        
        # 默认随意风格
        return ReplyStrategy.CASUAL

    def _build_system_prompt(
        self,
        context: InteractionContext,
        strategy: ReplyStrategy,
    ) -> str:
        """
        构建 LLM 系统提示词，编码用户画像和关系状态信息。
        """
        profile = context.user_profile
        state = context.relationship_state
        analysis = context.dialogue_analysis
        
        style_desc = self._describe_style(profile.style_params)
        
        prompt = f"""你是一个对话助手，根据用户的个人特征和与对方的关系提供个性化的回复建议。

【关于对方】
- 姓名：{profile.contact_name}
- 关系类型：{profile.contact_type.value}
- 关系阶段：{state.current_stage.value}
- 亲密度：{state.closeness:.1%}
- 信任度：{state.trust_level:.1%}

【你的表达风格】
{style_desc}

【当前对话特征】
- 消息意图：{analysis.intent}
- 情感倾向：{'正面' if analysis.sentiment > 0.3 else '负面' if analysis.sentiment < -0.3 else '中性'}
- 关键词：{', '.join(analysis.keywords) if analysis.keywords else '无'}

【回复策略】
采用 {strategy.value} 的风格进行回复。

请根据上述信息，生成一条符合你个人风格和对方关系阶段的自然回复。回复应该：
1. 符合你的表达习惯和风格特征
2. 考虑与对方的关系亲密度（更亲密的关系可以更随意）
3. 回复的长度和详细程度适当
4. 自然流畅，避免生硬或不符合语境

只返回回复内容，不需要额外说明。"""
        
        return prompt

    def _describe_style(self, style_params) -> str:
        """将风格参数转换为自然语言描述。"""
        descriptions = []
        
        if style_params.formality > 0.7:
            descriptions.append("你倾向于使用正式、规范的语言")
        elif style_params.formality < 0.3:
            descriptions.append("你倾向于使用随意、口语化的表达")
        else:
            descriptions.append("你的语言风格介于正式和随意之间")
        
        if style_params.initiative > 0.7:
            descriptions.append("你倾向于主动、积极地回应")
        elif style_params.initiative < 0.3:
            descriptions.append("你倾向于被动回应，回复较为简短")
        
        if style_params.emotion > 0.7:
            descriptions.append("你热情友好，愿意表达感情")
        elif style_params.emotion < 0.3:
            descriptions.append("你比较冷静理性，表情不多")
        
        if style_params.humor > 0.6:
            descriptions.append("你喜欢使用幽默、开玩笑")
        
        if style_params.verbosity > 0.7:
            descriptions.append("你的回复通常比较详细")
        elif style_params.verbosity < 0.3:
            descriptions.append("你的回复通常简洁明了")
        
        return "\n".join(f"- {desc}" for desc in descriptions) if descriptions else "- 你的表达风格中等"

    def _generate_alternatives(
        self,
        context: InteractionContext,
        primary_strategy: ReplyStrategy,
        primary_reply: str,
        num_alternatives: int = 2,
    ) -> List[str]:
        """
        生成替代回复方案，提供多样化选择。
        
        Args:
            context: 交互语境
            primary_strategy: 主策略
            primary_reply: 主要回复
            num_alternatives: 替代方案数量
        
        Returns:
            替代回复列表
        """
        alternatives = []
        
        # 选择与主策略不同的替代策略
        all_strategies = list(ReplyStrategy)
        other_strategies = [s for s in all_strategies if s != primary_strategy]
        
        for i, strategy in enumerate(other_strategies[:num_alternatives]):
            alt_system_prompt = self._build_system_prompt(context, strategy)
            alt_reply = self._llm.generate_reply(
                messages=[
                    {"role": "system", "content": alt_system_prompt},
                    {"role": "user", "content": context.dialogue_analysis.message_content},
                ]
            )
            if alt_reply != primary_reply:  # 避免完全重复
                alternatives.append(alt_reply)
            
            if len(alternatives) >= num_alternatives:
                break
        
        return alternatives[:num_alternatives]
