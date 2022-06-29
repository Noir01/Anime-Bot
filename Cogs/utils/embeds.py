import re
from datetime import datetime
from typing import Union

from discord import Colour, Embed, Member, User
from markdownify import markdownify

months = {
    "1": "January",
    "2": "February",
    "3": "March",
    "4": "April",
    "5": "May",
    "6": "June",
    "7": "July",
    "8": "August",
    "9": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}

spoilerREG = re.compile(r"(<span class='markdown_spoiler'><span>)(.+?)(</span></span>)", re.DOTALL)
newLineREG = re.compile(r"(\n)+(\s)*(\n)+")  # Regex that targets newlines and any spaces between them.
bracketREG = re.compile(r"\(.+?\)")

relevantStaffRoles = {"Story & Art", "Art", "Story", "Original Creator", "Director", "Music"}


def removeBrackets(string: str) -> str:
    return bracketREG.sub("", string).strip()


def get_media_embed(media: dict, trending: bool = False) -> Embed:
    """
    Returns an embed with the media information. Works for both anime and manga.
    """
    embedVar = Embed()
    embedVar.title = (
        media["title"]["romaji"]
        if media["title"]["romaji"]
        else (media["title"]["english"] if media["title"]["english"] else media["title"]["native"])
    )
    if media["description"]:
        description = newLineREG.sub("\n\n", markdownify(media["description"]))
        if len(description) > 4096:
            description = description[:4093] + "..."
    else:
        description = "_No description available._"
    embedVar.description = description
    embedVar.color = Colour(int(media["coverImage"]["color"][1:], 16)) if media["coverImage"]["color"] else Colour(69420).random()
    embedVar.url = media["siteUrl"]
    if media["coverImage"]["extraLarge"]:
        embedVar.set_thumbnail(url=media["coverImage"]["extraLarge"])
    if media["bannerImage"]:
        embedVar.set_image(url=media["bannerImage"])
    if media["format"]:
        embedVar.add_field(
            name="Format", value=(media["format"] if media["format"] in ("OVA", "TV") else media["format"].capitalize())
        )
    if media["episodes"] and (media["episodes"] > 1):
        embedVar.add_field(name="Episodes", value=media["episodes"])
    if media["duration"]:
        embedVar.add_field(
            name="Average runtime" if media["format"] not in {"MOVIE", "MUSIC"} else "Runtime", value=f"{media['duration']} minutes"
        )
    if media["chapters"]:
        embedVar.add_field(name="Chapters", value=str(media["chapters"]))
    if media["volumes"]:
        embedVar.add_field(name="Volumes", value=str(media["volumes"]))
    if media["status"]:
        embedVar.add_field(name="Status", value=media["status"].capitalize().replace("_", " "))
    if media["popularity"]:
        embedVar.add_field(name="Popularity", value="{:,}".format(media["popularity"]) + ("\nTrending" if trending else ""))
    if media["averageScore"]:
        embedVar.add_field(name="Score", value=f"{media['averageScore']/10}")
    if media["favourites"]:
        embedVar.add_field(name="Favourites", value="{:,}".format(media["favourites"]))
    if media["studios"]["edges"]:
        embedVar.add_field(
            name="Studio" if len(media["studios"]["edges"]) == 1 else "Studios",
            value="\n".join(f"[{node['node']['name']}]({node['node']['siteUrl']})" for node in media["studios"]["edges"])
            + " "
            + ("🇯🇵" if media["countryOfOrigin"] == "JP" else ("🇨🇳" if media["countryOfOrigin"] == "CN" else "🇰🇷")),
        )
    if media["season"] and media["seasonYear"]:
        embedVar.add_field(name="Season", value=media["season"].capitalize() + " " + str(media["seasonYear"]))
    if media["startDate"] and media["startDate"]["month"] and media["startDate"]["day"]:
        timestamp = str(
            int(
                datetime(year=media["startDate"]["year"], month=media["startDate"]["month"], day=media["startDate"]["day"]).timestamp()
            )
        )
        embedVar.add_field(
            name="Start date" if media["format"] != "MOVIE" else "Release date", value=f"<t:{timestamp}:D>\n_(<t:{timestamp}:R>)_"
        )
    if (
        media["endDate"]
        and media["endDate"]["month"]
        and media["endDate"]["day"]
        and media["format"] != "MOVIE"  # Don't want to show end date for movies
    ):
        timestamp = str(
            int(datetime(year=media["endDate"]["year"], month=media["endDate"]["month"], day=media["endDate"]["day"]).timestamp())
        )
        embedVar.add_field(name="End date", value=f"<t:{timestamp}:D>\n_(<t:{timestamp}:R>)_")
    if media["characters"]["edges"]:
        embedVar.add_field(
            name="Characters",
            value=" | ".join(
                [f"[{node['node']['name']['full']}]({node['node']['siteUrl']})" for node in media["characters"]["edges"]]
            ),
            inline=False,
        )
    if media["staff"]["edges"]:
        staff = []
        for edge in media["staff"]["edges"]:
            if removeBrackets(edge["role"]) in relevantStaffRoles:
                staff.append(f"[{edge['node']['name']['full']}]({edge['node']['siteUrl']}) _({edge['role']})_")
        embedVar.add_field(name="Staff", value=" | ".join(staff), inline=False)
    if media["genres"]:
        embedVar.add_field(name="Genres", value=" · ".join(media["genres"]), inline=False)
    if media["synonyms"]:
        embedVar.add_field(name="Synonyms", value=" | ".join(media["synonyms"][:5]), inline=False)
    if media["tags"]:
        tags = list()
        for tag in media["tags"]:
            if not tag["isMediaSpoiler"]:
                if tag["rank"] > 25:
                    tags.append(tag["name"])
        embedVar.add_field(name="Tags", value=" · ".join(tags[:15]), inline=False)
    embedVar.set_footer(
        text="Powered by Anilist API",
        icon_url="https://cdn.discordapp.com/attachments/811766823606943787/987361587352469544/anilistIcon.png",
    )
    return embedVar


