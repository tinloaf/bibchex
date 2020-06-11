from fuzzywuzzy import fuzz

from bibchex.config import Config
from bibchex.strutil import AbbrevFinder
from bibchex.util import sorted_pairs


class GenericFuzzySimilarityChecker(object):
    SEEN_NAMES = {}

    def __init__(self):
        self._cfg = Config()
        self._name = type(self).NAME
        self._cls = type(self)

        if self._name not in GenericFuzzySimilarityChecker.SEEN_NAMES:
            GenericFuzzySimilarityChecker.SEEN_NAMES[self._name] = set()

    async def check(self, entry):
        for field in self._cls.FIELDS:
            val = entry.data.get(field)
            if not val:
                continue
            GenericFuzzySimilarityChecker.SEEN_NAMES[self._name].add(val)

        return []

    @classmethod
    async def reset(cls):
        GenericFuzzySimilarityChecker.SEEN_NAMES[cls.NAME] = set()

    @classmethod
    async def complete(cls):
        name = cls.NAME
        problems = []
        # We only use sorted_pairs here for determinism, makes it easier to test
        for (n1, n2) in sorted_pairs(
                GenericFuzzySimilarityChecker.SEEN_NAMES[name]):
            if fuzz.partial_ratio(n1, n2) > 95:  # TODO make configurable
                problems.append((name,
                                 "{} names '{}' and '{}' seem very similar."
                                 .format(cls.MSG_NAME, n1, n2),
                                 ""))
        return problems


class GenericAbbrevChecker(object):
    SEEN_NAMES = {}

    def __init__(self):
        self._cfg = Config()
        self._name = type(self).NAME
        self._cls = type(self)

        if self._name not in GenericAbbrevChecker.SEEN_NAMES:
            GenericAbbrevChecker.SEEN_NAMES[self._name] = set()

    async def check(self, entry):
        for field in self._cls.FIELDS:
            val = entry.data.get(field)
            if not val:
                continue
            GenericAbbrevChecker.SEEN_NAMES[self._name].add(val)

        return []

    @classmethod
    async def reset(cls):
        GenericAbbrevChecker.SEEN_NAMES[cls.NAME] = set()

    @classmethod
    async def complete(cls):
        name = cls.NAME
        problems = []

        af = AbbrevFinder(GenericAbbrevChecker.SEEN_NAMES[name])
        for (s1, s2) in af.get():
            problems.append((name,
                             "{} '{}' could be an abbreviation of '{}'."
                             .format(cls.MSG_NAME, s1, s2),
                             ""))
        return problems
