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

from scraping.processors import GoogleScraper
from scraping.objects import HTMLDocument
from scraping.exporters.builtin import JSONExporter
from scraping import toolkit

from lxml import html

MONTHS = ('januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli',
          'augustus', 'september', 'oktober', 'november', 'december')

class NuScraper(GoogleScraper):
    term = '"Uitgegeven" AND "%(day)d %(month)s %(year)d"'
    site = 'nu.nl'

    def __init__(self, exporter, max_threads=None):
        term = '"Uitgegeven" AND "%(day)d %(month)s %(year)d"'
        super(NuScraper, self).__init__(exporter, max_threads)

    def formatTerm(self, date):
        return self.term % dict(day=date.day, month=MONTHS[date.month-1], year=date.year)

    def getDocumentPages(self, ap):
        # Filter on date. Google scrapers tend to be not accurate enough
        date = toolkit.readDate(ap.doc.cssselect("#datestamp td")[1].text)

        if toolkit.todate(date) == toolkit.todate(ap.date):
            ap.date = date
            return (ap,)
        return ()

    def getAllCommentPages(self, url):
        page = self.get(url, read=False, lxml=False)
        url = page.url
        if 'nieuw-reactie' not in url:
            doc = html.fromstring(str(page.read())).cssselect('div.pages')
            ppp = 200

            if not len(doc):
                pass
            elif doc[0].getchildren():
                lpage = 1
                for a in doc[0].cssselect('a'):
                    urlbase, start = a.get('href').split('=')
                    lpage = int(start) if int(start) > lpage else lpage

                for i in range(((lpage+ppp)//ppp)+1):
                    yield '{url}?pageStart={start}#{page}'.format(url=url, start=(i*ppp)+1, page=i)
            else:
                yield url
        
    def getDocument(self, art):
        art.text = doc = art.doc.cssselect('#leadarticle')[0]

        try:
            art.section = art._doc.cssselect('li.selected > a')[0].text
        except:
            art.section = 'Onbekend'

        art.medium = 231
        art.headline = doc.cssselect('h1')[0].text.strip()
        doc.cssselect('#datestamp')[0].drop_tree()
        doc.cssselect('h1')[0].drop_tree()

        try:
            doc.cssselect('#photo')[0].drop_tree()
            doc.cssselect('#artalso')[0].drop_tree()
        except IndexError:
            pass

        return art
        
    def getComments(self, art):
        nujij = art.doc.cssselect('#nujij-container > a')
        if not nujij:
            nujij = art.doc.cssselect('.jij > a')

        if not nujij:
            nujij = art.doc.cssselect('a.nujij')

        if not nujij:
            iframe = art.doc.cssselect('iframe.NUjijButton')
            if iframe:
                apidoc = self.get(iframe[0].get('src').replace("&amp;", '&'), log=False)
                nujij = apidoc.cssselect('a')

        if nujij:
            url = nujij[0].get('href')
            
            for url in self.getAllCommentPages(url):
                doc = self.get(url).cssselect('ol.reacties')

                if len(doc):
                    for li in doc[0].cssselect('.reacties > li'):
                        if li.get('class') == 'ad-reactie':
                            continue

                        ca = art.copy()
                        ca.medium = 257
                        ca.url = url

                        try:
                            ca.date = toolkit.readDate(li.cssselect('.tijdsverschil')[0].text)
                            ca.author = li.cssselect('strong')[0].text_content().strip()
                        except IndexError:
                            continue

                        try:
                            ca.text = li.find_class('reactie-body')[0]
                        except IndexError:
                            ca.text = '[Reactie verborgen]'

                        yield ca

if __name__ == '__main__':
    from datetime import date

    ex = JSONExporter(open('/home/martijn/nu.json', 'w'))
    sc = NuScraper(ex)

    for i in range(3, 20):
        sc.scrape(date(2011, 5, i))
    sc.quit()