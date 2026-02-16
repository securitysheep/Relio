"""配置加载模块：读取环境变量并提供系统配置参数。"""

import os
import sys
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any

# 若存在 python-dotenv，则自动加载项目根目录下的 .env 文件，便于本地开发。
try:  # pragma: no cover - optional helper
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

logger = logging.getLogger(__name__)


def get_app_data_dir() -> Path:
    """获取应用数据目录（用户可写）。
    
    - macOS 打包应用: ~/Library/Application Support/Relio/
    - 开发模式: 项目目录下的 data/
    """
    # 检测是否在打包的应用中运行
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的应用
        if sys.platform == 'darwin':
            # macOS: 使用 Application Support 目录
            app_support = Path.home() / "Library" / "Application Support" / "Relio"
        else:
            # Windows/Linux: 使用用户主目录
            app_support = Path.home() / ".relio"
        app_support.mkdir(parents=True, exist_ok=True)
        return app_support
    else:
        # 开发模式：使用项目目录下的 data/
        return Path(__file__).parent.parent / "data"


# 用户设置文件路径
USER_SETTINGS_FILE = get_app_data_dir() / "user_settings.json"


@dataclass
class IntimacyWeightSettings:
    """亲密度权重设置。"""
    # 衰减率
    decay_7_14: float = 0.1
    decay_14_30: float = 0.15
    decay_30_90: float = 0.2
    decay_90_plus: float = 0.3
    
    # 增长权重
    like_weight: int = 2
    dislike_weight: int = 1
    
    # 接受率变化
    acceptance_delta: float = 0.05
    rejection_delta: float = 0.05
    
    # 初始亲密度
    base_intimacy: Dict[str, int] = field(default_factory=lambda: {
        "家人": 35,
        "恋人": 45,
        "伴侣": 45,
        "亲密朋友": 30,
        "朋友": 25,
        "同事": 20,
        "熟人": 15,
        "陌生人": 10,
    })


@dataclass
class Settings:
    """对话回复决策系统的配置参数。"""
    # LLM API 配置
    api_key: str = "sk-eykgxclalrqyzjszgzrzopoqznkarqgaiuzcxhkquvvmbhrm"
    base_url: str = "https://api.siliconflow.cn/v1"
    model: str = "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"

    # 文本生成参数
    temperature: float = 0.7
    top_p: float = 0.7
    frequency_penalty: float = 0.5
    max_tokens: int = 512

    # 对话上下文管理
    max_history: int = 6

    # 数据存储目录（运行时会被替换为实际路径）
    data_dir: str = ""


