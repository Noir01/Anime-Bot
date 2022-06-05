import io
import os
import textwrap
from contextlib import redirect_stdout
from traceback import format_exc

import discord
from discord.ext import commands


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

    @commands.command(hidden=True)
    async def load(self, ctx: commands.Context, *, module: str):
        """Loads a module."""
        if ctx.author.id != 629243339379834880 and ctx.author.id != 497352662451224578:
            return
        try:
            await self.Client.load_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")
        else:
            await ctx.send("\N{OK HAND SIGN}")

    @commands.command(hidden=True)
    async def unload(self, ctx: commands.Context, *, module: str):
        """Unloads a module."""
        if ctx.author.id != 629243339379834880 and ctx.author.id != 497352662451224578:
            return
        try:
            await self.Client.unload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")
        else:
            await ctx.send("\N{OK HAND SIGN}")

    @commands.group(name="reload", hidden=True, invoke_without_command=True)
    async def _reload(self, ctx: commands.Context, *, module: str):
        """Reloads a module."""
        if ctx.author.id != 629243339379834880 and ctx.author.id != 497352662451224578:
            return
        try:
            await self.Client.reload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")
        else:
            await ctx.send("\N{OK HAND SIGN}")

    def cleanup_code(self, content: str) -> str:
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        content = content.replace("```", "\n```")
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        return content.strip("` \n")

    @commands.command(hidden=True, name="eval", aliases=["e"])
    async def _eval(self, ctx: commands.Context, *, body: str):
        """Evaluates a code"""
        if ctx.author.id != 629243339379834880 and ctx.author.id != 497352662451224578:
            return
        env = {
            "Client": self.Client,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "_": self._last_result,
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f"```py\n{value}{format_exc()}\n```")
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction("\u2705")
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f"```py\n{value}\n```")
            else:
                self._last_result = ret
                await ctx.send(f"```py\n{value}{ret}\n```")
