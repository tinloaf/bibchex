from bibchex.config import Config, ConfigurationError
from isbnlib import is_isbn10, is_isbn13, to_isbn10, to_isbn13, \
    canonical, notisbn, mask, clean


class ValidISBNChecker(object):
    NAME = "isbn_valid"

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, True):
            return []

        isbn = entry.data.get('isbn')
        if not isbn:
            return []

        if notisbn(isbn):
            return [("invalid_isbn", "ISBN {} is invalid.".format(isbn), "")]
        else:
            return []


class ISBNFormatChecker(object):
    NAME = "isbn_format"

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, True):
            return []

        fmt = self._cfg.get('isbn_format', entry)
        if not fmt:
            return []

        isbn = entry.data.get('isbn')
        if not isbn:
            return []

        clean_isbn = clean(isbn)
        if not clean_isbn or notisbn(clean_isbn):
            return []

        if fmt not in ('canonical', 'masked'):
            raise ConfigurationError(
                "The option 'isbn_format' must be \
                either of 'canonical' or 'masked'.")

        if fmt == 'canonical':
            cisbn = canonical(clean_isbn)
            if cisbn != isbn:
                return [(type(self).NAME,
                         "ISBN '{}' is not in canonical format.".format(isbn),
                         "Canonical format would be '{}'".format(cisbn))]
        elif fmt == 'masked':
            misbn = mask(clean_isbn)
            if misbn != isbn:
                return [(type(self).NAME,
                         "ISBN '{}' is not in masked format.".format(isbn),
                         "Masked format would be '{}'".format(misbn))]

        return []


class ISBNLengthChecker(object):
    NAME = "isbn_length"

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, True):
            return []

        length = self._cfg.get('isbn_length', entry, 13)
        if not length:
            return []

        isbn = entry.data.get('isbn')
        if not isbn:
            return []

        clean_isbn = clean(isbn)
        if not clean_isbn or notisbn(clean_isbn):
            return []

        if length not in (10, 13):
            raise ConfigurationError(
                "The option 'isbn_length' must be either of 10 or 13.")

        if length == 10:
            if not is_isbn10(clean_isbn):
                return [(type(self).NAME,
                         "ISBN '{}' is not of length 10.".format(isbn),
                         "ISBN-10 would be '{}'"
                         .format(to_isbn10(clean_isbn)))]
        elif length == 13:
            if not is_isbn13(clean_isbn):
                return [(type(self).NAME,
                         "ISBN '{}' is not of length 13.".format(isbn),
                         "ISBN-13 would be '{}'"
                         .format(to_isbn13(clean_isbn)))]

        return []
