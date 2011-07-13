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

from scraping.processors import PCMScraper
from scraping.objects import HTMLDocument, IndexDocument
from scraping import toolkit as stoolkit

import re

SESSION_URL = "http://mgl.x-cago.net/session.do"

LOGINURL1 = "http://mgl.x-cago.net/login.do?pub=ddl&r=krantdigitaal.ddl.x-cago.net"
LOGINURL2 = "http://mgl.x-cago.net/login.do;jsessionid=%s"
LOGINURL3 = "http://mgl.x-cago.net/session.do"

INDEX_URL = "http://krantdigitaal.ddl.x-cago.net/DDL/%(year)d%(month)02d%(day)02d/public/index_editions_js.html"

POST_DATA = {
    'username' : 'nel@nelruigrok.nl',
    'email' : 'x6waDjy',
    "r" : "krantdigitaal.ddl.x-cago.net",
    "pub" : "dll"
}

try:
    from urllib import urlencode
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urlencode, urljoin


class LimburgerScraper(PCMScraper):
    def __init__(self, exporter, max_threads=None, editie='MA'):
        """
        @type editie: str
        @param editie: 'editie' to scrape:
         * HL: Heuvelland
         * HE: Heerlen
         * MA: Maastricht
         * SI: Sittard-Geleen
         * NL: Venray / Venlo
         * ML: Weert / Roermond
        """
        self.editie = editie

        super(LimburgerScraper, self).__init__(exporter, max_threads=max_threads)

    def login(self):
        page = self.session.open(LOGINURL1)
        info = str(page.info())
        sessionid = re.search("=([0-9A-F]+)", info).group(1)

        html = self.session.open(LOGINURL2 % sessionid, urlencode(POST_DATA)).read()
        if "Sessie overschrijven" in html:
            data = urlencode({'overwrite' : 'on', 'pub' : 'ddl'})
            self.session.open(LOGINURL3,data).read()

    def init(self, date):
        index = INDEX_URL % {
            'year' : date.year,
            'month' : date.month,
            'day' : date.day,
        }

        edition = "DDL_%s" % self.editie
        lines = list(self.getdoc(index, read=False).readlines())

        print(self.getdoc(index, read=False).read())

        print(lines)
        while True:
            line = lines.pop()
            print(line)
            if edition in line: #s.pop():
                lines.pop()
                break

        print(lines.pop())

        

        return []

    def get(self, ipage): # ipage --> index_page
        return ipage

    def get_article(self, page):
        return page

if __name__ == '__main__':
    import datetime
    from scraping.exporters.builtin import JSONExporter

    ex = JSONExporter('/tmp/spitsnieuws.json')
    sc = LimburgerScraper(ex, max_threads=8)
    sc.scrape(datetime.date(2011, 6, 14))