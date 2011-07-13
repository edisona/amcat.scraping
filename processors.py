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
from BaseScraper, which provides an multithreaded scraping environment.

Tested on:
 * Python 2.6
 * Python 2.7
 * Python 3.1
 * Python 3.2
 """

from lxml.html import builder
from functools import partial
from lxml import html

try:
    from urllib import request
    from urllib.error import URLError
    from urllib.parse import unquote, urlencode, urljoin
except ImportError:
    import urllib2 as request
    from urllib2 import URLError
    from urllib import unquote
    from urllib import urlencode
    from urlparse import urljoin

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

try:
    import queue
except ImportError:
    import Queue as queue

from scraping import objects
from scraping import toolkit

import os, time, sys
import datetime
import threading
import traceback

__all__ = ['Scraper',]

class InheritError(Exception):
    pass

class Worker(object):
    """Workers consume work in the scrapers' work-queue. Each document yielded by
    scraper.get will result in a documment added to the document_queue.

    All items in the document-queue are consumed by the commit-thread."""

    def __init__(self, scraper):
        self.alive = True
        self.scraper = scraper
        self.queue = self.scraper.work_queue

        self.thread = threading.Thread(target=self.main)
        self.thread.start()

    def main(self):
        """For each document placed in scraper.work_queue by scrape(), pass it to
        get() and iterate over the results to put them in the document-queue."""
        while self.alive or not self.queue.empty():
            try:
                work = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                work.prepare(self.scraper)
            except:
                traceback.print_exc(file=sys.stdout)
            else:
                try:
                    for doc in self.scraper.get(work):
                        self.scraper.document_queue.put(doc)
                except Exception as e:
                    self.queue.task_done()
                    traceback.print_exc(file=sys.stdout)
                    sys.exit(1)

            self.queue.task_done()

    def quit(self):
        """End the workers' main loop. A worker only quits when the work-queue is empty"""
        self.alive = False
        self.thread.join()

class Scraper(object):
    """Base scraper object. 

    Documentation:
     * TODO"""
    def __init__(self, exporter, threads=None):
        """
        @type exporter: scraping.exporters.builtin.Exporter
        @param exporter: Exporter to use. Make sure this exporter is initialized.

        @type max_threads: integer
        @param max_threads: maximum amount of concurrent threads. Some scrapers (filesystem)
        may force this value to 1.
        """
        self.alive = True
        self.exporter = exporter

        self.work_queue = queue.Queue(maxsize=80)
        self.document_queue = queue.Queue(maxsize=5000)

        self.workers = []
        for i in range(threads or 5):
            w = Worker(self)
            self.workers.append(w)

        self.commit_thread = threading.Thread(target=self._commit)
        self.commit_thread.start()

    def _commit(self):
        """This function commits all documents in document_queue. To
        stop the loop, call `quit`."""
        while not self.document_queue.empty() or self.alive:
            # Keep running until all documents are committed, despite not
            # being alive. 
            try:
                doc = self.document_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            self.exporter.commit(doc)
            self.document_queue.task_done()

    ### SCRAPER FUNCTIONS ###
    def init(self, date):
        return []

    def get(self, doc):
        return []

    ### PUBLIC FUNCTIONS ###
    def scrape(self, auto_quit=True, **kwargs):
        """Scrape for a certain date. Scrapers may support date=None.

        @type auto_quit: Boolean
        @param auto_quit: Automatically quit when done with this date

        @param kwargs: arguments to pass to scraper.init"""
        try:
            for work in self.init(**kwargs):
                if not isinstance(work, objects.Document):
                    raise(ValueError("init() should yield a Document-object not %s" % type(work)))
                self.work_queue.put(work)
        except Exception as e:
            traceback.print_exc(file=sys.stdout)

        if auto_quit: self.quit()

    def quit(self, close_exporter=True):
        """Quit commit loop. *Must* be called after scraping.

        @type close_exporter: Boolean
        @param close_exporter: Wether or not to close the exporter. Defaults to True."""
        for worker in self.workers:
            worker.quit()

        self.alive = False
        self.commit_thread.join()
        if close_exporter:
            self.exporter.close()

