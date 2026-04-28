from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    discord_token: str
    langbly_api_key: str
    langbly_base_url: str
    database_path: str
    log_file_path: str
    user_rate_limit_per_min: int
    guild_rate_limit_per_min: int
    supported_lang_cache_minutes: int


def _get_value(data: dict, key: str, default=None, required: bool = False):
    value = os.getenv(key)
    if value is None:
        value = data.get(key)
    if value is None:
        value = default
    if required and not value:
        raise RuntimeError(f"Missing required config value: {key}")
    return value


def _get_env_only(key: str, required: bool = False) -> str:
    value = os.getenv(key)
    if required and not value:
        raise RuntimeError(f"Missing required config value: {key}")
    return value or ""


def load_config() -> Config:
    load_dotenv()
    config_path = Path(os.getenv("BOT_CONFIG_PATH", "config.json"))
    data = {}
    if config_path.exists():
        data = json.loads(config_path.read_text(encoding="utf-8"))

    discord_token = _get_env_only("DISCORD_TOKEN", required=True)
    langbly_api_key = _get_env_only("LANGBLY_API_KEY", required=True)
    langbly_base_url = _get_value(data, "LANGBLY_BASE_URL", "https://api.langbly.com")
    database_path = _get_value(data, "DATABASE_PATH", "data/translation_bot.db")
    log_file_path = _get_value(data, "LOG_FILE_PATH", "data/lang_detect.log")
    user_rate_limit = int(_get_value(data, "USER_RATE_LIMIT_PER_MIN", 15))
    guild_rate_limit = int(_get_value(data, "GUILD_RATE_LIMIT_PER_MIN", 100))
    cache_minutes = int(_get_value(data, "SUPPORTED_LANG_CACHE_MINUTES", 720))

    return Config(
        discord_token=discord_token,
        langbly_api_key=langbly_api_key,
        langbly_base_url=langbly_base_url,
        database_path=database_path,
        log_file_path=log_file_path,
        user_rate_limit_per_min=user_rate_limit,
        guild_rate_limit_per_min=guild_rate_limit,
        supported_lang_cache_minutes=cache_minutes,
    )
