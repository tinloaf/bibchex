Available Data Sources
======================

.. _file_sources:

Data sources are services that are used to pull in meta data for your references. The meta data in your BibTeX file is then compared to the pulled data and differences are highlighted. This page lists the used sources together with their quirks and options, if any.


CrossRef
--------

The Crossref source pulls data from crossref.org, the largest DOI registry. Most publications that have a DOI should have their meta data registered at crossref. To also be able to find publications for which you do not have set a DOI in your BibTeX file, we perform a :ref:`reverse DOI search <reverse_doi>` first for any publication without a known DOI.

**Options**:

crossref_plus
  If you are a subscriber to "Crossref Plus", set this option to your token to use the "premium" API instead of the free one. The retrieved data should be the same as for the free API, but you might see improved performance.

crossref_mailto
  If you use the free API, Crossref mandates submitting a valid email address with each request to contact you in case of problems. **Please set this option to an email address that you can receive.**

doi_fuzzy_threshold
  A number between 0 and 100 (in percent). This defines how large the fuzzy similarity between the title in your BibTeX file and the title of a publication retrieved via :ref:`reverse DOI search <reverse_doi>` must be for the DOI to be considered. 


DataCite
--------

DataCite is a DOI registry mainly intended for research data publications. Meta data for publications registrered with DataCite is pulled via their API.

ISBN
----

The ISBN data source uses one of several ISBN-to-meta-data providers (at the moment: Google Books and openlibrary.org by the Internet Archive) to retrieve meta data for any publication that has an ISBN. Currently, there is no reverse ISBN search, so you must set the ISBN manually for all your publications having an ISBN.

Meta
----

The Meta data source retrieves the website pointed to by a BibTeX entry's URL (or the DOI, if no URL is given). Most of the time, this URL leads to a publisher's page about the relevant publication. Many of these publisher pages contain embedded meta data in a machine-readable form. If this is the case, this meta data is retrieved.

.. _reverse_doi:

Reverse DOI Search
------------------

Currently, only the Crossref source supports `reverse DOI search`. For all your BibTeX item which
have no DOI set (and which can consequently not be looked up by Crossref and DataCite), this will
try to automatically determine a DOI by searching for the title and authors on Crossref. If a
publication is returned the title of which matches your set title to at least
``doi_fuzzy_threshold`` percent (using a fuzzy match), the retrieved DOI will be assumed to belong
to the respective entry.
