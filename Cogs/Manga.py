from discord import ApplicationContext
from discord.commands import slash_command, Option
from discord.ext import commands


class Manga(commands.Cog):
    def __init__(self, Client) -> None:
        self.Client = Client

    @slash_command(description="Searches for a manga with provided name using the Anilist API.")
    async def manga(
        self,
        ctx: ApplicationContext,
        name: Option(str, "The name of the manga to search for."),
    ):
        if ctx.channel.is_nsfw():
            query = """"""


def setup(Client):
    Client.add_cog(Manga(Client))
