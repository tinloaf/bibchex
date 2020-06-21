import os
import asyncio
import re

from fuzzywuzzy import fuzz

from bibchex.config import Config
from bibchex.strutil import AbbrevFinder
from bibchex.util import chunked_pairs


class GenericFuzzySimilarityChecker(object):
    SEEN_NAMES = {}
    NUMBER_RE = re.compile(r'\d+\S*')

    def __init__(self):
        self._cfg = Config()
        self._name = type(self).NAME
        self._cls = type(self)

        if self._name not in GenericFuzzySimilarityChecker.SEEN_NAMES:
            GenericFuzzySimilarityChecker.SEEN_NAMES[self._name] = set()

    def _normalize_name(self, name):
        name = GenericFuzzySimilarityChecker.NUMBER_RE.sub('', name)
        return name.strip()

    async def check(self, entry):
        for field in self._cls.FIELDS:
            val = entry.data.get(field)
            if not val:
                continue
            GenericFuzzySimilarityChecker.SEEN_NAMES[self._name]\
                                         .add((val, self._normalize_name(val)))

        return []

    @ classmethod
    async def reset(cls):
        GenericFuzzySimilarityChecker.SEEN_NAMES[cls.NAME] = set()

    @ classmethod
    async def complete(cls, ui):
        cfg = Config()

        def compute(seen_names, chunk_count, chunk_number):
            problems = []
            # nn1/nn2 are the normalized forms of the names
            for ((n1, nn1), (n2, nn2)) in chunked_pairs(
                    list(seen_names), chunk_count, chunk_number):
                if (nn1 == nn2):
                    continue

                if fuzz.partial_ratio(nn1, nn2) > 90:  # TODO make configurable
                    problems.append((name,
                                     "{} names '{}' and '{}' seem very similar."
                                     .format(cls.MSG_NAME, n1, n2),
                                     ""))
            return problems

        name = cls.NAME
        item_count = len(GenericFuzzySimilarityChecker.SEEN_NAMES[name])
        ui.message("FuzzySim", (f"Fuzzy-checking pairwise similarity "
                                f"of {cls.MSG_NAME}s. Testing "
                                f"{item_count*(item_count - 1) / 2 - item_count} pairs. "
                                "This might take a while."))

        collected_problems = []
        chunk_count = min(len(os.sched_getaffinity(0)) * 10,
                          len(GenericFuzzySimilarityChecker.SEEN_NAMES[name]))
        tasks = []
        for i in range(0, chunk_count):
            tasks.append(
                asyncio.get_event_loop().run_in_executor(
                    cfg.get_executor(),
                    compute, GenericFuzzySimilarityChecker.SEEN_NAMES[name],
                    chunk_count, i))

        collected_results = await asyncio.gather(*tasks)

        # Flatten lists
        return [item for sublist in collected_results for item in sublist]


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

    @ classmethod
    async def reset(cls):
        GenericAbbrevChecker.SEEN_NAMES[cls.NAME] = set()

    @ classmethod
    async def complete(cls, ui):
        name = cls.NAME
        problems = []

        af = AbbrevFinder(GenericAbbrevChecker.SEEN_NAMES[name])
        for (s1, s2) in af.get():
            problems.append((name,
                             "{} '{}' could be an abbreviation of '{}'."
                             .format(cls.MSG_NAME, s1, s2),
                             ""))
        return problems
