from testutils import set_config, run_to_checks
from aioresponses import aioresponses
import pytest


@pytest.fixture
def mhttp():
    with aioresponses() as m:
        yield m


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
