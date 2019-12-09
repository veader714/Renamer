from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import subprocess
import os
import tvdb
import re

tv = tvdb.TVDB()


def guessSeriesName(filelist):
	return 0

def getMostCommonString(filelist):
	return 0

def isEpisodeOnlyNumeric():
	return 0

# This is where we need to see if we have sub separators..... e.g: xxx_-_xxx where the real separator is the -
def pruneSeparators(episode,separationList, separators = " .-_"):
	separators = separationList.keys()
	print(episode['title'])
	for separator, stringChunks in separationList.items():
		for chunk, i in enumerate(stringChunks):
			if i != 0 and i != len(stringChunks) - 1:
				if stringChunks[i - 1] == stringChunks[i + 1] and stringChunks[i - 1] in separators:
					# we may have a sub separator
					print(stringChunks[i - 1])
				
# This function will have problems with TV shows that have the same name but are differentiated by the year
# since often the name of the show will include the year inside parenthesis
def removeExtraCrap(filename,betweenChars=["[]","()"],separators = " .-_"):
	for group in betweenChars:
		while filename.find(group[0]) != -1 and filename.find(group[1]) != -1:
			startIndex = filename.find(group[-0])
			endIndex = filename.find(group[1])
			if startIndex != 0:
				if endIndex != len(filename) - 1 and  filename[startIndex - 1] == filename[endIndex + 1] and filename[startIndex - 1] in separators:
					startIndex = startIndex - 1
			beforeChunk = filename[:startIndex]
			afterChunk = filename[endIndex + 1:]
			filename = beforeChunk + afterChunk
	if filename[0] in separators:
		filename = filename[1:]
	if filename[-1] in separators:
		filename = filename[:-1]
	return filename

def filenameToEpisodeObject(filepath):
	episodeData = {}
	path, f = os.path.split(filepath)
	tf = f.split('.')
	episodeData['extension'] = tf[-1:]
	episodeData['path'] = path
	episodeData['originalFile'] = f
	cleanFile = '.'.join(tf[:-1])
	cleanedFile = removeExtraCrap(cleanFile)
	episodeData['title'] = cleanedFile
	return episodeData


# Starting from left to right, starts joining the separations together and seeing how close to the show we can get. Once it finds the 
# closest matching string it cuts that off the separation list. The separation list is probably not necessary until dealing with the episode titles
# but it does help to increase the accuracy of the fuzzy search
#
# Improvements: Search for, and remove, the series from the filename w/o having to split stuff a bunch?
def popSeriesFromFile(episode,separationList,tvdbEpisodeInfo={},currentEpData={},currentSeriesData=[]):
	filename = episode['title']
	series = tvdbEpisodeInfo['series']['seriesName']
	seriesFormatted = series.replace(' ',"{separator}")
	highestRatio = 0
	highestRatioChunk = ""
	highestRatioSep = ""
	for separator,splitString in separationList.items():
		if(len(splitString) > 1):
			sepSeries = seriesFormatted.format(separator=separator)
			for i in range(0,len(splitString) - 1):
				chunk = separator.join(filename.split(separator,i)[:i])
				ratio = fuzz.ratio(chunk.lower(),sepSeries.lower())
				if ratio > highestRatio:
					highestRatio = ratio
					highestRatioChunk = chunk
					highestRatioSep = separator
	finalString = ""
	for separator,splitString in separationList.items():
		builtString = separator.join(splitString)
		partition = builtString.partition(highestRatioChunk)
		finalString = partition[0] + partition[2]
		if finalString[0] in separationList.keys():
			finalString = finalString[1:]
		if highestRatioSep == separator:
			currentEpData['modifiedTitle'] = finalString
		separationList[separator] = finalString.split(separator)


