"""LLM 客户端：封装与 OpenAI 兼容接口的交互。"""

import logging
from typing import List

from openai import OpenAI

from .config import Settings
from .history_store import Message


class LLMClient:
    """薄封装，负责调用聊天补全接口并处理异常。"""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = OpenAI(api_key=settings.api_key, base_url=settings.base_url)

    def refresh_client(self) -> None:
        """重新创建 OpenAI 客户端，使用当前 settings 中的配置。
        
        当用户在设置界面修改 API Key 或 Base URL 后调用此方法，
        使新配置生效。
        """
        self._client = OpenAI(
            api_key=self._settings.api_key,
            base_url=self._settings.base_url
        )
        logging.info("LLM client refreshed with new settings")

    def generate_reply(self, messages: List[Message]) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._settings.model,
                messages=messages,
                temperature=self._settings.temperature,
                top_p=self._settings.top_p,
                frequency_penalty=self._settings.frequency_penalty,
                max_tokens=self._settings.max_tokens,
                stream=False,
                response_format={"type": "text"},
            )
            return response.choices[0].message.content
        except Exception as err:  # pragma: no cover - defensive log path
            logging.error("LLM request failed: %s", err)
            return "抱歉，我暂时无法回复。稍后再试一次。"

    
