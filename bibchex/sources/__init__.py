from .crossref import CrossrefSource
from .meta import MetaSource
from .isbn import ISBNSource
from .datacite import DataCiteSource

SOURCES = [DataCiteSource, CrossrefSource, MetaSource, ISBNSource]
