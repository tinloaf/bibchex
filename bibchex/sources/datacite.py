import asyncio
import urllib
import requests
from functools import partial

from bibchex.data import Suggestion
from bibchex.problems import RetrievalProblem
from bibchex.asyncrate import SyncRateLimiter


def path_exists(d, path):
    for element in path:
        if element not in d:
            return False
        d = d[element]

    return True


class DataCiteSource(object):
    def __init__(self, ui):
        self._ratelimit = SyncRateLimiter(100, 60)
        self._ui = ui

    async def query(self, entry):
        loop = asyncio.get_event_loop()

        problem = None
        result = None

        self._ui.increase_subtask('DataCiteQuery')

        try:
            result = await loop.run_in_executor(
                None, partial(self._query_blocking, entry))
        except requests.exceptions.RequestException as e:
            self._ui.error("datacite", "Connection problem: {}".format(e))
            problem = e
        except RetrievalProblem as e:
            self._ui.error("datacite", "Retrieval problem: {}".format(e))
            problem = e

        return (result, problem)

    def _query_blocking(self, entry):
        doi = entry.get_probable_doi()

        if not doi:
            self._ui.finish_subtask('DataCiteQuery')
            return None

        # Okay, we're actually going to make a HTTP request
        self._ratelimit.get()

        url = "https://api.datacite.org/dois/{}".format(
            urllib.parse.quote(doi))
        response = requests.get(url)

        if response.status_code != 200:
            self._ui.finish_subtask('DataCiteQuery')
            return None

        try:
            data = response.json()
        except ValueError:
            self._ui.warn("DataCite", "Response did not contain JSON")
            self._ui.finish_subtask('DataCiteQuery')
            return None

        if 'errors' in data:
            self._ui.finish_subtask('DataCiteQuery')
            return None

        attrs = data['data']['attributes']

        s = Suggestion('datacite', entry)

        # Authors
        for i in range(0, len(attrs['creators'])):
            adata = attrs['creators'][i]
            if 'givenName' in adata and 'familyName' in adata:
                s.add_author(adata['givenName'], adata['familyName'])

        # Editors
        for i in range(0, len(attrs['contributors'])):
            adata = attrs['contributors'][i]
            if adata.get('contributorType') == 'Editor':
                if 'givenName' in adata and 'familyName' in adata:
                    s.add_editor(adata['givenName'], adata['familyName'])

        # Title…s?
        # TODO what happens if there are multiple titles?
        if path_exists(attrs, ('titles', 0, 'title')):
            s.add_field('title', attrs['titles'][0]['title'])

        if 'publisher' in attrs:
            s.add_field('publisher', attrs['publisher'])

        if 'publicationYear' in attrs:
            s.add_field('year', attrs['publicationYear'])

        if 'url' in attrs:
            s.add_field('url', attrs['url'])

        ctype = None
        if path_exists(attrs, ('container', 'type')):
            ctype = attrs['container']['type']
            cdata = attrs['container']

        if ctype == 'Journal':
            if 'title' in cdata:
                s.add_field('journal', cdata['title'])
        elif ctype == 'Book Series':
            if 'title' in cdata:
                s.add_field('booktitle', cdata['title'])

        if ctype in ('Journal', 'Book Series'):
            if 'volume' in cdata:
                s.add_field('volume', cdata['volume'])
            if 'issue' in cdata:
                s.add_field('issue', cdata['issue'])
            if cdata.get('identifierType') == 'ISSN':
                s.add_field('issn', cdata['identifier'])
            if 'firstPage' in cdata and 'lastPage' in cdata:
                s.add_field(
                    'pages', '{}--{}'.format(cdata['firstPage'],
                                             cdata['lastPage']))

        if path_exists(attrs, ('type', 'bibtex')):
            s.add_field('ENTRYTYPE', attrs['type']['bibtex'])

        self._ui.finish_subtask('DataCiteQuery')
        return s
