from __future__ import annotations

import discord
from discord import app_commands

from ..db import Database
from ..rate_limiter import RateLimiter
from ..translation import TranslationError, Translator


def register_user_commands(
    tree: app_commands.CommandTree,
    db: Database,
    translator: Translator,
    rate_limiter: RateLimiter,
) -> None:
    @app_commands.command(name="setlang", description="Set your preferred language")
    @app_commands.describe(language_code="Language code like en, es, fr, ja")
    async def setlang(interaction: discord.Interaction, language_code: str) -> None:
        language_code = language_code.lower().strip()
        try:
            supported = await translator.get_supported_languages()
        except TranslationError:
            await interaction.response.send_message(
                "Language lookup failed. Please try again later.",
                ephemeral=True,
            )
            return

        if language_code not in supported:
            await interaction.response.send_message(
                "Unsupported language code. Use /lang-codes to see valid codes.",
                ephemeral=True,
            )
            return

        await db.set_user_lang(interaction.user.id, language_code)
        await interaction.response.send_message(
            f"Language set to {language_code}.", ephemeral=True
        )

    @app_commands.command(name="mylang", description="Show your preferred language")
    async def mylang(interaction: discord.Interaction) -> None:
        lang = await db.get_user_lang(interaction.user.id)
        if not lang:
            await interaction.response.send_message(
                "No language set. Use /setlang <code>.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"Your language is {lang}.", ephemeral=True
        )

    @app_commands.command(name="translate", description="Translate a message to your language")
    @app_commands.describe(message_id="Message ID to translate")
    async def translate_cmd(interaction: discord.Interaction, message_id: str) -> None:
        if interaction.guild is None or interaction.channel is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return

        if await db.is_channel_disabled(interaction.guild.id, interaction.channel.id):
            await interaction.response.send_message(
                "Translation is disabled in this channel.", ephemeral=True
            )
            return

        user_lang = await db.get_user_lang(interaction.user.id)
        if not user_lang:
            await interaction.response.send_message(
                "Set your language first with /setlang <code>.",
                ephemeral=True,
            )
            return

        if not rate_limiter.allow_user(interaction.user.id):
            await interaction.response.send_message(
                "You are translating too fast. Please wait a moment.",
                ephemeral=True,
            )
            return
        if not rate_limiter.allow_guild(interaction.guild.id):
            await interaction.response.defer(ephemeral=True)
            await interaction.delete_original_response()
            return

        try:
            target_message = await interaction.channel.fetch_message(int(message_id))
        except (ValueError, discord.HTTPException):
            await interaction.response.send_message(
                "Message not found in this channel.", ephemeral=True
            )
            return

        if len(target_message.content.strip()) < 3:
            await interaction.response.send_message(
                "Message too short to translate.", ephemeral=True
            )
            return

        try:
            detected = await translator.detect_language(target_message.content)
        except TranslationError:
            await interaction.response.send_message(
                "Translation failed. Please try again later.",
                ephemeral=True,
            )
            return

        if detected == user_lang:
            await interaction.response.send_message(
                "Message is already in your language.", ephemeral=True
            )
            return

        try:
            translated = await translator.translate(
                target_message.content, target_lang=user_lang, source_lang=detected
            )
        except TranslationError:
            await interaction.response.send_message(
                "Translation failed. Please try again later.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            _format_translation(target_message, detected, user_lang, translated),
            ephemeral=True,
        )

    @app_commands.command(name="lang-codes", description="Show supported language codes")
    async def lang_codes(interaction: discord.Interaction) -> None:
        try:
            supported = await translator.get_supported_languages()
        except TranslationError:
            await interaction.response.send_message(
                "Language lookup failed. Please try again later.",
                ephemeral=True,
            )
            return

        codes = sorted(supported)
        chunks: list[str] = []
        current = []
        for code in codes:
            current.append(code)
            if len(", ".join(current)) >= 1500:
                chunks.append(", ".join(current))
                current = []
        if current:
            chunks.append(", ".join(current))

        try:
            for index, chunk in enumerate(chunks, start=1):
                prefix = f"Language codes ({index}/{len(chunks)}):\n"
                await interaction.user.send(prefix + chunk)
            await interaction.response.send_message(
                "I sent you the language codes in DM.",
                ephemeral=True,
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                "I couldn't DM you. Please enable DMs from this server and try again.",
                ephemeral=True,
            )

    tree.add_command(setlang)
    tree.add_command(mylang)
    tree.add_command(translate_cmd)
    tree.add_command(lang_codes)


def _format_translation(
    message: discord.Message,
    source_lang: str,
    target_lang: str,
    translated: str,
) -> str:
    return (
        "Translation\n"
        f"From: {source_lang} To: {target_lang}\n"
        f"Author: {message.author.display_name}\n"
        f"Message: {translated}"
    )
