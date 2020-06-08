from setuptools import setup, find_packages

# read the contents of the README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'Readme.rst'), encoding='utf-8') as f:
    long_description = f.read()

requires = [
    "aiohttp>=3.6.2",
    "bibtexparser>=1.1.0",
    "crossref-commons-reverse>=0.0.7.1",
    "fuzzywuzzy>=0.18.0",
    "isbnlib>=3.10.3",
    "Jinja2>=2.11.1",
    "nameparser>=1.0.6",
    "python-dateutil>=2.8.1",
    "ratelimit>=2.2.1"
    ]

test_requires = [
    "pytest>=5.4.3",
    "pytest-asyncio>=0.12.0",
    "pytest-datadir-ng>=1.1.1",
    "aioresponses>=0.6.4"
]

setup(
    name="bibchex",
    version="0.1.2",
    packages=find_packages(),

    setup_requires=["pytest-runner>=5.2"],
    install_requires=requires,
    tests_require = requires + test_requires,
    
    author="Lukas Barth",
    author_email="pypi@mbox.tinloaf.de",
    description="Check your BibTeX files for consistency and sanity.",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    keywords="bibtex latex bibliography",
    url="http://github.com/tinloaf/bibchex/",   # project home page, if any
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
