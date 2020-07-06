import pytest_datadir_ng
from testutils import set_config

from testutils import make_entry
from bibchex.data import Suggestion
from bibchex.unify import Unifier


class TestUnifier:
    def test_unify_entry(self, datadir, event_loop):
        set_config({'unify_booktitle': [
            [r'\d{4} IEEE (?P<name>[^\(]*) \((?P<short>[^\)]*)\)',
             r'Proceedings of the \d*(th|st|nd|rd) {name} \({short}.*\)'],
        ]})

        unify_me = make_entry(
            {'booktitle':
             ('2016 IEEE International Parallel and'
              ' Distributed Processing Symposium (IPDPS)')})

        u = Unifier()
        sugg = u.unify_entry(unify_me)

        assert (sugg.data['booktitle'][0] ==
                (r'Proceedings of the \d*(th|st|nd|rd)'
                 r' International Parallel and Distributed'
                 r' Processing Symposium \(IPDPS.*\)',
                 Suggestion.KIND_RE))

    def test_unify_suggestion(self, datadir, event_loop):
        set_config({'unify_booktitle': [
            [r'\d{4} IEEE (?P<name>[^\(]*) \((?P<short>[^\)]*)\)',
             r'Proceedings of the \d*(th|st|nd|rd) {name} \({short}.*\)'],
        ]})

        dummy_entry = make_entry({})
        sugg = Suggestion('test', dummy_entry)
        sugg.add_field('booktitle',
                       ('2016 IEEE International Parallel and'
                        ' Distributed Processing Symposium (IPDPS)'))

        u = Unifier()
        u.unify_suggestion(sugg)

        assert (sugg.data['booktitle'][0] ==
                (r'Proceedings of the \d*(th|st|nd|rd)'
                 r' International Parallel and Distributed'
                 r' Processing Symposium \(IPDPS.*\)',
                 Suggestion.KIND_RE))

    def test_chaining(self, datadir, event_loop):
        set_config({'unify_booktitle': [
            [r'(?P<prefix>.*)first(?P<suffix>.*)',
                r'{prefix}1st{suffix}', 'kind:plain', 'priority:50'],
            [r'(?P<prefix>.*) IEEE(?P<suffix>.*)',
                r'{prefix}{suffix}', 'kind:regex']
        ]})

        unify_me = make_entry(
            {'booktitle':
             ('Proceedings of the first IEEE conference on whatever')})

        u = Unifier()
        sugg = u.unify_entry(unify_me)

        assert (sugg.data['booktitle'][0] ==
                ((r'Proceedings of the 1st conference on whatever'),
                 Suggestion.KIND_RE))

        # Test chain-unifying suggestion
        sugg = Suggestion('test', unify_me)
        sugg.add_field('booktitle',
                       ('Proceedings of the first'
                        ' IEEE conference on whatever'))
        u.unify_suggestion(sugg)

        assert(sugg.data['booktitle'][0] ==
               (r'Proceedings of the 1st conference on whatever',
                Suggestion.KIND_RE))

    def test_repeating(self, datadir, event_loop):
        set_config({'unify_booktitle': [
            [r'(?P<prefix>.*) remove(?P<suffix>.*)',
                r'{prefix}{suffix}', 'priority:50', 'repeat', 'kind:plain'],
        ]})

        unify_me = make_entry(
            {'booktitle':
             ('Proceedings remove of remove some remove conference')})

        u = Unifier()
        sugg = u.unify_entry(unify_me)

        assert (sugg.data['booktitle'][0] ==
                ((r'Proceedings of some conference'),
                 Suggestion.KIND_PLAIN))

        # Test repeat-unifying suggestion
        sugg = Suggestion('test', unify_me)
        sugg.add_field('booktitle',
                       'Proceedings remove of remove some remove conference')

        u.unify_suggestion(sugg)

        assert(sugg.data['booktitle'][0] ==
               ('Proceedings of some conference', Suggestion.KIND_PLAIN))
