import concurrent
import sys
import asyncio
import logging

import bibtexparser

from bibchex.data import Entry, Problem
from bibchex.differ import Differ
from bibchex.sources import SOURCES, CrossrefSource
from bibchex.ui import UI
from bibchex.checks import CCHECKERS
from bibchex.output import HTMLOutput
from bibchex.config import Config
from bibchex.unify import Unifier

LOGGER = logging.getLogger(__name__)

class Checker(object):
    def __init__(self, filename, out_filename):
        self._fname = filename
        self._out_filename = out_filename

        self._bibtex_data = None
        self._entries = {}
        self._suggestions = {}

        self._retrieval_errors = []
        self._diffs = []
        self._problems = []
        self._global_problems = []

        self._unifier = Unifier()

        self._ui = UI()
        self._cfg = Config()

    async def run(self):
        LOGGER.info("Parsing BibTeX")
        self._parse()
        LOGGER.info("Applying unification rules")
        self._unify()
        LOGGER.info("Retrieving missing DOIs")
        await self._find_dois()
        LOGGER.info("Retrieving metadata")
        await self._retrieve()
        LOGGER.info("Calculating differences")
        self._diff()
        LOGGER.info("Running consistency checks")
        await self._check_consistency()
        # TODO Retrieval Errors should be part of the HTML output

        self._filter_diffs()
        self._filter_problems()

        LOGGER.info("Writing output")
        self._output()
        LOGGER.info("Done.")

    def _filter_diffs(self):
        filtered_diffs = [diff for diff in self._diffs
                          if not self._entries[diff.entry_id]
                          .should_ignore_diff(diff.source, diff.field)]

        self._diffs = filtered_diffs

    def _filter_problems(self):
        filtered_probs = [prob for prob in self._problems
                          if not self._entries[prob.entry_id]
                          .should_ignore_problem(prob.problem_type)]

        self._problems = filtered_probs

    def _output(self):
        html_out = HTMLOutput(list(self._entries.values()), self._diffs,
                              self._problems, self._global_problems,
                              self._fname)
        html_out.write(self._out_filename)

    def _print_retrieval_errors(self):
        LOGGER.warn("############################################")
        LOGGER.warn("##    Errors occurred during retrieval    ##")
        LOGGER.warn("############################################")

        for p in self._retrieval_errors:
            LOGGER.warn("main", " - {}".format(p))

    def _diff(self):
        for (_, entry) in self._entries.items():
            d = Differ(entry)
            for s in self._suggestions.get(entry.get_id(), []):
                self._diffs.extend(d.diff(s))

    async def _check_consistency(self):
        tasks = []
        task_info = []
        for CChecker in CCHECKERS:
            if hasattr(CChecker, 'reset'):
                await CChecker.reset()

        for CChecker in CCHECKERS:
            for entry in self._entries.values():
                ccheck = CChecker()
                if self._cfg.get("check_{}".format(CChecker.NAME), entry, True):
                    task = ccheck.check(entry)
                    task_info.append((CChecker, entry))
                    tasks.append(task)

        results = await asyncio.gather(*tasks)
        for ((CChecker, entry), problems) in zip(task_info, results):
            for (problem_type, message, details) in problems:
                self._problems.append(
                    Problem(entry.get_id(), CChecker.NAME, problem_type,
                            message, details))

        for CChecker in CCHECKERS:
            if hasattr(CChecker, 'complete'):
                global_results = await CChecker.complete(self._ui)
                for (problem_type, message, details) in global_results:
                    self._global_problems.append(
                        Problem(None, CChecker.NAME, problem_type,
                                message, details))

    async def _find_dois(self):
        cs = CrossrefSource(self._ui)

        entry_order = (entry for entry in self._entries.values()
                       if entry.get_doi() is None)

        # Filter out entries for which bibchex-nodoi is set.
        entry_order = list(
            filter(lambda e: not e.options.get('nodoi', False), entry_order))

        tasks = []
        for entry in entry_order:
            task = cs.get_doi(entry)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        for (entry, (result, retrieval_error)) in zip(entry_order, results):
            if result:
                entry.add_suggested_doi(result)
            if retrieval_error:
                self._retrieval_errors.append(retrieval_error)

    async def _retrieve(self):
        entry_order = []
        tasks = []
        indices = []

        for SourceClass in SOURCES:
            #        for SourceClass in [ DataCiteSource ]:
            source = SourceClass(self._ui)

            i = 0
            for entry in self._entries.values():
                task = source.query(entry)
                entry_order.append(entry)
                tasks.append(task)
                indices.append(i)
                i += 1

        results = await asyncio.gather(*tasks)
        for (entry_index, raw_result) in zip(indices, results):
            entry = entry_order[entry_index]

            if not isinstance(raw_result, list):
                raw_result = [raw_result]

            for (result, retrieval_error) in raw_result:
                if result:
                    # Unify all suggested data
                    self._unifier.unify_suggestion(result)
                    self._suggestions[entry.get_id()].append(result)
                if retrieval_error:
                    if isinstance(retrieval_error, list):
                        self._retrieval_errors.extend(retrieval_error)
                    else:
                        self._retrieval_errors.append(retrieval_error)

    def _unify(self):
        for entry in self._entries.values():
            assert entry.get_id() not in self._suggestions
            self._suggestions[entry.get_id()] = [
                self._unifier.unify_entry(entry)
            ]
                        
    def _parse(self):
        with open(self._fname) as bibtex_file:
            parser = bibtexparser.bparser.BibTexParser(
                common_strings=True)
            # TODO how much of my own magic ist still necessary here?
#            parser.customization = bibtexparser.customization.\
#                homogenize_latex_encoding
            self._bibtex_data = parser.parse_file(bibtex_file)
        entry_list = [Entry(bentry, self._ui)
                      for bentry in self._bibtex_data.entries]
        entry_keys = set((entry.get_id() for entry in entry_list))
        if len(entry_keys) != len(entry_list):
            LOGGER.error("ERROR! Duplicate keys detected!")
            sys.exit(-1)

        self._entries = {entry.get_id(): entry for entry in entry_list}


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # TODO this is a very large number of threads. Maybe check instead how many
    # are currently sleeping, and scale up only if too many are sleeping?
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(1000))
    c = Checker(sys.argv[1], sys.argv[2])
    loop.run_until_complete(c.run())
