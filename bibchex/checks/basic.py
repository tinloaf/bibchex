import aiohttp
import re

from bibchex.config import Config


class DOIChecker(object):
    NAME = "doi"

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, True):
            return []

        doi = entry.data.get('doi')
        if not doi:
            suggested_doi = entry.get_doi()
            details = ""
            if suggested_doi:
                details = "Suggested DOI: {}".format(suggested_doi)
            elif entry.get_suggested_dois():
                details = "Suggested DOIs: {}".format(
                    entry.get_suggested_dois())

            return [(type(self).NAME, "Missing DOI", details)]

        return []


class DOIURLChecker(object):
    NAME = "doi_url"
    DOI_RE = re.compile(r'https?://(dx\.)?doi.org/.*')

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, True):
            return []

        url = entry.data.get('url')
        problems = []
        if not url:
            return []

        m = DOIURLChecker.DOI_RE.match(url)
        if m:
            problems.append((type(self).NAME, "URL points to doi.org", ""))

        return problems


class DeadURLChecker(object):
    NAME = "dead_url"

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, True):
            return []

        url = entry.data.get('url')
        problems = []
        if not url:
            return []

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                status = resp.status
                if status >= 400 or status < 200:
                    problems.append((type(self).NAME, "URL seems inaccessible",
                                     "Accessing URL '{}' gives status code {}"
                                     .format(url, status)))

        return problems


class RequiredFieldsChecker(object):
    NAME = "required_fields"

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, True):
            return []

        problems = []

        required_fields = self._cfg.get('required', entry)
        for field_raw in required_fields:
            field = field_raw.lower()

            if field == 'author':
                # Special handling
                if len(entry.authors) == 0:
                    problems.append(
                        (type(self).NAME,
                         "Required field 'author' missing", ""))
            elif field == 'editor':
                # Special handling
                if len(entry.editors) == 0:
                    problems.append(
                        (type(self).NAME,
                         "Required field 'editor' missing", ""))
            else:
                if field not in entry.data:
                    problems.append(
                        (type(self).NAME,
                         "Required field '{}' missing".format(field), ""))

        return problems


class ForbiddenFieldsChecker(object):
    NAME = "forbidden_fields"

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, True):
            return []

        problems = []

        forbidden_fields = self._cfg.get('forbidden_fields', entry, [])
        for field_raw in forbidden_fields:
            field = field_raw.lower()

            if field == 'author':
                # Special handling
                if len(entry.authors) > 0:
                    problems.append(
                        (type(self).NAME,
                         "Forbidden field 'author' present", ""))
            if field == 'editor':
                # Special handling
                if len(entry.editors) > 0:
                    problems.append(
                        (type(self).NAME,
                         "Forbidden field 'editor' present", ""))
            else:
                if field in entry.data:
                    problems.append(
                        (type(self).NAME,
                         "Forbidden field '{}' present".format(field), ""))

        return problems
