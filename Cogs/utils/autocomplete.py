from discord import Interaction
from discord.app_commands import Choice

from .tags import adultTags, normalTags


async def tag_autocomplete(interaction: Interaction, tags: str) -> list[Choice[str]]:
    incompleteTag = tags.split(",")[-1].strip()
    completeTags = []

    for tag in normalTags if not interaction.channel.is_nsfw() else adultTags:
        if incompleteTag.lower() in tag.lower():
            result = tag if tags.count(",") == 0 else ", ".join([i.strip().capitalize() for i in tags.split(",")[:-1]]) + ", " + tag
            completeTags.append(Choice(name=result, value=result))

    return completeTags[:25]
