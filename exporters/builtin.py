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
"""Exporters define how, well, data is exported.

This module only contains scrapers without special import needs."""

import json
import datetime

class Exporter(object):
    """Methods don't have to be thread-safe, since the main-loop will never
    spawn multiple `commit` threads."""
    def __init__(self):
        self.id = self._idfactory()
        self.closed = False

    def _idfactory(self, id=-1):
        while True:
            id += 1
            yield id

    def commit(self, obj):
        """Commit an object and return its id."""
        if self.closed: raise IOError("Exporter already closed!")

    def close(self):
        """Called to finish exporter (typically by scraper.quit() )"""
        if self.closed:
            raise IOError("Exporter already closed!")

        self.closed = True

class DatetimeAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) in (datetime.datetime, datetime.date):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)

class JSONExporter(Exporter):
    """Export data as JSON format"""
    def __init__(self, io, close_io=True):
        """
        @type io: file-like object
        @param io: object to write data to

        @type close_io: Boolean
        @param close_io: Wether `close` should call close on the io-object.
        """
        super(JSONExporter, self).__init__()

        self.close_io = close_io
        self.io = io
        self.io.write('[\n')

        self.first = True

    def commit(self, obj):
        super(JSONExporter, self).commit(obj)

        if obj._id is not None:
            # Already comitted
            return obj._id

        if not self.first:
            self.io.write(',\n')
        else:
            self.first = False

        parent = obj.getparent()
        pid = self.commit(parent) if parent else None
        obj._id = oid = next(self.id)

        props = obj.getprops()
        props.update(dict(parent=pid, id=oid))

        json.dump(props, self.io, indent=2, cls=DatetimeAwareJSONEncoder)

        return oid

    def close(self):
        super(JSONExporter, self).close()

        self.io.write('\n]')
        if self.close_io:
            self.io.close()