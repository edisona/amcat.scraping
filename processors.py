###########################################################################
#          (C) Vrije Universiteit, Amsterdam (the Netherlands)            #
#                                                                         #
# This file is part of AmCAT - The Amsterdam Content Analysis Toolkit     #
#                                                                         #
# AmCAT is free software: you can redistribute it and/or modify it under  #
# the terms of the GNU Affero General Public License as published by the  #
# Free Software Foundation, either version 3 of the License, or (at your  #
# option) any later version.                                              #
#                                                                         #
# AmCAT is distributed in the hope that it will be useful, but WITHOUT    #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or   #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public     #
# License for more details.                                               #
#                                                                         #
# You should have received a copy of the GNU Affero General Public        #
# License along with AmCAT.  If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################
"""This module contains the main scraping-logic. All scrapers have to inherit
from BaseScraper, which provides an multithreaded scraping environment."""

from lxml.html import builder
from functools import partial
from urllib import request
from lxml import html

from scraping import objects

import os, time
import configparser
import queue
import multiprocessing
import urllib
import datetime
import threading

class InheritError(Exception):
    pass

class Scraper(object):
    """Base scraper object.

    Documentation:
     * TODO

     """
    def __init__(self, exporter, max_threads=5):
        """
        @type exporter: scraping.exporters.builtin.Exporter
        @param exporter: Exporter to use. Make sure this exporter is initialized.

        @type max_threads: integer
        @param max_threads: maximum amount of concurrent threads. Some scrapers (filesystem)
        may force this value to 1.
        """
        self.alive = False
        self.exporter = exporter

        self.commit_queue = queue.Queue(maxsize=5000)
        self.min_threads = threading.activeCount()
        self.max_threads = max_threads + self.min_threads

        self.start()

    def _wait(self, threads=None):
        threads = threads or self.max_threads
        while threading.activeCount() > threads:
            pass

    def _commit(self):
        """This function commits all documents/comments in commit_queue. To
        stop the loop, call `quit`."""
        while not self.commit_queue.empty() or self.alive:
            # Keep running until all articles are committed, despite not
            # being alive. 
            try:
                art = self.commit_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            self.exporter.commit(art)
            self.commit_queue.task_done()

    def _getContent(self, page):
        """_getContent is called in a seperate thread for each document object
        yielded by getPages"""
        page.prepare(self)   
             
        for page in self.getDocumentPages(page):
            page.prepare(self)
            
            doc = self.getDocument(page)
            self.commit_queue.put(doc)
            
            # Get comments
            comm = doc.copy(parent=doc)
            for c in self.getComments(comm):
                self.commit_queue.put(c)

    def start(self):
        """Start commit-loop"""
        self.alive = True

        target = partial(self._commit)
        self.commit_thread = threading.Thread(target=target)
        self.commit_thread.start()

    ### SCRAPE FUNCTIONS ###
    def getPages(self, date):
        """Get article index-pages.
        
        @type date: datetime.datetime object or None
        @param date: date to get pages for
        
        @return: an iterable containing instances of Article objects
        containing at least an url property. Objects are passed separately
        to getDocumentPages()."""
        raise InheritError("Scrapers must override this method.")
        
    def getDocumentPages(self, page):
        """Get article pages
        
        @type page: Document object
        @param page: Page containing an index with references to document-pages"""
        return [page,]
        
    def getDocument(self, page):
        """Get article texts.
        
        @type page: Document object
        @return: Document object or None"""
        raise InheritError("Scrapers must override this method.")
        
    def getComments(self, comment):
        """For each article returned, this function is triggered.
        
        @type comment: comment object
        @param comment: comment object based on document returned
        by getDocument."""
        return []

    ### PUBLIC FUNCTIONS ###
    def scrape(self, date=None):
        """Scrape all articles for `date`. If None, scraper should error or
        (preferably) fetch all available articles.
        
        Warning: function may quite before all documents are committed,
        though you're free to call this function again. Please call
        `quit` to make sure all is committed."""
        for p in self.getPages(date):
            self._wait()
            
            part = partial(self._getContent, p)
            threading.Thread(target=part).start()

    def quit(self, close_exporter=True):
        """Quit commit loop. *Must* be called after scraping.

        @type close_exporter: Boolean
        @param close_exporter: Wether or not to close the exporter. Defaults to True."""
        self._wait(self.min_threads+1)
        self.alive = False
        self.commit_thread.join()

        if close_exporter:
            self.exporter.close()

