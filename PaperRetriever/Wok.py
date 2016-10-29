# -*- coding:utf8 -*-
#!/usr/bin/env python
import re
import urllib
import socket
import urllib2
import threading


'''
retrieve at web of knowledge(science)
process:
1.get search id
2.send data(search id,retrieval expression,year,etc.) to action URL
3.extract paper number from response page
notice:
1.when there are too many search records(about 190),searcher has to change search id
2.based on web of knowledge v5.22.3
3.login through IP address
'''

__author__ = 'brink'
__version__ = "v.5.22.3"

'''
edit date: 2016-10-15
'''

class Searcher(object): 
       
    def __init__(self):
        self.sid = self.getSearchID()
        self.__recordsNum = 0
        self.__basicData = [('product', "WOS"),
                        ('search_mode', "AdvancedSearch"),
                        ('SID', self.sid),
                        ('action', "search"),
                        ('period', "Year Range")]
        self.__actionURL = 'http://apps.webofknowledge.com/WOS_AdvancedSearch.do'
        # self.__seqNum = 0  # sequence number of search history. self.__recordsNum is ok.
            
    def getSearchID(self):
        newSession = urllib2.urlopen('http://www.webofknowledge.com/')
        url302 = newSession.url
        '''
        when using urllib.urlopen, the format of URL is unpredictable. 
        StackOverflow said that function had been deprecated.
        '''
        try:
            searchID = re.findall('&SID=(.+?)&', url302)[0]  # extract id
        except IndexError:
            print url302 + "error"
        return searchID
            
    def updateSid(self):
        # when there are too many records, need change sid
        if self.__recordsNum == 150:
            # index number is right, don't change
            self.__basicData[3] = ('SID', self.getSearchID())
            self.__recordsNum = 0
    
    resReg = re.compile(r'(\d+)\_div" class="historyResults">\s*<a href="(.+?)".+?>(.+?)<')                
    def getResultsNum(self):        
        results = Searcher.resReg.findall(self.__resultHtml)
        # results:[[sequence number,results info URL,results amount],[...],...]
        # self.infoURL='http://apps.webofknowledge.com/'+results[0][1]
        try:
            seqNum = int(results[0][0])
            if seqNum < self.__recordsNum:
                # it indicates that results number is zero
                raise IndexError
        except IndexError:
            print self.__basicData[0][1], 'return 0 results.'
            resultsNum = 0
            return resultsNum
        resultsNum = results[0][2]
        resultsNum = int(resultsNum.replace(",", ""))  # transfer to integer
        # results info page URL, contain each records's info url 
        self.infoURL = 'http://apps.webofknowledge.com/' + results[0][1]
        return resultsNum
    
    def setYearRange(self, start="", end=""):
        # default 1900-now
        if start != "" and end != "":
            self.__basicData.append(('startYear', start))
            self.__basicData.append(('endYear', end))
        
    def selectCitationIndex(self, *citationIndexs):
        '''
        citation indexes include: 
        "SCI","SSCI","AHCI","ISTP",
        "ISSHP","ESCI","IC","CCR"
        default: select all
        '''
        for db in citationIndexs:
            self.__basicData.append(('editions', db))
            
    def setDocType(self, dType=None):
        '''
        Article, Abstract of Published Item, Art Exhibit Review,
        Bibliography, Biogtaphical-Item, Book, Book Chapter,
        Chronology, Correction, 'Correction, Addition',
        Dance Performance Review, Database Review, Discussion,
        Editorial Material, Excerpt, 'Fiction, Creative Prose',
        Film Review, Hardware Review, Item About an Individual,
        Letter, Meeting Abstract, Meeting Summary,
        Music Performance Review, Music Score Review,
        News Item, Note, Poetry, Proceedings Paper,
        Record Review, Reprint, Review, Script,
        Software Review, TV Review, Radio Review,
        TV Review, Radio Review Video, Theater Review        
        
        default: select all types
        '''
        if dType != None:
            self.__basicData.append(('value(input3):', dType))
    
    def setDocLang(self, lang=None):
        # set document languages
        if lang != None:
            self.__basicData.append(('value(input3):', lang))
    
    def executeSearch(self, searchExpression):
        '''
        use search expression (string) as parameter. execute search and return page code
        '''
        if self.__basicData[0][0] != 'value(input1)':
            # change search expression
            self.__basicData.insert(0, ('value(input1)', searchExpression))
        else:
            # add search expression
            self.__basicData[0] = ('value(input1)', searchExpression)
            # check if need to change search id
            self.updateSid()
        d = urllib.urlencode(self.__basicData)
        # set timeout time in order to avoid the request being hanged for a long time.
        self.__resultHtml = urllib2.urlopen(self.__actionURL, d, timeout=25).read()
        self.__recordsNum += 1
        return self.__resultHtml
        
    '''
    Using self.infoURL to extract more advanced data.
    '''
    def getResultsURL(self):
        '''
        results page url==self.infoURL
        results paper url:
        http://apps.webofknowledge.com/full_record.do?
        product=WOS&search_mode=AdvancedSearch&
        qid=1&SID=3EYayYBAEmEUtZozCmr&page=1&doc=1&
        cacheurlFromRightClick=no
        paper info page url==urllopen(results paper url) 
        ''' 
        pass
        
    def getPaperPage(self):
        pass
    
    def extractAuthor(self):
        pass
    
    def extractKeyWord(self):
        pass
    def extractJournalInfo(self):
        pass
    
    def extractCitationNum(self):
        pass
    
    
class ThreadSearcher(threading.Thread):
    '''
    based on Searcher object.
    using multi-threaded to improve efficiency.
    '''
    
    def __init__(self, retrieveExQueue,  # retrieve expression queue, expected a list.
                  lock,  # threading.Lock() object.
                  results  # store results,expected a dictionary.
                ):
        super(ThreadSearcher, self).__init__()
        self.retrieveExQueue = retrieveExQueue
        self.citationIndexs = []
        self.results = results
        self.startYear = ""
        self.endYear = ""
        self.dType = None
        self.lang = None
        self.lock = lock
        
    def run(self):
        s = Searcher()
        s.setYearRange(self.startYear, self.endYear)
        s.setDocType(self.dType)
        s.setDocLang(self.lang)
        s.selectCitationIndex(*self.citationIndexs)
        while len(self.retrieveExQueue) != 0:
            self.lock.acquire()
            searchEx = self.retrieveExQueue.pop(0).strip()
            self.lock.release()
            try:
                s.executeSearch(searchEx)
            except socket.error:
                # the site server or network isn't stable, time out.
                self.retrieveExQueue.append(searchEx)
                print 'Bad network, a thread is timeout.'
                continue                
            except:
                self.retrieveExQueue.append(searchEx)
                continue
            num = s.getResultsNum()
            self.results[searchEx] = num
            print searchEx, num, threading.current_thread().name
    
    '''
    set advanced retrieval conditions for each thread by using 
    the following function.
    The parameters of these functions are same to Searher's member
    methods. 
    '''
    def setYearRange(self, startYear, endYear):
        self.startYear = startYear
        self.endYear = endYear
        
    def setDocType(self, dType):
        self.dType = dType
        
    def setDocLang(self, lang):
        self.lang = lang
        
    def selectCitationIndex(self, *citationIndexs):
        self.citationIndexs = citationIndexs

 
    
    
