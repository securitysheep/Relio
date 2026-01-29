"""记忆提取服务：使用 LLM 从对话中自动提取长期记忆。"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from openai import OpenAI

from .config import Settings


@dataclass
class ExtractedProfileMemory:
    """提取的对象特征。"""
    content: str
    confidence: float  # 0~1


@dataclass
class ExtractedExperienceMemory:
    """提取的关系事件。"""
    event: str
    impact: float  # -1~+1
    event_time: Optional[str] = None


@dataclass
class ExtractedStrategyMemory:
    """提取的沟通策略。"""
    pattern: str
    effectiveness: float  # 0~1


@dataclass
class ExtractionResult:
    """提取结果。"""
    profiles: List[ExtractedProfileMemory]
    experiences: List[ExtractedExperienceMemory]
    strategies: List[ExtractedStrategyMemory]


# 记忆提取的系统提示词
EXTRACTION_SYSTEM_PROMPT = """你是一个对话分析专家。你的任务是从用户与特定联系人的对话记录中，提取有价值的长期记忆信息。

请分析对话内容，提取以下三类信息：

## 1. 对象特征 (profile_traits)
关于联系人的个人特点、偏好、习惯等，如：性格特点、喜好厌恶、生活习惯、职业背景等。
- content: 特征描述（简洁明了，如"喜欢吃辣"、"晚睡晚起"）
- confidence: 置信度 0.0~1.0（根据证据强度判断）

## 2. 关系事件 (experiences)
双方之间发生过的事情，**重点关注：**
- 共同经历的活动（如一起吃饭、看电影、旅行）
- 对话中提到的计划或约定（如约好周末见面）
- 讨论过的话题（如讨论了某个餐厅）
- 任何涉及双方互动的内容

字段说明：
- event: 事件描述（如"讨论了晚餐去哪家餐厅"、"提到想一起看月亮"）
- impact: 对关系的影响 -1.0~+1.0（正面互动为正，负面互动为负，中性为0）
- event_time: 发生时间，使用相对时间表述（如"今天"、"昨天"、"前天"、"上周"、"上个月"），系统会自动转换为具体日期

## 3. 沟通策略 (strategies)
从对话模式中发现的有效或无效沟通方式。
- pattern: 策略模式描述
- effectiveness: 有效性 0.0~1.0

## 输出格式
请以 JSON 格式输出，结构如下：
```json
{
  "profile_traits": [
    {"content": "喜欢篮球运动", "confidence": 0.9}
  ],
  "experiences": [
    {"event": "一起讨论了晚餐的安排", "impact": 0.5, "event_time": "今天"}
  ],
  "strategies": [
    {"pattern": "使用幽默语气能获得更积极的回应", "effectiveness": 0.8}
  ]
}
```

## 注意事项
- 只提取有明确证据支持的信息，不要臆测
- 置信度和影响程度要客观评估
- 如果某类信息没有发现，返回空数组
- 避免重复提取相同内容
- 特征描述要简洁，一般不超过20字
- **关系事件要积极识别**：对话中讨论的任何共同话题、计划、活动都算事件
- 即使是简短的日常对话，也可能包含关系事件（如"讨论了天气"、"分享了心情"）"""


class MemoryExtractor:
    """从对话中提取长期记忆的服务。"""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = OpenAI(api_key=settings.api_key, base_url=settings.base_url)
        self._logger = logging.getLogger(__name__)

    def _convert_relative_time(self, time_str: Optional[str]) -> Optional[str]:
        """将相对时间转换为具体日期格式 (YYYY-MM-DD)。
        
        Args:
            time_str: 相对时间字符串，如"今天"、"昨天"、"上周"等
        
        Returns:
            具体日期字符串，如"2026-01-29"
        """
        if not time_str:
            return datetime.now().strftime("%Y-%m-%d")
        
        time_str = time_str.strip()
        today = datetime.now()
        
        # 相对时间映射
        relative_mappings = {
            "今天": 0,
            "刚才": 0,
            "刚刚": 0,
            "昨天": -1,
            "前天": -2,
            "大前天": -3,
        }
        
        # 检查简单映射
        if time_str in relative_mappings:
            target_date = today + timedelta(days=relative_mappings[time_str])
            return target_date.strftime("%Y-%m-%d")
        
        # 检查"X天前"格式
        days_ago_match = re.match(r'(\d+)\s*天前', time_str)
        if days_ago_match:
            days = int(days_ago_match.group(1))
            target_date = today - timedelta(days=days)
            return target_date.strftime("%Y-%m-%d")
        
        # 检查"上周"/"上个星期"
        if time_str in ("上周", "上个星期", "上星期"):
            target_date = today - timedelta(weeks=1)
            return target_date.strftime("%Y-%m-%d")
        
        # 检查"上个月"
        if time_str in ("上个月", "上月"):
            # 简单处理：减去30天
            target_date = today - timedelta(days=30)
            return target_date.strftime("%Y-%m-%d")
        
        # 检查"本周"/"这周"
        if time_str in ("本周", "这周", "这个星期"):
            return today.strftime("%Y-%m-%d")
        
        # 检查"X周前"格式
        weeks_ago_match = re.match(r'(\d+)\s*周前', time_str)
        if weeks_ago_match:
            weeks = int(weeks_ago_match.group(1))
            target_date = today - timedelta(weeks=weeks)
            return target_date.strftime("%Y-%m-%d")
        
        # 如果已经是日期格式 (YYYY-MM-DD 或类似)，直接返回
        date_pattern = re.match(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?', time_str)
        if date_pattern:
            year, month, day = date_pattern.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 无法识别的格式，返回今天的日期
        self._logger.debug("无法识别的时间格式: %s，使用今天日期", time_str)
        return today.strftime("%Y-%m-%d")

    def extract_from_conversation(
        self, 
        contact_name: str,
        conversation: List[dict],
        existing_memories: Optional[dict] = None,
    ) -> ExtractionResult:
        """
        从对话中提取记忆。
        
        Args:
            contact_name: 联系人名称
            conversation: 对话记录列表，每条包含 role 和 content
            existing_memories: 已有的记忆（用于去重）
        
        Returns:
            ExtractionResult: 提取的记忆结果
        """
        if not conversation:
            return ExtractionResult(profiles=[], experiences=[], strategies=[])

        # 构建对话文本
        conversation_text = self._format_conversation(contact_name, conversation)
        
        # 构建提示
        user_prompt = f"""请分析以下与「{contact_name}」的对话记录，提取长期记忆信息。

