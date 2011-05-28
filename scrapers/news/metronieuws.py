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
from scraping.processors import GoogleScraper

class MetronieuwsScraper(GoogleScraper):
    site = 'metronieuws.nl'

    def formatTerm(self, date):
        t = '"Geplaatst %(year)s-%(month)02d-%(day)02d"'
        return t % dict(year=date.year, month=date.month, day=date.day)
        
    def getDocument(self, page):
        if '.xml' in page.url: return

        page.section = page.url.split('/')[-4]
        
        go = page.doc.cssselect('#date')[0].text.split()
        date, time = go[-3], go[-1]
        
        hour, minute = map(int, time.split(':'))
        year, month, day = map(int, date.split('-'))
        
        page.date = datetime(year, month, day, hour, minute)
        page.headline = page.doc.cssselect('title')[0].text[:-10]
        page.text = page.doc.cssselect('.article-paragraph')
        
        try:
            page.author = page.doc.cssselect('.name')[0].text
        except IndexError:
            pass
        
        return page
        
if __name__ == '__main__':
    from scraping.exporters.builtin import JSONExporter

    ex = JSONExporter('/tmp/metronieuws.json')
    sc = MetronieuwsScraper(ex, max_threads=8)
    sc.scrape(datetime(2011, 5, 5))
    sc.quit()