from typing import Literal, Optional, Union

import discord
import psycopg
import psycopg_pool
from discord import Interaction, app_commands, ui, ButtonStyle
from discord.ext import commands
from psycopg.types.json import Jsonb


class Confirm(ui.View):
    def __init__(self, timeout: int = 60) -> None:
        super().__init__()
        self.value = None
        self.timeout = timeout

    @ui.button(label="Confirm", style=ButtonStyle.success)
    async def confirm(self, interaction: Interaction, button: ui.Button):
        self.value = True
        self.stop()

    @ui.button(label="Cancel", style=ButtonStyle.grey)
    async def cancel(self, interaction: Interaction, button: ui.Button):
        self.value = False
        self.stop()


class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.existingAnimeTables = set()
        self.existingMangaTables = set()

    async def updateExistingTables_(self, curr: psycopg.AsyncCursor) -> None:
        """
        Updates the existingAnimeTables and existingMangaTables sets with the names of all tables in the database.
        """
        await curr.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        result = await curr.fetchall()
        for tableTuple in result:
            if tableTuple[0].startswith("a"):
                self.existingAnimeTables.add(tableTuple[0])
            elif tableTuple[0].startswith("m"):
                self.existingMangaTables.add(tableTuple[0])

    async def find_(self, userId: int, curr: psycopg.AsyncCursor) -> Optional[int]:
        """
        Returns the anilist id of the user with the given discord id, or None if no user with the given id exists and vice versa.
        """
        if len(str(id)) > 15:
            await curr.execute(f"SELECT anilist from discord_anilist WHERE discord={userId}")
            result = await curr.fetchone()
            if not result:
                return
            else:
                return result[0]
        else:
            await curr.execute(f"SELECT discord from discord_anilist WHERE anilist={userId}")
            result = await curr.fetchone()
            if not result:
                return
            else:
                return result[0]

    async def update_(self, _list: str, discordId: int, anilistId: int, pool: psycopg_pool.AsyncConnectionPool, force: bool) -> bool:
        async with pool.connection() as conn:
            async with conn.cursor() as curr:
                if _list == "Anime":
                    query = """
                            query ($id: Int, $page: Int, $perPage: Int) {
                                Page(page: $page, perPage: $perPage) {
                                    pageInfo {
                                    total
                                    currentPage
                                    lastPage
                                    hasNextPage
                                    perPage
                                    }
                                    mediaList (userId: $id, type: ANIME, sort: UPDATED_TIME_DESC) {
                                    mediaId
                                    status
                                    progress
                                    score
                                    media {
                                        episodes
                                    }
                                    }
                                }
                                }
                            """
                elif _list == "Manga":
                    query = """
                            query ($id: Int, $page: Int, $perPage: Int) {
                                Page(page: $page, perPage: $perPage) {
                                    pageInfo {
                                    total
                                    currentPage
                                    lastPage
                                    hasNextPage
                                    perPage
                                    }
                                    mediaList (userId: $id, type: MANGA, sort: UPDATED_TIME_DESC) {
                                    mediaId
                                    status
                                    progress
                                    score
                                    media {
                                        chapters
                                    }
                                    }
                                }
                                }
                            """
                mlist = []
                nextPage = True
                page = 1
                while nextPage:
                    variables = {"id": anilistId, "page": page, "perPage": 50}
                    async with self.bot.session.post(
                        "https://graphql.anilist.co", json={"query": query, "variables": variables}
                    ) as resp:
                        response = await resp.json()
                    if force:
                        nextPage = response["data"]["Page"]["pageInfo"]["hasNextPage"]
                    else:
                        nextPage = False
                    mlist += response["data"]["Page"]["mediaList"]
                    page += 1
                # Not really sure what this does but it was in the original code
                mlist = [x for n, x in enumerate(mlist) if x not in mlist[:n]]
                if _list == "Anime":
                    if not self.existingAnimeTables:
                        await self.updateExistingTables_(curr)

                    anime = set()
                    for media in mlist:
                        anime.add("a" + str(media["mediaId"]))
                        if ("a" + str(media["mediaId"])) not in self.existingAnimeTables:
                            await curr.execute(
                                f"""
                                CREATE TABLE IF NOT EXISTS {'a' + str(media['mediaId'])} (Discord bigint PRIMARY KEY, 
                                                                                        Anilist int UNIQUE, 
                                                                                        Status text, Progress int, Score text, Episodes int)
                                """
                            )
                        await curr.execute(
                            f"""
                            INSERT INTO {'a' + str(media['mediaId'])} (Discord, Anilist, Status, Progress, Score, Episodes)
                            VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (Discord) DO
                            UPDATE
                            SET (Status,
                                Progress,
                                Score,
                                Episodes) = (EXCLUDED.Status,
                                EXCLUDED.Progress,
                                EXCLUDED.Score,
                                EXCLUDED.Episodes)
                            """,
                            (
                                discordId,
                                anilistId,
                                media["status"],
                                media["progress"],
                                media["score"],
                                (0 if not media["media"]["episodes"] else media["media"]["episodes"]),
                            ),
                        )
                    await curr.execute("SELECT anime FROM general WHERE discord=%s", (discordId,))
                    try:
                        result = set((await curr.fetchone())[0]["anime"])
                        if force:
                            await curr.execute(
                                "UPDATE general SET anime=%s WHERE discord=%s", (Jsonb({"anime": list(anime)}), discordId)
                            )
                            if result - anime:
                                for table in result - anime:
                                    await curr.execute(f"DELETE FROM {table} WHERE discord=%s", (discordId,))
                        else:
                            if anime - result:
                                await curr.execute(
                                    "UPDATE general SET anime=%s WHERE discord=%s", (Jsonb({"anime": list(anime | result)}), discordId)
                                )
                    except TypeError:
                        await curr.execute(
                            "INSERT INTO general (discord, anilist, anime) VALUES (%s, %s, %s) ON CONFLICT (discord) DO UPDATE SET anime=EXCLUDED.anime",
                            (discordId, anilistId, Jsonb({"anime": list(anime)})),
                        )
                    return True
                elif _list == "Manga":
                    if not self.existingMangaTables:
                        await self.updateExistingTables_(curr)

                    manga = set()
                    for media in mlist:
                        manga.add("m" + str(media["mediaId"]))
                        if ("m" + str(media["mediaId"])) not in self.existingMangaTables:
                            await curr.execute(
                                f"""
                                CREATE TABLE IF NOT EXISTS {'m' + str(media['mediaId'])} (Discord bigint PRIMARY KEY, 
                                                                                        Anilist int UNIQUE, 
                                                                                        Status text, Progress int, Score text, Chapters int)
                                """
                            )
                        await curr.execute(
                            f"""
                            INSERT INTO {'m' + str(media['mediaId'])} (Discord, Anilist, Status, Progress, Score, Chapters)
                            VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (Discord) DO
                            UPDATE
                            SET (Status,
                                Progress,
                                Score,
                                Chapters) = (EXCLUDED.Status,
                                EXCLUDED.Progress,
                                EXCLUDED.Score,
                                EXCLUDED.Chapters)
                            """,
                            (
                                discordId,
                                anilistId,
                                media["status"],
                                media["progress"],
                                media["score"],
                                (0 if not media["media"]["chapters"] else media["media"]["chapters"]),
                            ),
                        )
                    await curr.execute("SELECT manga FROM general WHERE discord=%s", (discordId,))
                    try:
                        result = set((await curr.fetchone())[0]["manga"])
                        if force:
                            await curr.execute(
                                "UPDATE general SET manga=%s WHERE discord=%s", (Jsonb({"manga": list(manga)}), discordId)
                            )
                            if result - manga:
                                for table in result - manga:
                                    await curr.execute(f"DELETE FROM {table} WHERE discord=%s", (discordId,))
                        else:
                            if manga - result:
                                await curr.execute(
                                    "UPDATE general SET anime=%s WHERE discord=%s",
                                    (Jsonb({"manga": list(manga | result)}), discordId),
                                )
                        return True
                    except TypeError:
                        await curr.execute(
                            "INSERT INTO general (discord, anilist, manga) VALUES (%s, %s, %s) ON CONFLICT (discord) DO UPDATE SET manga=EXCLUDED.manga",
                            (discordId, anilistId, Jsonb({"manga": list(manga)})),
                        )

    @app_commands.command(name="ping", description="Pings the bot.")
    async def _ping(self, interaction: Interaction) -> None:
        await interaction.response.send_message(f"Pong! That took about {round(self.bot.latency * 1000)}ms.")

    @app_commands.command(name="set", description="Links an Anilist profile to your Discord profile.")
    @app_commands.describe(username="The username of the Anilist profile to link.")
    async def _set(self, interaction: Interaction, username: str) -> None:
        """
        Links an Anilist profile to your Discord profile.
        """
        query = """
query ($name: String, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    users(name: $name) {
      id
      name
      siteUrl
    }
  }
}
    """
        variables = {"name": username, "page": 1, "perPage": 1}
        async with self.bot.session.post("https://graphql.anilist.co", json={"query": query, "variables": variables}) as resp:
            response = await resp.json()
        users = response["data"]["Page"]["users"]
        if not users:
            await interaction.response.send_message("No matching Anilist account found.")
            return
        user = users[0]
        async with self.bot.pool.connection() as conn:
            async with conn.cursor() as curr:
                if await self.find_(user["id"], curr):
                    await interaction.response.send_message(
                        f"[{user['name']}](https://anilist.co/user/{user['name']}) is already registered under another discord account."
                    )
                    return
                view = Confirm()
                await interaction.response.send_message(
                    content=f"Is [{user['name']}]({user['siteUrl']}) the account you want to link?",
                    view=view,
                )
                if not await view.wait():
                    if view.value:
                        await curr.execute("DELETE FROM discord_anilist WHERE discord=%s", (interaction.user.id,))
                        await curr.execute(
                            "INSERT INTO discord_anilist (discord, anilist) VALUES (%s, %s)", (interaction.user.id, user["id"])
                        )
                        p = await interaction.edit_original_message(
                            content=f"Successfully registered [{user['name']}](https://anilist.co/user/{user['name']}).\nNow adding you to the database.",
                            view=None,
                        )
                        await self.update_(
                            _list="Anime", discordId=interaction.user.id, anilistId=user["id"], pool=self.bot.pool, force=True
                        )
                        await self.update_(
                            _list="Manga", discordId=interaction.user.id, anilistId=user["id"], pool=self.bot.pool, force=True
                        )
                        await p.edit(
                            content="Successfully registered [{user['name']}](https://anilist.co/user/{user['name']}).\nSuccessfully added you to the database.",
                            view=None,
                        )
                    else:
                        await interaction.edit_original_message(content="Please try again with your username.", view=None)

    @app_commands.command(name="unset", description="Unlinks your Anilist profile from your Discord profile.")
    async def _unset(self, interaction: Interaction) -> None:
        async with self.bot.pool.connection() as conn:
            async with conn.cursor() as curr:
                if not await self.find_(interaction.user.id, curr):
                    await interaction.response.send_message("You are not linked to any Anilist account.")
                    return
                view = Confirm()
                for child in view.children:
                    if child.style == discord.ButtonStyle.success:
                        child.style = discord.ButtonStyle.danger
                    elif child.style == discord.ButtonStyle.danger:
                        child.style = discord.ButtonStyle.success
                await interaction.response.send_message(
                    "Are you sure you want to unlink your Anilist account?",
                    view=view,
                )
                if not await view.wait():
                    if view.value:
                        await curr.execute(f"DELETE FROM discord_anilist WHERE discord={interaction.user.id}")
                        await interaction.edit_original_message(content="Successfully unlinked your Anilist account.", view=None)
                    else:
                        await interaction.edit_original_message(content="Operation aborted.", view=None)

    @app_commands.command(name="update", description="Updates the bot's database.")
    @app_commands.rename(_list="list")
    @app_commands.describe(
        _list="The list you want to update",
        user="The user you want to update. Defaults to you.",
        force="Pass True to import your entire list.",
    )
    async def _update(
        self,
        interaction: Interaction,
        _list: Literal["Anime", "Manga"],
        user: Union[discord.Member, discord.User] = None,
        force: Optional[bool] = False,
    ) -> None:
        await interaction.response.defer()
        if user is None:
            user = interaction.user
        async with self.bot.pool.connection() as conn:
            async with conn.cursor() as curr:
                anilistID = await self.find_(user.id, curr)

                if anilistID is None:
                    await interaction.followup.send(f"You are not linked to any Anilist account. Use `/set` to link one.")
                    return

                if await self.update_(_list=_list, discordId=user.id, anilistId=anilistID, force=force, pool=self.bot.pool):
                    await interaction.followup.send("Successfully updated your list.")


async def setup(bot):
    await bot.add_cog(General(bot))
