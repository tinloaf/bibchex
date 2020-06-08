import pytest_datadir_ng
from testutils import make_entry, parse_to_entries


class TestParsing:
    def test_parsing_urls(self, datadir):
        f = datadir['escaped.bib']
        entries = parse_to_entries(f)

        assert len(entries) == 2

        expected = 'https://url.de/with_some_underscores--and---dashes?yo&foo=bar%baz'

        assert entries['dummyNoSlashes'].data.get('url') == expected
        assert entries['dummy'].data.get('url') == expected
        
    def test_parsing_dois(self, datadir):
        f = datadir['escaped.bib']
        entries = parse_to_entries(f)

        assert len(entries) == 2

        expected = r'10.1000/this-fancy_doi%would!indeed&---be"valid'

        assert entries['dummyNoSlashes'].data.get('doi') == expected
        assert entries['dummy'].data.get('doi') == expected
        
        
