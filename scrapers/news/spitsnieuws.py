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

from datetime import datetime

from scraping.processors import HTTPScraper
from scraping.objects import HTMLDocument

class SpitsnieuwsScraper(HTTPScraper):
    def __init__(self, exporter, max_threads=None):
        super(SpitsnieuwsScraper, self).__init__(exporter, max_threads=max_threads)
        
        self.index_url = "http://www.spitsnieuws.nl/archives/%(year)s/%(month)02d/"
        
    def getPages(self, date):
        url = self.index_url % {'year' : date.year, 'month' : date.month}
        ulist = self.get(url).cssselect('#colprim ul')[0]
        for li in ulist.findall('li'):
            day = int(next(li.itertext())[:-2].split('-')[0])
            if day is not date.day:
                continue
            
            yield HTMLDocument(date=date,
                               url=li.find('a').get('href'),
                               headline=li.find('a').text)
        
    def _parseDate(self, date, time):
        day, month, year = map(int, date.split('-'))
        hour, minute = map(int, time.split(':'))
        year += 2000
        
        return datetime(year, month, day, hour, minute)
        
    def getDocument(self, ap):        
        art = ap.doc.cssselect('div.artikel')[0]
        
        footer = art.cssselect('.artikelfooter')[0].itertext()
        
        ap.author = next(footer)
        date, time = next(footer).split('|')[1:3]
        ap.date = self._parseDate(date, time)
        ap.text = art.findall('p')
        
        return ap
    
    def getComments(self, refcom):        
        for c in refcom.doc.cssselect('.reactie'):
            doc = refcom.copy()
            
            p = c.findall('p')
            footer = p[-1]
            doc.text = p[:-1]
            
            iter = footer.itertext()
            doc.author = next(iter)
            timedate = next(iter).strip() or next(iter)
            date, time = timedate.split('|')[1:3]
            
            doc.date = self._parseDate(date, time)
            
            yield doc

if __name__ == '__main__':
    from scraping.exporters.builtin import JSONExporter

    ex = JSONExporter('/tmp/spitsnieuws.json')
    sc = SpitsnieuwsScraper(ex, max_threads=8)
    sc.scrape(datetime(2011, 5, 5))
    sc.quit()