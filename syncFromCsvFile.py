#!/usr/bin/python
#
# Author: fLa
#
from urllib2 import Request, urlopen, URLError, HTTPError
import json
import sys
import os.path
import csv

# 
# How to import Filmtipset to Trakt.tv:
# 1 Export your movies from www.filmtipset.se
# 2 Open the xls in Google Drive / Spreadsheet
# 3 Save as "tab separated file" .tsv
# 4 tr -d '\r' < FilmtipsetFixad.tsv > FilmtipsetFixad_unix.tsv
# 5a awk -F"\t" '{print "tt" $7 "," $6}' Filmtipset_20170109.tsv > Filmtipset_20170109_movies.csv
# 5b awk -F"\t" '{print "tt" $7 "," $5 "," $6}' Filmtipset_20170109.tsv > Filmtipset_20170109_ratings.csv
# NOTE: For rating to work it is recommended max synbc 200 movie ratings at a time, split your file like this:
# split -a 1 -d -l 200 Filmtipset_20170109_ratings.csv Filmtipset_20170109_ratings_part_
# and then sync them one by one and check numbers on your profile page in between.
#

# Fill in your application API client ID from https://trakt.tv/oauth/applications below
# or leave it empty and you will be propmted for it on execution.
clientID           = ""
# Fill in your access token (get it from getAuthorizationBearerAccessTokenCode.py)
# or leave it empty and you will be propmted for it on execution.
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

def printUsage():
  print("\nUsage: " + sys.argv[0] + " <add | removemovies | rate | rateremove> <csvFile>")
  print("  add              Add the movies listed in csvFile")
  print("  removemovies     Remove the movies listed in csvFile")
  print("  rate             Rate the movies listed in csvFile")    
  print("  rateremove       Remove the rating for the movies listed in csvFile")
  print("  csvFile          A comma separated file with IMDb ID (tt0000000) or rate and date.")
  print("\nExamples:")
  print("\t" + sys.argv[0] + " add Filmtipset_20170109_movies.csv")
  print("")


if len(sys.argv) != 3:
  print(color.RED + "Invalid number of arguments" + color.END)
  printUsage()
  exit(1)


#------------------------------------------------------------------------------------------
 
def syncFromCsvFile(operation, filePath):
  csvFile = open(filePath, 'r')
  if operation == "add" or operation == "removemovies":
    fieldnames = ("imdb","at")
    reader = csv.DictReader( csvFile, fieldnames)
    #Now we have: {'at': '2006-02-04 12:35:36', 'imdb': 'tt117571'}
  elif operation == "rate" or operation == "rateremove":
    fieldnames = ("imdb","rating","at")
    reader = csv.DictReader( csvFile, fieldnames)        
  else:
    print("INTERNAL ERROR, unsupported operation " + operation)
    exit(2)
  
  # Create json structure
  jsonValues = { "movies" : [] }
  for row in reader:     
    # Padd zero to IMDb IDs needing it
    if len(row["imdb"]) != 9:
      row["imdb"] = "tt%s" % row["imdb"][2:].rjust(7, '0')                    
    if operation == "add" or operation == "removemovies":
      movie = { "watched_at": row["at"], "ids": { "imdb": row["imdb"] } }
    elif operation == "rate":
      # make the rating a number and also change from 1-5 to 1-10
      rating = int(row["rating"]) * 2
      movie = { "rated_at": row["at"], "rating": rating, "ids": { "imdb": row["imdb"] } }
    elif operation == "rateremove":
      movie = { "ids": { "imdb": row["imdb"] } }
    jsonValues["movies"].append(movie)
  #print json.dumps(jsonValues, indent=4, separators=(',', ': '))
  #exit(1)

  # The clienID and authorizationToken, might have changed so must do it here.
  headers = { 
   'Content-Type': 'application/json',
   'Authorization': 'Bearer %s' % authorizationToken,
   'trakt-api-version': '2',
   'trakt-api-key': '%s' % clientID
  }
  
  values = json.dumps(jsonValues)
  if operation == "add":
    request_syncHistory = Request('https://api.trakt.tv/sync/history', data=values, headers=headers) 
  elif operation == "removemovies":
    request_syncHistory = Request('https://api.trakt.tv/sync/history/remove', data=values, headers=headers)    
  elif operation == "rate":
    request_syncHistory = Request('https://api.trakt.tv/sync/ratings', data=values, headers=headers)
  elif operation == "rateremove":
    request_syncHistory = Request('https://api.trakt.tv/sync/ratings/remove', data=values, headers=headers)        
  else:
    print("ERROR - unsupported operation!")
    exit(2)
  try:
    print(color.PURPLE + "Please wait while syncing with Trakt.tv" + color.END)
    response = urlopen(request_syncHistory, timeout = 300)
  except HTTPError as e:
    if e.code == 401:
       print(color.RED + "Authorization failed - your credentials are invalid!\nMake sure the autorization token is still valid and check your client ID is correct." + color.END)
       exit(1)
    elif e.code == 400:
       print(color.RED + "Bad Request - request couldn't be parsed!" + color.END)
       exit(1)
    elif e.code == 403:
       print(color.RED + "Invalid API credentials or unapproved app." + color.END)
       exit(1)     
    elif e.code == 524:
       print(color.RED + "Trakt.tv server time-out and closed the connection. Your file is to big, but probably all is synced anyway. Wait 5-10 minutes and review your Trakt.tv profile." + color.END)
       exit(1)                                  
    else:
       print(color.RED + "Unknown Error!! HTTP response code " + color.END)
       print(e)
       exit(1)
  except Exception:
    print(color.RED + "ERROR\nUnexpected exception" + color.END)      
    print(sys.exc_info())
    exit(1) 

  response_body = response.read()
  #TODO check response code 201 204
  try:
    parsed_json = json.loads(response_body)
  except ValueError, e:   
    print(color.RED + "Invalid data received:" + color.END)  
    print(response_body)   
    exit(1)
  print(color.PURPLE + "Sync ended." + color.END)
  return parsed_json      



