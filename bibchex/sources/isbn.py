import asyncio
from functools import partial

import bibtexparser

from bibchex.data import Suggestion, Entry
from bibchex.problems import RetrievalProblem
from isbnlib import meta, registry, notisbn, ISBNLibException
from bibchex.asyncrate import SyncRateLimiter


class ISBNSource(object):
    def __init__(self, ui):
        self._providers = set(('goob', 'openl'))
        self._ratelimit = SyncRateLimiter(100, 60)
        self._ui = ui

        # We use isbnlib's own bibtex formatter to do the
        # field mapping for us.
        self._formatter = registry.bibformatters['bibtex']

        # TODO detect more providers

    async def query(self, entry):
        loop = asyncio.get_event_loop()

        tasks = []
        problem = None

        for provider in self._providers:
            self._ui.increase_subtask('ISBNQuery')
            task = loop.run_in_executor(
                None, partial(self._query_blocking, entry, provider))
            tasks.append(task)

        try:
            gathered = await asyncio.gather(*tasks)
        except RetrievalProblem as e:
            problem = e

        results = [res for res in gathered if res]
        if problem:
            results.append((None, problem))

        return results

    def _query_blocking(self, entry, provider):
        isbn = entry.data.get('isbn')

        # Okay, we're actually going to make a HTTP request
        self._ratelimit.get()

        if not isbn:
            self._ui.finish_subtask('ISBNQuery')
            return None

        if notisbn(isbn):
            self._ui.finish_subtask('ISBNQuery')
            return (None, "{} is not a valid ISBN.".format(isbn))

        try:
            bibtex_data = self._formatter(meta(isbn, service=provider))
        except ISBNLibException as e:
            return (None, e)

        parsed_data = bibtexparser.loads(bibtex_data)

        if len(parsed_data.entries) != 1:
            raise RetrievalProblem(
                "ISBN search did not return exactly one result.")

        retrieved = Entry(parsed_data.entries[0], self._ui)
        s = Suggestion("isbn_{}".format(provider), entry)
        for (k, v) in retrieved.data.items():
            if k.lower() == 'id':
                continue
            s.add_field(k, v)

        for (first, last) in s.authors:
            s.add_author(first, last)

        for (first, last) in s.editors:
            s.add_editor(first, last)

        return (s, None)
