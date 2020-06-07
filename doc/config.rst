BibCheX Configuration
=====================

.. _file_config:

This page explains all possible options that can be specified in the config JSON file.

Configuration is possible at multiple levels. The config JSON file must contain an object at its top
level. In this object, all configuration options can be set. Additionally, the top object can have a
key ``sub``, which can contain a list of JSON objects. Each object contains option overrides for
specific cases, e.g. specific BibTeX item types. See :ref:`config overrides <sub_config>` and
:ref:`per-item configuration <item_config>` for details.

Main Configuration Options
--------------------------

required
  List of fields that must be present in every item
	**Type**: list of string

forbidden
  List of fields that must never be present
	**Type**: list of string
	
wanted
  List of fields the value of which interests us. All other fields will not be checked against the data returned by data sources.
	
dot_initials
  Whether authors' initials should be dotted, i.e., 'John R. Doe' instead of 'John R Doe'
	**Type**: boolean

authors_ignore_allcaps
  Whether to ignore author name capitalization for data sources that return names in all caps.
	**Type**: boolean

title_ignore_allcaps
  Whether to ignore title capitalization for data sources that return names in all caps
	**Type**: boolean
	

Individual checkers
-------------------

All checks (i.e., tests that do not compare to data fetched from some source) can be enabled or
disabled. Each checker has a name; refer to the :ref:`list of checkers <file_checkers>` for the
names of the checkers. Additionally, the output will tell you the names of the checkers that have
detected problems. Each such checker can be enabled/disabled by setting the option
``check_<checker_name>``. For example, setting ``check_journal_abbrev`` to ``false`` will disable
the check for abbreviated journal names.

By default, all checkers are enabled. Some checkers take additional options. These are listed on the
:ref:`list of checkers <file_checkers>`.
  
Data sources
------------

Some of the data sources take additional options. These are:

crossref_plus
  Your crossref plus credentials, in case you have them. If you don't set this option, the free version will be used.
	**Type**: string

crossref_mailto
  If you use the free Crossref API access, please provide a valid email address here.
	**Type**: string
	

.. _sub_config:

Config Overrides
----------------

The `sub` key in the main config object can contain overrides for all config options. The `sub` key expects a list of objects. Each object must contain the keys `select_field` and `select_re`, where `select_field` expects the name of a BibTeX field, and `select_re` expects a regular expression. For each entry in your BibTeX file, if the specified field matches the specified regular expression, the specified overrides will be applied. There always is a field named `entrytype` that contains the type of the BibTeX entry.

In the following example, the required fields (option `required`) are configured to be `author` and `title`. For entries of type `article`, we also want the `journal` to be specified:

.. code-block:: yaml

	 {
			"required": ["author", "title"],

			"sub": [
					{
							"select_field": "entrytype",
							"select_re": "article",
							"required": ["author", "title", "journal"]
					}
			]
	}


.. _item_config:

Per-Item Configuration
----------------------

Problems raised by :ref:`checkers <file_checkers>` as well as differences to the data pulled in by :ref:`data sources <file_sources>` can be ignored on a per-item basis.

To ignore a problem raised by a checker, find the name of the checker. The output HTML file tells you the name of the checker for each problem. Then, in your BibTeX file, add to the item in question a field ``bibchex-ignore-problems``. The data of that field is a semicolon-separated list of checker names to ignore.

As an example, an item for which problems raised by the ``dead_url`` and ``isbn_length`` checkers should be ignored could look like this:

.. code-block:: bibtex

	@article {myarticle
		 title={Foo},
		 authors={John Doe},
		 doi={01234},
		 bibchex-ignore-problems={dead_url;isbn_length}
	}

To ignore differences to data pulled from some data source, add a field ``bibchex-ignore-diffs``. The data of that field is a semicolon-separated list of tokens of the form ``<data source>.<field>``. This specifies that the data for ``<field>`` pulled from the data source ``<data source>`` should be ignored when computing differences. The ``<field>`` specifier can be set to ``*`` to ignore all data from the respective data source.

As an example, an item for which no comparison to the data from crossref should take place could look like this:

.. code-block:: bibtex

  @article {myarticle
	   title={Foo},
	   authors={John Doe},
	   doi={01234},
	   bibchex-ignore-diffs={crossref.*}
	}

If you just want to ignore differences in the ``date`` field for data coming from crossref, you instead write:

.. code-block:: bibtex

	@article {myarticle
		 title={Foo},
		 authors={John Doe},
		 doi={01234},
		 bibchex-ignore-diffs={crossref.date}
	}

