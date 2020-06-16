from bibchex.strutil import split_at_multiple, tokenize_braces
from bibchex.config import Config


class HasTitleChecker(object):
    NAME = "has_title"

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        problems = []

        if entry.data.get('title') is None:
            problems.append(
                (type(self).NAME,
                 "Missing title", ""))

        return problems


class TitleCapitalizationChecker(object):
    NAME = 'title_capitalization'

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        title = entry.raw_data.get('title', "")

        tokens = tokenize_braces(title)
        unbraced_part = "".join(
            (part for (braced, part) in tokens if not braced))

        words = list(filter(lambda s: len(s) > 0,
                            split_at_multiple(unbraced_part, [" ", "-"])))
        problems = []

        for word in words:
            upper_count = sum((int(c.isupper()) for c in word))
            if upper_count > 1:
                if word[0] != '{' or word[-1] != '}':
                    problems.append(('unbraced_acronym',
                                     "Capitalization of '{}' in the title is \
                                     lost".format(word),
                                     ("The word '{}' in the title contains "
                                      "multiple capital letters, indicating "
                                      "that capitalization is important. "
                                      "To preserve capitalization, the word "
                                      "should be in curly braces.")
                                     .format(word)))

        return problems
