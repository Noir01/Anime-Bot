from logging import Handler, Formatter, LogRecord
from os import environ

import discord
from aiohttp import ClientSession
from requests import post
from discord.ext.commands import Bot
from psycopg_pool import AsyncConnectionPool
from discord import Intents, Object

from Cogs.utils.queries import createGeneralSQLQuery, createDiscordAnilistSQLQuery

# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# Postgres needs this to run on Windows


class WebhookHandler(Handler):
    def emit(self, record: LogRecord) -> None:
        logEntry = self.format(record)
        return post(url=environ['WEBHOOK_URL'], json={"content": logEntry})


class WebhookFormatter(Formatter):
    def formatTime(self, record: LogRecord, datefmt: str | None = ...) -> str:
        return f"<t:{int(record.created)}:D> <t:{int(record.created)}:T>" # Full date and time


class Animebot(Bot):
    def __init__(self):
        super().__init__(command_prefix=",", intents=Intents.default(), application_id=807048421500387329)
        self.initial_extensions = [
            "Cogs.General",
            "Cogs.Mod",
            "Cogs.Anime",
            "Cogs.Manga"
        ]

    async def setup_hook(self):
        self.session = ClientSession()
        self.pool = AsyncConnectionPool(conninfo=environ["DATABASE_URL"])
        async with self.pool.connection() as conn:
            async with conn.cursor() as curr:
                await curr.execute(createGeneralSQLQuery)
                await curr.execute(createDiscordAnilistSQLQuery)
        for ext in self.initial_extensions:
            await self.load_extension(ext)

    async def close(self):
        await self.session.close()
        await self.pool.close()
        await super().close()

    async def on_ready(self):
        print("Ready!")


bot = Animebot()
bot.run(
    environ["TOKEN"],
    log_handler=WebhookHandler(level=20),
    log_formatter=WebhookFormatter("[{asctime}] [{levelname:<8}] {name}: {message}", style="{"),
)
