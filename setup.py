from setuptools import setup, find_packages

setup(
    name="bibchex",
    version="0.1",
    packages=find_packages(),

    install_requires=["aiohttp>=3.6.2",
                      "bibtexparser>=1.1.0",
                      "crossref-commons-reverse>=0.0.7.1",
                      "fuzzywuzzy==0.18.0",
                      "isbnlib>=3.10.3",
                      "Jinja2>=2.11.1",
                      "nameparser>=1.0.6",
                      "python-dateutil>=2.8.1",
                      "ratelimit>=2.2.1"],

    author="Lukas Barth",
    author_email="pypi@mbox.tinloaf.de",
    description="Check your BibTeX files for consistency and sanity!",
    keywords="bibtex latex bibliography",
    url="http://github.com/tinloa/bibchex/",   # project home page, if any
    project_urls={
        "Bug Tracker": "https://github.com/tinloaf/bibchex/issues",
        "Documentation": "https://tinloaf.github.io/bibchex/",
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
    ],

    entry_points={
        'console_scripts': [
            "bibchex = bibchex.__main__:main"
        ]
    },

    package_data={
        "": ["data/*"],
    }
)
