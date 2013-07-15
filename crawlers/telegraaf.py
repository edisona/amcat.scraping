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

from amcat.scraping.crawler import Crawler
from amcat.scraping.document import HTMLDocument
from amcat.tools.toolkit import readDate
from scraping.newssites.telegraaf import scrape_unit
import re


class TelegraafCrawler(Crawler):
    medium_name = "telegraaf.nl"
    initial_url = "http://www.telegraaf.nl"
    include_patterns = [
        re.compile("http://www.telegraaf.nl"),
        ]
    deny_patterns = [
        re.compile("/wuz/")
        ]


    def article_url(self, url):
        pattern = re.compile("/\d+/__[a-zA-Z0-9_]+__.html")
        if pattern.search(url):
            return True
        else:
            return False


    def _scrape_unit(self, urldoc):
        url = urldoc[0]
        page = HTMLDocument(url = urldoc[0])
        page.prepare(self)
        for unit in scrape_unit(self, page):
            yield unit
        
if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.debug_module("amcat.scraping.crawler")
    amcatlogging.debug_module("amcat.scraping.scraper")
    amcatlogging.debug_module("amcat.scraping.document")
    cli.run_cli(TelegraafCrawler)

