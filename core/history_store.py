"""对话历史存储：为每个联系人维护短历史，供决策与生成使用。"""

from collections import defaultdict, deque
from typing import Deque, Dict, List, Literal, TypedDict


Role = Literal["system", "user", "assistant"]


class Message(TypedDict):
    role: Role
    content: str


class ConversationStore:
    """按联系人分桶保存有限长度的消息历史，避免上下文过长。"""

    def __init__(self, max_history: int = 6):
        self._max_history = max_history
        self._sessions: Dict[str, Deque[Message]] = defaultdict(deque)

    def _trim(self, user_id: str) -> None:
        window = self._sessions[user_id]
        while len(window) > self._max_history:
            window.popleft()

    def add_user_message(self, user_id: str, content: str) -> None:
        self._sessions[user_id].append({"role": "user", "content": content})
        self._trim(user_id)

    def add_bot_message(self, user_id: str, content: str) -> None:
        self._sessions[user_id].append({"role": "assistant", "content": content})
        self._trim(user_id)

    def history(self, user_id: str) -> List[Message]:
        return list(self._sessions[user_id])