def load_user_settings() -> Dict[str, Any]:
    """从文件加载用户保存的设置。"""
    if USER_SETTINGS_FILE.exists():
        try:
            with open(USER_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load user settings: {e}")
    return {}


def save_user_settings(settings: Dict[str, Any]) -> bool:
    """保存用户设置到文件。"""
    try:
        USER_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USER_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        logger.info(f"User settings saved to {USER_SETTINGS_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save user settings: {e}")
        return False


def load_settings() -> Settings:
    """优先读取用户保存的设置，然后是环境变量，最后是默认值。"""
    # 先加载用户保存的设置
    user_settings = load_user_settings()
    api_settings = user_settings.get("api", {})
    
    # API 配置：用户设置 > 环境变量 > 默认值
    api_key = api_settings.get("api_key") or os.getenv("SILICONFLOW_API_KEY", Settings.api_key)
    if not api_key:
        raise RuntimeError("Missing SILICONFLOW_API_KEY environment variable. Set it before running.")

    base_url = api_settings.get("base_url") or os.getenv("SILICONFLOW_BASE_URL", Settings.base_url)
    model = api_settings.get("model") or os.getenv("SILICONFLOW_MODEL", Settings.model)

    temperature = api_settings.get("temperature") if "temperature" in api_settings else float(os.getenv("LLM_TEMPERATURE", Settings.temperature))
    top_p = api_settings.get("top_p") if "top_p" in api_settings else float(os.getenv("LLM_TOP_P", Settings.top_p))
    frequency_penalty = api_settings.get("frequency_penalty") if "frequency_penalty" in api_settings else float(os.getenv("LLM_FREQUENCY_PENALTY", Settings.frequency_penalty))
    max_history = api_settings.get("max_history") if "max_history" in api_settings else int(os.getenv("LLM_MAX_HISTORY", Settings.max_history))
    max_tokens = api_settings.get("max_tokens") if "max_tokens" in api_settings else int(os.getenv("LLM_MAX_TOKENS", Settings.max_tokens))

    data_dir = os.getenv("DATA_DIR") or str(get_app_data_dir())

    return Settings(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        max_history=max_history,
        max_tokens=max_tokens,
        data_dir=data_dir,
    )


def save_api_settings(settings: Settings) -> bool:
    """保存 API 设置。"""
    user_settings = load_user_settings()
    user_settings["api"] = {
        "api_key": settings.api_key,
        "base_url": settings.base_url,
        "model": settings.model,
        "temperature": settings.temperature,
        "top_p": settings.top_p,
        "frequency_penalty": settings.frequency_penalty,
        "max_tokens": settings.max_tokens,
        "max_history": settings.max_history,
    }
    return save_user_settings(user_settings)


def load_intimacy_weight_settings() -> IntimacyWeightSettings:
    """加载亲密度权重设置。"""
    user_settings = load_user_settings()
    weight_settings = user_settings.get("intimacy_weights", {})
    
    if not weight_settings:
        return IntimacyWeightSettings()
    
    return IntimacyWeightSettings(
        decay_7_14=weight_settings.get("decay_7_14", 0.1),
        decay_14_30=weight_settings.get("decay_14_30", 0.15),
        decay_30_90=weight_settings.get("decay_30_90", 0.2),
        decay_90_plus=weight_settings.get("decay_90_plus", 0.3),
        like_weight=weight_settings.get("like_weight", 2),
        dislike_weight=weight_settings.get("dislike_weight", 1),
        acceptance_delta=weight_settings.get("acceptance_delta", 0.05),
        rejection_delta=weight_settings.get("rejection_delta", 0.05),
        base_intimacy=weight_settings.get("base_intimacy", IntimacyWeightSettings().base_intimacy),
    )


def save_intimacy_weight_settings(
    decay_settings: Dict[str, float],
    growth_settings: Dict[str, Any],
    base_intimacy: Dict[str, int],
) -> bool:
    """保存亲密度权重设置。"""
    user_settings = load_user_settings()
    user_settings["intimacy_weights"] = {
        "decay_7_14": decay_settings.get("decay_7_14", 0.1),
        "decay_14_30": decay_settings.get("decay_14_30", 0.15),
        "decay_30_90": decay_settings.get("decay_30_90", 0.2),
        "decay_90_plus": decay_settings.get("decay_90_plus", 0.3),
        "like_weight": growth_settings.get("like_weight", 2),
        "dislike_weight": growth_settings.get("dislike_weight", 1),
        "acceptance_delta": growth_settings.get("acceptance_delta", 0.05),
        "rejection_delta": growth_settings.get("rejection_delta", 0.05),
        "base_intimacy": base_intimacy,
    }
    return save_user_settings(user_settings)


# ============ 主题设置 ============

THEME_LIGHT = "light"
THEME_DARK = "dark"
THEME_SYSTEM = "system"


def load_theme_setting() -> str:
    """加载保存的主题设置。
    
    Returns:
        主题设置值: 'light', 'dark', 或 'system'
    """
    user_settings = load_user_settings()
    return user_settings.get("theme", THEME_SYSTEM)


def save_theme_setting(theme: str) -> bool:
    """保存主题设置。
    
    Args:
        theme: 主题值 ('light', 'dark', 或 'system')
    
    Returns:
        是否保存成功
    """
    if theme not in (THEME_LIGHT, THEME_DARK, THEME_SYSTEM):
        logger.warning(f"Invalid theme value: {theme}")
        return False
    
    user_settings = load_user_settings()
    user_settings["theme"] = theme
    return save_user_settings(user_settings)
