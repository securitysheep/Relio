"""核心系统：对话回复决策系统引擎。"""

import logging

from .config import load_settings
from .user_profile import UserProfileManager, ContactType
from .relationship_state import RelationshipStateManager
from .history_store import ConversationStore
from .conversation_analyzer import ConversationAnalyzer
from .reply_decision import ReplyDecisionEngine
from .llm_client import LLMClient
from .storage import DataStorage


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DialogueDecisionSystem:
    """对话回复决策系统的核心引擎。"""

    def __init__(self):
        """初始化系统组件。"""
        self.settings = load_settings()

        # 初始化各类管理器
        self.profile_manager = UserProfileManager()
        self.state_manager = RelationshipStateManager()
        self.conversation_store = ConversationStore(max_history=self.settings.max_history)

        # 初始化分析与决策模块
        self.analyzer = ConversationAnalyzer()
        self.llm_client = LLMClient(self.settings)
        self.decision_engine = ReplyDecisionEngine(self.llm_client)

        # 初始化数据存储
        self.storage = DataStorage(data_dir=self.settings.data_dir)

        # 加载已有数据
        self._load_data()

        logger.info("System initialized successfully")

    def _load_data(self) -> None:
        """从存储加载已有的用户画像和关系状态。"""
        self.storage.load_all(
            self.profile_manager,
            self.state_manager,
        )

    def _save_data(self) -> None:
        """保存当前的用户画像和关系状态。"""
        self.storage.save_all(
            self.profile_manager,
            self.state_manager,
        )

    def process_message(
        self,
        contact_id: str,
        contact_name: str,
        message_content: str,
        contact_type: ContactType = ContactType.FRIEND,
    ) -> dict:
        """
        处理一条消息，生成回复决策建议。

        Args:
            contact_id: 联系人 ID
            contact_name: 联系人名称
            message_content: 消息内容
            contact_type: 联系人类型

        Returns:
            包含回复建议和分析结果的字典
        """
        logger.info(
            "Processing message from %s (%s): %s...",
            contact_name,
            contact_id,
            message_content[:50],
        )

        # 1. 获取或创建用户画像
        profile = self.profile_manager.get_or_create_profile(
            contact_id=contact_id,
            contact_name=contact_name,
            contact_type=contact_type,
        )

        # 2. 获取关系状态
        state = self.state_manager.get_state(contact_id)

        # 3. 添加消息到对话历史
        self.conversation_store.add_user_message(contact_id, message_content)

        # 4. 执行对话分析
        conversation_history = self.conversation_store.history(contact_id)
        analysis = self.analyzer.analyze_dialogue(
            contact_id=contact_id,
            message_content=message_content,
            conversation_history=[msg["content"] for msg in conversation_history],
        )

        # 5. 匹配用户画像与关系状态
        context = self.analyzer.match_profile_and_state(analysis, profile, state)

        # 6. 生成回复决策
        recommendation = self.decision_engine.generate_reply(context, conversation_history)

        # 7. 记录交互
        profile.update_interaction()
        self.state_manager.record_interaction(contact_id)

        logger.info("Reply recommendation generated for %s", contact_name)

        return {
            "contact_id": contact_id,
            "contact_name": contact_name,
            "analysis": {
                "intent": analysis.intent,
                "sentiment": analysis.sentiment,
                "keywords": analysis.keywords,
            },
            "user_profile": {
                "contact_type": profile.contact_type.value,
                "style_params": {
                    "formality": profile.style_params.formality,
                    "initiative": profile.style_params.initiative,
                    "emotion": profile.style_params.emotion,
                    "humor": profile.style_params.humor,
                    "verbosity": profile.style_params.verbosity,
                },
            },
            "relationship_state": {
                "current_stage": state.current_stage.value,
                "closeness": state.closeness,
                "trust_level": state.trust_level,
            },
            "recommendation": {
                "recommendation_id": recommendation.recommendation_id,
                "suggested_reply": recommendation.suggested_reply,
                "strategy": recommendation.strategy.value,
                "confidence_score": recommendation.confidence_score,
                "alternative_replies": recommendation.alternative_replies,
            },
        }

    def get_system_status(self) -> dict:
        """获取系统当前状态统计。"""
        profiles = self.profile_manager.list_profiles()
        states = self.state_manager.list_states()

        return {
            "total_contacts": len(profiles),
            "total_interactions": sum(p.total_messages for p in profiles.values()),
            "system_initialized": True,
        }

    def save(self) -> None:
        """对外暴露的保存方法。"""
        self._save_data()