class HTTPScraper(Scraper):
    """HTTPScraper extends a normal scraper with some utilities for web scraping."""
    def __init__(self, exporter, max_threads=None):
        karg = dict() if not max_threads else dict(max_threads=max_threads)
        super(HTTPScraper, self).__init__(exporter, **karg)

        self.scraped_urls = []
        self.session = self._createSession()
        self.login()
        
    def _createSession(self):
        c = request.HTTPCookieProcessor()
        s = request.build_opener(c)
        request.install_opener(s)
                
        return s

    def _getContent(self, page):
        """This scraper fetches the contents of a webpage, and parses them using lxml."""
        if page.url in self.scraped_urls:
            return

        self.scraped_urls.append(page.url)
        super(HTTPScraper, self)._getContent(page)
    
    def login(self):
        """Alter session to hold login credentials"""
        pass

    def filter(self, docs, date):
        def todate(d):
            if type(d) == datetime.datetime:
                return d.date()
            return d

        if date:
            date = todate(date)
            for doc in docs:
                if todate(doc.date) > date:
                    continue
                elif todate(doc.date) == date:
                    yield doc
                else:
                    break
        else:
            for doc in docs: yield doc

    def get(self, url, read=True, lxml=True, encoding=None, log=True, attempt=0):
        """`get` makes three attempts to retrieve the given url.
        
        PS: Blame VK. """
        ht = 'Content-Type'

        def _getenc(ro):
            # Return charset (from HTTP-Headers). If not found, return None.
            headers = dict(ro.getheaders())
            if ht in headers:
                for arg in headers[ht].split(';'):
                    if arg.strip().startswith('charset='):
                        return arg.strip()[8:]
            return None

        try:
            fo = self.session.open(url)
            if not read:
                res = fo
            elif not lxml:
                res = fo.read()
            else:
                enc = encoding or _getenc(fo)
                if enc:
                    res = str(fo.read(), encoding=enc)
                    res = html.fromstring(res)
                else:
                    res = html.parse(fo).getroot()                        
            
            if log:
                print('Retrieved "%s"' % urllib.parse.unquote(url))
            return res

        except urllib.error.URLError as e:
            if attempt > 3:
                raise(e)

            time.sleep(1.5)
                
            return self.get(url, attempt=attempt+1, read=read, lxml=lxml)

class GoogleScraper(HTTPScraper):
    def __init__(self, exporter, max_threads=None, pages_per_search=100):
        super(GoogleScraper, self).__init__(exporter, max_threads=max_threads)

        # Initialize cookies
        self.get('http://www.google.nl')

        self.google_url = 'http://www.google.nl/search?'
        self.pps = pages_per_search

    def _createSession(self):
        s = super(GoogleScraper, self)._createSession()
        s.addheaders = [('User-agent', 'Mozilla/5.0')]
              
        return s

    def _genurl(self, term, site, page=0):
        q = term + ' site:%s' % site

        query = {
            'num' : self.pps,
            'hl' : 'nl',
            'btnG' : 'Zoeken',
            'q' : q,
            'start' : page * self.pps
        }

        return self.google_url + urllib.parse.urlencode(query)

    def formatTerm(self, date):
        pass

    def getPages(self, date, page=0):
        term = self.formatTerm(date)
        url = self._genurl(term, self.site, page)
        
        results = self.get(url).cssselect('h3.r > a.l')
        for a in results:
            d = objects.HTMLDocument()
            d.url = a.get('href')
            d.date = date

            yield d

        if len(results) == self.pps:
            for d in self.getPages(date, page=page+1):
                yield d