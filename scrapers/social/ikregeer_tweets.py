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

INDEX_URL = "http://ikregeer.nl/personen/"

from scraping.processors import HTTPScraper, CommentScraper, Form
from scraping.objects import HTMLDocument

from amcat.tools import toolkit
from amcat.model.medium import Medium

from urlparse import urljoin

from pprint import pprint
from lxml import etree

class IkRegeerTwitterForm(Form):
    #date = forms.DateField()
    pass

class IkRegeerTwitterScraper(HTTPScraper, CommentScraper):
    """ Scrape the tweets from ikregeer.nl."""
    options_form = IkRegeerTwitterForm
    try:
        medium = Medium.objects.get(name="Ikregeer - tweets")
    except:
        medium = Medium(name="Ikregeer - tweets", language_id=4) #lang=nl
        medium.save()

    def __init__(self, options):
        super(IkRegeerTwitterScraper, self).__init__(options)

    def get_politicians(self):
        """ Yields the urls to all the pages contianing the politicians.
        """
        doc = self.getdoc(INDEX_URL)
        for link in doc.cssselect("h2.entry-title a"):
            yield urljoin(INDEX_URL, link.get("href"))

    def init(self):
        for url in self.get_politicians():
            page = 1
            done = False
            while not done:
                doc = self.getdoc(url+"?view=tweets&page=%d" % (page))
                pprint(url+"?view=tweets?page=%d" % (page))
                yield HTMLDocument(url=url+"?view=tweets&page=%d"%(page))
                if doc.cssselect("a#pg-next"): 
                    # If page has a "next page" button: continue with
                    # the next page.
                    page += 1
                else:
                    done = True

    def main(self, doc):
        #print(etree.tostring(doc.doc))
        for tweet in doc.doc.cssselect("div.post-container.clearfix"):
            copy = doc.copy()
            #pprint(etree.tostring(tweet))
            if not tweet.cssselect("div.entry-summary"):
                pprint("SKIPPING!")
                continue
            copy.props.headline = "" # No headline
            copy.props.text = tweet.cssselect("div.entry-summary")[0].text
            copy.props.author = tweet.cssselect("h2.entry-title")[0].text
            copy.props.date = toolkit.readDate(
                tweet.cssselect("div.entry-meta.entry-header")[0].text)
            yield copy

if __name__ == '__main__':
    from amcat.scripts import cli
    cli.run_cli(IkRegeerTwitterScraper)
