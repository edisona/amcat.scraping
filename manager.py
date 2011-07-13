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

"""This module contains a function called `main`. Every scraper should
call this function in its `if __name__ == '__main__'`.

Furthermore, it contains tools for bin/manage.py"""

from amcat.tools import toolkit
from scraping import exporters

import sys
import inspect
import re
import datetime
import argparse

TYPE_MAP = {
    # For parse_doc
    'datetime.date' : datetime.date,
    'datetime.datetime' : datetime.datetime,
    'int' : int,
    'integer' : int,
    'str' : str,
    'unicode' : unicode,
    'basestring' : str,
    'string' : str
}

EXPORTER_MAP = {
    'json' : (exporters.builtin.JSONExporter, ('io',)),
    'dummy' : (exporters.builtin.Exporter, ())
}

CONVERTER_MAP = {
    datetime.date : toolkit.readDate,
    datetime.datetime : toolkit.readDate
}

DOC_RE = re.compile('@(type|param) (\w+): (.+)')
def parse_doc(func):
    """Parse a doc-string.

    @return: { u'argument' : {
                   u'type' : (type,),
                   u'param' : 'help text' }
    """
    lines = [DOC_RE.search(line) for line in func.__doc__.split("\n")]

    opts = {}
    for line in (l for l in lines if l):
        typ, arg, text = line.groups()

        if arg not in opts:
            opts[arg] = dict()

        if typ == 'type':
            opts[arg]['type'] = tuple(TYPE_MAP[t.strip()] for t in text.split(','))
            opts[arg]['type_raw'] = text
        else:
            opts[arg][typ] = text

    return opts

def main(scraper):
    """This function is called in a scraper file to provide an automatically build
    command-line interface for it."""
    doc = parse_doc(scraper.init)

    # Add keyword arguments to parser
    p = argparse.ArgumentParser()
    for arg, entries in doc.items():
        try:
            p.add_argument(arg, type=entries['type'], help=entries['param'])
        except TypeError:
            # Type not recognized
            p.add_argument(arg, type=str, help=entries['param'])

    # Add optional scraper arguments
    sa = p.add_argument_group('scraper arguments')
    sa.add_argument('--max-threads', help='Number of threads to use while scraping.', metavar="N")

    # Add exporter arguments
    p.add_argument("exporter", type=str, help="exporter to use {json|dummy|amcatdb}")
    ea = p.add_argument_group('JSON exporter arguments')
    ea.add_argument("--io", help="Output file", metavar="FILE")

    parsed = p.parse_args()

    # Generate keyword arguments for scraper.init function
    kwargs = {}
    for arg in doc.keys():
        types = doc[arg]['type']
        value = getattr(parsed, arg)

        for _type in types:
            try:
                value = CONVERTER_MAP.get(_type, _type)(getattr(parsed, arg))
            except:
                continue

        kwargs[arg] = value

    exp = EXPORTER_MAP[parsed.exporter]

    exp_kwargs = {}
    for kwarg in exp[1]:
        if not getattr(parsed, kwarg):
            print('%s needs %s-argument' % (parsed.exporter, kwarg))
            sys.exit(1)
        exp_kwargs[kwarg] = getattr(parsed, kwarg)

    exp = exp[0](**exp_kwargs)
    scr = scraper(exp)
    scr.scrape(**kwargs)