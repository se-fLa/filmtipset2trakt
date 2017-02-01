# filmtipset2trakt
### Tool to import data from www.filmtipset.se to www.trakt.tv

With these tools you can migrate all your watched movies and movie ratings from [Filmtipset](http://www.filmtipset.se) to [Trakt](http://trakt.tv)

## How to
Follow these instructions to migrate your data from Filmtipset.se to Trakt.tv.
Both Windows and Linux is supported. It requires Python 2, not compatible with Python 3.

### Get needed API key - this only need to be done once
First you need to get an authorization key to be able to import data to Trakt, to do this create an "API App" on trakt.tv

1. Login to your Trakt.tv account and go to [Your API Apps](https://trakt.tv/oauth/applications)
1. Click "NEW APPLICATION"
1. Fill in a name such as "Filmtipset" or what ever you like.
1. Fill in the "Redirect uri:" field, it can be anything but must be filled in. I suggest you use *http://not.used*
1. The rest of the fields can be left untouched
1. Click *SAVE APP*
1. Now open the newly created API app and on it's page you find the **unique client ID** and **client secret** - both 64 characters strings, these are needed in next step.
1. Run the `getAuthorizationBearerAccessTokenCode.py` script and enter the *client ID* and *client secret* when the scripts ask for it.
1. Follow the instructions from the script, it will tell you to visit https://trakt.tv/activate and fill in a PIN code in order to approve the API request. The script will poll and wait until it detects the request have been approved.

When you have approved the new API client using the PIN on the activate webpage the script will output your unique 64 character long **authorization bearer** needed for all future request to import data to trakt.tv.

This is how it will look when executing `getAuthorizationBearerAccessTokenCode.py`:
```
	Create your application API keys at https://trakt.tv/oauth/applications below (the redirect URI cam be anything)
	Enter your Trakt.tv API app Client ID    : bcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
	Enter your Trakt.tv API app Client Secret: 1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef

	Visit the URL below and approve the application API to use
	your Trakt.tv account using this PIN code 0A1BC3F4
	https://trakt.tv/activate
	Waiting for you to approve the PIN code...
	Waiting for you to approve the PIN code...
	Waiting for you to approve the PIN code...
	Waiting for you to approve the PIN code...
	Waiting for you to approve the PIN code...
	PIN approved.

	You new authorization bearer access token for this client ID is a1b2c3d4e5f6g7890a1b2c3d4e5f6g7890a1b2c3d4e5f6g7890a1b2c3d4e5f6g7890

	EXITING
```

### Export data from Filmtipset
1. Visit your personal page on [Filmtipset](http://www.filmtipset.se/yourpage.cgi), under the list of your latest rated movies there is a link "**Exportera denna lista**", click this link and a file will be downloaded to your computer containing all your seen and rated movies.
1. Open up this file in Google Drive / Speadsheet or Microsoft Excel or similair tool that can handle csv data.
1. Save the file as a "*tab separated file*", for example with the name Filmtipset-windowsCR.tsv
1. We now need to reformat data slightly before it can be processed and synced to Trakt. Run the commands listed below, you will need a Linux shell or do it manually in Notepad, for windows users you also have an option to install and use [Bash Shell](http://www.howtogeek.com/249966/how-to-install-and-use-the-linux-bash-shell-on-windows-10/). What we are doing is first using *tr* to translate windows newline characters to unix newlines and save this in a new file named Filmtipset-unix.tsv. If you are doing this manually this step is not needed. Then we use *awk* to parse out the imdb movie id together with it's seen date, respective with the rating and saving those in two new comma separated files Filmtipset_movies.csv and Filmtipset_ratings.csv, these are the files we will use for syncing.
	```
	tr -d '\r' < Filmtipset-windowsCR.tsv > Filmtipset-unix.tsv
	awk -F"\t" '{print "tt" $7 "," $6}' Filmtipset-unix.tsv > Filmtipset_movies.csv
	awk -F"\t" '{print "tt" $7 "," $5 "," $6}' Filmtipset-unix.tsv > Filmtipset_ratings.csv
	```
	The file with movies shall consist of the IMDB id and datetime separated with a comma. Either create this file using above commands or do it manually. Verify the file looks like this example before continuing:
	```
	tt3062096,2016-12-11 22:33:57
	tt3110958,2017-01-05 22:21:12
	tt2404435,2016-12-27 18:59:11
	```
	The ratings file shall consist of IMDB id followed by the rating followed by the datetime, separated by commas. All ratings will be doubled, e.g the script converts from rating scale 1-5 to 2-10. For example:
	```
	tt3062096,4,2016-12-11 22:33:57
	tt3110958,4,2017-01-05 22:21:12
	tt2404435,3,2016-12-27 18:59:11
	```

	**NOTE:** For importing ratings without failures it is recommended to max sync 200 movie ratings at a time, split your file like this if you have more then 200 movies (This is only needed for the ratings, not movies. Importing 2000 movies in one csv file has been tested without issues):
	```
	split -a 1 -d -l 200 Filmtipset_ratings.csv Filmtipset_ratings_part_
	```
	and then sync them one file at a time (you can check the progress on trakt.tv in between).

### Import data to Trakt.tv
1. To import the data to your Trakt.tv account you use the script `syncFromCsvFile.py`
1. It will prompt you for your API keys, to avoid having to type them in everytime you can add them inside the script.
1. To import your seen movies run:
	* ```syncFromCsvFile.py add Filmtipset_movies.csv```
1. To import the rating of movies run:
	* ```syncFromCsvFile.py rate Filmtipset_movies.csv```

If there where any errors or failures importing movies they are listed after the task completes, commonly this happens for movies missing at Trakt or wrong IMDB id (duplicate/depricated IMDB id etc).

Since Filmtipset uses a rating scale of 1-5 and Trakt uses 1-10 the score from Filmtipset is doubled, for example a Filmtipset rating of 3 becomes 6 on Trakt.

See below for full usage and how to remove all that was imported.
You can also manually add movies and tv-shows or single episodes using the IMDB id number using `addOneToHistory.py`, see below for usage.

### Made a misstake?
If something goes wrong and you want to revert you can also remove data from Trakt using *removemovies* and *rateremove* as argument to syncFromCsvFile.py

Note that it takes some time for the imported data to be reflected on your Trakt account. **Allow 5-10 minutes before all imported movies are visible**, especially it takes longer time for ratings to appear.

## Script usage help:
```
$ ./syncFromCsvFile.py --help

Usage: ./syncFromCsvFile.py <add | removemovies | rate | rateremove> <csvFile>
  add              Add the movies listed in csvFile
  removemovies     Remove the movies listed in csvFile
  rate             Rate the movies listed in csvFile
  rateremove       Remove the rating for the movies listed in csvFile
  csvFile          A comma separated file with IMDb ID (tt0000000) or rate and date.

Examples:
	./syncFromCsvFile.py add Filmtipset_20170109_movies.csv

```
```
$ ./addOneToHistory.py --help

Usage: ./addOneToHistory.py <type> <IMDb_ID[:season]> <datetime>
  type       Type of item to add. Accepts 'movies', 'shows' or 'episodes'.
             If only a show is passed, all episodes for the show will be added. If a season is specified, only episodes in that season will be added.
  IMDb_ID    The movie IMDb ID.
  datetime   The watched datetime in UTC following ISO8601 format.

Examples:
	Add one movie
		./addOneToHistory.py movies tt0120737 2017-01-01T20:30Z
	Add one single episode of a show
		./addOneToHistory.py episodes tt2057241 '2017-01-02 19:00:12'
	Add one season of a show
		./addOneToHistory.py shows tt0369179:3 '2017-01-03 18:00'
	Add all episodes of all seasons of a show
		./addOneToHistory.py shows tt1628033 '2017-01-04 13:00Z'

```

## Improvements needed
* Add parsing of data into the script so it is not necessary to awk the data before sync.
* Automatically split rating in chunks of 200 to avoid trakt.tv failures.
* Automatic save the authorization bearer from getAuthorizationBearerAccessTokenCode.py in a config file and read this file from other scripts to avoid user having to edit scripts.
* Make it compatible with Python2 and Python3.
