from logging import Formatter, Handler, LogRecord
from os import environ

from aiohttp import ClientSession
from discord import Intents
from discord.ext.commands import Bot
from discord.utils import escape_markdown
from psycopg_pool import AsyncConnectionPool
from requests import post

from Cogs.utils.queries import createDiscordAnilistSQLQuery, createGeneralSQLQuery

# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# Psycopg needs this to run on Windows asynchronously.


class WebhookHandler(Handler):
    def emit(self, record: LogRecord) -> None:
        logEntry = self.format(record)
        return post(url=environ["WEBHOOK_URL"], json={"content": escape_markdown(logEntry)})


class WebhookFormatter(Formatter):
    def formatTime(self, record: LogRecord, datefmt: str | None = ...) -> str:
        return f"<t:{int(record.created)}:D> <t:{int(record.created)}:T>"  # Full date and time


class Animebot(Bot):
    def __init__(self):
        super().__init__(command_prefix=",", intents=Intents.default(), application_id=807048421500387329)
        self.initial_extensions = ["Cogs.General", "Cogs.Mod", "Cogs.Anime", "Cogs.Manga", "Cogs.Character"]

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
    log_formatter=WebhookFormatter("[{asctime}] [{levelname}] {name}: {message}", style="{"),
)
