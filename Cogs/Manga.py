from datetime import datetime, timedelta
from typing import Optional

from discord import Colour, Interaction
from discord.app_commands import Range, command, describe
from discord.ext import commands
from discord.ui import View

from .utils.buttons import NumberedButton
from .utils.embeds import get_media_embed, get_media_list_embed
from .utils.queries import mediaGraphQLQuery, trendingGraphQLQuery


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
    @describe(name="The name of the manga to search for.", limit="The number of results to return. Defaults to 10.")
    async def _manga(
        self,
        interaction: Interaction,
        name: str,
        limit: Optional[Range[int, 1, 25]] = 10,
    ) -> None:
        await interaction.response.defer()
        query = mediaGraphQLQuery
        variables = {"search": name, "perPage": limit, "page": 1, "type": "MANGA"}
        params = {"query": query, "variables": variables}
        if not interaction.channel.is_nsfw():
            params["variables"]["isAdult"] = False
        async with self.bot.session.post("https://graphql.anilist.co/", json=params) as resp:
            response = await resp.json()
        if not response["data"]["Page"]["media"]:
            await interaction.edit_original_message("No manga found for that search.")
            return
        searchEmbedVar = get_media_list_embed(response["data"]["Page"]["media"], interaction.user)
        view = View(timeout=60)
        for i in range(0, len(response["data"]["Page"]["media"])):
            view.add_item(NumberedButton(i + 1))
        await interaction.edit_original_message(embed=searchEmbedVar, view=view)
        await view.wait()
        if view.value is None:
            searchEmbedVar.color = Colour(int("B20000", 16))
            await interaction.edit_original_message(embed=searchEmbedVar, view=None)
            return
        media = response["data"]["Page"]["media"][view.value - 1]
        if (not self.trending) or datetime.now() - self.last_updated > timedelta(hours=1):
            await self.updateTrending()
        mainEmbedVar = get_media_embed(media=media, trending=media["id"] in self.trending)
        await interaction.edit_original_message(embed=mainEmbedVar, content=None, view=None)


async def setup(bot: commands.Bot):
    await bot.add_cog(Manga(bot))
