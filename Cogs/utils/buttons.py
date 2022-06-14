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