def get_media_list_embed(mediaList: list[dict[str, str]], user: Union[Member, User]) -> Embed:
    embedVar = Embed()
    embedVar.title = "Search results"
    embedVar.description = f"<@{user.id}>, Please click on the respective button to get view it."
    embedVar.color = user.color if not str(user.color) == "#000000" else Colour(69420).random()

    embedVar.set_footer(
        text="Powered by Anilist API",
        icon_url="https://cdn.discordapp.com/attachments/811766823606943787/987361587352469544/anilistIcon.png",
    )
    x = 1
    for media in mediaList:
        value = ""
        if not media["title"]["romaji"] and media["title"]["english"]:
            value += media["title"]["english"] + "\n"
        if media["status"]:
            value += media["status"].capitalize().replace("_", " ") + " · "
        if media["season"] and media["seasonYear"]:
            value += media["season"].capitalize() + " " + str(media["seasonYear"]) + " · "
        if media["episodes"] and (media["format"] not in {"OVA", "MOVIE", "MUSIC"}):
            value += str(media["episodes"]) + " episodes · "
        if media["format"]:
            value += media["format"].capitalize() if media["format"] == "MOVIE" else media["format"]
        if media["chapters"]:
            value += " · " + str(media["chapters"]) + " chapters"
        if media["volumes"]:
            value += " · " + str(media["volumes"]) + " volumes"
        embedVar.add_field(
            name=f"{x}) {media['title']['romaji'] if media['title']['romaji'] else (media['title']['english'] if media['title']['english'] else media['title']['native'])}",
            value=value,
            inline=False,
        )
        x += 1
    return embedVar


