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
from scraping.objects import HTMLDocument
from scraping import toolkit as stoolkit

INDEX_URL = ""

class TemplateScraper(HTTPScraper):
    def __init__(self, exporter, max_threads=None):
        super(ExampleScraper, self).__init__(exporter, max_threads=max_threads)

    def init(self, date):
        return []

    def get(self, page):
        return []

if __name__ == '__main__':
    import datetime
    from scraping.exporters.builtin import JSONExporter

    ex = JSONExporter('/tmp/template.json')
    sc = TemplateScraperScraper(ex, max_threads=8)
    sc.scrape(datetime.date(2011, 6, 14))