from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import html
from typing import Optional

import aiohttp


class TranslationError(RuntimeError):
    pass


@dataclass
class SupportedLanguagesCache:
    languages: set[str]
    expires_at: datetime


class Translator:
    def __init__(self, api_key: str, base_url: str, cache_minutes: int = 720) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._cache_minutes = cache_minutes
        self._session: Optional[aiohttp.ClientSession] = None
        self._supported_cache: Optional[SupportedLanguagesCache] = None

    async def __aenter__(self) -> "Translator":
        timeout = aiohttp.ClientTimeout(total=20)
        self._session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._session:
            await self._session.close()

    async def detect_language(self, text: str) -> str:
        data = await self._request("", {"q": text, "target": "en"})
        try:
            return data["data"]["translations"][0]["detectedSourceLanguage"]
        except (KeyError, IndexError) as exc:
            raise TranslationError("Unexpected detect response") from exc

    async def translate(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
        payload = {"q": text, "target": target_lang}
        if source_lang:
            payload["source"] = source_lang
        data = await self._request("", payload)
        try:
            translated = data["data"]["translations"][0]["translatedText"]
            return html.unescape(translated)
        except (KeyError, IndexError) as exc:
            raise TranslationError("Unexpected translate response") from exc

    async def get_supported_languages(self) -> set[str]:
        if self._supported_cache and self._supported_cache.expires_at > datetime.utcnow():
            return self._supported_cache.languages

        data = await self._request("/languages", {"target": "en"}, method="GET")
        try:
            languages = {lang["language"] for lang in data["data"]["languages"]}
        except (KeyError, TypeError) as exc:
            raise TranslationError("Unexpected languages response") from exc

        self._supported_cache = SupportedLanguagesCache(
            languages=languages,
            expires_at=datetime.utcnow() + timedelta(minutes=self._cache_minutes),
        )
        return languages

    async def _request(self, path: str, payload: dict, method: str = "POST") -> dict:
        if not self._session:
            raise TranslationError("Translator session not initialized")

        url = f"{self._base_url}/language/translate/v2{path}"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            if method == "GET":
                async with self._session.get(url, params=payload, headers=headers) as resp:
                    data = await resp.json()
            else:
                async with self._session.post(url, json=payload, headers=headers) as resp:
                    data = await resp.json()
        except aiohttp.ClientError as exc:
            raise TranslationError("Translation API request failed") from exc

        if "error" in data:
            message = data["error"].get("message", "Translation API error")
            raise TranslationError(message)

        return data
