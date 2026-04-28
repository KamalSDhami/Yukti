from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from .commands.admin import register_admin_commands
from .commands.user import register_user_commands
from .config import load_config
from .db import Database
from .lang_logger import LanguageLogger
from .listeners import register_listeners
from .rate_limiter import RateLimiter
from .translation import Translator


async def _run_bot() -> None:
    config = load_config()

    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    bot = commands.Bot(command_prefix="!", intents=intents)
    db = Database(config.database_path)
    await db.init()
    lang_logger = LanguageLogger(config.log_file_path)
    rate_limiter = RateLimiter(
        config.user_rate_limit_per_min, config.guild_rate_limit_per_min
    )

    @bot.event
    async def on_ready() -> None:
        await bot.tree.sync()
        logging.getLogger(__name__).info("Logged in as %s", bot.user)

    async with Translator(
        config.langbly_api_key,
        config.langbly_base_url,
        cache_minutes=config.supported_lang_cache_minutes,
    ) as translator:
        register_user_commands(bot.tree, db, translator, rate_limiter)
        register_admin_commands(bot.tree, db)
        register_listeners(bot, db, translator, rate_limiter, lang_logger)

        try:
            await bot.start(config.discord_token)
        finally:
            await db.close()


def main() -> None:
    asyncio.run(_run_bot())


if __name__ == "__main__":
    main()
