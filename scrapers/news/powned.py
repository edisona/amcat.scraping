from __future__ import unicode_literals, print_function, absolute_import
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

"""Scraper for http://www.powned.tv/"""

from datetime import datetime

from scraping.objects import HTMLDocument
from scraping.exporters.builtin import JSONExporter
from scraping.processors import HTTPScraper

from urllib.parse import urljoin
from scraping import toolkit
from lxml.html import fromstring, tostring as _tostring

from lxml.builder import E as builder

tostring = lambda s: _tostring(s, encoding="ISO-8859-1")

class PownedScraper(HTTPScraper):
    def __init__(self, exporter, max_threads=10):
        super(PownedScraper, self).__init__(exporter=exporter, max_threads=max_threads)

        self.baseurl = 'http://www.powned.tv/'

        fp = self.get(self.baseurl)
        ip = fp.cssselect('#sidebar > a.buttonarrow')[0].get('href')

        self.indexpage = self.get(urljoin(self.baseurl, ip))

    def getAllPages(self):
        doc = self.indexpage.cssselect('#maincol-large')[0]

        for li in doc.cssselect('ul > li'):
            span, a = li.getchildren()

            url = a.get('href')

            if not url: continue

            year = url.split('/')[-3]
            day, month, time = span.text.split()
            date = toolkit.readDate(" ".join((day, month, year, time)))

            art = HTMLDocument()
            art.date, art.url, art.headline = (date, url, a.text)
            yield art

        prev = doc.cssselect('a.buttonarrow.left')
        if prev:
            self.indexpage = self.get(prev[0].get('href'))
            for p in self.getAllPages():
                yield p

    def getPages(self, date):
        pages = self.getAllPages()
        return pages if not date else toolkit.filter_arts(pages, date)

    def getDocument(self, art):
        art.doc = art.doc.cssselect('#maincol-med')[0]

        art.text = []
        art.text.append(builder.h1(art.doc.cssselect('.artikel-intro > p')[0].text))
        art.text.append(art.doc.cssselect('.artikel-main')[0])

        art.author = art.doc.cssselect('.author-date')[0].text.split('|')[0]

        return art

    def getComments(self, comm):
        for zwitsal in comm.doc.cssselect('span.baby'):
            # Delete all 'zwitsal'-images to ease processing below
            zwitsal.drop_tree()

        for div in comm.doc.cssselect('#comments .comment'):
            ca = comm.copy()

            ca.externalid = div.get('id')
            ca.text = div.getchildren()[:-1]

            footer = div.getchildren()[-1].text.split(' | ')
            ca.date = toolkit.readDate(",".join((footer[-3], footer[-2])))
            ca.author = " | ".join(footer[:-3])

            yield ca

    def getImages(self, art):
        return ()

if __name__ == '__main__':
    ex = JSONExporter(open('/home/martijn/PowNED.json', 'w'))

    sc = PownedScraper(ex)
    sc.scrape(None)
    sc.quit()