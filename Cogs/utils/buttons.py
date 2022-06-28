from typing import Union

import discord


class NumberedButton(discord.ui.Button):
    def __init__(self, index: int, user: Union[discord.User, discord.Member]):
        super().__init__(label=str(index))
        self.index = index
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            return
        self.view.value = self.index
        self.view.stop()


class Confirm(discord.ui.View):
    def __init__(self, user: Union[discord.User, discord.Member], timeout: int = 60) -> None:
        super().__init__()
        self.value = None
        self.timeout = timeout
        self.user = user

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return
        self.value = False
        self.stop()


class InverseConfirm(discord.ui.View):
    def __init__(self, user: Union[discord.User, discord.Member], timeout: int = 60) -> None:
        super().__init__()
        self.value = None
        self.timeout = timeout
        self.user = user

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.success)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            return
        self.value = False
        self.stop()


class Pagination(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], user: Union[discord.User, discord.Member], timeout: int = 60) -> None:
        super().__init__(timeout=timeout)
        self.pages = embeds
        self.current_page = 0
        self.user = user

    async def format_page(self, interaction: discord.Interaction) -> None:
        if self.current_page < 0:
            self.current_page = len(self.pages) - 1
        elif self.current_page == len(self.pages):
            self.current_page = 0
        return await interaction.response.edit_message(embed=self.pages[self.current_page])

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.gray)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user != self.user:
            return
        self.current_page -= 1
        await self.format_page(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.gray)
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user != self.user:
            return
        self.current_page += 1
        await self.format_page(interaction)
