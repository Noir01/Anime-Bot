import io
import os
import textwrap
import typing
from contextlib import redirect_stdout
from traceback import format_exc

import discord
from discord.ext import commands


class Mod(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self._last_result = None

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
    async def load(self, ctx: commands.Context, *, module: str) -> None:
        """Loads a module."""
        if ctx.author.id != 629243339379834880 and ctx.author.id != 497352662451224578:
            return
        try:
            await self.bot.load_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")
        else:
            await ctx.send("\N{OK HAND SIGN}")

    @commands.command(hidden=True)
    async def unload(self, ctx: commands.Context, *, module: str) -> None:
        """Unloads a module."""
        if ctx.author.id != 629243339379834880 and ctx.author.id != 497352662451224578:
            return
        try:
            await self.bot.unload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")
        else:
            await ctx.send("\N{OK HAND SIGN}")

    @commands.group(name="reload", hidden=True, invoke_without_command=True)
    async def _reload(self, ctx: commands.Context, *, module: str) -> None:
        """Reloads a module."""
        if ctx.author.id != 629243339379834880 and ctx.author.id != 497352662451224578:
            return
        try:
            await self.bot.reload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f"{e.__class__.__name__}: {e}")
        else:
            await ctx.send("\N{OK HAND SIGN}")

    @commands.command(name="sync", hidden=True)
    @commands.is_owner()
    async def _sync(
        self, ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: typing.Optional[typing.Literal["~", "*"]] = None
    ) -> None:
        """Syncs the bot with the guilds.
            !sync -> global sync
            !sync ~ -> sync current guild
            !sync * -> copies all global app commands to current guild and syncs
            !sync id_1 id_2 -> syncs guilds with id 1 and 2"""
        if not guilds:
            if spec == "~":
                fmt = await self.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                self.bot.tree.copy_global_to(guild=ctx.guild)
                fmt = await self.bot.tree.sync(guild=ctx.guild)
            else:
                fmt = await self.bot.tree.sync()

            await ctx.send(f"Synced {len(fmt)} commands {'globally' if spec is None else 'to the current guild.'}")
            return

        fmt = 0
        for guild in guilds:
            try:
                await self.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                fmt += 1

        await ctx.send(f"Synced the tree to {fmt}/{len(guilds)} guilds.")

    def cleanup_code(self, content: str) -> str:
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        content = content.replace("```", "\n```")
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        return content.strip("` \n")

    @commands.command(hidden=True, name="eval", aliases=["e"])
    async def _eval(self, ctx: commands.Context, *, body: str) -> None:
        """Evaluates a code"""
        if ctx.author.id != 629243339379834880 and ctx.author.id != 497352662451224578:
            return
        env = {
            "Client": self.bot,
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


async def setup(bot):
    await bot.add_cog(Mod(bot))