class HTTPScraper(Scraper):
    def __init__(self, exporter, max_threads=None):
        super(HTTPScraper, self).__init__(exporter, max_threads)

        # Create session
        c = request.HTTPCookieProcessor()
        s = request.build_opener(c)
        request.install_opener(s)

        self.session = s

        try:
            self.login()
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            self.quit()

    def login(self):
        pass

    def getdoc(self, url, read=True, lxml=True, encoding=None, attempts=3):
        """Fetch a document from `url`. This method tries to determine the encoding of the document
        by looking at the HTTP headers. If those are missing, it leaves lxml to decide the
        encoding. 

        Furthermore, it tries three times to fetch the url before raising an error.

        @type url: str / unicode
        @param url: url to fetch

        @type read: boolean
        @param read: if False, return file-like object

        @type lxml: boolean
        @param lxml: if False, return bytes only

        @type encoding: boolean
        @param encoding: force an encoding of the document

        @type attempts: integer
        @param attempts: bail out after n tries"""
        def _getenc(ro):
            """Return charset (from HTTP-Headers). If not found, return None."""
            ht = 'Content-Type'

            headers = dict(ro.getheaders()) if hasattr(ro, 'getheaders') else dict(ro.headers)
            if ht in headers:
                for arg in headers[ht].split(';'):
                    if arg.strip().startswith('charset='):
                        return arg.strip()[8]

        print('Retrieving "%s"' % unquote(url))
        for i in range(attempts):
            try:
                fo = self.session.open(url)
                if not read:
                    return fo
                elif not lxml:
                    return fo.read()

                enc = encoding or _getenc(fo)
                if enc is not None:
                    # Encoding found or forced!
                    res = str(fo.read(), encoding=enc)
                    return html.fromstring(res)
                else:
                    # Let lxml decide the encoding
                    return html.parse(fo).getroot()
            except URLError as e:
                if (i+1 < attempts):
                    time.sleep(1.5)
                    continue
                else:
                    raise(e)

class PCMScraper(HTTPScraper):
    """Scraper for PCM Newspapers"""
    def login(self):
        doc = self.getdoc(self.login_url)
        frm = toolkit.parse_form(doc.cssselect('form')[0])
        frm.update(self.login_data)

        return self.session.open(self.login_url, urlencode(frm)).read()

class CommentScraper(Scraper):
    """A CommentScraper replaces `get` with `main` and `comments`."""
    def get(self, date):
        for doc in self.main(date):
            yield doc

            com = doc.copy(parent=doc)
            for c in self.comments(com):
                yield c

    def main(self, date):
        return []

    def comments(self, com):
        return []

class GoogleScraper(HTTPScraper):
    """Some websites don't have archives. Google enables us to search for those pages."""
    def __init__(self, exporter, max_threads=None, domain=None, pps=100):
        """
        @type domain: str
        @param domain: domain to limit search to

        @type pps: int
        @param pps: pages per search"""
        super(GoogleScraper, self).__init__(exporter, max_threads)

        self.session.addheaders = [('User-agent', 'Mozilla/5.0')]
        self.google_url = 'http://www.google.nl/search?'
        self.domain = domain
        self.pps = pps

        # Init cookies
        self.getdoc(self.google_url)

    def _genurl(self, term, page=0):
        q = term + ' site:%s' % self.domain if self.domain else term

        query = {
            'num' : self.pps,
            'hl' : 'nl',
            'btnG' : 'Zoeken',
            'q' : q,
            'start' : page * self.pps
        }

        return self.google_url + urlencode(query)

    def formatterm(self, date):
        return None

    def init(self, date, page=0):
        term = self.formatterm(date)
        url = self._genurl(term, page)

        results = self.getdoc(url).cssselect('h3.r > a.l')
        for a in results:
            url = a.get('href')
            yield objects.HTMLDocument(url=url, date=date)

        if len(results) == self.pps:
            for d in self.init(date, page=page+1):
                yield d