## 对话记录
{conversation_text}

"""
        if existing_memories:
            existing_text = self._format_existing_memories(existing_memories)
            if existing_text:
                user_prompt += f"""## 已有记忆（请避免重复提取）
{existing_text}

"""

        user_prompt += "请以 JSON 格式输出提取结果："

        # 调用 LLM
        try:
            self._logger.info("Starting memory extraction for %s with %d messages", contact_name, len(conversation))
            self._logger.debug("Conversation text:\n%s", conversation_text)
            
            response = self._client.chat.completions.create(
                model=self._settings.model,
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,  # 低温度以获得更稳定的输出
                max_tokens=1024,
                response_format={"type": "text"},
            )
            result_text = response.choices[0].message.content
            self._logger.info("LLM response received, length=%d", len(result_text) if result_text else 0)
            self._logger.debug("LLM response:\n%s", result_text)
            return self._parse_result(result_text)
        except Exception as err:
            self._logger.error("Memory extraction failed: %s", err)
            return ExtractionResult(profiles=[], experiences=[], strategies=[])

    def _format_conversation(self, contact_name: str, conversation: List[dict]) -> str:
        """格式化对话记录。"""
        lines = []
        for msg in conversation:
            role = msg.get("role", "")
            # 兼容 "content" 和 "text" 两种键名
            content = msg.get("content") or msg.get("text", "")
            if role == "user":
                lines.append(f"我: {content}")
            elif role == "assistant":
                lines.append(f"{contact_name}: {content}")
            else:
                lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _format_existing_memories(self, memories: dict) -> str:
        """格式化已有记忆。"""
        parts = []
        
        profiles = memories.get("profile_traits", [])
        if profiles:
            profile_texts = [f"- {p.get('content', '')}" for p in profiles[:5]]
            parts.append("对象特征:\n" + "\n".join(profile_texts))
        
        experiences = memories.get("key_experiences", [])
        if experiences:
            exp_texts = [f"- {e.get('event', '')}" for e in experiences[:5]]
            parts.append("关系事件:\n" + "\n".join(exp_texts))
        
        return "\n\n".join(parts)

    def _parse_result(self, text: str) -> ExtractionResult:
        """解析 LLM 返回的 JSON 结果。"""
        profiles = []
        experiences = []
        strategies = []

        try:
            # 尝试提取 JSON 块
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = text.strip()
                # 如果以 { 开头，尝试找到匹配的 }
                if json_str.startswith('{'):
                    brace_count = 0
                    end_idx = 0
                    for i, c in enumerate(json_str):
                        if c == '{':
                            brace_count += 1
                        elif c == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = i + 1
                                break
                    json_str = json_str[:end_idx]

            data = json.loads(json_str)

            # 解析 profile_traits
            for item in data.get("profile_traits", []):
                if isinstance(item, dict) and item.get("content"):
                    profiles.append(ExtractedProfileMemory(
                        content=str(item["content"]).strip(),
                        confidence=float(item.get("confidence", 0.7)),
                    ))

            # 解析 experiences
            for item in data.get("experiences", []):
                if isinstance(item, dict) and item.get("event"):
                    raw_time = item.get("event_time")
                    # 将相对时间转换为具体日期
                    event_time = self._convert_relative_time(raw_time)
                    experiences.append(ExtractedExperienceMemory(
                        event=str(item["event"]).strip(),
                        impact=float(item.get("impact", 0.0)),
                        event_time=event_time,
                    ))

            # 解析 strategies
            for item in data.get("strategies", []):
                if isinstance(item, dict) and item.get("pattern"):
                    strategies.append(ExtractedStrategyMemory(
                        pattern=str(item["pattern"]).strip(),
                        effectiveness=float(item.get("effectiveness", 0.5)),
                    ))

        except json.JSONDecodeError as err:
            self._logger.warning("Failed to parse extraction result: %s", err)
        except Exception as err:
            self._logger.error("Unexpected error parsing result: %s", err)

        return ExtractionResult(
            profiles=profiles,
            experiences=experiences,
            strategies=strategies,
        )

    # ==================== 语义比对服务 ====================

    def compare_semantic_similarity(
        self,
        items_to_compare: List[dict],
        memory_type: str,
    ) -> List[dict]:
        """
        使用 LLM 批量比对新记忆与现有记忆的语义相似性。
        
        Args:
            items_to_compare: 待比对列表，每项包含 new_item 和 existing_items
            memory_type: 记忆类型 ("profile", "experience", "strategy")
        
        Returns:
            比对结果列表，包含相似项信息
        """
        if not items_to_compare:
            return []
        
        # 构建比对提示
        if memory_type == "profile":
            type_desc = "对象特征"
            field_name = "content"
        elif memory_type == "experience":
            type_desc = "关系事件"
            field_name = "event"
        else:
            type_desc = "沟通策略模式"
            field_name = "pattern"
        
        prompt = f"""请分析以下「{type_desc}」的语义相似性。

