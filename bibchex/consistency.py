import asyncio
import aiohttp
import re

from .config import Config

class NameChecker(object):
    NAME = "author-names"
    def __init__(self):
        pass

    async def check(self, entry):
        return check_one("authors", "Author", entry) + check_one("editors", "Editor", entry)

    async def check_one(self, field, name, entry):
        problems = []
        for author in getattr(entry, field):
            (first, last) = author
            first_lower_count = sum((int(c.islower()) for c in first))
            if first_lower_count == 0:
                problems.append(
                    ("bogus_firstname", "{} '{} {}' seems to have a bogus first name.".format(name, first, last), ""))
        return problems
    

class DOIChecker(object):
    NAME = "doi"
    def __init__(self):
        pass

    async def check(self, entry):
        doi = entry.data.get('doi')
        if not doi:
            suggested_doi = entry.get_doi()
            details = ""
            if suggested_doi:
                details = "Suggested DOI: {}".format(suggested_doi)
            elif entry.get_suggested_dois():
                details = "Suggested DOIs: {}".format(entry.get_suggested_dois())
                
            return [("missing_doi", "Missing DOI", details)]
        else:
            return []


class URLChecker(object):
    NAME = "url"

    def __init__(self):
        self.doi_re = re.compile('https?://(dx\.)?doi.org/.*')

    async def check(self, entry):
        url = entry.data.get('url')
        problems = []
        if not url:
            return []

        m = self.doi_re.match(url)
        if m:
            problems.append(("doi_url", "URL points to doi.org", ""))

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                status = resp.status
                if status >= 400 or status < 200:
                    problems.append(("dead_url", "URL seems inaccessible", "Accessing URL '{}' gives status code {}".format(url, status)))

        return problems

class RequiredFieldsChecker(object):
    NAME = "required_fields"

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        problems = []
        
        required_fields = self._cfg.get('required', entry)
        for field_raw in required_fields:
            field = field_raw.lower()

            if field == 'author':
                # Special handling
                if len(entry.authors) == 0:
                    problems.append(("missing_field", "Required field 'author' missing", ""))
            elif field == 'editor':
                # Special handling
                if len(entry.editors) == 0:
                    problems.append(("missing_field", "Required field 'editor' missing", ""))
            else:
                if field not in entry.data:
                    problems.append(("missing_field", "Required field '{}' missing".format(field), ""))

        return problems
