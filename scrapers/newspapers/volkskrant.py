# -*- coding: utf-8 -*-
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

from scraping.processors import HTTPScraper
from scraping.objects import HTMLDocument, IndexDocument
from scraping import toolkit as stoolkit

LOGIN_URL = "https://caps.volkskrant.nl/service/login"
INDEX_URL = "http://www.volkskrant.nl/vk-online/VK/%(year)d%(month)02d%(day)02d___/VKN01_001/"

POST_DATA = {
    'username' : 'nruigrok@hotmail.com',
    'password' : '5ut5jujr'
}

try:
    from urllib import urlencode
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urlencode, urljoin


class VolkskrantScraper(HTTPScraper):
    def __init__(self, exporter, max_threads=None):
        super(VolkskrantScraper, self).__init__(exporter, max_threads=1)

    def login(self):
        doc = self.getdoc(LOGIN_URL)
        frm = stoolkit.parse_form(doc.cssselect('form')[0])
        frm.update(POST_DATA)

        self.session.open(LOGIN_URL, urlencode(frm)).read()

    def init(self, date):
        index = INDEX_URL % dict(year=date.year, month=date.month, day=date.day)

        doc = self.getdoc(index)
        for opt in doc.cssselect('#select_page_top optgroup > option'):
            url = urljoin(index, '../%s' % opt.get('value')) + '/'
            
            if 'VKN01' in url:
                # We're not interested in the newspaper-attachments (sports, etc.)
                yield IndexDocument(url=url)

    def get(self, ipage): # ipage --> index_page
        ipage.bytes = self.getdoc(urljoin(ipage.props.url, './page.jpg'), lxml=False)
        ipage.page = ipage.props.url.split('_')[-1].strip('/')

        doc = self.getdoc(ipage.props.url)
        for art in doc.cssselect('#articles > area'):
            page = HTMLDocument()

            # Getting coordinates
            page.coords = []
            for div in doc.cssselect('div.%s' % art.get('class')):
                coord = stoolkit.parse_coord(div.get('style'))
                page.coords.append(coord)

            page.props.url = urljoin(ipage.props.url, art.get('class') + '.html')
            page.prepare(self)

            # Try two times.
            try:
                yield self.get_article(page)
            except:
                yield self.get_article(page)

            ipage.addchild(page)

        yield ipage

    def get_article(self, page):        
        rurl = page.doc.getchildren()[1].getchildren()[0].get('src')
        aurl = urljoin(page.props.url, rurl).replace('header', 'text')
        doc = self.getdoc(aurl).cssselect('#article')[0]

        page.props.headline = doc.cssselect('h1')[0].text
        page.props.text = doc.cssselect('.body > p')

        return page

if __name__ == '__main__':
    import datetime
    from scraping.exporters.builtin import JSONExporter

    ex = JSONExporter('/tmp/spitsnieuws.json')
    sc = VolkskrantScraper(ex, max_threads=2)
    sc.scrape(datetime.date(2011, 6, 14))