.. BibCheX documentation master file, created by
   sphinx-quickstart on Mon Jun  1 19:28:48 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to BibCheX's documentation!
===================================

BibCheX is a tool to sanity- and consistency-check your BibTeX reference files. Aside from checks ensuring your preferred style guidelines are met, Bibchex pulls in bibliographic data from sources such as CrossRef and cross-checks your BibTeX files against this data. The the :ref:`list of available checkers <file_checkers>` and the :ref:`list of available data sources <file_sources>` for what can be checked (against).

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   config
   checkers
   sources
	 

Getting started
---------------

This walks you quickly through running BibCheX on your .bib file. 

Installation
^^^^^^^^^^^^ 

Installing BibCheX from source should be as easy as running

.. code-block:: bash

	 python setup.py install


in the source folder. Alternatively, you can install BibCheX from PyPI using ``pip``:

.. code-block:: bash
	 
	 pip install bibchex


Configuration
^^^^^^^^^^^^^

Configuration determines which style rules should be checked for. BibCheX comes with a default configuration which matches my personal taste, but probably not yours. So you can run BibCheX without customizing the config, but you might not be happy with the result.

You can find the default configuration at ``bibchex/data/default_config.json`` in the source. Copy that file to ``~/.config/bibchex.json`` or anywhere else. If you did copy it to some arbitrary location, you must pass the path to that file via the ``--config`` command line switch.

Have a look at the configuration documenation TODO to see what can be configured.


Running
^^^^^^^

BibCheX can be run in three modes. In GUI mode, text mode or silent mode. Okay, "GUI" is kind of a lie, it's more of a TUI. But anyways, it provides progress bars, so yay for GUI mode!

BibCheX expects as first positional argument the path to your ``.bib`` file, and as second a path to a (non-existent) HTML file, to which it will write its output. Running BibCheX (in GUI mode) can be as easy as:

.. code-block:: bash
								
	 bibchex /path/to/my/references.bib /path/to/the/desired/output.html


This should open a text UI with some scrolling log messages and progress bars on the top. Once everything is finished, press any key to close the UI and open ``/path/to/the/desired/output.html`` in any browser to have a look at the result.

Running BibCheX without the GUI can be done like this:

.. code-block:: bash

	 bibchex --cli /path/to/my/references.bib /path/to/the/desired/output.html


Remember that you may have to pass your custom configuration JSON file if you have placed in a nonstandard location:

.. code-block:: bash
								
	 bibchex --cli --config /path/to/your/config.json /path/to/my/references.bib /path/to/the/desired/output.html


**Please Note**: The (free) crossref API required a valid email address to be set for usage. By default, a dummy address is configured. Please change this to a valid address before actually using BibCheX!

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
