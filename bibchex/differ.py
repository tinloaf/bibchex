from isbnlib import canonical, to_isbn13

from bibchex.util import unlatexify, unify_hyphens
from bibchex.strutil import lower_case_first_letters, crush_spaces, is_allcaps
from bibchex.data import Difference
from bibchex.config import Config


def is_initial(s):
    return (len(s) == 1) or (len(s) == 2 and s[1] == '.')


def isbn_differ(entry_data, suggestion_data):
    entry_isbn = to_isbn13(canonical(entry_data))
    if not entry_isbn:
        return True

    suggestion_isbns = [to_isbn13(canonical(s)) for s in suggestion_data]

    return entry_isbn not in suggestion_isbns


class Differ(object):
    FIELD_PROPERTIES = {
        'doi': {'case': False},
        'title': {'first_letter_case': False},
        'isbn': {'diff_func': isbn_differ}
    }

    def __init__(self, entry):
        self._entry = entry
        self._cfg = Config()

    def diff(self, suggestion):
        """Compute and return a list of differences between the
        entity of this Differ and the list of suggestions passed."""
        return self._diff_general(suggestion) + \
            self._diff_people('authors', suggestion) + \
            self._diff_people('editors', suggestion)

    def _diff_people(self, field, suggestion):
        diffs = []

        assert field in ('authors', 'editors')
        if field == 'authors':
            singular = 'Author'
        else:
            singular = 'Editor'

        sugg_field = getattr(suggestion, field)
        entry_field = getattr(self._entry, field)

        if len(sugg_field) == 0:
            return []

        for i in range(0, max(len(sugg_field), len(entry_field))):
            if i >= len(sugg_field):
                diffs.append(
                    Difference(self._entry.get_id(),
                               suggestion.source,
                               '{} {}'.format(singular, i + 1),
                               'Person not present in retrieved \
                               {}: {} {}'.format(field, *entry_field[i])))
                continue

            if i >= len(entry_field):
                diffs.append(
                    Difference(self._entry.get_id(),
                               suggestion.source,
                               '{} {}'.format(singular, i + 1),
                               'Additional person in retrieved \
                               {}: {} {}'.format(field, *sugg_field[i])))
                continue

            entry_first, entry_last = entry_field[i]
            sugg_first, sugg_last = sugg_field[i]

            raw_sugg_first = sugg_first
            raw_sugg_last = sugg_last

            if self._cfg.get('authors_ignore_allcaps', self._entry, True):
                if is_allcaps("{} {}".format(sugg_first, sugg_last)):
                    sugg_first = sugg_first.lower()
                    sugg_last = sugg_last.lower()

                    entry_first = entry_first.lower()
                    entry_last = entry_last.lower()

            difference = False
            if crush_spaces(sugg_last) != crush_spaces(entry_last):
                difference = True

            # Check first names individually
            entry_first_words = entry_first.split(" ")
            sugg_first_words = entry_first.split(" ")
            if len(entry_first_words) != len(sugg_first_words):
                difference = True
            else:
                for (word_e, word_s) in zip(entry_first_words,
                                            sugg_first_words):
                    if not is_initial(word_e) and not is_initial(word_s):
                        difference |= (word_e != word_s)
                    else:
                        difference |= (word_s[0] != word_e[0])

            if difference:
                diffs.append(
                    Difference(self._entry.get_id(),
                               suggestion.source,
                               '{} {}'.format(singular, i + 1),
                               'Suggested {} name: \
                               {} {}'.format(singular.lower(),
                                             raw_sugg_first,
                                             raw_sugg_last)))
        return diffs

    def _diff_general(self, suggestion):
        diffs = []

        # Find fields where we have data in the entry, which is different from
        # the data in the suggestion
        for field in self._entry.data.keys():
            if field in suggestion.data:
                if isinstance(suggestion.data[field], list):
                    suggestion_data = suggestion.data[field]
                else:
                    suggestion_data = [suggestion.data[field]]

                entry_data = unlatexify(self._entry.data[field])

                # Cast everything to string
                suggestion_data = [str(d) for d in suggestion_data]

                # Unify hyphens
                entry_data = unify_hyphens(entry_data)
                suggestion_data = [unify_hyphens(d) for d in suggestion_data]

                # Crush spaces
                entry_data = crush_spaces(entry_data)
                suggestion_data = [crush_spaces(d) for d in suggestion_data]

                field_props = Differ.FIELD_PROPERTIES.get(field, {})

                if not field_props.get('case', True):
                    entry_data = entry_data.lower()
                    suggestion_data = [d.lower() for d in suggestion_data]

                if not field_props.get('first_letter_case', True):
                    entry_data = lower_case_first_letters(entry_data)
                    suggestion_data = [lower_case_first_letters(
                        d) for d in suggestion_data]

                if 'diff_func' in field_props:
                    if field_props['diff_func'](entry_data, suggestion_data):
                        diffs.append(Difference(
                            self._entry.get_id(),
                            suggestion.source,
                            field, suggestion.data[field]))
                else:
                    if entry_data not in suggestion_data:
                        diffs.append(Difference(
                            self._entry.get_id(),
                            suggestion.source,
                            field, suggestion.data[field]))

        # Find fields in the 'wanted' option for which the suggestion has data,
        # but the entry has not.
        wanted = set(self._cfg.get('wanted', self._entry, []))
        forbidden = set(self._cfg.get('forbidden', self._entry, []))
        wanted = wanted - forbidden
        for field in wanted:
            if field not in self._entry.data and field in suggestion.data:
                diffs.append(Difference(self._entry.get_id(),
                                        suggestion.source, field,
                                        suggestion.data[field]))

        return diffs
