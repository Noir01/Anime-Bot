import logging
from os import environ

import aiohttp
import discord
import requests
from discord.ext import commands
from psycopg_pool import AsyncConnectionPool

# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# Postgres needs this to run on Windows


class WebhookHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        logEntry = self.format(record)
        return requests.post(url=environ['WEBHOOK_URL'], json={"content": logEntry})


class WebhookFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = ...) -> str:
        return f"<t:{int(record.created)}:f>"


class Animebot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=",", intents=discord.Intents.default(), application_id=807048421500387329)
        self.initial_extensions = [
            "Cogs.General",
            "Cogs.Mod",
        ]

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        self.pool = AsyncConnectionPool(conninfo=environ["DATABASE_URL"])
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(
                    """CREATE TABLE IF NOT EXISTS general (discord bigint PRIMARY KEY,
                                                                          anilist int UNIQUE,
                                                                          anime JSON, manga JSON)"""
                )
                await curr.execute(
                    """CREATE TABLE IF NOT EXISTS discord_anilist (discord bigint PRIMARY KEY,
                                                                                  anilist int UNIQUE)"""
                )
        for ext in self.initial_extensions:
            await self.load_extension(ext)

    async def close(self):
        await super().close()
        await self.session.close()
        await self.pool.close()

    async def on_ready(self):
        print("Ready!")


bot = Animebot()
bot.run(environ["TOKEN"], log_handler=WebhookHandler(level=20), log_formatter=WebhookFormatter("[{asctime}] [{levelname:<8}] {name}: {message}", style="{"))
