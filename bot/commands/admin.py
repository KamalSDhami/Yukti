from __future__ import annotations

import discord
from discord import app_commands

from ..db import Database


def register_admin_commands(tree: app_commands.CommandTree, db: Database) -> None:
    @app_commands.command(name="translate-disable", description="Disable translation in a channel")
    @app_commands.describe(channel="Channel to disable translations in")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def translate_disable(
        interaction: discord.Interaction, channel: discord.TextChannel
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        await db.set_channel_disabled(interaction.guild.id, channel.id, True)
        await interaction.response.send_message(
            f"Translation disabled in {channel.mention}.", ephemeral=True
        )

    @translate_disable.error
    async def translate_disable_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You need Manage Channels permission to use this command.",
                ephemeral=True,
            )
        else:
            raise error

    @app_commands.command(name="translate-enable", description="Enable translation in a channel")
    @app_commands.describe(channel="Channel to enable translations in")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def translate_enable(
        interaction: discord.Interaction, channel: discord.TextChannel
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        await db.set_channel_disabled(interaction.guild.id, channel.id, False)
        await interaction.response.send_message(
            f"Translation enabled in {channel.mention}.", ephemeral=True
        )

    @translate_enable.error
    async def translate_enable_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You need Manage Channels permission to use this command.",
                ephemeral=True,
            )
        else:
            raise error

    @app_commands.command(name="translate-status", description="Show channels with translation disabled")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def translate_status(interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        disabled = await db.list_disabled_channels(interaction.guild.id)
        if not disabled:
            await interaction.response.send_message(
                "No channels are disabled.", ephemeral=True
            )
            return
        mentions = [f"<#{channel_id}>" for channel_id in disabled]
        await interaction.response.send_message(
            "Disabled channels:\n" + "\n".join(mentions),
            ephemeral=True,
        )

    @translate_status.error
    async def translate_status_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You need Manage Channels permission to use this command.",
                ephemeral=True,
            )
        else:
            raise error

    @app_commands.command(name="lang-stats", description="Show detected language stats")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lang_stats(interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return
        stats = await db.get_lang_stats(interaction.guild.id, days=7)
        if not stats:
            await interaction.response.send_message(
                "No language data yet.", ephemeral=True
            )
            return
        lines = [f"{lang}: {count}" for lang, count in stats]
        await interaction.response.send_message(
            "Top languages (7 days):\n" + "\n".join(lines),
            ephemeral=True,
        )

    @lang_stats.error
    async def lang_stats_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You need Manage Channels permission to use this command.",
                ephemeral=True,
            )
        else:
            raise error

    tree.add_command(translate_disable)
    tree.add_command(translate_enable)
    tree.add_command(translate_status)
    tree.add_command(lang_stats)