def get_character_embed(character: dict, user: Union[Member, User]) -> Embed:
    """
    Returns an embed for a character.
    """
    embedVar = Embed()
    embedVar.title = character["name"]["full"]
    embedVar.color = user.color if not str(user.color) == "#000000" else Colour(69420).random()
    embedVar.url = character["siteUrl"]
    if character["image"]["large"]:
        embedVar.set_thumbnail(url=character["image"]["large"])
    if character["description"] is not None:
        description = newLineREG.sub("\n\n", markdownify(spoilerREG.sub("", character["description"])))
        if len(description) > 4096:
            description = description[:4093] + "..."
    else:
        description = "_No description available._"
    embedVar.description = description
    if character["name"]["alternative"]:
        embedVar.add_field(
            name="Alternative names", value=" | ".join([character["name"]["native"]] + character["name"]["alternative"]), inline=False
        )
    if character["gender"]:
        embedVar.add_field(name="Gender", value=character["gender"])
    if character["dateOfBirth"]["month"] and character["dateOfBirth"]["day"]:
        embedVar.add_field(
            name="Birthday", value=f"{character['dateOfBirth']['day']} {months[str(character['dateOfBirth']['month'])]}"
        )
    if character["animeconnection"]["edges"]:
        for edge in character["animeconnection"]["edges"]:
            for va in edge["voiceActors"]:
                if va["languageV2"] == "Japanese":
                    japaneseVA = f"[{va['name']['full']}]({va['siteUrl']})"
                    embedVar.add_field(name="Voice actor", value=japaneseVA)
                    break
            else:
                continue
            break
        value = ""
        mainRoles = []
        supportingRoles = []
        backgroundRoles = []
        for edge in character["animeconnection"]["edges"]:
            if edge["characterRole"] == "MAIN":
                mainRoles.append(
                    f"- [{edge['node']['title']['romaji'] if edge['node']['title']['romaji'] else edge['node']['title']['english']}]({edge['node']['siteUrl']})\n"
                )
            elif edge["characterRole"] == "SUPPORTING":
                supportingRoles.append(
                    f"- [{edge['node']['title']['romaji'] if edge['node']['title']['romaji'] else edge['node']['title']['english']}]({edge['node']['siteUrl']})\n"
                )
            elif edge["characterRole"] == "BACKGROUND":
                backgroundRoles.append(
                    f"- [{edge['node']['title']['romaji'] if edge['node']['title']['romaji'] else edge['node']['title']['english']}]({edge['node']['siteUrl']})\n"
                )
        tempVar = "Main roles\n" + "".join(mainRoles)
        if mainRoles and len(value) + len(tempVar) <= 1024:
            value += tempVar
        tempVar = "Supporting roles\n" + "".join(supportingRoles)
        if supportingRoles and len(value) + len(tempVar) <= 1024:
            value += tempVar
        tempVar = "Background roles\n" + "".join(backgroundRoles)
        if backgroundRoles and len(value) + len(tempVar) <= 1024:
            value += tempVar
        if value:
            embedVar.add_field(name="Anime", value=value, inline=False)
    if character["mangaconnection"]["edges"]:
        value = ""
        mainRoles = []
        supportingRoles = []
        backgroundRoles = []
        for edge in character["mangaconnection"]["edges"]:
            if edge["characterRole"] == "MAIN":
                mainRoles.append(
                    f"- [{edge['node']['title']['romaji'] if edge['node']['title']['romaji'] else edge['node']['title']['english']}]({edge['node']['siteUrl']})\n"
                )
            elif edge["characterRole"] == "SUPPORTING":
                supportingRoles.append(
                    f"- [{edge['node']['title']['romaji'] if edge['node']['title']['romaji'] else edge['node']['title']['english']}]({edge['node']['siteUrl']})\n"
                )
            else:
                backgroundRoles.append(
                    f"- [{edge['node']['title']['romaji'] if edge['node']['title']['romaji'] else edge['node']['title']['english']}]({edge['node']['siteUrl']})\n"
                )
        tempVar = "Main roles\n" + "".join(mainRoles)
        if mainRoles and len(value) + len(tempVar) <= 1024:
            value += tempVar
        tempVar = "Supporting roles\n" + "".join(supportingRoles)
        if supportingRoles and len(value) + len(tempVar) <= 1024:
            value += tempVar
        tempVar = "Background roles\n" + "".join(backgroundRoles)
        if backgroundRoles and len(value) + len(tempVar) <= 1024:
            value += tempVar
        if value:
            embedVar.add_field(name="Manga", value=value, inline=False)

    while len(embedVar) > 6000:
        embedVar._fields = embedVar._fields[:1]

    return embedVar
