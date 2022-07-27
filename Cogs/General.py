from typing import Literal, Optional, Union

import psycopg_pool
from discord import AllowedMentions, Interaction, Member, User, app_commands
from discord.ext import commands
from psycopg import AsyncCursor
from psycopg.types.json import Jsonb

from .utils.buttons import Confirm, InverseConfirm
from .utils.queries import createTableSQLQueryGenerator, updateGraphQLQuery, updateTableSQLQueryGenerator


class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.existingAnimeTables = set()
        self.existingMangaTables = set()

    async def updateExistingTables_(self, curr: AsyncCursor) -> None:
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

    @staticmethod
    async def find_(userId: int, curr: AsyncCursor) -> Optional[int]:
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
        async with pool.connection() as conn, conn.cursor() as curr:
            query = updateGraphQLQuery
            mlist = []
            nextPage = True
            page = 1

            while nextPage:
                variables = {"id": anilistId, "page": page, "perPage": 50, "type": _list.upper()}

                async with self.bot.session.post("https://graphql.anilist.co", json={"query": query, "variables": variables}) as resp:
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
                            await curr.execute(createTableSQLQueryGenerator(type_="Anime", name="a" + str(media["mediaId"])))

                        await curr.execute(
                            updateTableSQLQueryGenerator(type_="Anime", name="a" + str(media["mediaId"])),
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
                                await curr.execute(createTableSQLQueryGenerator(type_="Manga", name="m" + str(media["mediaId"])))
                            )

                        await curr.execute(
                            updateTableSQLQueryGenerator(type_="Manga", name="m" + str(media["mediaId"])),
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
                                    "UPDATE general SET anime=%s WHERE discord=%s", (Jsonb({"manga": list(manga | result)}), discordId)
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

        async with self.bot.pool.connection() as conn, conn.cursor() as curr:
            if await self.find_(user["id"], curr):
                await interaction.response.send_message(
                    content=f"Is [{user['name']}]({user['siteUrl']}) the account you want to link?", view=view
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
        async with self.bot.pool.connection() as conn, conn.cursor() as curr:
            if not await self.find_(interaction.user.id, curr):
                await interaction.response.send_message("You are not linked to any Anilist account.")
                return

            view = InverseConfirm(user=interaction.user)
            await interaction.response.send_message("Are you sure you want to unlink your Anilist account?", view=view)

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
        user: Union[Member, User] = None,
        force: Optional[bool] = False,
    ) -> None:
        await interaction.response.defer()

        if user is None:
            user = interaction.user

        async with self.bot.pool.connection() as conn, conn.cursor() as curr:
            anilistID = await self.find_(user.id, curr)

            if anilistID is None:
                await interaction.followup.send(
                    content=f"{user.mention} is not linked to any Anilist account. Use `/set` to link one.",
                    allowed_mentions=AllowedMentions.none(),
                )
                return

            if await self.update_(_list=_list, discordId=user.id, anilistId=anilistID, force=force, pool=self.bot.pool):
                await interaction.followup.send("Successfully updated your list.")


async def setup(bot):
    await bot.add_cog(General(bot))
