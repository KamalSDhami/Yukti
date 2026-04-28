from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

from .db import Database
from .lang_logger import LanguageLogger
from .rate_limiter import RateLimiter
from .translation import TranslationError, Translator


def _is_flag_emoji(emoji: discord.PartialEmoji) -> bool:
    if emoji.id is not None:
        return False
    value = emoji.name
    if not value or len(value) != 2:
        return False
    return all(0x1F1E6 <= ord(char) <= 0x1F1FF for char in value)


def register_listeners(
    bot: commands.Bot,
    db: Database,
    translator: Translator,
    rate_limiter: RateLimiter,
    lang_logger: LanguageLogger,
) -> None:
    @bot.event
    async def on_message(message: discord.Message) -> None:
        if message.author.bot or message.webhook_id is not None:
            return
        if message.guild is None:
            return
        if await db.is_channel_disabled(message.guild.id, message.channel.id):
            return
        if len(message.content.strip()) < 3:
            return

        try:
            detected = await translator.detect_language(message.content)
        except TranslationError:
            return

        await db.log_language_detection(
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            user_id=message.author.id,
            detected_language=detected,
            target_language="",
            character_count=len(message.content),
        )
        lang_logger.log_detection(
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            user_id=message.author.id,
            detected_language=detected,
            target_language="",
            character_count=len(message.content),
        )

    @bot.event
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent) -> None:
        if payload.user_id == bot.user.id:
            return
        if payload.guild_id is None:
            return
        if not _is_flag_emoji(payload.emoji):
            return
        if await db.is_channel_disabled(payload.guild_id, payload.channel_id):
            return

        user_lang = await db.get_user_lang(payload.user_id)
        user = bot.get_user(payload.user_id)
        if user is None:
            try:
                user = await bot.fetch_user(payload.user_id)
            except discord.HTTPException:
                user = None
        if not user_lang:
            if user:
                await _safe_dm(user, "Set your language with /setlang <code>.")
            return

        if not rate_limiter.allow_user(payload.user_id):
            if user:
                await _safe_dm(user, "You are translating too fast. Please wait a moment.")
            return
        if not rate_limiter.allow_guild(payload.guild_id):
            return

        channel = bot.get_channel(payload.channel_id)
        if channel is None:
            try:
                channel = await bot.fetch_channel(payload.channel_id)
            except discord.HTTPException:
                return

        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.HTTPException:
            return

        if len(message.content.strip()) < 3:
            return

        try:
            detected = await translator.detect_language(message.content)
        except TranslationError:
            if user:
                await _safe_dm(user, "Translation failed. Please try again later.")
            return

        if detected == user_lang:
            return

        try:
            translated = await translator.translate(
                message.content, target_lang=user_lang, source_lang=detected
            )
        except TranslationError:
            if user:
                await _safe_dm(user, "Translation failed. Please try again later.")
            return

        if user:
            await _safe_dm(user, _format_translation(message, detected, user_lang, translated))


async def _safe_dm(user: discord.User, content: str) -> None:
    try:
        await user.send(content)
    except discord.HTTPException:
        return


def _format_translation(
    message: discord.Message,
    source_lang: str,
    target_lang: str,
    translated: str,
) -> str:
    translated = _trim_text(translated, 1500)
    return (
        "Translation\n"
        f"From: {source_lang} To: {target_lang}\n"
        f"Author: {message.author.display_name}\n"
        f"Message: {translated}"
    )


def _trim_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."
