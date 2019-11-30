import requests
import json
import time

class TVDB:
    __lastTokenRefresh = -1
    __loginData = {
	        "apikey":"42528FAC6093648C"
        }
    __tvURL = "https://api.thetvdb.com/"
    __token = ""
    def __init__(self):
        if TVDB.__lastTokenRefresh == -1:
            TVDB.__token = self.__getLoginToken(TVDB.__loginData)
            TVDB.__lastTokenRefresh = time.time()
        elif self.__tokenNeedsRefresh():
            self.__refreshLoginToken()

    def __tokenNeedsRefresh(self):
        if time.time() - TVDB.__lastTokenRefresh >= 70000:
            return True
        return False
    def __getLoginToken(self,key):
        d = self.__postRequest('login',key, requiresToken = False)
        if 'token' in d:
            return d['token']
        else:
            print(d)
        
    def __refreshLoginToken(self):
        return self.__getRequest('refresh_token')

    def __postRequest(self,url,payload,headers = {'content-type':'application/json'}, requiresToken = True):
        if 'content-type' not in headers:
            headers.update({'content-type':'application/json'})
        if requiresToken:
            headers.update({'Authorization' : 'Bearer ' + TVDB.__token})
        url = TVDB.__tvURL + url
        r = requests.post(url,data = json.dumps(payload), headers=headers)
        return r.json()
        
    def __getRequest(self,url,payload = {},headers = {}, requiresToken = True):
        if requiresToken:
            headers.update({'Authorization' : 'Bearer ' + TVDB.__token})
        url = TVDB.__tvURL + url
        r = requests.get(url,headers = headers,params = payload)
        return r.json()

    def getEpisodesBySeriesID(self,seriesID):
        if self.__tokenNeedsRefresh():
            self.__refreshLoginToken()
        data = self.__getRequest('series/' + str(seriesID) + '/episodes')
        if(data['links']['last'] > 1):
            episodeData = data['data']
            nextPage = data['links']['next']
            while nextPage != None:
                rd = self.__getRequest('series/' + str(seriesID) + '/episodes',payload = {'page' : nextPage} )
                nextPage = rd['links']['next']
                episodeData = episodeData + rd['data']
            return episodeData
        else:
            return data['data']
            
    def searchSeries(self,searchString):
        if self.__tokenNeedsRefresh():
            self.__refreshLoginToken()
        data = self.__getRequest('search/series',payload = { 'name': searchString }, requiresToken = True)
        return data['data']

    def getSeriesbyID(self,seriesID):
        if self.__tokenNeedsRefresh():
            self.__refreshLoginToken()
        data = self.__getRequest('series/' + str(seriesID))
        return data['data']
    
    def getSeasonByID(self,seasonID):
        if self.__tokenNeedsRefresh():
            self.__refreshLoginToken
        data = self.__getRequest('series/season/' + str(seasonID))
        print(data)
        return data
