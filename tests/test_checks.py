from testutils import set_config, run_to_checks
from aioresponses import aioresponses
import pytest


@pytest.fixture
def mhttp():
    with aioresponses() as m:
        yield m


class TestTitleChecks:
    def test_title_capitalization(self, datadir, event_loop):
        f = datadir['problem_title.bib']

        set_config({'check_title_capitalization': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('boringTitle', 'title_capitalization') not in problem_set
        assert ('bracedTitle', 'title_capitalization') not in problem_set
        assert ('fancyTitle', 'title_capitalization') in problem_set
        assert ('buggyTitle', 'title_capitalization') not in problem_set

    def test_has_title(self, datadir, event_loop):
        f = datadir['problem_title.bib']

        set_config({'check_has_title': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('boringTitle', 'has_title') not in problem_set
        assert ('noTitle', 'has_title') in problem_set


class TestPublicationChecks:
    def test_booktitle_format(self, datadir, event_loop):
        f = datadir['problem_publication.bib']

        set_config({'check_booktitle_format': True,
                    'booktitle_format':
                    (r'Proceedings of the \d+(th|st|rd|nd) .*'
                     r" \([a-z]*[A-Z]+[a-z]*’{short_year}\)")})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('wrongBooktitle', 'booktitle_format') in problem_set
        assert ('wrongYear', 'booktitle_format') in problem_set
        assert ('goodBooktitle', 'booktitle_format') not in problem_set

    def test_journal_abbrev(self, datadir, event_loop):
        f = datadir['problem_publication.bib']

        set_config({'check_journal_abbrev': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('dottedJournal', 'journal_abbrev') in problem_set
        assert ('abbrevJournal', 'journal_abbrev') in problem_set
        assert ('fullJournal', 'journal_abbrev') not in problem_set

    def test_journal_similarity(self, datadir, event_loop):
        f = datadir['problem_publication.bib']

        set_config({'check_journal_similarity': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.source, problem.message)
                          for problem in global_problems)

        assert len(problem_set) == 1
        assert (('journal_similarity',
                 ("Journal names 'Theoretica Computer Science' and "
                  "'Theoretical Computer Science'"
                  " seem very similar.")) in problem_set or
                ('journal_similarity',
                 ("Journal names 'Theoretical Computer Science' and "
                  "'Theoretica Computer Science'"
                  " seem very similar.")) in problem_set)

    def test_publisher_similarity(self, datadir, event_loop):
        f = datadir['problem_publication.bib']

        set_config({'check_publisher_similarity': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.source, problem.message)
                          for problem in global_problems)

        assert len(problem_set) == 1
        assert (('publisher_similarity',
                 ("Publisher names 'Some Fancy Publishing Hose' and "
                  "'Some Fancy Publishing House'"
                  " seem very similar.")) in problem_set or
                ('publisher_similarity',
                 ("Publisher names 'Some Fancy Publishing House' and "
                  "'Some Fancy Publishing Hose'"
                  " seem very similar.")) in problem_set)

    def test_journal_mutual_abbrev(self, datadir, event_loop):
        f = datadir['problem_publication.bib']

        set_config({'check_journal_mutual_abbrev': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.source, problem.message)
                          for problem in global_problems)

        assert ('journal_mutual_abbrev',
                ("Journal 'Theoretica Computer Science' could be an abbreviation of "
                 "'Theoretical Computer Science'.")) in problem_set
        assert ('journal_mutual_abbrev',
                ("Journal 'Theo Comp Sci' could be an abbreviation of "
                 "'Theoretical Computer Science'.")) in problem_set
        assert ('journal_mutual_abbrev',
                ("Journal 'Theo Comp Sci' could be an abbreviation of "
                 "'Theoretica Computer Science'.")) in problem_set
        assert ('journal_mutual_abbrev',
                ("Journal 'TCS' could be an abbreviation of "
                 "'Theoretica Computer Science'.")) in problem_set
        # Many more!

    def test_publisher_mutual_abbrev(self, datadir, event_loop):
        f = datadir['problem_publication.bib']

        set_config({'check_publisher_mutual_abbrev': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.source, problem.message)
                          for problem in global_problems)

        assert ('publisher_mutual_abbrev',
                ("Publisher 'So Fa Pu Ho' could be an abbreviation of "
                 "'Some Fancy Publishing House'.")) in problem_set

    def test_prefer_organization(self, datadir, event_loop):
        f = datadir['problem_publication.bib']

        set_config({'check_prefer_organization': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('fullJournal', 'prefer_organization') in problem_set
        assert ('abbrevJournal', 'prefer_organization') not in problem_set

    def test_prefer_date(self, datadir, event_loop):
        f = datadir['problem_publication.bib']

        set_config({'check_prefer_date': True,
                    'prefer_date_or_year': False})
        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('abbrevJournal', 'prefer_date') not in problem_set
        assert ('fullJournal', 'prefer_date') in problem_set
        assert ('shortJournal', 'prefer_date') in problem_set
        assert ('typoJournal', 'prefer_date') in problem_set

        set_config({'check_prefer_date': True,
                    'prefer_date_or_year': True})
        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('abbrevJournal', 'prefer_date') not in problem_set
        assert ('fullJournal', 'prefer_date') in problem_set
        assert ('shortJournal', 'prefer_date') in problem_set
        assert ('typoJournal', 'prefer_date') not in problem_set

    def test_parseable_date(self, datadir, event_loop):
        f = datadir['problem_publication.bib']

        set_config({'check_date_parseable': True})
        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('brokenDate', 'date_parseable') in problem_set
        assert ('abbrevJournal', 'date_parseable') not in problem_set


class TestISBNChecks:
    def test_valid_isbn(self, datadir, event_loop):
        f = datadir['problem_isbn.bib']

        set_config({'check_isbn_valid': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('hasInvalidISBN', 'isbn_valid') in problem_set
        assert ('cormen13masked', 'isbn_valid') not in problem_set
        assert ('cormen13unmasked', 'isbn_valid') not in problem_set
        assert ('cormen10unmasked', 'isbn_valid') not in problem_set
        assert ('cormen10masked', 'isbn_valid') not in problem_set

    def test_isbn_format(self, datadir, event_loop):
        f = datadir['problem_isbn.bib']

        set_config({'check_isbn_format': True,
                    'isbn_format': 'canonical'})
        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('hasInvalidISBN', 'isbn_format') not in problem_set
        assert ('cormen13masked', 'isbn_format') in problem_set
        assert ('cormen13unmasked', 'isbn_format') not in problem_set
        assert ('cormen10unmasked', 'isbn_format') not in problem_set
        assert ('cormen10masked', 'isbn_format') in problem_set

        set_config({'check_isbn_format': True,
                    'isbn_format': 'masked'})
        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('hasInvalidISBN', 'isbn_format') not in problem_set
        assert ('cormen13masked', 'isbn_format') not in problem_set
        assert ('cormen13unmasked', 'isbn_format') in problem_set
        assert ('cormen10unmasked', 'isbn_format') in problem_set
        assert ('cormen10masked', 'isbn_format') not in problem_set

    def test_isbn_length(self, datadir, event_loop):
        f = datadir['problem_isbn.bib']

        set_config({'check_isbn_length': True,
                    'isbn_length': 13})
        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('hasInvalidISBN', 'isbn_length') not in problem_set
        assert ('cormen13masked', 'isbn_length') not in problem_set
        assert ('cormen13unmasked', 'isbn_length') not in problem_set
        assert ('cormen10unmasked', 'isbn_length') in problem_set
        assert ('cormen10masked', 'isbn_length') in problem_set

        set_config({'check_isbn_length': True,
                    'isbn_length': 10})
        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('hasInvalidISBN', 'isbn_length') not in problem_set
        assert ('cormen13masked', 'isbn_length') in problem_set
        assert ('cormen13unmasked', 'isbn_length') in problem_set
        assert ('cormen10unmasked', 'isbn_length') not in problem_set
        assert ('cormen10masked', 'isbn_length') not in problem_set


class TestBasicChecks:
    def test_doi(self, datadir, event_loop):
        f = datadir['problem_basic.bib']

        set_config({'check_doi': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('noDOI', 'doi') in problem_set
        assert ('DOIfromURL', 'doi') in problem_set
        assert ('withDOI', 'doi') not in problem_set

        for problem in problems:
            if problem.entry_id == 'DOIfromURL' and \
               problem.source == 'doi':
                assert problem.details == 'Suggested DOI: 10.1000/1234'

    def test_doi_url(self, datadir, event_loop):
        f = datadir['problem_basic.bib']

        set_config({'check_doi_url': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('DOIfromURL', 'doi_url') in problem_set
        assert ('withDOI', 'doi_url') not in problem_set

    def test_dead_url(self, mhttp, datadir, event_loop):
        f = datadir['problem_basic.bib']

        set_config({'check_dead_url': True})

        mhttp.get('https://dx.doi.org/10.1000/1234', status=200)
        mhttp.get('https://dead.url/notfound', status=404)

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('deadURL', 'dead_url') in problem_set
        assert ('DOIfromURL', 'dead_url') not in problem_set

    def test_required(self, mhttp, datadir, event_loop):
        f = datadir['problem_basic.bib']

        set_config({'check_required_fields': True,
                    'required': ['author', 'editor', 'title']})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('noAuthors', 'required_fields') in problem_set
        assert ('noEditors', 'required_fields') in problem_set
        assert ('noTitle', 'required_fields') in problem_set
        assert ('complete', 'required_fields') not in problem_set

    def test_forbidden(self, mhttp, datadir, event_loop):
        f = datadir['problem_basic.bib']

        set_config({'check_forbidden_fields': True,
                    'forbidden_fields': ['author', 'editor', 'title']})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('noAuthors', 'forbidden_fields') in problem_set
        assert ('noEditors', 'forbidden_fields') in problem_set
        assert ('noTitle', 'forbidden_fields') in problem_set
        assert ('complete', 'forbidden_fields') in problem_set
        assert ('almostEmpty', 'forbidden_fields') not in problem_set


class TestAuthorChecks:
    def test_initial_dotted(self, datadir, event_loop):
        f = datadir['problem_authors.bib']

        set_config({'check_author_initial_dotted': True,
                    'author_initial_want_dotted': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('hasAbbrevMiddleInitials',
                'author_initial_dotted') in problem_set
        assert ('hasAbbrevSpaceMiddleInitials',
                'author_initial_dotted') in problem_set
        assert ('hasDottedMiddleInitials',
                'author_initial_dotted') not in problem_set
        assert ('hasDottedSpaceMiddleInitials',
                'author_initial_dotted') not in problem_set
        assert ('hasAbbrevFirst', 'author_initial_dotted') in problem_set
        assert ('hasFullName', 'author_initial_dotted') not in problem_set

        set_config({'check_author_initial_dotted': True,
                    'author_initial_want_dotted': False})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('hasAbbrevMiddleInitials',
                'author_initial_dotted') not in problem_set
        assert ('hasAbbrevSpaceMiddleInitials',
                'author_initial_dotted') not in problem_set
        assert ('hasDottedMiddleInitials',
                'author_initial_dotted') in problem_set
        assert ('hasDottedSpaceMiddleInitials',
                'author_initial_dotted') in problem_set
        assert ('hasAbbrevFirst', 'author_initial_dotted') not in problem_set
        assert ('hasFullName', 'author_initial_dotted') not in problem_set

    def test_allcaps_names(self, datadir, event_loop):
        f = datadir['problem_authors.bib']

        set_config({'check_author_names_allcaps': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('hasAllcapsFirst', 'author_names_allcaps') in problem_set
        assert ('hasAllcapsLast', 'author_names_allcaps') in problem_set
        assert ('hasFullName', 'author_names_allcaps') not in problem_set
        assert ('hasDottedLast', 'author_names_allcaps') not in problem_set
        assert ('hasAbbrevLast', 'author_names_allcaps') not in problem_set

    def test_first_name_initial(self, datadir, event_loop):
        f = datadir['problem_authors.bib']

        set_config({'check_author_names_firstinitial': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('hasDottedFirst', 'author_names_firstinitial') in problem_set
        assert ('hasAbbrevFirst', 'author_names_firstinitial') in problem_set
        assert ('hasFullName', 'author_names_firstinitial') not in problem_set
        assert ('hasAbbrevLast', 'author_names_firstinitial') not in problem_set

    def test_middle_name_initial(self, datadir, event_loop):
        f = datadir['problem_authors.bib']

        set_config({'check_author_names_middleinitial': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('hasDottedMiddleInitials',
                'author_names_middleinitial') in problem_set
        assert ('hasDottedSpaceMiddleInitials',
                'author_names_middleinitial') in problem_set
        assert ('hasAbbrevMiddleInitials',
                'author_names_middleinitial') in problem_set
        assert ('hasAbbrevSpaceMiddleInitials',
                'author_names_middleinitial') in problem_set
        assert ('hasFullName', 'author_names_middleinitial') not in problem_set

    def test_last_name_initial(self, datadir, event_loop):
        f = datadir['problem_authors.bib']

        set_config({'check_author_names_lastinitial': True})

        (problems, global_problems) = run_to_checks(f, event_loop)
        problem_set = set((problem.entry_id, problem.source)
                          for problem in problems)

        assert ('hasAbbrevLast', 'author_names_lastinitial') in problem_set
        assert ('hasDottedLast', 'author_names_lastinitial') in problem_set
