import discord

class NumberedButton(discord.ui.Button):
    def __init__(self, index: int):
        super().__init__(label=str(index))
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        self.view.value = self.index
        self.view.stop()

class Confirm(discord.ui.View):
    def __init__(self, timeout: int = 60) -> None:
        super().__init__()
        self.value = None
        self.timeout = timeout

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()

class InverseConfirm(discord.ui.View):
    def __init__(self, timeout: int = 60) -> None:
        super().__init__()
        self.value = None
        self.timeout = timeout

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.success)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()

class Pagination(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], timeout: int = 60) -> None:
        super().__init__(timeout=timeout)
        self.pages = embeds
        self.current_page = 0
    
    async def format_page(self, interaction: discord.Interaction) -> None:
        if self.current_page < 0:
            self.current_page = len(self.pages) - 1
        elif self.current_page == len(self.pages):
            self.current_page = 0
        return await interaction.response.edit_message(embed=self.pages[self.current_page])

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.gray)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_page -= 1
        await self.format_page(interaction)
    
    @discord.ui.button(label="➡️", style=discord.ButtonStyle.gray)
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_page += 1
        await self.format_page(interaction)