def popEpisodeSeasonFromFile(episode,separationList,tvdbEpisodeInfo={},currentEpData={}):
	if(currentEpData['modifiedTitle']):
		filename = currentEpData['modifiedTitle']
	else:
		filename = episode['title']
	format1Check = re.compile('[sS]\d\d[eE]\d\d[aAbBcCdD]') # May god have mercy on my soul when I have to deal with a show using this as an episode title.....
	format2Check = re.compile('[sS]\d\d[eE]\d\d')
	abovedir,curdir = os.path.split(episode['path'])
	if 'season' in curdir.lower():
		curdir_l = curdir.lower()
		currentEpData['seasonNumber'] = curdir_l.split('season')[1]

	format1Result = format1Check.findall(filename)
	if len(format1Result) > 0:
		
		print("format 1")
		# episode naming convention is somewhat standard(SXXEXXa and SXXEXXb format is not handled well at all, needs to be SXXEXX and SXXEXX+1)
		# if the file has two episodes (common in cartoons where is each episode is ~11 mins long and some people are stupid enough to put them in a single file)
		# the format should be Show.SXXEXXEXX+1.Episode1Title.Episode2Title
		# I'm making the assumption that if one file has this format, all other files will. Whenever I process the filenames I can correct as necessary
		# and yes I realize this is redundant
		
	else:
		format2Result = format2Check.findall(filename)
		if len(format2Result) > 0:
			print("format 2")
			#episode naming convention is standard and Plex can likely handle it (should we just split it off at this point????)
			season = format2Result[0][1:3]
			episode = format2Result[0][4:6]
			currentEpData['seasonNumber'] = season
			currentEpData['episodeNumber'] = episode
			currentEpData['modifiedTitle'] = format2Check.split(filename)[1]
		else:
			# How the fuck do we want to do this.....
			# Episode does not have SXXEXX format
			# Could have format XXX... which is just the absolute episode number
			# Could have format SEE... Season 1 Episode 23 -> 123
			# Could be something I've never seen before....
			pruneSeparators(episode, separationList)

	format2List = formatCheck2.split(filename)


def popEpisodeTitlesFromFile(filename,separationList,rvdbEpisodeInfo={},currentEpData={}):
	return 0

# 
def extractEpisodeInfo(episode,tvdbEpisodeInfo={},tvdbEpisodeNameList = []):
	cleanFile = episode['title']
	commonSeparators = " .-_" # These are the most common separators, and will probably need revisiting
	separationList = {}
	for char in commonSeparators:
		separationList[char] = cleanFile.split(char)
	popSeriesFromFile(episode,separationList,tvdbEpisodeInfo)
	popEpisodeSeasonFromFile(episode,separationList,tvdbEpisodeInfo)
	

def createSeasonFolders(path, seasonCount):
	for i in range(1,seasonCount + 1):
		try:
			os.mkdir(path + '/Season ' + str(i))
		except OSError:
			print("unable to create folder: " + path + '/Season ' + str(i))
		else:
			print("created folder")

def extractEpisodesFromPath(path,tvdbEpisodeInfo = {}):
	if ';' in path:
		return
	if os.path.isfile(path):
		extractEpisodeInfo(path,None,tvdbEpisodeInfo)
	episodeList =[]
	for root, subFolders, files in os.walk(path):
		for f in files:
			filepath = os.path.join(root,f)
			if subprocess.run("/usr/bin/mediainfo \""+ filepath + "\" | grep Format",shell=True,stdout = subprocess.DEVNULL).returncode == 0:
				print("found media file")
				episodeList.append(filenameToEpisodeObject(filepath))
			else:
				print("not a media file")
	if(tvdbEpisodeInfo != None):
		tvdbEpisodeNameList = []
		for episode in tvdbEpisodeInfo['episodes']:
			tvdbEpisodeNameList.append(episode['episodeName'])
	for episode in episodeList:
		extractEpisodeInfo(episode,tvdbEpisodeInfo = tvdbEpisodeInfo,tvdbEpisodeNameList = tvdbEpisodeNameList)
		
def renameEpisodes(episodeList, tvdbEpisodeData):
	return 0

# masterlist = os.listdir("/srv/Schustore/Videos/TV Shows")
# createSeasonFolders("/srv/Schustore/Downloads/Mega/test",3)
folderlist = os.listdir("/srv/Schustore/Downloads/Mega/test")
show = folderlist[2]	
pshows = tv.searchSeries(show)
testshow = pshows[0]['id']
showInfo = {'series':pshows[0],'episodes':tv.getEpisodesBySeriesID(testshow)}
print(showInfo['episodes'])
extractEpisodesFromPath(os.path.join("/srv/Schustore/Downloads/Mega/test/" + show),showInfo)
# renameEpisodes(folderlist[0],tv.getEpisodesBySeriesID(testshow))
