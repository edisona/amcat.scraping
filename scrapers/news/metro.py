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

from scraping.processors import GoogleScraper
from scraping.objects import HTMLDocument
from scraping import toolkit as stoolkit

import datetime

TERM = '"Geplaatst %(year)s-%(month)02d-%(day)02d"'

class MetroScraper(GoogleScraper):
    def __init__(self, exporter, max_threads=None):
        super(MetroScraper, self).__init__(exporter, max_threads, domain='metronieuws.nl')

    def formatterm(self, date):
        return TERM % dict(year=date.year, month=date.month, day=date.day)

    def get(self, page):
        if '.xml' in page.props.url:
            pass
        else:
            page.props.section = page.props.url.split('/')[-4]

            go = page.doc.cssselect('#date')[0].text.split()
            date, time = go[-3], go[-1]

            hour, minute = map(int, time.split(':'))
            year, month, day = map(int, date.split('-'))

            page.props.headline = page.doc.cssselect('title')[0].text[:-10]
            page.props.text = page.doc.cssselect('.article-paragraph')

            date = datetime.datetime(year, month, day, hour, minute)
            if stoolkit.todate(date) == stoolkit.todate(page.props.date):
                page.props.date = date

                try:
                    page.props.author = page.doc.cssselect('.name')[0].text
                except IndexError:
                    pass

                yield page

if __name__ == '__main__':
    import datetime
    from scraping.exporters.builtin import JSONExporter

    ex = JSONExporter('/tmp/metro.json')
    sc = MetroScraper(ex, max_threads=8)
    sc.scrape(datetime.date(2011, 6, 14))