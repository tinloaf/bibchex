from bibchex.strutil import split_at_multiple


class TitleCapitalizationChecker(object):
    NAME = 'title_capitalization'

    async def check(self, entry):
        title = entry.raw_data.get('title', "")
        words = list(filter(lambda s: len(s) > 0,
                            split_at_multiple(title, [" ", "-"])))

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
