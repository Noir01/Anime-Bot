import discord
from discord.commands import Option, slash_command
import psycopg
from traceback import format_exc
from os import environ

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

@Client.slash_command()
async def execute(ctx: discord.ApplicationContext, query: Option(str, "SQL Query to run", autocomplete=get_sql_commands)):
    conn = psycopg.connect("postgresql://postgres:8Da2vF3ky6X2G7yBkhNZ@containers-us-west-1.railway.app:8039/railway")
    with conn.cursor() as curr:
        try:
            curr.execute(query)
            await ctx.send(curr.fetchall())
        except psycopg.errors.ActiveSqlTransaction:
            await ctx.respond("psycopg.errors.ActiveSqlTransaction: CREATE DATABASE cannot run inside a transaction block")
        except BaseException:
            await ctx.respond(format_exc())

Client.run(environ['TOKEN'])