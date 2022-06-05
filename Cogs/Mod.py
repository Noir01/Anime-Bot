import discord
from discord.ext import commands
import os
from traceback import format_exc

class Mod(commands.cog):
    def __init__(self, bot: commands.bot):
        self.bot = bot

    @commands.command(name="sql", aliases=["exec"], hidden=True)
    async def _sqlexecute(self, ctx: commands.Context, *, sql_query: str) -> None:
        if ctx.author.id != 629243339379834880:
            return
        await ctx.channel.typing()
        async with self.bot.pool.connection() as conn:
            async with conn.cursor() as curr:
                try:
                    await curr.execute(sql_query)
                    await ctx.send("Query executed.")
                    result = str(await curr.fetchall())
                    try:
                        await ctx.send("Result:\n```" + result + "```")
                    except discord.errors.HTTPException:
                        with open("result.txt", "w") as f:
                            f.write(result)
                        await ctx.send(content="Result:\n", file=discord.File("result.txt"))
                        os.remove("result.txt")
                except BaseException:
                    await ctx.send(format_exc())