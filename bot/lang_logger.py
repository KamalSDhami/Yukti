from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path


class LanguageLogger:
    def __init__(self, log_file_path: str) -> None:
        Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger("language_detection")
        if not self._logger.handlers:
            handler = logging.FileHandler(log_file_path, encoding="utf-8")
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)
        self._log_file_path = log_file_path

    def log_detection(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int,
        detected_language: str,
        target_language: str,
        character_count: int,
    ) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        line = (
            f"{timestamp},{guild_id},{channel_id},{user_id},"
            f"{detected_language},{target_language},{character_count}"
        )
        self._logger.info(line)
