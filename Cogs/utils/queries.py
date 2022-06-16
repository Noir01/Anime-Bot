createGeneralSQLQuery : str = """
CREATE TABLE IF NOT EXISTS general (
  discord bigint PRIMARY KEY, anilist int UNIQUE, 
  anime JSON, manga JSON
)
"""

createDiscordAnilistSQLQuery: str = """
CREATE TABLE IF NOT EXISTS discord_anilist (
  discord bigint PRIMARY KEY, anilist int UNIQUE
)
"""
