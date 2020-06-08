import re
from html.parser import HTMLParser
from urllib.parse import urlparse, urlunparse

import aiohttp
from nameparser import HumanName

from bibchex.config import Config
from bibchex.asyncrate import AsyncRateLimiter
from bibchex.util import parse_datetime
from bibchex.problems import RetrievalProblem
from bibchex.data import Suggestion


class RedirectException(Exception):
    def __init__(self, url, base_url):
        super().__init__()
        self.url = url
        self.base_url = base_url


class MetadataHTMLParser(HTMLParser):
    # TODO are there editors in meta tags?
    REFRESH_RE = re.compile(r'(\d)+;\s*url=\'(?P<url>.*)\'')

    SPECIAL = set(('date', 'author'))

    MAPPING = {
        'dc.title': 'title',
        'citation_title': 'title',
        'citation_publication_date': 'date',
        'dc.issued': 'date',
        'citation_doi': 'doi',
        'dc.identifier': 'doi',
        'citation_author': 'author',
        'dc.creator': 'author',
        'citation_volume': 'volume',
        'citation_issn': 'issn',
        'citation_publisher': 'publisher',
        'citation_journal_title': 'journal',
        'citation_conference_title': 'booktitle'

    }

    def __init__(self, ui, url):
        super(MetadataHTMLParser, self).__init__()
        self._ui = ui
        self._url = url

        self._metadata = {}
        self._authors = []

    def get_metadata(self):
        return self._metadata

    def get_authors(self):
        return self._authors

    def handle_author(self, name, content):
        n = HumanName(content)
        first = " ".join((n.first, n.middle))
        last = " ".join((n.title, n.last))
        if n.suffix:
            last += ", {}".format(n.suffix)

        self._authors.append((first, last))

    def handle_date(self, name, content):
        res = parse_datetime(content)
        self._metadata.update(res)

    def handle_other(self, name, content):
        if name not in self._metadata:
            self._metadata[name] = [content]
        else:
            self._metadata[name].append(content)

    def handle_refresh(self, content):
        m = MetadataHTMLParser.REFRESH_RE.match(content)
        if not m:
            raise RetrievalProblem("Did not understand meta refresh redirect.")

        new_url = m.groupdict()['url']

        raise RedirectException(new_url, self._url)

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return

        # Handle http-equiv redirects
        is_redirect = False
        content = None
        for (k, v) in attrs:
            if k == 'http-equiv' and v.lower() == 'refresh':
                is_redirect = True
            if k == 'content':
                content = v

        if is_redirect:
            self.handle_refresh(content)

        name = None
        content = None
        for (k, v) in attrs:
            if k == 'name':
                name = v.lower()
            elif k == 'content':
                content = v

        if name and name in MetadataHTMLParser.MAPPING:
            mapped_name = MetadataHTMLParser.MAPPING[name]
            if mapped_name in MetadataHTMLParser.SPECIAL:
                getattr(self, 'handle_{}'.format(mapped_name))(
                    mapped_name, content)
            else:
                self.handle_other(mapped_name, content)

    def handle_endtag(self, tag):
        pass

    def handle_data(self, data):
        pass


class MetaSource(object):
    DOI_RE = re.compile(r'https?://(dx\.)?doi.org/.*')
    HTTP_RE = re.compile(r'https?://.*', re.IGNORECASE)

    def __init__(self, ui):
        self._ui = ui
        self._cfg = Config()
        self._ratelimit = AsyncRateLimiter(100, 60)

    async def query(self, entry):
        problem = None
        result = None
        self._ui.increase_subtask('MetaQuery')
        url = self._sanitize_url(entry.data.get(
            'url'), entry.get_probable_doi())
        try:
            done = False
            while not done:
                try:
                    done = True
                    result = await self._execute_query(entry, url)
                except RedirectException as e:
                    done = False
                    url = self._handle_relative_url(e.url, e.base_url)

        except aiohttp.ClientError as e:
            self._ui.error("meta", "Connection problem: {}".format(e))
            problem = e
        except RetrievalProblem as e:
            self._ui.error("meta", "Retrieval problem: {}".format(e))
            problem = e

        return (result, problem)

    def _sanitize_url(self, url, doi):
        if doi:
            return "https://dx.doi.org/{}".format(doi)

        if url and MetaSource.DOI_RE.match(url):
            # Exclude DOI urls
            url = None

        if url and not MetaSource.HTTP_RE.match(url):
            # Maybe they forgot the http?
            url = "http://{}".format(url)

        return url

    def _handle_relative_url(self, newurl, baseurl):
        new_parsed = urlparse(newurl)
        if new_parsed.netloc:
            # Seems to be a complete url
            return newurl

        base_parsed = urlparse(baseurl)

        return urlunparse((base_parsed.scheme, base_parsed.netloc,
                           new_parsed.path, new_parsed.params,
                           new_parsed.query, new_parsed.fragment))

    async def _execute_query(self, entry, url):
        if not url:
            self._ui.finish_subtask('MetaQuery')
            return None

        # Okay, we're actually going to make a HTTP request
        await self._ratelimit.get()

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                status = resp.status
                if status != 200:
                    raise RetrievalProblem(
                        "Accessing URL {} returns status {}"
                        .format(url, status))

                html = await resp.text()

                parser = MetadataHTMLParser(self._ui, str(resp.url))
                parser.feed(html)

                s = Suggestion("meta", entry)

                for (k, v) in parser.get_metadata().items():
                    s.add_field(k, v)

                for (first, last) in parser.get_authors():
                    s.add_author(first, last)

                return s
