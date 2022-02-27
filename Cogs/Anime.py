from discord import (
    ActionRow,
    ApplicationContext,
    Embed,
    Color,
    Interaction,
)
from discord.commands import slash_command, Option
from discord.ext import commands
from discord.ui import View, Button
from datetime import date, datetime
from requests import post
from markdownify import markdownify


class NumberedButton(Button):
    def __init__(self, index: int):
        super().__init__(label=str(index))
        self.index = index

    async def callback(self, interaction: Interaction):
        self.view.value = self.index
        self.view.stop()


class Anime(commands.Cog):
    def __init__(self, Client) -> None:
        self.Client = Client

    @slash_command(description="Searches for an anime with provided name using the Anilist API.")
    async def anime(
        self,
        ctx: ApplicationContext,
        name: Option(str, "The name of the anime to search for."),
        limit: Option(
            int,
            "Maximum number of entries to view at a time. Defaults to 10.",
            min_value=1,
            max_value=25,
        ) = 10,
    ):
        await ctx.defer()
        if ctx.channel.is_nsfw():
            query = """
    query ($id: Int, $page: Int, $perPage: Int, $search: String) {
      Page (page: $page, perPage: $perPage) {
          pageInfo {
              total
              currentPage
              lastPage
              hasNextPage
              perPage
          }
          media (id: $id, search: $search, type: ANIME, sort: POPULARITY_DESC) {
              id
              title {
                  romaji
                  english
                    native
              }
                  isAdult
                  duration
                  idMal
              format
              episodes
              duration
                  siteUrl
                  trending
                    countryOfOrigin
                  season
                  seasonYear
              status
                  studios (isMain:true) {
                    edges {
                      node {
                    name
                    isAnimationStudio
                    siteUrl
                  }
                    }
                  }
              staff (sort: RELEVANCE) {
                edges {
                  node {
                    name {
                      first
                      middle
                      last
                      full
                      native
                      userPreferred
                    }
                    siteUrl
                  }
                }
              }
              description(asHtml:false)
                  startDate {
                year
                month
                day
              }
                  endDate {
                year
                month
                day
              }
              bannerImage
              popularity
                  externalLinks {
                    url
                site
                  }
              favourites
              genres
              tags {
                name
                isMediaSpoiler
              }
              synonyms
              characters(role: MAIN, page: 1, perPage: 10, sort: ROLE_DESC) {
                edges {
                  node {
                    name {
                      full
                    }
                    siteUrl
                  }
                }
              }
              coverImage {
                extraLarge
                color
              }

          }
      }
  }"""
        else:
            query = """
    query ($id: Int, $page: Int, $perPage: Int, $search: String) {
      Page (page: $page, perPage: $perPage) {
          pageInfo {
              total
              currentPage
              lastPage
              hasNextPage
              perPage
          }
          media (id: $id, search: $search, type: ANIME, sort: POPULARITY_DESC, isAdult:false) {
              id
              title {
                  romaji
                  english
                    native
              }
                  isAdult
                  duration
                  idMal
              format
                  siteUrl
              episodes
              duration
                  trending
                    countryOfOrigin
                  season
                  seasonYear
              status
                  studios (isMain:true) {
                    edges {
                      node {
                    name
                    isAnimationStudio
                    siteUrl
                  }
                    }
                  }
              staff (sort: RELEVANCE) {
                edges {
                  node {
                    name {
                      first
                      middle
                      last
                      full
                      native
                      userPreferred
                    }
                    siteUrl
                  }
                }
              }
              description(asHtml:false)
                  startDate {
                year
                month
                day
              }
                  endDate {
                year
                month
                day
              }
              bannerImage
              popularity
                  externalLinks {
                    url
                site
                  }
              favourites
              genres
              tags {
                name
                isMediaSpoiler
              }
              synonyms
              characters(role: MAIN, page: 1, perPage: 10, sort: ROLE_DESC) {
                edges {
                  node {
                    name {
                      full
                    }
                    siteUrl
                  }
                }
              }
              coverImage {
                extraLarge
                color
              }

          }
      }
  }"""
        variables = {"search": name, "perPage": limit, "page": 1}
        response = post(
            "https://graphql.anilist.co", json={"query": query, "variables": variables}
        ).json()
        embedVar = Embed(
            title="Search results",
            description=f"<@{ctx.author.id}>, Please click on the respective button to get view it.",
            color=ctx.author.color
            if not str(ctx.author.color) == "#000000"
            else Color(69420).random(),
        )
        embedVar.set_footer(
            text="Powered by Anilist API",
            icon_url="https://anilist.co/img/icons/icon.svg",
        )
        x = 1
        if not response["data"]["Page"]["media"]:
            await ctx.respond("No anime found for that search.", ephemaral=True)
            return
        for media in response["data"]["Page"]["media"]:
            value = ""
            if not media["title"]["romaji"]:
                value += media["title"]["english"] + "\n"
            if media["status"]:
                value += media["status"].capitalize().replace("_", " ") + " · "
            if media["season"] and media["seasonYear"]:
                value += media["season"].capitalize() + " " + str(media["seasonYear"]) + " · "
            if media["episodes"] and (media["format"] != "OVA" or media["format"] != "MOVIE"):
                value += str(media["episodes"]) + " episodes · "
            if media["format"]:
                value += (
                    media["format"].capitalize() if media["format"] == "MOVIE" else media["format"]
                )
            embedVar.add_field(
                name=f"{x}) {media['title']['romaji'] if media['title']['romaji'] else (media['title']['english'] if media['title']['english'] else media['title']['native'])}",
                value=value,
                inline=False,
            )
            x += 1
        view = View()
        for i in range(0, len(response["data"]["Page"]["media"])):
            view.add_item(NumberedButton(i + 1))
        question = await ctx.respond(embed=embedVar, view=view)
        await view.wait()
        if view.value:
            media = response["data"]["Page"]["media"][view.value - 1]
        else:
            embedVar.color = Color(int("B20000", 16))
            await question.edit(embed=embedVar, view=None)
            return
        embedVar = Embed(
            title=media["title"]["romaji"]
            if media["title"]["romaji"]
            else (
                media["title"]["english"] if media["title"]["english"] else media["title"]["native"]
            ),
            description=markdownify(media["description"]),
            color=Color(int(media["coverImage"]["color"][1:], 16))
            if media["coverImage"]["color"]
            else Color(69420).random(),
            url=media["siteUrl"],
        )
        if media["coverImage"]["extraLarge"]:
            embedVar.set_thumbnail(url=media["coverImage"]["extraLarge"])
        if media["bannerImage"]:
            embedVar.set_image(url=media["bannerImage"])
        if media["format"]:
            embedVar.add_field(
                name="Format",
                value=(
                    media["format"].capitalize() if media["format"] == "MOVIE" else media["format"]
                ),
            )
        if media["status"]:
            embedVar.add_field(
                name="Status",
                value=media["status"].capitalize().replace("_", " "),
            )
        if media["season"] and media["seasonYear"]:
            embedVar.add_field(
                name="Season", value=media["season"].capitalize() + " " + str(media["seasonYear"])
            )
        if media["episodes"]:
            embedVar.add_field(
                name="Episodes",
                value=f"{media['episodes']} {('_(Average runtime ' + str(media['duration']) + ' minutes)_') if media['episodes'] else ''}",
            )
        if media["popularity"]:
            embedVar.add_field(name="Popularity", value="{:,}".format(media["popularity"]))
        if media["favourites"]:
            embedVar.add_field(name="Favourites", value="{:,}".format(media["favourites"]))
        if media["studios"]:
            embedVar.add_field(
                name="Studio" if len(media["studios"]["edges"]) == 1 else "Studios",
                value=", ".join(
                    f"[{node['node']['name']}]({node['node']['siteUrl']})"
                    for node in media["studios"]["edges"]
                )
                + " "
                + "🇯🇵"
                if media["countryOfOrigin"] == "JP"
                else ("🇨🇳" if media["countryOfOrigin"] == "CN" else "🇰🇷"),
            )
        if media["startDate"] and media["startDate"]["month"] and media["startDate"]["day"]:
            timestamp = str(
                int(
                    datetime(
                        year=media["startDate"]["year"],
                        month=media["startDate"]["month"],
                        day=media["startDate"]["day"],
                    ).timestamp()
                )
            )
            embedVar.add_field(name="Start date", value=f"<t:{timestamp}:D> _(<t:{timestamp}:R>)_")
        if media["endDate"] and media["endDate"]["month"] and media["endDate"]["day"]:
            timestamp = str(
                int(
                    datetime(
                        year=media["endDate"]["year"],
                        month=media["endDate"]["month"],
                        day=media["endDate"]["day"],
                    ).timestamp()
                )
            )
            embedVar.add_field(name="End date", value=f"<t:{timestamp}:D> _(<t:{timestamp}:R>)_")
        await question.edit(embed=embedVar, content=None, view=None)


def setup(Client):
    Client.add_cog(Anime(Client))
