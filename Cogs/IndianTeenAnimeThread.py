import discord
from discord.ext import commands

class IndianTeenAnimeThread(commands.Cog):
    def __init__(self, Client) -> None:
        self.Client = Client

def setup(Client):
    Client.add_cog(IndianTeenAnimeThread(Client))