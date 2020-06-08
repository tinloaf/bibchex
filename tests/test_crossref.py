import crossref_commons
import crossref_commons.retrieval
import crossref_commons.search

from unittest.mock import MagicMock

from bibchex.sources import CrossrefSource
from bibchex.ui import SilentUI

from testutils import make_entry


class TestCrossref:
    def test_reverse_doi_calls(self, monkeypatch, event_loop):
        mock_retrieval = MagicMock()
        mock_search = MagicMock()
        mock_search.search_publication = MagicMock(return_value=(0, []))
        monkeypatch.setattr(crossref_commons, "retrieval", mock_retrieval)
        monkeypatch.setattr(crossref_commons, "search", mock_search)

        cs = CrossrefSource(SilentUI())

        e = make_entry({'title': 'Testtitle',
                        'author': 'John Doe'})
        event_loop.run_until_complete(cs.get_doi(e))
        mock_search.search_publication.assert_any_call(
            [('bibliographic', 'Testtitle'), ('author', 'John Doe')], order='desc', sort='relevance'
        )

        mock_search.search_publication.reset_mock()
        e = make_entry({'title': 'Testtitle'})
        event_loop.run_until_complete(cs.get_doi(e))
        mock_search.search_publication.assert_called_with(
            [('bibliographic', 'Testtitle')], order='desc', sort='relevance'
        )

    def test_reverse_doi_steps(self, monkeypatch, event_loop):
        mock_retrieval = MagicMock()
        mock_search = MagicMock()
        mock_search.search_publication = MagicMock(return_value=(0, []))
        monkeypatch.setattr(crossref_commons, "retrieval", mock_retrieval)
        monkeypatch.setattr(crossref_commons, "search", mock_search)

        cs = CrossrefSource(SilentUI())

        e = make_entry({'title': 'Testtitle',
                        'author': 'John Doe'})
        # Succeed in step 1
        mock_search.search_publication.side_effect = [
            (1, [{'title': 'Testtitle', 'DOI': '1234'}])]
        event_loop.run_until_complete(cs.get_doi(e))
        mock_search.search_publication.assert_called_with(
            [('bibliographic', 'Testtitle'), ('author', 'John Doe')], order='desc', sort='relevance'
        )

        mock_search.search_publication.reset_mock()
        # Succeed in step 2
        mock_search.search_publication.side_effect = [(0, []),
                                                      (1, [{'title': 'Testtitle', 'DOI': '1234'}])]
        event_loop.run_until_complete(cs.get_doi(e))
        mock_search.search_publication.assert_any_call(
            [('bibliographic', 'Testtitle'), ('author', 'John Doe')], order='desc', sort='relevance'
        )
        mock_search.search_publication.assert_any_call(
            [('bibliographic', 'Testtitle'), ('author', 'Doe')], order='desc', sort='relevance'
        )

        mock_search.search_publication.reset_mock()
        # Succeed in step 3
        mock_search.search_publication.side_effect = [(0, []), (0, []),
                                                      (1, [{'title': 'Testtitle', 'DOI': '1234'}])]
        event_loop.run_until_complete(cs.get_doi(e))
        mock_search.search_publication.assert_any_call(
            [('bibliographic', 'Testtitle'), ('author', 'John Doe')], order='desc', sort='relevance'
        )
        mock_search.search_publication.assert_any_call(
            [('bibliographic', 'Testtitle'), ('author', 'Doe')], order='desc', sort='relevance'
        )
        mock_search.search_publication.assert_any_call(
            [('bibliographic', 'Testtitle')], order='desc', sort='relevance'
        )

    def test_reverse_doi_results(self, monkeypatch, event_loop):
        fake_return = (4, [
            {'title': 'foo',
             'DOI': '1234'},
            {'title': 'Bar',
             'DOI': 'abcd'},
            {'title': 'This is almost the correct titel',
             'DOI': 'fuzzy'},
            {'title': 'CASE SHOULD BE IRRELEVANT',
             'DOI': 'case'}
        ])

        mock_retrieval = MagicMock()
        mock_search = MagicMock()
        mock_search.search_publication = MagicMock(return_value=fake_return)
        monkeypatch.setattr(crossref_commons, "retrieval", mock_retrieval)
        monkeypatch.setattr(crossref_commons, "search", mock_search)

        cs = CrossrefSource(SilentUI())

        e = make_entry({'title': 'Bar'})
        result = event_loop.run_until_complete(cs.get_doi(e))
        mock_search.search_publication.assert_called_with(
            [('bibliographic', 'Bar')], order='desc', sort='relevance'
        )

        assert result[0] == "abcd"

        e = make_entry({'title': 'This is almost the correct title'})
        result = event_loop.run_until_complete(cs.get_doi(e))
        assert result[0] == "fuzzy"

        e = make_entry({'title': 'case should be irrelevant'})
        result = event_loop.run_until_complete(cs.get_doi(e))
        assert result[0] == "case"

    def test_query_calls(self, monkeypatch, event_loop):
        mock_retrieval = MagicMock()
        mock_search = MagicMock()
        mock_retrieval.get_publication_as_json = MagicMock()
        monkeypatch.setattr(crossref_commons, "retrieval", mock_retrieval)
        monkeypatch.setattr(crossref_commons, "search", mock_search)
        def side_effect(doi):
            raise ValueError()
        mock_retrieval.get_publication_as_json.side_effect = side_effect

        cs = CrossrefSource(SilentUI())
        
        e = make_entry({'doi': '1234'})
        result = event_loop.run_until_complete(cs.query(e))
        mock_retrieval.get_publication_as_json.assert_called_with(
            '1234'
        )
        
