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

from amcat.scraping.document import Document, HTMLDocument
from amcat.scraping.htmltools import create_cc_cookies
from lxml import etree
from amcat.tools.toolkit import readDate
from urlparse import urljoin
from urllib2 import HTTPError


INDEX_URL = "http://www.ad.nl/ad/nl/1401/archief/integration/nmc/frameset/archive/archiveDay.dhtml?archiveDay={y:04d}{m:02d}{d:02d}"
REACT_URL = "http://www.ad.nl/ad/reaction/listContent.do?componentId={cid}&navigationItemId={nid}&language=nl&pageType=articleDetail&reactionLayout=small&page={page}"


from amcat.scraping.scraper import HTTPScraper,DatedScraper

class WebADScraper(HTTPScraper, DatedScraper):
    medium_name = "AD website"

    def __init__(self, *args, **kwargs):
        super(WebADScraper, self).__init__(*args, **kwargs)

    def _set_cookies(self):
        for cookie in create_cc_cookies(".ad.nl"):
            self.opener.cookiejar.set_cookie(cookie)

    def _get_units(self):
        self.set_cookies()        

        y = self.options['date'].year
        m = self.options['date'].month
        d = self.options['date'].day
        

        url = INDEX_URL.format(**locals())
        index = self.getdoc(url) 
        
        for unit in index.cssselect('dl dd'):
            href = unit.cssselect('a')[0].get('href')
            yield HTMLDocument(url=href, date=self.options['date'])
        
    def _scrape_unit(self, page): 
        try:
            page.prepare(self)
        except HTTPError:
            return
        page.doc = self.getdoc(page.props.url)
        for comment in self.get_comments(page):
            yield comment
        try:
            article = self.get_article(page)
        except IndexError:
            pass
        else:
            yield article
        

    def get_article(self, page):
        try:
            page.props.author = etree.tostring(page.doc.cssselect("span.author")[0]).split("<br>")[0].split(":")[1].strip()
        except IndexError:
            page.props.author = "onbekend"
        try:
            page.props.headline = page.doc.cssselect("#articleDetailTitle")[0].text
        except IndexError:
            return
        page.props.text = page.doc.cssselect("section#detail_content")[0].text_content() 
        page.props.date = readDate(etree.tostring(page.doc.cssselect("span.author")[0]).split("<br/>")[1])
        
        


        return page

    def get_comments(self,page):
        for doc in self.get_reactions_pages(page):
            for li in doc.cssselect("ul li"):
                comment = Document()
                comment.props.author = li.cssselect("cite")[0].text.strip()
                comment.props.text = li.cssselect("blockquote")[0].text_content().strip()
                comment.props.date = readDate(li.cssselect("span.time")[0].text)
                comment.parent = page
                yield comment



    def get_reactions_pages(self,page):
        if not page.doc.cssselect("#reaction"):
            return
        split = page.props.url.split("/")
        c_id = split[9]
        n_id = split[5]
        firstpage = REACT_URL.format(page=0,cid=c_id,nid=n_id)
        print(firstpage)
        try:
            doc = self.getdoc(firstpage)
        except HTTPError:
            return
        try:
            total = int(doc.cssselect("div.pagenav")[0].text.split(" van ")[1])
        except IndexError:
            yield doc;return
        except AttributeError: #no comments, page is nonetype
            return
        for x in range(total-1):
            for a in doc.cssselect("div.pagenav a"):
                if "volgende" in a.text:
                    onclick = a.get('onclick')
            start=onclick.find("getReactions(")+13;end=onclick.find(")",start)
            args = [arg.strip("\"';() ") for arg in onclick[start:end].split(",")]
            href = args[0]
            url = urljoin("http://www.ad.nl/",href)
            print(url)
            yield self.getdoc(url)


if __name__ == '__main__':
    from amcat.scripts.tools import cli
    from amcat.tools import amcatlogging
    amcatlogging.debug_module("amcat.scraping.scraper")
    amcatlogging.debug_module("amcat.scraping.document")
    cli.run_cli(WebADScraper)


