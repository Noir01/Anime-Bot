from typing import Optional

from discord import Interaction
from discord.app_commands import Range, command, describe
from discord.ext import commands

from .utils.buttons import Pagination
from .utils.embeds import get_character_embed
from .utils.queries import characterGraphQLQuery


class Character(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @command(name="character", description="Searches for a character with provided name using the Anilist API.")
    @describe(name="The name of the character to search for.", limit="The max number of results to return. Defaults to 10.")
    async def _character(self, interaction: Interaction, name: str, limit: Optional[Range[int, 1, 25]] = 10) -> None:
        await interaction.response.defer()

        query = characterGraphQLQuery
        variables = {"search": name, "perPage": limit}
        params = {"query": query, "variables": variables}

        async with self.bot.session.post("https://graphql.anilist.co/", json=params) as resp:
            if not resp.status == 200:
                await interaction.edit_original_response(content="An error occurred while searching for anime.")
                return

            response = await resp.json()

        if len(response["data"]["Page"]["characters"]) == 0:
            await interaction.edit_original_response(content="No characters found for that search.")

        elif len(response["data"]["Page"]["characters"]) == 1:
            await interaction.edit_original_response(
                embed=get_character_embed(response["data"]["Page"]["characters"][0], user=interaction.user)
            )

        else:
            embeds = [get_character_embed(character, user=interaction.user) for character in response["data"]["Page"]["characters"]]
            view = Pagination(embeds=embeds, user=interaction.user, timeout=60)
            await interaction.edit_original_response(embed=view.pages[0], view=view)

            await view.wait()
            await interaction.edit_original_response(view=view.clear_items())


async def setup(bot: commands.Bot):
    await bot.add_cog(Character(bot))