#====================== MAIN =============================

if sys.argv[1] == "add":
  operation = "add"
elif sys.argv[1] == "removemovies":
  operation = "removemovies"
elif sys.argv[1] == "rate":
  operation = "rate"
elif sys.argv[1] == "rateremove":
  operation = "rateremove"
else:
  print(color.RED + "Unsupported operation: " + sys.argv[1] + color.END)
  printUsage()
  exit(1)
csvFile = sys.argv[2]

# Verify user input
if not os.path.isfile(csvFile):
  print(color.RED + "Invalid file!" + color.END)
  exit(1)

# TODO: Verify users csv file are in right format corresponding to the choosed operation

# Check authorization details
if not clientID or not authorizationToken:
  print(color.YELLOW + "Create your application API keys at https://trakt.tv/oauth/applications below (the redirect URI cam be anything)" + color.END)
if not clientID:
  clientID = raw_input("Enter your Trakt.tv API app Client ID    : ")
  if len(clientID) != 64:
    print(color.RED + "The client ID is invalid, should be 64 characters." + color.END)
    exit(1)          
if not authorizationToken:
  print(color.YELLOW + "Get your API authorization bearer token from getAuthorizationBearerAccessTokenCode.py" + color.END)
  authorizationToken = raw_input("Enter your Trakt.tv API authorization bearer token: ")
  if len(authorizationToken) != 64:
    print(color.RED + "The authorization bearer token is invalid, should be 64 characters." + color.END)
    exit(1)
                                        

jsonResponse = syncFromCsvFile(operation, csvFile)
#print json.dumps(jsonResponse, indent=3, separators=(',', ': '))
  
addedMovies = addedEpisodes = removedMovies = removedEpisodes = 0
if operation == "add" or operation == "rate":
  addedMovies = jsonResponse["added"]["movies"]
  if addedMovies != 0:
    print(color.GREEN + "Added %s movies" % addedMovies + color.END)

  addedEpisodes = jsonResponse["added"]["episodes"]
  if addedEpisodes != 0:
    print(color.GREEN + "Added %s episodes" % addedEpisodes + color.END)
elif operation == "removemovies" or operation == "rateremove":
  removedMovies = jsonResponse["deleted"]["movies"]
  if removedMovies != 0:
    if operation == "removemovies":
      print(color.GREEN + "Deleted %s movies" % removedMovies + color.END)
    elif operation == "rateremove":
     print(color.GREEN + "Removed rating for %s movies" % removedMovies + color.END)     
          
  removedEpisodes = jsonResponse["deleted"]["episodes"]
  if removedEpisodes != 0:
    if operation == "removemovies":
      print(color.GREEN + "Deleted %s episodes" % removedEpisodes + color.END)
    elif operation == "rateremove":
      print(color.GREEN + "Removed rating for %s episodes" % removedEpisodes + color.END)
else:
  print("INTERNAL ERROR, unsupported operation " + operation)
  exit(2)                    
  
notFoundMovies = jsonResponse["not_found"]["movies"]
if notFoundMovies:
  print(color.RED + "Following movies was not found and could not be synced:")
  for movie in notFoundMovies:
    print(movie["ids"]["imdb"])
  print(color.END)

notFoundShows = jsonResponse["not_found"]["shows"]
if notFoundShows:
  print(color.RED + "Following shows was not found and could not be synced:")
  for show in notFoundShows:
    print(show["ids"]["imdb"])   
  print(color.END)

notFoundSeasons = jsonResponse["not_found"]["seasons"]
if notFoundSeasons:
  print(color.RED + "Following seasons was not found and could not be synced:")
  for season in notFoundSeasons:
    print(season["ids"]["imdb"])
  print(color.END)

notFoundEpisodes = jsonResponse["not_found"]["episodes"]
if notFoundEpisodes:
  print(color.RED + "Following episodes was not found and could not be synced:")
  for episode in notFoundEpisodes:
    print(episode["ids"]["imdb"])
  print(color.END)

notFoundPeople = jsonResponse["not_found"]["people"]
if notFoundPeople:
  print(color.RED + "Following people was not found and could not be synced:")
  for people in notFoundPeople:
    print(people["ids"]["people"])
  print(color.END)

if addedMovies == addedEpisodes == removedMovies == removedEpisodes == 0:
  print(color.YELLOW + "No changes executed." + color.END)
else:
  print(color.YELLOW + "The above number may be inaccurate due a fault in Trakt.tv API!\nCheck your Trakt.tv profile, but note that it may take several minutes\nbefore changes are reflected in your Trakt.tv profile view." + color.END)
  
print(color.CYAN + "Done, exiting." + color.END)
exit(0)
