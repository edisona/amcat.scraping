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

import datetime

from scraping.processors import HTTPScraper
from scraping.objects import HTMLDocument
from scraping.exporters.builtin import JSONExporter
from scraping import toolkit

from lxml import html
from urllib import request, parse

class DGroupsScraper(HTTPScraper):
    def __init__(self, exporter, section, group, max_threads=None):
        """
        @type thread: str
        @param thread: group name
        """
        self.baseurl = "http://dgroups.org/"
        self.loginurl = "http://dgroups.org/login"
        self.groupurl = "http://dgroups.org/{section}/{group}".format(**locals())
        self.disuscurl = None # set in getPages

        super(DGroupsScraper, self).__init__(exporter, max_threads)

    def login(self):
        data = dict(username='jferguson@feweb.vu.nl', password='fergie1')
        self.session.open(self.loginurl, parse.urlencode(data).encode('utf-8'))

    def getAllPages(self, nr=1):
        page = self.get(self.discusurl + '&page=%d' % nr)

        try:
            maxi = int(page.cssselect("#ctl00_rightcolumn_pagingControl_lblPageCount")[0].text)
        except IndexError:
            # Try again..
            maxi = nr + 1
            nr = nr - 1
        else:
            for a in page.cssselect('table > tr > td > a'):
                yield parse.urljoin(self.baseurl, a.get('href'))

        nr+=1
        if maxi >= nr:
            print(maxi)
            for p in self.getAllPages(nr):
                yield p
        
    def getPages(self, date):
        doc = self.get(self.groupurl)

        a = doc.cssselect('.toolbar a')[4]
        self.discusurl = parse.urljoin(self.baseurl, a.get('href'))
        pages = self.getAllPages()

        for p in pages:
            d = HTMLDocument()
            d.url = p
            yield d
            
    def getDocument(self, ap, post=None):
        if post is None:
            try:
                post = ap.doc.cssselect('.post')[0]
            except IndexError:
                ap.doc = self.get(ap.url)
                return self.getDocument(ap)

        info = post.cssselect('.secondary-info')[0].itertext()
        datestr = " ".join(next(info).strip().split(' ')[1:4])

        if 'yesterday' in datestr:
            date = datetime.date.today() - datetime.timedelta(1)
        elif 'today' in datestr:
            date = datetime.date.today()
        else:
            ap.date = toolkit.readDate(datestr)

        ap.author = tmp = next(info)
        ap.text = post.cssselect('p')[0]
        ap.headline = ap.doc.cssselect('h2')[1].text.strip()

        return ap
        
    def getComments(self, comm):
        for post in comm.doc.cssselect('.post')[1:]:
            ca = comm.copy()
            yield self.getDocument(ca, post=post)

if __name__ == '__main__':
    ex = JSONExporter(open('/tmp/worldbank-gatnet.json', 'w'))
    sc = DGroupsScraper(ex, 'worldbank', 'GATNET', max_threads=2)

    sc.scrape(None)

    sc.quit()