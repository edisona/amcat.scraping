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
"""Document objects returned by various scraping-functions."""

from scraping.toolkit import dictionary
from scraping.html2text import html2text

from lxml import html
from lxml import etree
from html import parser

import copy
import types

class Document(object):
    """Object representing an document. No properties are
    forced upon constructing. This is the base for all other
    objects.

    __getattr__ and __setattr__ will raise errors when not
    initialized."""
    _id = None

    def __init__(self, parent=None):
        """@param parent: """
        object.__setattr__(self, '_properties', dict())
        object.__setattr__(self, '_parent', parent)

        if parent and not isinstance(parent, self.__class__):
            raise ValueError("`parent` should inherit from Document.")

    def __setattr__(self, name, value):
        if not hasattr(self, name) or name in self._properties:
            self._properties[name] = value
        else:
            object.__setattr__(self, name, value)

    def __getattr__(self, name):
        props = self.__dict__['_properties']
        if name in props:
            return props[name]
        else:
            raise AttributeError(name)

    def __delattr__(self, name):
        if name in self._properties:
            del self._properties[name]
        else:
            raise AttributeError(name)

    def getprops(self):
        """Get properties as a dict"""
        return self._properties

    def getparent(self):
        return self._parent

    def updateprops(self, dic):
        """Update properties.

        @type dic: dictionary
        @param dic: dictionary to use to update the properties"""
        self.__dict__['_properties'].update(dic)

    def copy(self, cls=None, parent=None):
        """Returns a copy of itself, with all the properties deep-copied."""
        parent = parent or self._parent
        cls = cls or Document

        d = cls(parent=parent)
        for k,v in self._properties.items():
            setattr(d, k, v)

        return d

    def prepare(self, processor):
        """This method prepares the document for processing. See HTMLDocument for
        sample usage."""
        pass

class HTMLDocument(Document):
    """Document object for HTML documents. This means that all properties are converted to
    MarkDown compatible text in `getprops`. Moreover, lxml.html objects (or even lists of
    lxml.html objects) are converted to text before returning."""
    doc = None # Used to store lxml object

    def _convert(self, val):
        t = type(val)

        if t is str:
            return val.strip()

        if t in (html.HtmlElement, etree._Element):
            try:
                return html2text(html.tostring(val, encoding=str)).strip()
            except parser.HTMLParseError, TypeError:
                print('Warning: html2text failed!')
                return 'Converting from HTML failed!'

        if t in (list, tuple, types.GeneratorType):
            """Check if all objects in list are HtmlElement and then proceed"""
            val = tuple(val)

            if all([type(e) in (html.HtmlElement, etree._Element) for e in val]):
                return "\n\n".join(map(self._convert, val))            

        # Unknown type
        return val

    def copy(self, parent=None):
        d = super(HTMLDocument, self).copy(cls=HTMLDocument, parent=parent)
        d.doc = self.doc
        return d

    @dictionary
    def getprops(self):
        """Return properties converted (where applicable) to MarkDown"""
        for k,v in self._properties.items():
            yield (k, self._convert(v))

    def prepare(self, processor):
        if self.doc is None and hasattr(self, 'url'):
            if hasattr(processor, 'get'):
                self.doc = processor.get(self.url)