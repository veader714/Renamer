from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import subprocess
import os
import tvdb
import re
import sys

class Renamer:
	__tv = tvdb.TVDB()

	def __init__(self):
		self.separationList = {}			# The current list of separations for the current episode
		self.tvdbSeriesInfo = {}			# The current info about the series from TVDB
		self.tvdbEpisodeNameList = []		# The list of episode names from the current series
		self.separators = " .-_"			# The list of common separators
		self.filelist = []					# The current list of files from the path given
		self.tvdbEpisodeMap = {}
		self.ignoreList = []
		self.loadIgnoreListFromFile('ignorelist')

	def guessSeriesName(self):
		return 0

	def getMostCommonString(self):
		return 0

	def isEpisodeOnlyNumeric(self):
		return 0

	# This is where we need to see if we have sub separators..... e.g: xxx_-_xxx where the real separator is the -
	def pruneSeparators(self,episode):
		separators = self.separators
		print(episode['title'])
		for separator, stringChunks in self.separationList.items():
			for i,chunk in enumerate(stringChunks):
				if i != 0 and i != len(stringChunks) - 1:
					if stringChunks[i - 1] == stringChunks[i + 1] and stringChunks[i - 1] in separators:
						# we may have a sub separator and we might be able to just take it out
						print(stringChunks[i - 1])
					
	def loadIgnoreListFromFile(self,filename):
		try:
			f = open(filename,'r')
			contents = f.readlines()
			for line in contents:
				self.ignoreList.append(line.strip('\n'))
			print(self.ignoreList)
		finally:
			f.close()
	def removeExtraCrap(self, filename,betweenChars=["[]","()"]):
		if(len(self.ignoreList)>0):
			for ignoreString in self.ignoreList:
				filename = self.__removeChunkFromStringIgnoreCase(filename,ignoreString)
		for group in betweenChars:
			inStart = 0
			endStart = 0
			while filename.find(group[0],inStart) != -1 and filename.find(group[1],endStart) != -1:
				startIndex = filename.find(group[-0],inStart)
				endIndex = filename.find(group[1],endStart)
				Chunk = filename[startIndex + 1:endIndex]
				if Chunk.isnumeric():
					inStart = startIndex + 1
					endStart = endIndex + 1
					continue
				if startIndex != 0:
					if endIndex != len(filename) - 1 and  filename[startIndex - 1] == filename[endIndex + 1] and filename[startIndex - 1] in self.separators:
						startIndex = startIndex - 1
				beforeChunk = filename[:startIndex]
				afterChunk = filename[endIndex + 1:]
				filename = beforeChunk + afterChunk
		
		if filename[0] in self.separators:
			filename = filename[1:]
		if filename[-1] in self.separators:
			filename = filename[:-1]
		
		return filename

	def filenameToEpisodeObject(self,filepath):
		episodeData = {}
		path, f = os.path.split(filepath)
		tf = f.split('.')
		episodeData['extension'] = tf[-1:][0]
		if episodeData['extension'] == 'srt':
			print("Found Subs")
			episodeData['type'] = 'sub'
		else:
			episodeData['type'] = 'ep'
		episodeData['path'] = path
		episodeData['originalFile'] = f
		cleanFile = '.'.join(tf[:-1])
		cleanedFile = self.removeExtraCrap(cleanFile)
		episodeData['title'] = cleanedFile
		return episodeData


	# Starting from left to right, starts joining the separations together and seeing how close to the show we can get. Once it finds the 
	# closest matching string it cuts that off the separation list. The separation list is probably not necessary until dealing with the episode titles
	# but it does help to increase the accuracy of the fuzzy search
	#
	# Improvements: Search for, and remove, the series from the filename w/o having to split stuff a bunch?
	def popSeriesFromFile(self,episode):
		filename = episode['title']
		series = self.tvdbSeriesInfo['series']['seriesName']
		seriesFormatted = series.replace(' ',"{separator}")
		highestRatio = 0
		highestRatioChunk = ""
		highestRatioSep = ""
		for separator,splitString in self.separationList.items():
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
		for separator,splitString in self.separationList.items():
			builtString = separator.join(splitString)
			partition = builtString.partition(highestRatioChunk)
			finalString = partition[0] + partition[2]
			if finalString[0] in self.separationList.keys():
				finalString = finalString[1:]
			if highestRatioSep == separator:
				episode['modifiedTitle'] = finalString
			self.separationList[separator] = finalString.split(separator)

	def popEpisodeSeasonFromFile(self,episode):
		if 'modifiedTitle' in episode:
			filename = episode['modifiedTitle']
		else:
			filename = episode['title']
		format1Check = re.compile('[sS]\d\d[eE]\d\d[aAbB]')
		format2Check = re.compile('[sS]\d\d[eE]\d\d')
		abovedir,curdir = os.path.split(episode['path'])
		if 'season' in curdir.lower():
			curdir_l = curdir.lower()
			episode['seasonNumber'] = curdir_l.split('season')[1]

		format1Result = format1Check.findall(filename)
		if len(format1Result) > 0:
			# this episode naming convention is somewhat standard(Plex does not handle the SXXEXXa and SXXEXXb format very well, it needs to be SXXEXX and SXXEXX+1)
			# if the file has two episodes (common in cartoons where is each episode is ~11 mins long and some people are stupid enough to put them in a single file)
			# the format should be Show.SXXEXXEXX+1.Episode1Title.Episode2Title
			# I'm making the assumption that if one file has this format, all other files will. Whenever I process the filenames I can correct as necessary
			# and yes I realize this is redundant
			season = format1Result[0][1:3]
			episodeNumber = int(format1Result[0][4:6])
			piece = str(format1Result[0][6]).lower()
			if piece == 'a':
				episodeNumber = (episodeNumber * 2) - 1
			if piece == 'b':
				episodeNumber = episodeNumber * 2
			episode['seasonNumber'] = season
			episode['episodeNumber'] = episodeNumber
			episode['modifiedTitle'] = format1Check.split(filename)[1]
			
			
		else:
			format2Result = format2Check.findall(filename)
			if len(format2Result) > 0:
				#episode naming convention is standard and Plex can likely handle it (should we just split it off at this point????)
				season = format2Result[0][1:3]
				episodeNumber = int(format2Result[0][4:6])
				episode['seasonNumber'] = season
				episode['episodeNumber'] = episodeNumber
				episode['modifiedTitle'] = format2Check.split(filename)[1]
			else:
				# How the fuck do we want to do this.....
				# Episode does not have SXXEXX format
				# Could have format XXX... which is just the absolute episode number
				# Could have format SEE... Season 1 Episode 23 -> 123
				# Could be something I've never seen before....
				self.pruneSeparators(episode)
		if episode['modifiedTitle'][0] in self.separators:
			episode['modifiedTitle'] = episode['modifiedTitle'][1:]
		for char in self.separators:
			self.separationList[char] = episode['modifiedTitle'].split(char)
	

	def popEpisodeTitlesFromFile(self,episode):
		episodeString = episode['modifiedTitle']
		print(episode['title'])
		chunkList = [i for i in re.split('\.|-|_| ',episodeString) if i]
		hasEpisode = True
		while hasEpisode:
			if len(chunkList) == 0:
				break
			guessData = {}
			bestGuess = ""
			bestGuessScore = -1
			bestGuessIt = -1	
			for i in range(0,len(chunkList)):
				builtChunk = ""
				if i == 0:
					builtChunk = chunkList[i]
				else:
					builtChunk = " ".join(chunkList[:i + 1])
				guess,guessScore = process.extractOne(builtChunk,self.tvdbEpisodeNameList)
				p1 = builtChunk.find('Part 1')
				p2 = builtChunk.find('Part 2')
				if p1 > -1:
					replacement = builtChunk.replace('Part 1','(1)') #some files may have part 1 or 2, but TVDB may have it listed in (1) or (2) format
					guessT,guessScoreT = process.extractOne(replacement,self.tvdbEpisodeNameList)
					if guessScoreT > guessScore:
						guessScore = guessScoreT
						builtChunk = replacement
				if p2 > -1:
					replacement = builtChunk.replace('Part 2','(2)') #This will probably be a file that is loaded, but we can do that later
					guessT,guessScoreT = process.extractOne(replacement,self.tvdbEpisodeNameList)
					if guessScoreT > guessScore:
						guessScore = guessScoreT
						builtChunk = replacement
				guessData[builtChunk] = guessScore
				if guessScore > bestGuessScore:
					bestGuessScore = guessScore
					bestGuess = guess
					bestGuessIt = i
				elif bestGuessScore == 100 and guessScore == 100 and i > bestGuessIt:
					bestGuess = guess
					bestGuessIt = i
			chunkList = chunkList[bestGuessIt + 1:]
			hasEpisode = Renamer.__calcEpisodePresence(guessData)
			if hasEpisode:
				if 'episodeList' not in episode:
					episode['episodeList'] = list()
				self.tvdbEpisodeNameList.remove(bestGuess)
				episode['episodeList'].append(bestGuess)
				print(bestGuess + "|" + str(bestGuessScore))
			else:
				# print(bestGuess + "|" + str(bestGuessScore) + " Failed")
				pass
		return 0

	# 
	def extractEpisodeInfo(self,episode):
		if episode['type'] == 'ep':
			cleanFile = episode['title']
			for char in self.separators:
				self.separationList[char] = cleanFile.split(char)
			self.popSeriesFromFile(episode)
			self.popEpisodeSeasonFromFile(episode)
			self.popEpisodeTitlesFromFile(episode)
			self.cleanUpEpisodeInfo(episode)
		else:
			pass #subtitles get past the media finder so we'll just handle them separately, which is fine since we want to keep them with their episodes
		
	def cleanUpEpisodeInfo(self,episode):
		if 'episodeList' in episode:
			if not episode['episodeList']:
				print(episode)
			for titleMatch in episode['episodeList']:
				pass
				#print(titleMatch)

	def createSeasonFolders(self,path, seasonCount):
		for i in range(1,seasonCount + 1):
			try:
				os.mkdir(path + '/Season ' + str(i))
			except OSError:
				print("unable to create folder: " + path + '/Season ' + str(i))
			else:
				print("created folder")

	def extractEpisodesFromPath(self,path):
		print(path)
		if ';' in path:
			return
		if os.path.isfile(path):
			self.extractEpisodeInfo(path)
		episodeList =[]
		for root, subFolders, files in os.walk(path):
			for f in files:
				filepath = os.path.join(root,f)
				if subprocess.run("/usr/bin/mediainfo \""+ filepath + "\" | grep Format",shell=True,stdout = subprocess.DEVNULL).returncode == 0:
					print("found media file")
					episodeList.append(self.filenameToEpisodeObject(filepath))
				else:
					print("not a media file")
		if(self.tvdbSeriesInfo != None):
			for episode in self.tvdbSeriesInfo['episodes']:
				self.tvdbEpisodeNameList.append(episode['episodeName'])
				self.tvdbEpisodeMap[episode['episodeName']] = {'SeasonNum':episode['airedSeason'],'EpisodeNum':episode['airedEpisodeNumber']}

		for episode in episodeList:
			self.extractEpisodeInfo(episode)

	def __calcEpisodePresence(nameData):
		print(nameData)
		if not nameData:
			return False
		#sortedList = sorted(nameData.items(), key=lambda item: item[1])
		nameList = [v for v in nameData.items() if v]
		average = sum(int(v[1]) for v in nameList) / len(nameList)
		maxScore = max(int(v[1]) for v in nameList)
		print("Average: " + str(average) + " | Max: " + str(maxScore))
		if maxScore >= 97 and average > 80:
			return True
		if average < 87:
			return False
		return True
	
	def __calculatePeaksAndValleys(self,nameList):
		peakCount = 0
		valleyCount = 0
		starting = True
		growing = False
		prev = -1
		for i in range(0,len(nameList)):
			print("Peak Count:" + str(peakCount) + " | Valley Count: " + str(valleyCount) + " | Growing: " + str(growing))
			item = nameList[i]
			if i == 0:
				if prev == -1:
					prev = item[1]
					continue
			if i == len(nameList) - 1:
				if item[1] > prev or growing:
					peakCount += 1
				if item[1] < prev or not growing:
					valleyCount += 1
			if starting:
				if item[1] > prev:
					growing = True
					valleyCount += 1
				if item[1] < prev:
					growing = False
					peakCount += 1
				starting = False
			else:
				if item[1] > prev and not growing:
					growing = True
					valleyCount += 1
				if item[1] < prev and growing:
					growing = False
					peakCount += 1
			prev = item[1]
		return peakCount,valleyCount
	def __removeChunkFromStringIgnoreCase(self,inString,chunk):
		loweredString = inString.lower()
		chunkPos = loweredString.find(chunk)
		chunkLen = len(chunk)
		while chunkPos != -1:
			if chunkPos != 0 and loweredString[chunkPos - 1] in self.separators and chunkLen + chunkPos < len(loweredString) and loweredString[chunkLen + chunkPos] in self.separators:
				loweredString = loweredString[:chunkPos - 1] + loweredString[chunkLen + chunkPos:]
				inString = inString[:chunkPos - 1] + inString[chunkLen + chunkPos:]
				chunkPos = loweredString.find(chunk, chunkPos + 1)
			elif chunkPos + chunkLen == len(loweredString) and chunkPos != 0 and loweredString[chunkPos - 1] in self.separators:
				loweredString = loweredString[:chunkPos - 1]
				inString = inString[:chunkPos - 1]
				chunkPos = loweredString.find(chunk, chunkPos + 1)
			elif chunkPos == 0 and loweredString[chunkLen + chunkPos] in self.separators:
				loweredString = loweredString[chunkLen + chunkPos:]
				inString = inString[chunkLen + chunkPos:]
				chunkPos = loweredString.find(chunk,chunkPos + 1)
			else:
				chunkPos = loweredString.find(chunk,chunkPos + 1) #I'm not comfortable removing chunks if they aren't surrounded by seperators
		return inString
		
	def renameEpisodes(self,episodeList, tvdbEpisodeData):
		return 0
	def processFolder(self,path):
		folderlist = os.listdir(path)
		show = folderlist[2]
		print(show)	
		pshows = Renamer.__tv.searchSeries(show)
		testshow = pshows[0]['id']
		self.tvdbSeriesInfo = {'series':pshows[0],'episodes':Renamer.__tv.getEpisodesBySeriesID(testshow)}
		self.extractEpisodesFromPath(os.path.join(path + show))

# masterlist = os.listdir("/srv/Schustore/Videos/TV Shows")
# createSeasonFolders("/srv/Schustore/Downloads/Mega/test",3)
r = Renamer()
print(sys.argv)
quit()
r.processFolder(sys.argv[1])
# renameEpisodes(folderlist[0],tv.getEpisodesBySeriesID(testshow))
