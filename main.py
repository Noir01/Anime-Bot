import asyncio
from os import environ

import aiohttp
import discord
from discord.ext import commands
from psycopg_pool import AsyncConnectionPool

# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) 
#Postgres needs this to run on Windows


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
                await curr.execute("""CREATE TABLE IF NOT EXISTS general (discord bigint PRIMARY KEY,
                                                                          anilist int UNIQUE,
                                                                          anime JSON, manga JSON)""")
                await curr.execute("""CREATE TABLE IF NOT EXISTS discord_anilist (discord bigint PRIMARY KEY,
                                                                                  anilist int UNIQUE)""")
        for ext in self.initial_extensions:
            await self.load_extension(ext)
        await self.tree.sync()

    async def close(self):
        await super().close()
        await self.session.close()
        await self.pool.close()

    async def on_ready(self):
        print("Ready!")


bot = Animebot()
bot.run(environ["TOKEN"])
