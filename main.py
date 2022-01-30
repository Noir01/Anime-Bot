#Formatted with Black, the uncompromising Python code formatter. https://github.com/psf/black
from asyncio import sleep
import discord
from discord.commands import Option, permissions
import psycopg
from traceback import format_exc
from os import environ
from requests import post

sqlCommands = [
    "ADD",
    "ADD CONSTRAINT",
    "ALTER",
    "ALTER COLUMN",
    "ALTER TABLE",
    "ALL",
    "AND",
    "ANY",
    "AS",
    "ASC",
    "BACKUP DATABASE",
    "BETWEEN",
    "CASE",
    "CHECK",
    "COLUMN",
    "CONSTRAINT",
    "CREATE INDEX",
    "CREATE OR",
    "CREATE TABLE",
    "CREATE PROCEDURE",
    "CREATE UNIQUE",
    "CREATE VIEW",
    "DATABASE",
    "DEFAULT",
    "DELETE",
    "DESC",
    "DISTINCT",
    "DROP",
    "DROP COLUMN",
    "DROP CONSTRAINT",
    "DROP DATABASE",
    "DROP DEFAULT",
    "DROP INDEX",
    "DROP TABLE",
    "DROP VIEW",
    "EXEC",
    "EXISTS",
    "FOREIGN KEY",
    "FROM",
    "FULL OUTER",
    "GROUP BY",
    "HAVING",
    "IN",
    "INDEX",
    "INNER JOIN",
    "INSERT INTO",
    "INSERT INTO SELECT",
    "IS NULL",
    "IS NOT",
    "JOIN",
    "LEFT JOIN",
    "LIKE",
    "LIMIT",
    "NOT",
    "NOT NULL",
    "OR",
    "ORDER BY",
    "OUTER JOIN",
    "PRIMARY KEY",
    "PROCEDURE",
    "RIGHT JOIN",
    "ROWNUM",
    "SELECT",
    "SELECT DISTINCT",
    "SELECT INTO",
    "SELECT TOP",
    "SET",
    "TABLE",
    "TOP",
    "TRUNCATE TABLE",
    "UNION",
    "UNION ALL",
    "UNIQUE",
    "UPDATE",
    "VALUES",
    "VIEW",
    "WHERE",
]
postgressURL = environ['DATABASE_URL']
Client = discord.Bot(debug_guilds=[890890610339373106])


def get_sql_commands(ctx: discord.AutocompleteContext):
    return [command for command in sqlCommands if ctx.value.lower() in command.lower()]


@Client.event
async def on_ready():
    print("Online now")
    global conn
    conn = psycopg.connect(postgressURL)


@Client.slash_command(
    description="Admin-level command to manually edit database.",
    default_permission=False,
)
@permissions.is_user(629243339379834880)
async def execute(
    ctx: discord.ApplicationContext,
    query: Option(
        str,
        "SQL Query to run",
        autocomplete=discord.utils.basic_autocomplete(get_sql_commands),
    ),
):
    global conn
    with conn.cursor() as curr:
        try:
            curr.execute(query)
            await ctx.respond(curr.fetchall())
        except psycopg.errors.ActiveSqlTransaction:
            await ctx.respond(
                "psycopg.errors.ActiveSqlTransaction: CREATE DATABASE cannot run inside a transaction block"
            )
        except BaseException:
            await ctx.respond(format_exc())


class LinkConfirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
        self.timeout = 300.0

    @discord.ui.button(
        emoji="<:AYes:765142287902441492>", style=discord.ButtonStyle.green
    )
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.value = True
        self.stop()

    @discord.ui.button(
        emoji="<:ANo:765142286681112576>", style=discord.ButtonStyle.danger
    )
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()


