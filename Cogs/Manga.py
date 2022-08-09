from datetime import datetime, timedelta
from typing import Optional

from discord import Colour, Interaction
from discord.app_commands import Choice, Range, command, describe
from discord.ext import commands
from discord.ui import View

from .utils.buttons import NumberedButton
from .utils.embeds import get_media_embed, get_media_list_embed
from .utils.queries import mediaGraphQLQuery, trendingGraphQLQuery
from .utils.autocomplete import tag_autocomplete


class Manga(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.trending = set()
        self.last_updated = datetime.now() - timedelta(hours=1)

    async def updateTrending(self):
        query = trendingGraphQLQuery
        async with self.bot.session.post("https://graphql.anilist.co", params={"query": query, "type": "MANGA"}) as resp:
            self.trending.add(media["id"] for media in ((await resp.json())["data"]["Trending"]["media"]))

    @command(name="manga", description="Searches for a manga with provided name using the Anilist API.")
    @describe(
        name="The name of the manga to search for. Can be left blank if tags are provided.",
        tags="Tags to filter results by. Split multiple tags with a comma.",
        limit="The number of results to return. Defaults to 10.",
    )
    async def _manga(
        self, interaction: Interaction, name: str = None, tags: str = None, limit: Optional[Range[int, 1, 25]] = 10
    ) -> None:
        if name is None and tags is None:
            await interaction.response.send_message("You must provide a name and/or tags to search for.", ephemeral=True)
            return

        await interaction.response.defer()

        query = mediaGraphQLQuery
        variables = {"perPage": limit, "page": 1, "type": "MANGA"}
        if name is not None:
            variables["search"] = name
        if tags is not None:
            variables["tags"] = [i.strip().capitalize() for i in tags.split(",")]
        params = {"query": query, "variables": variables}
        if not interaction.channel.is_nsfw():
            params["variables"]["isAdult"] = False

        async with self.bot.session.post("https://graphql.anilist.co/", json=params) as resp:
            if not resp.status == 200:
                await interaction.edit_original_response(content="An error occurred while searching for anime.")
                return

            response = await resp.json()

        if not response["data"]["Page"]["media"]:
            await interaction.edit_original_response(content="No manga found for that search.", view=None)
            return

        if len(response["data"]["Page"]["media"]) == 1:
            media: dict = response["data"]["Page"]["media"][0]
            if (not self.trending) or datetime.now() - self.last_updated > timedelta(hours=1):
                await self.updateTrending()
            mainEmbedVar = get_media_embed(media=media, trending=(media["id"] in self.trending))

            await interaction.edit_original_response(embed=mainEmbedVar, content=None, view=None)

        else:
            searchEmbedVar = get_media_list_embed(response["data"]["Page"]["media"], interaction.user)
            view = View(timeout=60)
            view.value = None
            for i in range(0, len(response["data"]["Page"]["media"])):
                view.add_item(NumberedButton(user=interaction.user, index=(i + 1)))
            await interaction.edit_original_response(embed=searchEmbedVar, view=view)
            await view.wait()

            if view.value is None:
                searchEmbedVar.color = Colour(int("B20000", 16))
                await interaction.edit_original_response(embed=searchEmbedVar, view=None)
                return

            media: dict = response["data"]["Page"]["media"][view.value - 1]

            if (not self.trending) or datetime.now() - self.last_updated > timedelta(hours=1):
                await self.updateTrending()

            mainEmbedVar = get_media_embed(media=media, trending=(media["id"] in self.trending))
            await interaction.edit_original_response(embed=mainEmbedVar, content=None, view=None)

    @_manga.autocomplete("tags")
    async def _anime_autocomplete(self, interaction: Interaction, tags: str) -> list[Choice[str]]:
        return await tag_autocomplete(interaction, tags)


async def setup(bot: commands.Bot):
    await bot.add_cog(Manga(bot))
