from bibchex.config import Config
from bibchex.util import parse_datetime, contains_abbreviation
from bibchex.checks.common import GenericFuzzySimilarityChecker,\
    GenericAbbrevChecker


class JournalAbbrevChecker(object):
    NAME = 'journal_abbrev'
    FIELDS = ['booktitle', 'journal']

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, False):
            return []
        problems = []
        for field in JournalAbbrevChecker.FIELDS:
            val = entry.data.get(field, '')
            if contains_abbreviation(val):
                problems.append(
                    ("abbreviated_journal",
                     "Publication title '{}' seems to contain an abbreviation"
                     .format(val), ""))

        return problems


class JournalSimilarityChecker(GenericFuzzySimilarityChecker):
    NAME = 'journal_similarity'
    FIELDS = ['booktitle', 'journal']
    MSG_NAME = "Journal"


class PublisherSimilarityChecker(GenericFuzzySimilarityChecker):
    NAME = 'publisher_similarity'
    FIELDS = ['organization', 'publisher']
    MSG_NAME = "Publisher"


class JournalMutualAbbrevChecker(GenericAbbrevChecker):
    NAME = 'journal_mutual_abbrev'
    MSG_NAME = 'Journal'
    FIELDS = ['booktitle', 'journal']


class PublisherMutualAbbrevChecker(GenericAbbrevChecker):
    NAME = 'publisher_mutual_abbrev'
    MSG_NAME = 'Publisher'
    FIELDS = ['organization', 'publisher']


class PreferOrganizationChecker(object):
    NAME = 'prefer_organization'

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if entry.data.get('publisher') and not entry.data.get('organization'):
            return [(type(self).NAME,
                     "Entry should prefer organization over publisher.", "")]

        return []


class PreferDateChecker(object):
    NAME = 'prefer_date'

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if ((entry.data.get('date') is None) and
            (
                (any((entry.data.get(key) for key in ('year', 'month', 'day')))
                 and not self._cfg.get('prefer_date_or_year', entry, True))
                or
                (any((entry.data.get(key) for key in ('month', 'day'))))
        )):
            return [(type(self).NAME,
                     ("The 'date' field is preferred over "
                      "the 'day/month/year' fields."),
                     "")]

        return []


class DateParseableChecker(object):
    NAME = 'date_parseable'

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not entry.data.get('date'):
            return []

        try:
            d = parse_datetime(entry.data.get('date'))
            return []
        except ValueError:
            return [(type(self).NAME,
                     "Unparseable date",
                     "The date string '{}' could not be parsed."
                     .format(entry.data.get('date')))]
