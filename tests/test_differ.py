import pytest_datadir_ng

from testutils import make_entry, parse_to_entries
from bibchex.data import Suggestion
from bibchex.differ import Differ

class TestDiffer:
    def test_re_suggestion(self, datadir):
        e = make_entry({'title': 'This is some title.',
                        'booktitle':
                        "Proceedings of the 20th Conference on Something Awesome (CSA'20)"})
        
        s = Suggestion('test', e)
        s.add_field('title', 'This is some title.', kind=Suggestion.KIND_RE)
        s.add_field('booktitle',
                    r'Proceedings of the \d+(th|st|rd|nd) .* \(.*\)',
                    kind=Suggestion.KIND_RE)

        d = Differ(e)
        result = d.diff(s)
        assert result == []

        s = Suggestion('nonmatching_test', e)
        s.add_field('booktitle',
                    r'Nope',
                    kind=Suggestion.KIND_RE)
        result = d.diff(s)
        assert len(result) == 1
