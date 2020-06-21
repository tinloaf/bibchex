import re
from html.parser import HTMLParser
from urllib.parse import urlparse, urlunparse
import asyncio
import base64

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
        'dc.identifier': {'field': 'doi',
                          'attr_ifpresent': {'scheme': 'doi'}},
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
        try:
            res = parse_datetime(content)
            self._metadata.update(res)
        except:
            self._ui.warn("Meta",
                          "Failed to parse date '{}'".format(content))

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
        other_attrs = {}
        for (k, v) in attrs:
            if k == 'name':
                name = v.lower()
            elif k == 'content':
                content = v
            else:
                other_attrs[k.lower()] = v

        if name and name in MetadataHTMLParser.MAPPING:
            if isinstance(MetadataHTMLParser.MAPPING[name], str):
                mapped_name = MetadataHTMLParser.MAPPING[name]
                if mapped_name in MetadataHTMLParser.SPECIAL:
                    getattr(self, 'handle_{}'.format(mapped_name))(
                        mapped_name, content)
                else:
                    self.handle_other(mapped_name, content)
            else:
                mapping_data = MetadataHTMLParser.MAPPING[name]
                mapped_name = mapping_data['field']
                skip = False

                for (k, v) in mapping_data.get('attr_ifpresent',
                                               dict()).items():
                    if k.lower() in other_attrs:
                        if other_attrs[k.lower()] != v.lower():
                            skip = True

                for (k, v) in mapping_data.get('attr', dict()).items():
                    if k.lower() not in other_attrs or \
                       other_attrs[k.lower()] != v.lower():
                        skip = True

                if not skip:
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
    DOI_RE = re.compile(r'https?://(dx\.)?doi.org/(?P<doi>.*)')
    HTTP_RE = re.compile(r'https?://.*', re.IGNORECASE)
    # This is sufficient to fool some of the less advanced bot-detection
    # heuristics into not blocking our requests. Looking at you, JSTOR!
    HEADERS = {
        'accept': ('text/html,application/xhtml+xml,'
                   'application/xml;q=0.9,image/webp,*/*;q=0.8'),
        'User-Agent': ('Mozilla/5.0 (X11; Ubuntu; '
                       'Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0')
    }

    def __init__(self, ui):
        self._ui = ui
        self._cfg = Config()
        # dx.doi.org (sometimes) has very harsh rate limits. This seems to be
        # some cloudflare magic
        self._ratelimit = AsyncRateLimiter(50, 10)
        self._doi_ratelimit = AsyncRateLimiter(20, 10)
        self._max_retries = 5
        self._retry_pause = 10  # Wait an additional 10 seconds before a retry

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
                    if url and MetaSource.DOI_RE.match(url):
                        result = await self._execute_doi_query(entry, url)
                    else:
                        result = await self._execute_query(entry, url)
                except RedirectException as e:
                    done = False
                    url = self._handle_relative_url(e.url, e.base_url)

        except aiohttp.ClientError as e:
            self._ui.finish_subtask('MetaQuery')
            self._ui.error("meta", "Connection problem: {}".format(e))
            problem = e
        except RetrievalProblem as e:
            self._ui.error("meta", "Retrieval problem: {}".format(e))
            problem = e

        return (result, problem)

    def _sanitize_url(self, url, doi):
        if url and MetaSource.DOI_RE.match(url) and doi:
            # Recreate clean DOI URL from DOI
            url = None

        if url:
            if not MetaSource.HTTP_RE.match(url):
                # Maybe they forgot the http?
                url = "http://{}".format(url)
            return url

        if doi:
            return "https://dx.doi.org/{}".format(doi)

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

    def _detect_captcha(self, text):
        captcha_re = re.compile(r'.*captcha.*', re.IGNORECASE)

        if captcha_re.match(text):
            return True
        else:
            return False

    async def _execute_query(self, entry, url, retry_number=0):
        if not url:
            self._ui.finish_subtask('MetaQuery')
            return None

        # Okay, we're actually going to make a HTTP request
        await self._ratelimit.get()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url,
                                       headers=MetaSource.HEADERS) as resp:
                    status = resp.status
                    if status == 403:
                        try:
                            html = await resp.text()
                            if self._detect_captcha(html):
                                self._ui.finish_subtask('MetaQuery')
                                self._ui.message(
                                    "Meta",
                                    (f"URL {url} requires a captcha to "
                                     "be solved. Giving up."))
                                raise RetrievalProblem(
                                    (f"URL {url} requires a "
                                     "captcha to be solved.")
                                )
                        except:
                            pass

                        if retry_number == self._max_retries:
                            self._ui.finish_subtask('MetaQuery')
                            raise RetrievalProblem(
                                (f"URL {url} still results in 403 "
                                 f"after {self._max_retries} retries."
                                 " Giving up."))
                        self._ui.debug("Meta",
                                       (f"Got a 403 while accessing {url}."
                                        f" Backing off. "
                                        f"Retry {retry_number+1}..."))
                        await self._ratelimit.backoff()
                        await asyncio.sleep(self._retry_pause)
                        return await self._execute_query(entry, url,
                                                         retry_number+1)

                    if status != 200:
                        self._ui.finish_subtask('MetaQuery')
                        raise RetrievalProblem(
                            "Accessing URL {} returns status {}"
                            .format(url, status))

                    try:
                        html = await resp.text()
                    except UnicodeDecodeError:
                        self._ui.finish_subtask('MetaQuery')
                        raise RetrievalProblem(
                            f"Content at URL {url} could not be interpreted")

                    parser = MetadataHTMLParser(self._ui, str(resp.url))
                    parser.feed(html)

                    sugg = Suggestion("meta", entry)

                    for (k, v) in parser.get_metadata().items():
                        sugg.add_field(k, v)

                    for (first, last) in parser.get_authors():
                        sugg.add_author(first, last)

                    self._ui.finish_subtask('MetaQuery')
                    return sugg
        except asyncio.TimeoutError:
            self._ui.finish_subtask('MetaQuery')
            self._ui.error("Meta",
                           f"Timeout trying to retrieve URL {url}")
            raise RetrievalProblem(
                f"Timeout trying to retrieve URL {url}")

    async def _execute_doi_query(self, entry, url, retry_number=0):
        m = MetaSource.DOI_RE.match(url)
        doi = m.groupdict()['doi']
        api_url = f"https://dx.doi.org/api/handles/{doi}"

        # Okay, we're actually going to make a HTTP request
        await self._doi_ratelimit.get()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as resp:
                    status = resp.status
                    if status == 403:
                        if retry_number == self._max_retries:
                            raise RetrievalProblem(
                                (f"URL {api_url} still results in 403 "
                                 f"after {self._max_retries} retries."
                                 " Giving up."))
                        self._ui.debug(
                            "Meta",
                            (f"Got a 403 while accessing {api_url}. "
                             f" Backing off. Retry {retry_number+1}."))
                        await self._doi_ratelimit.backoff()
                        await asyncio.sleep(self._retry_pause)
                        return await self._execute_doi_query(entry, url,
                                                             retry_number+1)

                    if status != 200:
                        self._ui.finish_subtask('MetaQuery')
                        raise RetrievalProblem(
                            f"Accessing URL {api_url} returns status {status}")

                    try:
                        data = await resp.json()
                    except UnicodeDecodeError:
                        self._ui.finish_subtask('MetaQuery')
                        raise RetrievalProblem(
                            (f"Content at URL {api_url} could not "
                             "be interpreted as JSON"))

                    target_url = None
                    for val in data.get('values', []):
                        if val.get('type') == 'URL':
                            if val['data']['format'] == 'string':
                                target_url = val['data']['value']
                            elif val['data']['format'] == 'base64':
                                target_url = base64.b64decode(
                                    val['data']['value'])

                    if target_url:
                        return await self._execute_query(entry, target_url)

                    self._ui.finish_subtask('MetaQuery')
                    self._ui.warn("Meta",
                                  (f"DOI-URL {api_url} did not resolve to a "
                                   "URL. Giving up."))
                    return None
        except asyncio.TimeoutError:
            self._ui.finish_subtask('MetaQuery')
            self._ui.error("Meta",
                           f"Timeout trying to retrieve URL {api_url}")
            raise RetrievalProblem(
                f"Timeout trying to retrieve URL {api_url}")
