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

import datetime

def dictionary(func):
    """This decorator converts a generator yielding (key, value) to a dictionary."""
    def _dictionary(*args, **kwargs):
        return dict(tuple(func(*args, **kwargs)))
    return _dictionary

def iterable(func):
    """This decorator converts a generator yielding to a tuple."""
    def _iterable(*args, **kwargs):
        return tuple(func(*args, **kwargs))
    return _iterable

def todate(date):
  """Convert datetime object to date object. If `date` can't be converted, return
  withouth modifying"""
  return date.date() if hasattr(date, 'date') else date
  
def filter_docs(docs, date):
    """Some websites do not provide an archive, but only 'previous' and 'next' links. By
    iterating over all pages descending, this function only returns the document with the
    correct date. It stoppes after a page older than `date` is detected.

    @type docs: generator of Documents
    @param docs: Documents in descending order

    @type date: datetime.datetime or datetime.date
    @param date: only return `docs` of `date`"""
    date = todate(date)
    for doc in docs:
        if todate(doc.props.date) == date:
            yield art
        elif todate(doc.props.date) < date:
            break

@dictionary
def parse_form(form):
    """Turn a form in to a dictionary, including hidden fields.

    @type form: lxml-html object
    @param form: form to parse"""
    for inp in form.cssselect('input'):
        yield (inp.get('name'), inp.get('value', None).encode('utf-8'))

@iterable
def parse_coord(coord):
    """Newspapers often create clickable articles using divs and styles. For example:
    
    left:331px; top:495px; width:72px; height:86px

    This function returns a tuple containing (left, top, width, height).

    @type coord: str
    @param coord: coordinate to parse"""
    coords = [x.strip() for x in coord.split(';')]
    return map(int, (x.split(':')[1][:-2] for x in coords))

def parse_coords(elements):
    """Uses parse_coord to parse multiple lxml.html elements' style attributes"""
    return [parse_coord(el.get('style')) for el in elements]