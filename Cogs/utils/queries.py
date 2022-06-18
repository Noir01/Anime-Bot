mediaGraphQLQuery: str = """
query ($page: Int, $perPage: Int, $search: String, $type: MediaType, $isAdult: Boolean) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      total
      currentPage
      lastPage
      hasNextPage
      perPage
    }
    media(search: $search, type: $type, sort: POPULARITY_DESC, isAdult: $isAdult) {
      id
      title {
        romaji
        english
        native
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
