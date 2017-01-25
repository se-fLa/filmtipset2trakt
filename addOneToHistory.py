#!/usr/bin/python
#
# Author: fLa
#
from urllib2 import Request, urlopen, URLError, HTTPError
import json
import sys

# Fill in your API keys from https://trakt.tv/oauth/applications below (the redirect URI cam be anything)
clientID           = ""
# Fill in your access token (get it from getAuthorizationBearerAccessTokenCode.py)
authorizationToken = ""

#==============================================================================================

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

headers = { 
  'Content-Type': 'application/json',
  'Authorization': 'Bearer %s' % authorizationToken,
  'trakt-api-version': '2',
  'trakt-api-key': '%s' % clientID
} 

def printUsage():
  print("\nUsage: " + sys.argv[0] + " <type> <IMDb_ID[:season]> <datetime>")
  print("  type       Type of item to add. Accepts 'movies', 'shows' or 'episodes'.")
  print("             If only a show is passed, all episodes for the show will be added. If a season is specified, only episodes in that season will be added.")
  print("  IMDb_ID    The movie IMDb ID.")
  print("  datetime   The watched datetime in UTC following ISO8601 format.")
  print("\nExamples:")
  print("\tAdd one movie")
  print("\t\t" + sys.argv[0] + " movies tt0120737 2017-01-01T20:30Z")
  print("\tAdd one single episode of a show")
  print("\t\t" + sys.argv[0] + " episodes tt2057241 '2017-01-02 19:00:12'")
  print("\tAdd one season of a show")
  print("\t\t" + sys.argv[0] + " shows tt0369179:3 '2017-01-03 18:00'")
  print("\tAdd all episodes of all seasons of a show")    
  print("\t\t" + sys.argv[0] + " shows tt1628033 '2017-01-04 13:00Z'")
  print("")


if len(sys.argv) < 4 or len(sys.argv) > 5:
  print(color.RED + "Invalid number of arguments" + color.END)
  printUsage()
  exit(1)


#------------------------------------------------------------------------------------------

def addMovie(itemType, imdb_tt_id, season, watchedUtcDatetime):
  if not season:
    values = """
    {
      "%(type)s": [
            {
               "watched_at": "%(date)s",
               "ids": {
                  "imdb": "%(imdb)s"
               }
            }
       ]
    }
    """ % {
     'type': itemType,
     'imdb': imdb_tt_id,
     'date': watchedUtcDatetime }
  else:
      values = """
      {
        "%(type)s": [
              {
                 "ids": {
                    "imdb": "%(imdb)s"
                 },
                 "seasons": [
                   {
                      "watched_at": "%(date)s",
                      "number": %(season)s
                   }
                 ]
             }
        ]
     }  
     """ % {
      'type': itemType,
      'imdb': imdb_tt_id,
      'date': watchedUtcDatetime,
      'season': season }

  request_syncHistory = Request('https://api.trakt.tv/sync/history', data=values, headers=headers) 
  try:
    response_body = urlopen(request_syncHistory).read()  
  except HTTPError as e:
     if e.code == 401:
       print(color.RED + "Authorization failed - your credentials are invalid!\nMake sure the autorization token is still valid and check your client ID is correct." + color.END)
       exit(1)
     elif e.code == 400:
       print(color.RED + "Bad Request - request couldn't be parsed!" + color.END)
       exit(1)
     else:
       print(color.RED + "Unknown Error!!" + color.END)
       exit(1)
  except Exception:
    print(color.RED + "ERROR\nUnexpected exception" + color.END)      
    exit(1) 
  try:
    parsed_json = json.loads(response_body)
  except ValueError, e:   
    print(color.RED + "Invalid data received:" + color.END)  
    print(response_body)   
    exit(1)
  return parsed_json      



#====================== MAIN =============================

itemType = sys.argv[1]
movieIMDbId = sys.argv[2]
watchedDatetime = sys.argv[3]

#Verify user input
season = ""
if not itemType in ["movies", "shows", "episodes"]:
  print(color.RED + "Invalid type specified" + color.END)
  exit(1)      
if itemType == "shows" and ':' in movieIMDbId:
  movieIMDbId, season = movieIMDbId.split(':')  
if len(movieIMDbId) != 9 or movieIMDbId[:2] != "tt":
  print(color.RED + "Invalid IMDb id" + color.END)
  exit(1)
#Trakt.tv API accept ISO8601 date format variations, skipp validation
#if len(watchedDatetime) != 17:
#  print(color.RED + "Invalid watched timestamp" + color.END)
#  exit(1)

jsonResponse = addMovie(itemType, movieIMDbId, season, watchedDatetime)
#{u'not_found': {u'movies': [{u'watched_at': u'2016-12-24T15:00+01:00', u'ids': {u'imdb': u'xtt3095734'}}], u'seasons': [], u'people': [], u'episodes': [], u'shows': []}, u'added': {u'movies': 0, u'episodes': 0}}

addedMovies = jsonResponse["added"]["movies"]
if addedMovies != 0:
  print(color.GREEN + "Added %s movies" % addedMovies + color.END)

addedEpisodes = jsonResponse["added"]["episodes"]
if addedEpisodes != 0:
  print(color.GREEN + "Added %s episodes" % addedEpisodes + color.END)
  
notFoundMovies = jsonResponse["not_found"]["movies"]
if notFoundMovies:
  print(color.RED + "Following movies was not found and could not be added:")
  for movie in notFoundMovies:
    print(movie["ids"]["imdb"])
  print(color.END)

notFoundShows = jsonResponse["not_found"]["shows"]
if notFoundShows:
  print(color.RED + "Following shows was not found and could not be added:")
  for show in notFoundShows:
    print(show["ids"]["imdb"])   
  print(color.END)

notFoundSeasons = jsonResponse["not_found"]["seasons"]
if notFoundSeasons:
  print(color.RED + "Following seasons was not found and could not be added:")
  for season in notFoundSeasons:
    print(season["ids"]["imdb"])
  print(color.END)

notFoundEpisodes = jsonResponse["not_found"]["episodes"]
if notFoundEpisodes:
  print(color.RED + "Following episodes was not found and could not be added:")
  for episode in notFoundEpisodes:
    print(episode["ids"]["imdb"])
  print(color.END)

notFoundPeople = jsonResponse["not_found"]["people"]
if notFoundPeople:
  print(color.RED + "Following people was not found and could not be added:")
  for people in notFoundPeople:
    print(people["ids"]["people"])
  print(color.END)



print(color.CYAN + "Done, exiting." + color.END)
exit(0)
