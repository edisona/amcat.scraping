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

from datetime import date, datetime

from scraping.processors import HTTPScraper
from scraping.objects import HTMLDocument
from scraping.exporters.builtin import JSONExporter

from lxml import html

class GeenstijlScraper(HTTPScraper):
    def __init__(self, exporter, max_threads=None):
        super(GeenstijlScraper, self).__init__(exporter, max_threads)
        
        self.index = self.get("http://www.geenstijl.nl/archief.html")
        self.medium = 242

    def getAllPages(self):
        for mo in self.index.cssselect('#colprim > ul:last-child > li > a'):
            for li in self.get(mo.get('href')).cssselect('#colprim .content li'):
                d,m,y = map(int, next(li.itertext()).split('-'))

                doc = HTMLDocument()
                doc.url = next(li.iterchildren()).get('href')
                doc.date = date(y+2000, m, d)

                yield doc
        
    def getPages(self, date):
        return self.filter(self.getAllPages(), date)
            
    def getDocument(self, ap):
        art = ap.doc.cssselect('#content article')[0]

        try:
            art.cssselect('img')[0].drop_tree()
        except IndexError:
            pass

        ap.headline = next(art.iterchildren()).text_content()
        ap.text = art.cssselect('p')

        footer = art.find('footer')
        ap.author = next(footer.itertext()).split('|')[0]
        date, time = footer.find('time').get('datetime').split('T')

        year, month, day = map(int, date.split('-'))
        hour, minute = map(int, time.split(':'))
        ap.date = datetime(year, month, day, hour, minute)
        
        return ap
        
    def getComments(self, comm):
        for c in comm.doc.cssselect('#comments > article'):
            ca = comm.copy()

            ca.text = c.findall('p')
            footer = "".join([t for t in c.find('footer').itertext()]).split(' | ')
            ca.author, date, time = footer[:-2], footer[-2], footer[-1]
            ca.author = " | ".join(ca.author)

            day, month, year = map(int, date.split('-'))
            hour, minute = map(int, time.split(':'))
            year += 2000
            
            ca.date = datetime(year, month, day, hour, minute)
                                                
            yield ca
                
if __name__ == '__main__':
    from datetime import date

    fo = open('/home/martijn/Geenstijl.json', 'w')
    ex = JSONExporter(fo)

    s = GeenstijlScraper(ex)
    s.scrape(date(2011, 6, 12))
    s.quit()

