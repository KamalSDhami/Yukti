# Discord Translation Bot

A production-ready multilingual translation bot for Discord servers. It translates on demand and keeps channels clean by delivering translations privately.

## Why this stack
- discord.py: async-first, stable app command support, easy integration with async storage and HTTP clients.
- Langbly Translate v2: Google Translate v2 compatible endpoint with secure Bearer auth.
- SQLite: persistent and lightweight, async via aiosqlite.

## Setup

### 1) Create a Discord application and bot
1. Create an application at https://discord.com/developers/applications
2. Add a bot user and copy the bot token.
3. Enable the Message Content Intent.
4. Invite the bot with permissions: Send Messages, Read Message History, Add Reactions, Use Application Commands.

### 2) Langbly API
1. Sign up at https://langbly.com/signup
2. Create an API key.
3. Optional: use the EU-only endpoint `https://eu.langbly.com` if required.

### 3) Configure the bot
1. Copy .env.example to .env and set `DISCORD_TOKEN` and `LANGBLY_API_KEY`.
2. Optional: Copy config.json.example to config.json for non-secret settings only.

### 4) Install dependencies and run
```
pip install -r requirements.txt
python -m bot.main
```

## Config reference

| Key | Description |
| --- | --- |
| DISCORD_TOKEN | Bot token from the Discord developer portal. |
| LANGBLY_API_KEY | Langbly API key (env only). |
| DISCORD_TOKEN | Discord bot token (env only). |
| LANGBLY_BASE_URL | Base URL for Langbly API (default: https://api.langbly.com). |
| DATABASE_PATH | SQLite database location. |
| LOG_FILE_PATH | Language detection log file. |
| USER_RATE_LIMIT_PER_MIN | Per-user translation requests per minute. |
| GUILD_RATE_LIMIT_PER_MIN | Per-server translation requests per minute. |
| SUPPORTED_LANG_CACHE_MINUTES | Cache duration for the language list. |

## Commands

| Command | Description | Permissions |
| --- | --- | --- |
| /setlang [code] | Set your preferred language. | Everyone |
| /mylang | Show your preferred language. | Everyone |
| /translate [message_id] | Translate a message to your language. | Everyone |
| /translate-disable [#channel] | Disable translation in a channel. | Manage Channels |
| /translate-enable [#channel] | Enable translation in a channel. | Manage Channels |
| /translate-status | List disabled channels. | Manage Channels |
| /lang-stats | Top 5 detected languages in last 7 days. | Manage Channels |

## Behavior notes
- Messages shorter than 3 characters are ignored.
- Bots and webhooks are ignored.
- Disabled channels are ignored.
- Reactions with flag emojis trigger a private translation via DM (Discord does not allow ephemeral responses for reactions).
- If a user has no language set, they are prompted to use /setlang on their first translation request.

## Logging and privacy
Language detection logs include only metadata: timestamp, guild_id, channel_id, user_id, detected_language, target_language, character_count. Message content is never logged.
