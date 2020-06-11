List of Checkers
================

.. _file_checkers:

This page lists all available checkers, i.e., checks that are run against your BibTeX file without pulling any data from data sources.

Note that each checker can be disabled by setting the option `check_<checker name>` to `false` in the :ref:`configuration <file_config>`.

Basic Checks
------------

DOI Checker
^^^^^^^^^^^

**Name**: `doi`

Checks that every entry has a DOI.

DOI URL Checker
^^^^^^^^^^^^^^^

**Name**: `doi_url`

Checks that URLs supplied in the `url` field do not point to `doi.org` - use the `doi` field for this instead.

Dead URL Checker
^^^^^^^^^^^^^^^^

**Name**: `dead_url`

Checks that URLs supplied in the `url` field can be accessed.

Required Fields Checker
^^^^^^^^^^^^^^^^^^^^^^^

**Name**: `required_fields`

Check that all required fields (configured via the config option `required`) are present.

Forbidden Fields Checker
^^^^^^^^^^^^^^^^^^^^^^^^

**Name**: `forbidden_fields`

Check that no forbidden fields (configured via the config option `forbidden`) are present.



Author Checks
-------------

Initial Dotted Check
^^^^^^^^^^^^^^^^^^^^

**Name**: `author_initial_dotted`

Checks if author initials are dotted. The 'dotted' form would be `John R. Doe`, the 'undotted' form would be `John R Doe`.

**Options:**

author_initial_want_dotted
  Set to `true` if you want the dotted form, to `false` if you want the undotted form.

Allcaps Name Checker
^^^^^^^^^^^^^^^^^^^^

**Name**: `author_names_allcaps`

Checks that author names are not in all caps.

First Name Initial Checker
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Name**: `author_names_firstinitial`

Checks that the first name of every author is not initialled. I.e., `John Doe` would be fine, `J Doe` or `J. Doe` would not.

Middle Name Initial Checker
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Name**: `author_names_middleinitial`

Checks that the middle names of every author are not initialled. I.e., `John Random Doe` would be fine, `John R Doe` or `John R. Doe` would not.

Last Name Initial Checker
^^^^^^^^^^^^^^^^^^^^^^^^^

**Name**: `author_names_lastinitial`

Checks that the last name of every author is not initialled. I.e., `John Doe` would be fine, `John D.` or `John D` would not.


ISBN Checks
-----------

Valid ISBN Checker
^^^^^^^^^^^^^^^^^^

**Name**: `isbn_valid`

Checks that a supplied ISBN is in fact a valid ISBN.

ISBN Format Checker
^^^^^^^^^^^^^^^^^^^

**Name**: `isbn_format`

Checks that all ISBNs are in the requested ISBN format.

**Options**:

isbn_format
  Set to either `"canonical"` or `"masked"`. This specifies the requested ISBN format.


ISBN Length Checker
^^^^^^^^^^^^^^^^^^^

**Name**: `isbn_length`

Checks that all ISBNs have the correct (requested) length.

**Options**:

isbn_length
  Set to either `10` or `13` (the number, not a string thereof) for the requested ISBN length


Publication Checks
------------------

Journal Abbrev Checker
^^^^^^^^^^^^^^^^^^^^^^

**Name**: `journal_abbrev`

Checks that journal names (in the fields `booktitle` and `journal`) do not contain abbreviations.

Journal Similarity Checker
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Name**: `journal_similarity`

Checks whether two journals (fields `booktitle` and `journal`) have very similar names and might actually mean the same journal in two different forms.

Publisher Similarity Check
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Name**: `publisher_similarity`

Checks whether two publishers (fields `organization` and `publisher`) have very similar names and might actually mean the same publisher in two different forms.


Journal Mutual Abbreviation Checker
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Name**: `journal_mutual_abbrev`

Checks whether two journals (fields `booktitle` and `journal`) could be abbreviations of each other.

Publisher Mutual Abbreviation Check
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Name**: `publisher_mutual_abbrev`

Checks whether two publishers (fields `organization` and `publisher`) could be abbreviations of each other.

Prefer Organization Checker
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Name**: `prefer_organization`

Checks whether the `publisher` field is set, but the `organization` field is not.

Prefer Date Checker
^^^^^^^^^^^^^^^^^^^

**Name**: `prefer_date`

Checks whether the `year`, `month` and / or `day` fields are set, but the `date` field is not.

**Options**:

prefer_date_or_year
  Do not emit an error if just `year`, but not `date`, `month` and `day` are set.

Date Parseable Checker
^^^^^^^^^^^^^^^^^^^^^^

**Name**: `date_parseable`

Checks if a date supplied via the `date` field is in a parseable form, i.e., a valid date.

Title Checks
------------

Capitalization Checker
^^^^^^^^^^^^^^^^^^^^^^

**Name**: `title_capitalization`

Checks that if the title contains a word with multiple capital letters, this words is set in curly braces. Otherwise, capitalization will likely be lost.
