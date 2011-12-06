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

from amcatscraping.processors import Scraper, Form
from amcatscraping.objects import Document

from amcat.tools import toolkit
from amcat.model.medium import Medium

from django import forms

import threading, Queue

import pycurl, json, urllib

STREAM_URL = "https://stream.twitter.com/1/statuses/filter.json"
USER = "floorter"
PASS = ""

class TwitterForm(Form):
    track = forms.CharField(max_length=8192, required=False)
    follow = forms.CharField(max_length=8192, required=False)

class TwitterScraper(Scraper):
    """ Get tweets frmo the twitter streaming api """
    options_form = TwitterForm
    try:
        medium = Medium.objects.get(name="Twitter")
    except:
        medium = Medium(name="Twitter", language_id=4) #lang=?
        medium.save()

    def __init__(self, options):
        super(TwitterScraper, self).__init__(options)
	self.json_queue = Queue.Queue()

    def listen(self):
        self.conn = pycurl.Curl()
        self.conn.setopt(pycurl.USERPWD, "%s:%s" % (USER, PASS))
        post = {}
        if self.options['track']:
            post['track'] = self.options['track']
        if self.options['follow']:
            post['follow'] = self.options['follow']
        self.conn.setopt(pycurl.POSTFIELDS, urllib.urlencode(post))
        self.conn.setopt(pycurl.URL, STREAM_URL)
        self.conn.setopt(pycurl.WRITEFUNCTION, self.receive)
        conn.perform()
    
    def recieve(self, data):
        if data.strip(): # Ignore keepalive empty lines
            data = json.loads(data)
            self.json_queue.put(data)

    def init(self):
	thread = threading.Thread(self.listen)
	thread.start()
        while True:
            yield Document(data=self.json_queue.get(True))

    def get(doc):
        doc.props.text = doc.data['text']
        doc.props.author = "%s (@%S)" % \
            (doc.data['user']['name'], doc.data['user']['screen_name'])
        doc.props.date = toolkit.readDate(doc.data['created_at'])
	yield doc
	




if __name__ == '__main__':
    from amcat.scripts.tools import cli
    cli.run_cli(TwitterScraper)