对于每个待检查的新条目，判断它与现有条目中是否存在语义基本相同的（意思相近、表达相似的内容）。

待检查列表：
"""
        for idx, item in enumerate(items_to_compare):
            new_text = item["new_text"]
            existing_texts = item["existing_texts"]
            prompt += f"""
【新条目 {idx + 1}】: {new_text}
现有条目：
"""
            for eidx, ext in enumerate(existing_texts):
                prompt += f"  - 编号 {eidx + 1}: {ext}\n"
        
        prompt += """
请以 JSON 格式输出，结构如下：
```json
{
  "comparisons": [
    {
      "new_index": 1,
      "similar_existing_index": 2,
      "similarity_reason": "两者都描述了喜欢运动的特点"
    },
    {
      "new_index": 2,
      "similar_existing_index": null,
      "similarity_reason": null
    }
  ]
}
```

规则：
- new_index: 新条目的编号（从1开始）
- similar_existing_index: 如果找到语义相似的现有条目，返回其编号（从1开始）；否则返回 null
- similarity_reason: 相似的原因说明；如果不相似则为 null
- 只有当两个条目**语义基本相同**时才判定为相似（仅相关不算相似）
"""

        try:
            response = self._client.chat.completions.create(
                model=self._settings.model,
                messages=[
                    {"role": "system", "content": "你是一个语义分析专家，善于判断文本之间的语义相似性。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1024,
            )
            result_text = response.choices[0].message.content
            
            # 解析结果
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = result_text.strip()
            
            data = json.loads(json_str)
            return data.get("comparisons", [])
            
        except Exception as err:
            self._logger.error("Semantic comparison failed: %s", err)
            return []

    def compare_strategy_patterns(
        self,
        new_pattern: str,
        existing_patterns: List[str],
    ) -> Optional[dict]:
        """
        使用 LLM 判断新策略模式与现有策略模式是否基本一致。
        
        Args:
            new_pattern: 新策略模式
            existing_patterns: 现有策略模式列表
        
        Returns:
            如果找到相似的，返回 {"index": 匹配索引, "reason": 原因}；否则返回 None
        """
        if not existing_patterns:
            return None
        
        prompt = f"""请判断以下新的沟通策略模式与现有策略模式中是否存在**基本一致**的。

【新策略模式】: {new_pattern}

【现有策略模式】:
"""
        for idx, pattern in enumerate(existing_patterns):
            prompt += f"  {idx + 1}. {pattern}\n"
        
        prompt += """
请以 JSON 格式输出：
```json
{
  "has_similar": true,
  "similar_index": 2,
  "similarity_reason": "两者都是关于使用幽默来改善沟通的策略"
}
```

规则：
- has_similar: 是否存在基本一致的策略模式
- similar_index: 相似的现有策略编号（从1开始）；如果不相似则为 null
- similarity_reason: 相似的原因说明
- 只有**策略模式基本一致**时才判定为相似（表达方式相同、目标相同）
"""

        try:
            response = self._client.chat.completions.create(
                model=self._settings.model,
                messages=[
                    {"role": "system", "content": "你是一个沟通策略分析专家。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=512,
            )
            result_text = response.choices[0].message.content
            
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = result_text.strip()
            
            data = json.loads(json_str)
            if data.get("has_similar") and data.get("similar_index"):
                return {
                    "index": data["similar_index"] - 1,  # 转为0-based索引
                    "reason": data.get("similarity_reason", ""),
                }
            return None
            
        except Exception as err:
            self._logger.error("Strategy comparison failed: %s", err)
            return None
