from typing import Literal

mediaGraphQLQuery: str = """
query ($page: Int, $perPage: Int, $search: String, $type: MediaType, $isAdult: Boolean, $tags: [String]) {
  Page(page: $page, perPage: $perPage) {
    media(search: $search, type: $type, sort: POPULARITY_DESC, isAdult: $isAdult, tag_in: $tags) {
      id
      title {
        romaji
        english
      }
      siteUrl
      isAdult
      type
      duration
      chapters
      volumes
      idMal
      studios (isMain: true) {
        edges {
          node {
            name
            siteUrl
          }
        }
      }
      format
      episodes
      nextAiringEpisode {
        episode
        airingAt
      }
      duration
      siteUrl
      trending
      countryOfOrigin
      season
      seasonYear
      status
      staff(sort: RELEVANCE) {
        edges {
          node {
            name {
              full
            }
            siteUrl
          }
          role
        }
      }
      description(asHtml: false)
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
      averageScore
      popularity
      externalLinks {
        url
        site
      }
      favourites
      averageScore
      genres
      tags {
        name
        isMediaSpoiler
        rank
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
}
"""

trendingGraphQLQuery: str = """
query ($type: MediaType) {
  Trending: Page(perPage: 10) {
    media(type: $type, sort: TRENDING_DESC) {
      id
      type
      title {
        romaji
      }

    }
  }
}
"""

characterGraphQLQuery: str = """
query ($id: Int, $page: Int, $perPage: Int, $search: String) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      total
      currentPage
      lastPage
      hasNextPage
      perPage
    }
    characters(id: $id, search: $search, sort: FAVOURITES_DESC) {
      id
      name {
        full
        native
        alternative
      }
      siteUrl
      favourites
      image {
        large
      }
      description (asHtml: true)
      dateOfBirth {
        month
        day
      }
      gender
      animeconnection: media (sort:POPULARITY_DESC, type: ANIME) {
        edges {
          characterRole
          voiceActors (sort:FAVOURITES_DESC) {
            name {
              full
            }
            siteUrl
            languageV2
          }
          node {
            title {
              romaji
            }
            type
            siteUrl
          }
        }
      }
      mangaconnection:media (sort:POPULARITY_DESC, type: MANGA) {
        edges {
          characterRole
          node {
            title {
              romaji
            }
            type
            siteUrl
          }
        }
      }
    }
  }
}
"""

allTablesSQLQuery: str = """
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'
"""

userSelectSQLQuery: str = """
SELECT %s from discord_anilist WHERE %s = %s
"""

updateGraphQLQuery: str = """
query ($id: Int, $page: Int, $perPage: Int, $type: MediaType) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      total
      currentPage
      lastPage
      hasNextPage
      perPage
    }
    mediaList(userId: $id, type: $type, sort: UPDATED_TIME_DESC) {
      mediaId
      status
      progress
      score
      media {
        episodes
        chapters
      }
    }
  }
}
"""

createGeneralSQLQuery: str = """
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


def createTableSQLQueryGenerator(type_: Literal["Anime", "Manga"], name: str) -> str:
    return f"""
CREATE TABLE IF NOT EXISTS {name} (
  Discord bigint PRIMARY KEY, Anilist int UNIQUE, 
  Status text, Progress int, Score text, 
  {'Episodes' if type_ == "Anime" else 'Chapters'} int
)
"""


def updateTableSQLQueryGenerator(type_: Literal["Anime", "Manga"], name: str) -> str:
    return f"""
INSERT INTO {name} (
  Discord, Anilist, Status, Progress, 
  Score, {'Episodes' if type_ == "Anime" else 'Chapters'}
) 
VALUES 
  (%s, %s, %s, %s, %s, %s) ON CONFLICT (Discord) DO 
UPDATE 
SET 
  (Status, Progress, Score, {'Episodes' if type_ == "Anime" else 'Chapters'}) = (
    EXCLUDED.Status, EXCLUDED.Progress, 
    EXCLUDED.Score, EXCLUDED.{'Episodes' if type_ == "Anime" else 'Chapters'}
  )
"""
