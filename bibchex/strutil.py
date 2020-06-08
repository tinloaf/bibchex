import re


def split_at_multiple(s, delims):
    tokens = s.split(delims[0])

    for delim in delims[1:]:
        tokens = [t for inner_s in tokens for t in inner_s.split(delim)]

    return tokens


def split_camelcase(s):
    tokens = []
    last_alpha = False
    start = 0
    for i in range(0, len(s)):
        if s.isupper() and last_alpha:
            tokens += s[start:i]
            start = i
        last_alpha = s.isalpha()

    tokens += s[start:len(s)]

    return tokens


def lower_case_first_letters(original):
    def is_word_separator(s):
        return s.isspace() or s in ['-', '/']

    phrase = str(original)
    i = 0
    last_whitespace = True
    while i < len(phrase):
        if last_whitespace and not is_word_separator(phrase[i]):
            lower_letter = phrase[i].lower()
            # TODO The efficiency is below 9000. :(
            phrase = phrase[:i] + lower_letter + phrase[i+1:]

        last_whitespace = is_word_separator(phrase[i])

        i += 1
    return phrase


WS_RE = re.compile(r'\s+')


def crush_spaces(original):
    phrase = original.strip()
    return WS_RE.sub(' ', phrase)


def merge_lines(original):
    return original.replace('\n', ' ')


def is_allcaps(s):
    return not any((c.islower() for c in s))


class AbbrevFinder(object):
    def __init__(self, strings, ignorecase=True):
        self._strings = strings
        self._res = []
        self._pairs = []
        self._ignorecase = ignorecase

        self._prepare_res()
        self._find_pairs()

    def _prepare_res(self):
        for s in self._strings:
            tokens = split_at_multiple(s, " .,")
            tokens = [
                t for inner_s in tokens for t in split_camelcase(inner_s)]
            if self._ignorecase:
                r = re.compile(".*".join((re.escape(t)
                                          for t in tokens)), re.IGNORECASE)
            else:
                r = re.compile(".*".join((re.escape(t) for t in tokens)))
            self._res.append((s, r))

    def _find_pairs(self):
        self._pairs = []
        for (s1, regex) in self._res:
            for s2 in self._strings:
                if ((s1.lower() == s2.lower()) and self._ignorecase) or \
                   (s1 == s2):
                    continue

                if regex.search(s2) is not None:
                    self._pairs.append((s1, s2))

    def get(self):
        return self._pairs
