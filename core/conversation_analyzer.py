"""对话分析模块：语义分析、上下文提取与画像匹配。"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from .user_profile import UserProfile
from .relationship_state import RelationshipState


@dataclass
class DialogueAnalysis:
    """对话分析结果。"""
    message_id: str                     # 消息唯一标识
    contact_id: str                     # 联系人 ID
    message_content: str                # 消息内容
    
    # 语义信息
    sentiment: float = 0.0              # 情感倾向 (-1=负面, 0=中性, 1=正面)
    keywords: List[str] = None          # 关键词提取结果
    intent: str = "general"             # 消息意图 (greeting/question/complaint/other/general)
    
    # 上下文信息
    conversation_history: List[str] = None  # 最近对话历史摘要
    context_length: int = 0             # 上下文消息数
    
    # 分析时间戳
    analyzed_at: str = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.conversation_history is None:
            self.conversation_history = []
        if self.analyzed_at is None:
            self.analyzed_at = datetime.now().isoformat()


@dataclass
class InteractionContext:
    """交互语境：综合分析结果、用户画像与关系状态。"""
    dialogue_analysis: DialogueAnalysis
    user_profile: UserProfile
    relationship_state: RelationshipState
    
    # 综合评估
    matching_score: float = 0.0         # 用户画像与关系状态的匹配度
    recommendation_confidence: float = 0.0  # 推荐的置信度


class ConversationAnalyzer:
    """对话分析器：执行语义分析、上下文提取、用户画像与关系匹配。"""

    def __init__(self):
        self._message_counter = 0

    def analyze_dialogue(
        self,
        contact_id: str,
        message_content: str,
        conversation_history: Optional[List[str]] = None,
    ) -> DialogueAnalysis:
        """
        分析一条对话消息。
        
        Args:
            contact_id: 联系人 ID
            message_content: 消息内容
            conversation_history: 对话历史（用于上下文分析）
        
        Returns:
            DialogueAnalysis 对象
        """
        self._message_counter += 1
        message_id = f"msg_{contact_id}_{self._message_counter}"
        
        # 执行语义分析
        sentiment = self._analyze_sentiment(message_content)
        keywords = self._extract_keywords(message_content)
        intent = self._classify_intent(message_content)
        
        # 处理上下文历史
        if conversation_history is None:
            conversation_history = []
        
        analysis = DialogueAnalysis(
            message_id=message_id,
            contact_id=contact_id,
            message_content=message_content,
            sentiment=sentiment,
            keywords=keywords,
            intent=intent,
            conversation_history=conversation_history[-5:] if conversation_history else [],
            context_length=len(conversation_history),
        )
        
        return analysis

    def match_profile_and_state(
        self,
        analysis: DialogueAnalysis,
        profile: UserProfile,
        state: RelationshipState,
    ) -> InteractionContext:
        """
        将对话分析结果与用户画像、关系状态进行匹配。
        
        Args:
            analysis: 对话分析结果
            profile: 用户画像
            state: 关系状态
        
        Returns:
            InteractionContext 对象
        """
        # 计算匹配度：基于关键词、意图、情感等因素
        matching_score = self._calculate_matching_score(
            analysis, profile, state
        )
        
        # 计算推荐置信度
        confidence = self._calculate_confidence(
            analysis, profile, state, matching_score
        )
        
        context = InteractionContext(
            dialogue_analysis=analysis,
            user_profile=profile,
            relationship_state=state,
            matching_score=matching_score,
            recommendation_confidence=confidence,
        )
        
        return context

    # ========== 私有方法 ==========

    def _analyze_sentiment(self, text: str) -> float:
        """
        分析消息的情感倾向。
        
        简单实现：基于关键词匹配。
        在实际应用中，可集成专业的情感分析模型。
        
        Returns:
            -1.0 (负面) 到 1.0 (正面)
        """
        # 简单的关键词情感分析
        positive_keywords = {
            '好': 0.5, '开心': 1.0, '喜欢': 0.8, '棒': 0.8,
            '谢谢': 0.6, '爱': 0.9, '美': 0.7, '太好': 1.0,
        }
        negative_keywords = {
            '坏': -0.5, '难受': -0.8, '讨厌': -0.9, '烦': -0.7,
            '生气': -0.8, '伤心': -0.9, '糟': -0.8, '差': -0.6,
        }
        
        sentiment_score = 0.0
        word_count = 0
        
        for word, score in positive_keywords.items():
            if word in text:
                sentiment_score += score
                word_count += 1
        
        for word, score in negative_keywords.items():
            if word in text:
                sentiment_score += score
                word_count += 1
        
        if word_count > 0:
            sentiment_score /= word_count
        
        return max(-1.0, min(1.0, sentiment_score))

    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取消息中的关键词。
        
        简单实现：长度较长的词语。
        在实际应用中，可使用 jieba、TextRank 等分词工具。
        """
        # 简单的分词（按空格和标点符号）
        import re
        words = re.findall(r'\w+', text, re.UNICODE)
        # 过滤长度过短的词
        keywords = [w for w in words if len(w) >= 2]
        return keywords[:10]  # 返回前 10 个关键词

    def _classify_intent(self, text: str) -> str:
        """
        分类消息的意图。
        
        Returns:
            'greeting' (问候)、'question' (提问)、'complaint' (投诉)、'other' 或 'general' (通用)
        """
        text_lower = text.lower()
        
        # 问候意图
        greeting_keywords = {'你好', '早上好', '晚安', 'hi', 'hello', '嗨'}
        if any(kw in text for kw in greeting_keywords):
            return 'greeting'
        
        # 问题意图
        question_keywords = {'?', '？', '怎样', '如何', '为什么', '是什么', '什么时候'}
        if any(kw in text for kw in question_keywords):
            return 'question'
        
        # 投诉意图
        complaint_keywords = {'投诉', '抱怨', '不满', '有问题', '出错', '坏了'}
        if any(kw in text for kw in complaint_keywords):
            return 'complaint'
        
        return 'general'

    def _calculate_matching_score(
        self,
        analysis: DialogueAnalysis,
        profile: UserProfile,
        state: RelationshipState,
    ) -> float:
        """
        计算对话分析与用户画像、关系状态的匹配度。
        
        综合考虑：
        - 消息意图与关系状态的相关性
        - 情感倾向与用户风格的匹配
        - 交互频率与关系阶段的一致性
        """
        score = 0.0
        factors = 0
        
        # 因素 1：情感匹配
        if analysis.sentiment > 0 and profile.style_params.emotion > 0.5:
            score += 0.5
        elif analysis.sentiment < 0 and profile.style_params.emotion < 0.5:
            score += 0.3
        factors += 1
        
        # 因素 2：交互频率匹配
        score += state.interaction_frequency * 0.3
        factors += 1
        
        # 因素 3：信任度影响
        score += state.trust_level * 0.2
        factors += 1
        
        if factors > 0:
            score /= factors
        
        return max(0.0, min(1.0, score))

    def _calculate_confidence(
        self,
        analysis: DialogueAnalysis,
        profile: UserProfile,
        state: RelationshipState,
        matching_score: float,
    ) -> float:
        """
        计算推荐的置信度。
        
        基于：
        - 匹配度
        - 上下文长度（更多历史 = 更高置信）
        - 关系稳定性（亲密度越高置信越高）
        """
        confidence = matching_score * 0.5
        
        # 上下文贡献
        context_factor = min(1.0, analysis.context_length / 10.0)
        confidence += context_factor * 0.3
        
        # 关系稳定性贡献
        confidence += state.closeness * 0.2
        
        return max(0.0, min(1.0, confidence))
