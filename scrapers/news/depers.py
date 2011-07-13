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

from amcat.tools import toolkit

import datetime
from lxml import html

DAYS = ('maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag')
MONTHS = ('januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus',
          'september', 'oktober', 'november', 'december')

TERM = '"Gepubliceerd: %(dayname)s %(day)d %(month)s %(year)d"'

class DePersScraper(GoogleScraper):
    def __init__(self, exporter, max_threads=None):
        super(DePersScraper, self).__init__(exporter, max_threads, domain='depers.nl')

    def formatterm(self, date):
        return TERM % {
            'dayname' : DAYS[date.isoweekday() - 1],
            'day' : date.day,
            'month' : MONTHS[date.month - 1],
            'year' : date.year
        }

    def get(self, page):
        p = page.doc.cssselect('p.datum_nieuws')[0]
        p.drop_tree()

        info = html.tostring(p).split('<br>')
        if len(info) == 3:
            # Author available
            page.props.author = html.fromstring(info[0]).text.strip()[6:]
            page.props.date = toolkit.readDate(info[1].strip()[14:])
        else:
            page.props.date = toolkit.readDate(p.text.strip()[14:])

        page.props.text = page.doc.cssselect('.lbox440')[0]
        page.props.headline = page.doc.cssselect('h1')[0].text

        yield page

if __name__ == '__main__':
    from scraping.exporters.builtin import JSONExporter

    ex = JSONExporter('/tmp/template.json')
    sc = DePersScraper(ex, max_threads=8)
    sc.scrape(datetime.date(2011, 5, 14))