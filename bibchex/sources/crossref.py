import re
import asyncio
import os
from functools import partial

import crossref_commons.retrieval
import crossref_commons.search
from fuzzywuzzy import fuzz
from ratelimit import RateLimitException

from bibchex.data import Suggestion
from bibchex.problems import RetrievalProblem
from bibchex.config import Config
from bibchex.strutil import flexistrip

TYPE_MAPPING = {
    'journal-article': ['article'],
    'book-chapter': ['inproceedings', 'inbook', 'incollection'],
    'book': ['book'],
    'monograph': ['book'],
    'proceedings-article': ['inproceedings', 'article'],
    'dissertation': ['book'],
    'report': ['article', 'misc'],
    'reference-entry': ['article', 'inproceedings']
}

# Left: Field from crossref, Right: Field in Bibtex
FIELD_MAPPING = {
    'DOI': 'doi',
    'ISBN': 'isbn',
    'ISSN': 'issn',
    'URL': 'url',
    'page': 'pages',
    'publisher': 'publisher',
    'title': 'title',
    'volume': 'volume',
    'container-title': {'article': 'journal', 'inproceedings': 'booktitle',
                        'default': 'journal'},
}


class CrossrefSource(object):
    QUERY_FIELDS = ['doi']
    DOI_URL_RE = re.compile(r'https?://(dx\.)?doi\.org/.*')

    def __init__(self, ui):
        self._ui = ui
        self._cfg = Config()

        # Check if we have crossref credentials and set them via environment
        # variable. The environment variables are read by crossref_commons
        if self._cfg.get('crossref_plus'):
            self._ui.message("Crossref", "Setting Crossref Plus token")
            os.environ['CR_API_PLUS'] = self._cfg.get('crossref_plus')
        if (self._cfg.get('crossref_mailto') and
                len(self._cfg.get('crossref_mailto')) > 0):
            # TODO make version dynamic
            os.environ['CR_API_AGENT'] = \
                ('BibChex/0.1 '
                 '(https://github.com/tinloaf/bibchex; mailto:{})').format(
                     self._cfg.get('crossref_mailto'))
            os.environ['CR_API_MAILTO'] = self._cfg.get('crossref_mailto')
        else:
            self._ui.warn("CrossRef",
                          ("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                           "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                           " Please set crossref_mailto in your config! \n"
                           " Not setting crossref_mailto may cause all your CrossRef"
                           " requests to fail."
                           "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
                           "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"))
            os.environ['CR_API_AGENT'] = \
                'BibChex/0.1 (https://github.com/tinloaf/bibchex)'

    def _get_doi_blocking(self, entry, step):
        """
        Steps:
           1: query by title + authors (first and last names)
           2: query by title + authors (only last names)
           3: query by title
        """
        title = entry.data.get('title')
        if title is None:
            # Without a title, we're chanceless.
            return None

        q = [('bibliographic', title)]

        if step in (1, 2):
            for (first, last) in entry.authors:
                if step == 2:
                    q.append(('author', "{}".format(last)))
                else:
                    q.append(('author', "{} {}".format(first, last)))

        try:
            (count, results) = crossref_commons.search.search_publication(
                q, sort="relevance", order="desc")
        except Exception as e:
            self._ui.error("CrossRef",
                           (f"Error reverse-searching for {entry.get_id()}: "
                            f"{e}"))
            return None

        if count > 0 and results:
            for i in range(0, min(10, count)):
                if 'title' not in results[i] or 'DOI' not in results[i]:
                    # Bogus data
                    continue
                suggested_title = results[i]['title']
                doi = results[i]['DOI']

                if not isinstance(suggested_title, list):
                    suggested_title = [suggested_title]
                for possibility in suggested_title:
                    fuzz_score = fuzz.partial_ratio(title.lower(),
                                                    possibility.lower())
                    if fuzz_score >= self._cfg.get('doi_fuzzy_threshold', entry,
                                                   90):
                        return doi

        return None

    async def get_doi(self, entry):
        loop = asyncio.get_event_loop()
        done = False
        retries = 20
        backoff = 1
        problem = None
        result = None
        step = 1
        self._ui.increase_subtask('CrossrefDOI')
        try:
            while not done:
                try:
                    result = await loop.run_in_executor(
                        None, partial(self._get_doi_blocking, entry, step))
                    if result:
                        done = True
                    else:
                        # Too specific search? Loosen search terms
                        if step < 3:
                            step += 1
                        else:
                            done = True
                except RateLimitException:
                    if retries == 0:
                        return (None, RetrievalProblem("Too many retries"))
                    await asyncio.sleep(backoff)
                    backoff = backoff * 2
                    retries -= 1
                    done = False

        except RetrievalProblem as e:
            problem = e

        self._ui.finish_subtask('CrossrefDOI')

        return (result, problem)

    async def query(self, entry):
        loop = asyncio.get_event_loop()
        done = False
        retries = 20
        backoff = 1
        problem = None
        result = None
        self._ui.increase_subtask('CrossrefQuery')
        try:
            while not done:
                try:
                    result = await loop.run_in_executor(
                        None, partial(self._query_blocking, entry))
                    done = True
                except RateLimitException:
                    if retries == 0:
                        return (None, RetrievalProblem("Too many retries"))
                    await asyncio.sleep(backoff)
                    backoff = backoff * 2
                    retries -= 1
                    done = False

        except RetrievalProblem as e:
            problem = e

        return (result, problem)

    def _query_blocking(self, entry):
        doi = entry.get_probable_doi()
        if not doi:
            self._ui.finish_subtask('CrossrefQuery')
            return None

        try:
            data = crossref_commons.retrieval.get_publication_as_json(doi)
        except ValueError as e:
            self._ui.finish_subtask('CrossrefQuery')
            if str(e) == f"DOI {doi} does not exist":
                # This isn't really an error, CrossRef just does not know
                # about them
                pass
            else:
                self._ui.error("CrossRef",
                               (f"Error retrieving data for {entry.get_id()}. "
                                f"{e}"))
            return None

        s = Suggestion("crossref", entry)

        # Special handling for type
        btype = TYPE_MAPPING.get(data['type'])
        if not btype:
            self._ui.warn(
                "Crossref", "Type {} not found in crossref source. (Entry {})"
                .format(data['type'], entry.get_id()))
        else:
            s.add_field('entrytype', btype)

        # Special handling for authors
        for author_data in data.get('author', []):
            s.add_author(author_data.get('given', "").strip(),
                         author_data.get('family', "").strip())

        # Special handling for editors
        for editor_data in data.get('editor', []):
            s.add_editor(editor_data.get('given', "").strip(),
                         editor_data.get('family', "").strip())

        # Special handling for journal / book title
        if btype in ['journal-article', 'book-chapter']:
            journal = flexistrip(data.get('container-title'))
            if journal:
                s.add_field('journal', journal)

        # Special handling for URL. Only take it if it's not a DOI-Url
        url = flexistrip(data.get('URL'))
        if url and (CrossrefSource.DOI_URL_RE.match(url) is None):
            s.add_field('url', url)

        # All other fields
        for field_from, field_to in FIELD_MAPPING.items():
            if isinstance(field_to, dict):
                if entry.data['entrytype'] in field_to:
                    field_to = field_to[entry.data['entrytype']]
                else:
                    field_to = field_to.get('default')

            if not field_to:
                continue

            if field_from in data:
                s.add_field(field_to, flexistrip(data[field_from]))

        self._ui.finish_subtask('CrossrefQuery')
        return s
