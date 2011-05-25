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

import re
import datetime

def dictionary(func):
    """This decorator converts a generator yielding (key, value) to a dictionary."""
    def _dictionary(*args, **kwargs):
        return dict(tuple(func(*args, **kwargs)))
    return _dictionary

def todate(date):
  """Convert datetime object to date object. If `date` can't be converted, return
  withouth modifying"""
  if hasattr(date, 'date'):
      return date.date()
  return date
  


###########################################################################
##                     Date(time) functions                              ##
###########################################################################

MONTHNAMES = (('jan', 'janv', 'ener', 'gennaio'),
              ('feb', 'fevr', 'feve'),
              ('mar', 'mrt', 'maa', 'mar', 'mai'),
              ('apr', 'avri', 'abri'),
              ('may', 'mai', 'mei', 'mayo', 'maggio'),
              ('jun', 'juin','giugno'),
              ('jul', 'juil', 'luglio'),
              ('aug', 'aout', 'agos'),
              ('sep', 'setem', 'settembre'),
              ('oct', 'okt', 'out', 'ottobre'),
              ('nov'),
              ('dec', 'dez', 'dici', 'dicembre'))

class _DateFormat(object):
    """Format definition for parsing dates"""
    def __init__(self, expr, yeargroup=3, monthgroup=2, daygroup=1,
                 monthisname=False, swapamerican=False):
        self.expr = expr
        self.yeargroup = yeargroup
        self.monthgroup = monthgroup
        self.daygroup = daygroup
        self.monthisname = monthisname
        self.swapamerican = swapamerican
    def readDate(self, date, american=False):
        """Read the given date, producing a y,m,d tuple"""
        match = re.search(self.expr, date)
        if not match: return
        y, m, d = [match.group(x)
                   for x in (self.yeargroup, self.monthgroup, self.daygroup)]
        if self.monthisname:
            m = _monthnr(m)
            if not m: return
        y, m, d = map(int, (y, m, d))
        # 2-digit year logic:
        if y < 40: y = 2000 + y
        elif y < 100: y = 1900 + y
        # dmy vs mdy
        if american and self.swapamerican:
            m, d = d, m
        return y, m, d
         
_DATEFORMATS = (
    _DateFormat("(\d{4})[-/](\d{1,2})[-/](\d{1,2})", 1,2,3),
    _DateFormat("(\d{1,2})[-/](\d{1,2})[-/](\d{4})", 3,2,1,swapamerican=True),
    _DateFormat("(\w+),?\s+(\d{1,2})\s*,?\s+(\d{4})",3,1,2,True),
    _DateFormat("(\w+)\s+(\d{1,2})\s*,?\s+(\d{4})",  3,1,2,True),
    _DateFormat("(\d{1,2})(?:\w\w?|\.)?\s+(\w*)\s+(\d{4})",3,2,1,True),
    _DateFormat("\w*?,?\s*(\d{1,2})\s+(\w+)\s+(\d{4})",3,2,1,True),
    _DateFormat("(\d{1,2})\.?\s+(\w*)\s+(\d{4})",    3,2,1,True),
    _DateFormat("(\d{1,2})[- ](\w+)[- ](\d{2,4})",   3,2,1,True),
    _DateFormat("(\w+) (\d{1,2}), (\d{4})",          3,1,2,True),
    _DateFormat("(\d{1,2})[-/](\d{1,2})[-/](\d{2})", 3,2,1,swapamerican=True),
)

def _monthnr(monthname):
    """Try to get a month number corresponding to the month
    name (prefix) in monthname"""
    for i, names in enumerate(MONTHNAMES):
        for name in names:
            if monthname.lower().startswith(name.lower()):
                return i+1

        
def readDate(datestr, lax=False, rejectPre1970=False, american=False):
    """Try to read a date(time) string with unknown format

    Attempt a number of date formats to read str

    @param string: the date string to read
    @param lax: if True, return None if no match was found instead of
      raising an error
    @param rejectPre1970: if True, reject dates before 1970 (to catch
      problems with incorrect parses)
    @param american: prefer MDY over DMY
    @return: a \C{datetime.datetime} object 
    """
    if datestr == None:
      return None

    time = None
    if ':' in datestr:
         m = re.match("(.*?)(\d+:[\d:]+)", datestr)
         if m:
             datestr, timestr = m.groups()
             try: time = tuple(map(int, timestr.split(":")))
             except ValueError: time = []
             if len(time) == 3: pass
             elif len(time) == 2: time = time + (0,)
             elif lax: time = None
             else: raise ValueError("Could not parse time part "
                                    +"('%s') of datetime string '%s'"
                                    % (timestr, string))
    for df in _DATEFORMATS:
        date = df.readDate(datestr, american=american)
        if date: break
        
    datestr = datestr.lower()
    if not date:
        # For 'October 20, 2010'
        for i, prefixes in enumerate(MONTHNAMES):
            if datestr.startswith(prefixes):
                month_plus_day, year = datestr.split(',')
                day = month_plus_day.split(' ')[1]
                date = int(year), i+1, int(day)
        
    if not date:        
        # For '22 November 2006 Wednesday 10:23 AM (Central European Time)'
        s = datestr.split(' ')
        if len(s)>2:
            for i, prefixes in enumerate(MONTHNAMES):
                if s[1].startswith(prefixes):
                    try:
                        date = int(s[2]), i+1, int(s[0])
                    except:
                        continue
                    else:
                        break
            
    if not date:
        if lax: return
        raise ValueError("Could not parse datetime string '%s'" % (string))

    if date[0] < 1970 and rejectPre1970:
        if lax: return None
        raise ValueError("Rejecting datetime string %s -> %s"
                         % (string, date))

    if not time: time = (0, 0, 0)
    return datetime.datetime(*(date + time))