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

INDEX_URL = "http://www.spitsnieuws.nl/archives/%(year)s%(month)02d/"

from scraping.processors import HTTPScraper, CommentScraper
from scraping.objects import HTMLDocument

from amcat.tools import toolkit
from scraping import toolkit as stoolkit

from lxml.html import tostring

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

class SpitsnieuwsScraper(HTTPScraper, CommentScraper):
    def __init__(self, exporter, max_threads=None):
        super(SpitsnieuwsScraper, self).__init__(exporter, max_threads=max_threads)

    def init(self, date):
        """
        @type date: datetime.date, datetime.datetime
        @param date: date to scrape for.
        """
        url = INDEX_URL % dict(year=date.year, month=date.month)
        
        for li in self.getdoc(url).cssselect('.ltMainContainer ul li.views-row'):
            docdate = toolkit.readDate(li.text.strip('\n\r •:')).date()
            if docdate == stoolkit.todate(date):
                href = li.cssselect('a')[0].get('href')
                href = urljoin(INDEX_URL, href)

                yield HTMLDocument(url=href)

    def main(self, doc):
        doc.props.headline = doc.doc.cssselect('h2.title')[0].text
        doc.props.text = doc.doc.cssselect('div.mainArticleContainer .content p')

        footer = doc.doc.cssselect('p.ltLink.fltlft')[0].text.split('|')
        doc.props.author = footer[0].strip()
        doc.props.date = toolkit.readDate(" ".join(footer[1:3]))

        yield doc

    def comments(self, doc):
        lis = doc.doc.cssselect('ul.reactiesList.fltlft > li')

        for li in lis:
            comm = doc.copy()
            comm.props.text = li.cssselect('p')[:-1]

            footer = li.cssselect('li > p')[-1].text_content().strip().split('|')
            comm.props.date = toolkit.readDate(" ".join(footer[-3:-1]))
            comm.props.author = "|".join(footer[:-3]).strip()

            yield comm

if __name__ == '__main__':
    from scraping.manager import main
    
    main(SpitsnieuwsScraper)