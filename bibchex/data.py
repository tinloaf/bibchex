import re

from bibchex.util import unlatexify
from bibchex.strutil import merge_lines, crush_spaces, split_at_multiple

# Authors and editors are handled separately
FIELDS = ('ID', 'ENTRYTYPE', 'journal', 'comments', 'pages',
          'abstract', 'title', 'year', 'month', 'day', 'date',
          'volume', 'keyword', 'url', 'doi', 'booktitle',
          'publisher', 'number', 'isbn', 'issn', 'address',
          'edition', 'organization')
UNLATEXIFY_FIELDS = ('title', 'abstract', 'journal', 'booktitle', 'url', 'doi')
BOOL_OPTIONS = ("nodoi",)


def parse_bool(s):
    return s.lower().strip() in ("1", "true", "yes")


class Difference(object):
    def __init__(self, entry_id, source, field, suggestion):
        self.entry_id = entry_id
        self.source = source
        self.field = field
        self.suggestion = suggestion


class Problem(object):
    def __init__(self, entry_id, source, problem_type, message, details):
        self.entry_id = entry_id
        self.problem_type = problem_type
        self.source = source
        self.message = message
        self.details = details


class Entry(object):
    DOI_RE = re.compile(r'https?://(dx\.)?doi.org/(?P<doi>.*)')

    def __init__(self, bibtex_entry, ui):
        self._bentry = bibtex_entry
        self._id = bibtex_entry['ID']

        self.data = {}
        self.raw_data = {}
        self.options = {}
        self.authors = []
        self.editors = []

        self._ignore_diffs = {}
        self._ignore_problems = set()

        self._deduced_doi = None
        self._suggested_dois = []

        self._parse()
        self.authors = self._parse_people('author')
        self.editors = self._parse_people('editor')
        self._parse_options()
        self._doi_from_url()

        self._parse_ignore_diffs()
        self._parse_ignore_problems()

        self._ui = ui

    def get_id(self):
        return self._id

    def get_doi(self):
        if 'doi' in self.data:
            return self.data['doi']

        return self._deduced_doi

    def get_probable_doi(self):
        if self.get_doi():
            return self.get_doi()

        if self._suggested_dois:
            best_doi = max(set(self._suggested_dois),
                           key=self._suggested_dois.count)
            return best_doi

        return None

    def get_suggested_dois(self):
        return self._suggested_dois

    def add_suggested_doi(self, doi):
        self._suggested_dois.append(doi)

    def _doi_from_url(self):
        if 'doi' in self.data:
            return

        m = Entry.DOI_RE.match(self.data.get('url', ""))
        if not m:
            return

        self._deduced_doi = m.group('doi')

    def _parse_options(self):
        for k, v in self._bentry.items():
            if k[:len("bibchex-")] == "bibchex-":
                if k in ("bibchex-ignore-diffs", "bibchex-ignore-problems"):
                    pass  # Handled separately
                option = k[len("bibchex-"):].lower()
                if option in BOOL_OPTIONS:
                    self.options[option] = parse_bool(v)
                else:
                    self.options[option] = v

    def _parse_ignore_diffs(self):
        if 'bibchex-ignore-diffs' not in self._bentry:
            return

        ignores = self._bentry['bibchex-ignore-diffs'].split(';')
        for ignore in ignores:
            tokens = ignore.split('.')
            source = tokens[0].lower()

            if source not in self._ignore_diffs:
                self._ignore_diffs[source] = set()

            if len(tokens) > 1:
                self._ignore_diffs[source].add(tokens[1].lower())
            else:
                self._ignore_diffs[source].add("*")

    def _parse_ignore_problems(self):
        if 'bibchex-ignore-problems' not in self._bentry:
            return

        self._ignore_problems = set(
            (ignore.lower() for ignore in
             self._bentry['bibchex-ignore-problems'].split(';')))

    def should_ignore_diff(self, source, field):
        ignores = self._ignore_diffs.get(source.lower(), set())
        return field.lower().replace(" ", "") in ignores or "*" in ignores

    def should_ignore_problem(self, problem_type):
        return problem_type.lower() in self._ignore_problems

    def _parse_people(self, fieldname):
        # First, split the authors' names by 'and', which may not be
        # enclosed in braces
        # TODO check brace-enclosing

        if fieldname not in self._bentry:
            return []

        authors_raw = crush_spaces(merge_lines(self._bentry[fieldname]))
        authors_split = split_at_multiple(authors_raw, [' and ', ' AND '])
        result = []

        for author_name in authors_split:
            comma_count = author_name.count(',')
            if comma_count == 0:
                # Name is to be read literally.
                # Everything including the second-to-last capitalized
                # word becomes the first name
                words = author_name.split(' ')
                if len(words) == 1:
                    # Okay, only a last name
                    first_last = 0
                else:
                    i = len(words) - 2
                    while i > 0:
                        if words[i][0].isupper():
                            break
                        i -= 1
                    first_last = i + 1

                first_name = " ".join(words[:first_last])
                last_name = " ".join(words[first_last:])
            elif comma_count == 1:
                # Last, First format
                (last_name, first_name) = author_name.split(",")
                first_name = first_name.strip()
            elif comma_count == 2:
                # Special case for Doe, Jr., Jon
                (last_name, jr, first_name) = author_name.split(",")
                jr = jr.strip()
                first_name = first_name.strip()
                last_name = "{}, {}".format(last_name, jr)
            else:
                self._ui.warning("Entry",
                                 "Unrecognized {} format for '{}'"
                                 .format(fieldname, author_name))
                continue

            result.append(
                (unlatexify(first_name), unlatexify(last_name)))
        return result

    def _parse(self):
        for k, v in self._bentry.items():
            if k in FIELDS:
                if k.lower() in UNLATEXIFY_FIELDS:
                    self.data[k.lower()] = unlatexify(merge_lines(v))
                    self.raw_data[k.lower()] = merge_lines(v)
                else:
                    self.data[k.lower()] = merge_lines(v)


class Suggestion(object):
    def __init__(self, source, entry):
        self._entry = entry
        self.data = {}
        self.source = source
        self.authors = []
        self.editors = []

    def add_field(self, k, vs):
        self.data[k] = vs

    def add_author(self, first, last):
        self.authors.append((first, last))

    def add_editor(self, first, last):
        self.editors.append((first, last))
