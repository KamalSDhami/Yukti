from __future__ import annotations

import asyncio
import logging
import os

import discord
from discord.ext import commands
from aiohttp import web

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
        runner = await _start_health_server()
        try:
            await bot.start(config.discord_token)
        finally:
            await _stop_health_server(runner)
            await db.close()


async def _start_health_server() -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/health", _health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.getLogger(__name__).info("Health server running on port %s", port)
    return runner


async def _stop_health_server(runner: web.AppRunner) -> None:
    await runner.cleanup()


async def _health_check(request: web.Request) -> web.Response:
    return web.Response(text="ok")


def main() -> None:
    asyncio.run(_run_bot())


if __name__ == "__main__":
    main()