class LinkConfirmDisabled(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.timeout = 10

    @discord.ui.button(
        emoji="<:AYes:765142287902441492>",
        style=discord.ButtonStyle.green,
        disabled=True,
    )
    async def confirm(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        pass

    @discord.ui.button(
        emoji="<:ANo:765142286681112576>",
        style=discord.ButtonStyle.danger,
        disabled=True,
    )
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        pass


@Client.slash_command(
    description="Used to link an Anilist profile to your Discord profile."
)
async def link(
    ctx: discord.ApplicationContext,
    username: Option(str, "Username of the anilist account you want to link."),
):
    await ctx.defer()
    query = """
query ($name: String, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    users(name: $name) {
      id
      name
      siteUrl
    }
  }
}
    """
    variables = {"name": username, "page": 1, "perPage": 1}
    url = "https://graphql.anilist.co"
    response = post(url, json={"query": query, "variables": variables}).json()
    users = response["data"]["Page"]["users"]
    if not users:
        await ctx.respond("No matching [Anilist](https://anilist.co) accounts found.")
        return
    user = users[0]
    global conn
    with conn.cursor() as curr:
        curr.execute("SELECT * from discord_anilist")
        for pair in curr.fetchall():
            if pair[1] == user["id"]:
                await ctx.respond(
                    f"[{user['name']}](https://anilist.co/user/{user['name']}) is already registered under another discord account."
                )
                return
        view = LinkConfirm()
        question = await ctx.respond(
            f"Is [{user['name']}]({user['siteUrl']}) the account you want to link?",
            view=view,
        )
        await view.wait()
        disabledView = LinkConfirmDisabled()
        if view.value is None:
            await question.edit("Timed out.", view=disabledView)
        elif view.value:
            curr.execute(f"DELETE FROM discord_anilist WHERE discord={ctx.author.id}")
            curr.execute(
                f"INSERT INTO discord_anilist VALUES ({ctx.author.id}, {user['id']})"
            )
            await question.edit(
                f"Successfully registered [{user['name']}](https://anilist.co/user/{user['name']}).",
                view=disabledView,
            )
        elif not view.value:
            await question.edit(
                "Please try again with your username.", view=disabledView
            )
    conn.commit()


@Client.slash_command(description="Used to import your lists from Anilist.")
async def update(
    ctx: discord.ApplicationContext,
    list: Option(str, "The list you want to update.", choices=["Anime", "Manga"]),
    member: Option(
        discord.Member, "The user you want to update. Defaults to you."
    ) = None,
    force: Option(bool, "Pass True to import your entire list.") = False,
):
    await ctx.defer()
    if member is None:
        member = ctx.author
    with conn.cursor() as curr:
        curr.execute("SELECT * FROM discord_anilist")
        userID = False
        for pair in curr.fetchall():
            if pair[0] == member.id:
                userID = pair[1]
        if not userID:
            await ctx.respond(
                "No matching Anilist user found. Link your Anilist account using `/link`."
            )
            return
        if list == "Anime":
            query = """
            query ($id: Int, $page: Int, $perPage: Int) {
      Page(page: $page, perPage: $perPage) {
        pageInfo {
          total
          currentPage
          lastPage
          hasNextPage
          perPage
        }
        mediaList (userId: $id, type: ANIME, sort: UPDATED_TIME_DESC) {
          mediaId
          status
          progress
          score
          media {
            episodes
          }
        }
      }
    }
            """
            mlist = []
            nextPage = True
            page = 1
            while nextPage:
                variables = {"id": userID, "page": page}
                page += 1
                response = post(
                    "https://graphql.anilist.co",
                    json={"query": query, "variables": variables},
                ).json()
                if force:
                    nextPage = response["data"]["Page"]["pageInfo"]["hasNextPage"]
                else:
                    nextPage = False
                mlist += response["data"]["Page"]["mediaList"]
            mlist = [x for n, x in enumerate(mlist) if x not in mlist[:n]]
            for media in mlist:
                tableName = "a" + str(media["mediaId"])
                curr.execute(
                    f"CREATE TABLE IF NOT EXISTS {tableName} (Discord bigint PRIMARY KEY, Anilist int UNIQUE, Status text, Progress int, Score text, Episodes int)"
                )
                curr.execute(f"SELECT * FROM {tableName} WHERE Discord={ctx.author.id}")
                if not curr.fetchall():
                    curr.execute(
                        f"INSERT INTO {tableName} (Discord, Anilist, Status, Progress, Score, Episodes) VALUES ({ctx.author.id}, {userID}, '{media['status']}', {media['progress']}, '{media['score']}', {0 if not media['media']['episodes'] else media['media']['episodes']})"
                    )
                else:
                    curr.execute(
                        f"UPDATE {tableName} SET Status='{media['status']}', Progress={media['progress']}, Score='{media['score']}', Episodes={0 if not media['media']['episodes'] else media['media']['episodes']} WHERE Discord={ctx.author.id}"
                    )
                await sleep(0.5)
        if list == "Manga":
            query = """
            query ($id: Int, $page: Int, $perPage: Int) {
      Page(page: $page, perPage: $perPage) {
        pageInfo {
          total
          currentPage
          lastPage
          hasNextPage
          perPage
        }
        mediaList (userId: $id, type: MANGA, sort: UPDATED_TIME_DESC) {
          mediaId
          status
          progress
          score
          media {
            chapters
          }
        }
      }
    }
            """
            mlist = []
            nextPage = True
            page = 1
            while nextPage:
                variables = {"id": userID, "page": page}
                page += 1
                response = post(
                    "https://graphql.anilist.co",
                    json={"query": query, "variables": variables},
                ).json()
                if force:
                    nextPage = response["data"]["Page"]["pageInfo"]["hasNextPage"]
                else:
                    nextPage = False
                mlist += response["data"]["Page"]["mediaList"]
            mlist = [x for n, x in enumerate(mlist) if x not in mlist[:n]]
            for media in mlist:
                tableName = "m" + str(media["mediaId"])
                curr.execute(
                    f"CREATE TABLE IF NOT EXISTS {tableName} (Discord bigint PRIMARY KEY, Anilist int UNIQUE, Status text, Progress int, Score text, Chapters int)"
                )
                curr.execute(f"SELECT * FROM {tableName} WHERE Discord={ctx.author.id}")
                if not curr.fetchall():
                    curr.execute(
                        f"INSERT INTO {tableName} (Discord, Anilist, Status, Progress, Score, Chapters) VALUES ({ctx.author.id}, {userID}, '{media['status']}', {media['progress']}, '{media['score']}', {0 if not media['media']['chapters'] else media['media']['chapters']})"
                    )
                else:
                    curr.execute(
                        f"UPDATE {tableName} SET Status='{media['status']}', Progress={media['progress']}, Score='{media['score']}', Chapters={0 if not media['media']['chapters'] else media['media']['chapters']} WHERE Discord={ctx.author.id}"
                    )
                await sleep(0.5)
    conn.commit()
    await ctx.respond("Done")


Client.run(environ("TOKEN"))