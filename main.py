import discord
from discord.commands import Option, slash_command, permissions
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
    "CREATE DATABASE",
    "CREATE INDEX",
    "CREATE OR",
    "CREATE TABLE"
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
    "DROP CONSTRAINT"
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
    "RIGHT JOIN"
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
    "WHERE"
]
postgressURL = environ['DATABASE_URL']
Client = discord.Bot(debug_guilds=[697493731611508737])

def get_sql_commands(ctx: discord.AutocompleteContext):
    return [
        command for command in sqlCommands if ctx.value.lower() in command.lower()
    ]

@Client.event
async def on_ready():
    print("Online now")
    global conn
    conn = psycopg.connect(postgressURL)
    conn.autocommit = True

@Client.slash_command(description="Admin-level command to manually edit database.", default_permission=False)
@permissions.is_user(629243339379834880)
async def execute(ctx: discord.ApplicationContext, query: Option(str, "SQL Query to run", autocomplete=discord.utils.basic_autocomplete(get_sql_commands))):
    global conn
    with conn.cursor() as curr:
        try:
            curr.execute(query)
            await ctx.respond(curr.fetchall())
        except psycopg.errors.ActiveSqlTransaction:
            await ctx.respond("psycopg.errors.ActiveSqlTransaction: CREATE DATABASE cannot run inside a transaction block")
        except BaseException:
            await ctx.respond(format_exc())

class LinkConfirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
        self.timeout = 300.0

    @discord.ui.button(emoji="<:AYes:765142287902441492>", style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(emoji="<:ANo:765142286681112576>", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()

@Client.slash_command(description="Used to link an Anilist profile to your Discord profile.")
async def link(ctx: discord.ApplicationContext, username: Option(str, "Username of the anilist account you want to link.")):
    await ctx.defer()
    query = '''
query ($name: String, $page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    users(name: $name) {
      id
      name
      siteUrl
    }
  }
}
    '''
    variables = {'name': username, 'page': 1, 'perPage': 1}
    url = 'https://graphql.anilist.co'
    response = post(url,json={'query': query,'variables': variables}).json()
    users = response['data']['Page']['users']
    if not users:
        await ctx.respond("No matching [Anilist](https://anilist.co) accounts found.")
        return
    user = users[0]
    global conn
    with conn.cursor() as curr:
        curr.execute("SELECT * from discord_anilist")
        for pair in curr.fetchall():
            if pair[1] == user['id']:
                await ctx.respond(f"[{user['name']}](https://anilist.co/user/{user['name']}) is already registered under another discord account.")
                return
        view = LinkConfirm()
        question = await ctx.respond(f"Is [{user['name']}]({user['siteUrl']}) the account you want to link?", view=view)
        await view.wait()
        if view.value is None:
            await question.edit("Timed out.")
        elif view.value:
            curr.execute(f"DELETE FROM discord_anilist WHERE discord={ctx.author.id}")
            curr.execute(f"INSERT INTO discord_anilist VALUES ({ctx.author.id}, {user['id']})")
            await question.edit(f"Successfully registered [{user['name']}](https://anilist.co/user/{user['name']}).")
        elif not view.value:
            await question.edit("Please try again with your username.")

Client.run(environ['TOKEN'])