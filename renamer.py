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
# 
#
# The series name will include any separators as part of the filename. TODO:Check both series name as it is written in the file name and also check the 
#
# Improvements: Search for, and remove, the series from the filename w/o having to split stuff a bunch?
def popSeriesFromFile(episode,separationList,tvdbEpisodeInfo={},currentEpData={},currentSeriesData=[]):
	filename = episode['title']
	series = tvdbEpisodeInfo['series']['seriesName']
	seriesFormatted = series.replace(' ',"{separator}")
	highestRatio = 0
	highestRatioChunk = ""
	for separator,splitString in separationList.items():
		if(len(splitString) > 1):
			sepSeries = seriesFormatted.format(separator=separator)
			for i in range(0,len(splitString) - 1):
				chunk = separator.join(filename.split(separator,i)[:i])
				ratio = fuzz.ratio(chunk.lower(),sepSeries.lower())
				if ratio > highestRatio:
					highestRatio = ratio
					highestRatioChunk = chunk
	finalString = ""
	for separator,splitString in separationList.items():
		builtString = separator.join(splitString)
		partition = builtString.partition(highestRatioChunk)
		finalString = partition[0] + partition[2]
		if finalString[0] in separationList.keys():
			finalString = finalString[1:]
		separationList[separator] = finalString.split(separator)
	print(separationList)


def popEpisodeSeasonFromFile(episode,separationList,tvdbEpisodeInfo={},currentEpData={}):
	filename = episode['title']
	formatCheck1 = re.compile('[sS]\d\d[eE]\d\d[aAbBcCdD]')
	formatCheck2 = re.compile('[sS]\d\d[eE]\d\d')
	abovedir,curdir = os.path.split(episode['path'])
	if 'season' in curdir.lower():
		curdir_l = curdir.lower()
		currentEpData['season'] = curdir_l.split('season')[1]
	format1List = formatCheck1.split(filename)
	if len(format1List) != 1 and filename not in format1List:
		print('something')
	format2List = formatCheck2.split(filename)


def popEpisodeTitlesFromFile(filename,separationList,rvdbEpisodeInfo={},currentEpData={}):
	return 0


def extractEpisodeInfo(episode,tvdbEpisodeInfo={},tvdbEpisodeNameList = []):
	cleanFile = episode['title']
	commonSeparators = " .-_" # These are the most common separators, and will probably need 
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
extractEpisodesFromPath(os.path.join("/srv/Schustore/Downloads/Mega/test/" + show),showInfo)
# renameEpisodes(folderlist[0],tv.getEpisodesBySeriesID(testshow))
