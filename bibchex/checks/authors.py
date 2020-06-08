from bibchex.config import Config


class InitialDottedChecker(object):
    NAME = 'author_initial_dotted'

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, True):
            return []

        authors = await self.check_one("authors", "Author", entry)
        editors = await self.check_one("editors", "Editor", entry)
        return authors + editors

    async def check_one(self, field, name, entry):
        should_dot = self._cfg.get('author_initial_want_dotted', entry, True)
        problems = []
        for author in getattr(entry, field):
            (first, last) = author

            words = first.split(" ") + last.split(" ")
            for word in words:
                if len(word) == 0:
                    continue
                if not any(c.islower() for c in word):
                    if should_dot and word[-1] != '.':
                        problems.append(
                            (type(self).NAME,
                             "{} {} {} seems to have an undotted initial."
                             .format(name, first, last), ""))

                    if not should_dot and word.find('.') != -1:
                        problems.append(
                            (type(self).NAME,
                             "{} {} {} seems to have a dotted initial."
                             .format(name, first, last), ""))

        return problems


class AllcapsNameChecker(object):
    NAME = "author_names_allcaps"

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, True):
            return []

        authors = await self.check_one("authors", "Author", entry)
        editors = await self.check_one("editors", "Editor", entry)
        return authors + editors

    async def check_one(self, field, name, entry):
        problems = []
        for author in getattr(entry, field):
            (first, last) = author
            first_lower_count = sum((int(c.islower()) for c in first))
            first_upper_count = sum((int(c.isupper()) for c in first))
            # Length check > 1 b/c otherwise it is considered an abbreviation
            if first_lower_count == 0 and first_upper_count > 1:
                problems.append(
                    (type(self).NAME,
                     "{} '{} {}' seems to have an all-caps first name."
                     .format(name, first, last), ""))
            last_lower_count = sum((int(c.islower()) for c in last))
            last_upper_count = sum((int(c.isupper()) for c in last))
            if last_lower_count == 0 and last_upper_count > 1:
                problems.append(
                    (type(self).NAME,
                     "{} '{} {}' seems to have an all-caps last name."
                     .format(name, first, last), ""))
        return problems


class FirstNameInitialChecker(object):
    NAME = "author_names_firstinitial"

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, True):
            return []

        authors = await self.check_one("authors", "Author", entry)
        editors = await self.check_one("editors", "Editor", entry)
        return authors + editors

    async def check_one(self, field, name, entry):
        problems = []
        for author in getattr(entry, field):
            (given, last) = author
            if len(given) == 0:
                continue

            first = list(filter(lambda s: len(s) > 0, given.split(" ")))[0]
            first_lower_count = sum((int(c.islower()) for c in first))
            if first_lower_count == 0:
                problems.append(
                    (type(self).NAME,
                     ("{} '{} {}' seems to have a first name "
                      "that is in abbreviated or all-caps.")
                     .format(name, given, last), ""))
        return problems


class MiddleNameInitialChecker(object):
    NAME = "author_names_middleinitial"

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, True):
            return []

        authors = await self.check_one("authors", "Author", entry)
        editors = await self.check_one("editors", "Editor", entry)
        return authors + editors

    async def check_one(self, field, name, entry):
        problems = []
        for author in getattr(entry, field):
            (given, last) = author
            if len(given) == 0:
                continue

            tokens = list(filter(lambda s: len(s) > 0, given.split(" ")))
            if len(tokens) == 1:
                continue

            middle = " ".join(tokens[1:])

            middle_lower_count = sum((int(c.islower()) for c in middle))
            if middle_lower_count == 0:
                problems.append(
                    (type(self).NAME,
                     ("{} '{} {}' seems to have a middle name that "
                      "is in abbreviated or all-caps.")
                     .format(name, given, last), ""))
        return problems


class LastNameInitialChecker(object):
    NAME = "author_names_lastinitial"

    def __init__(self):
        self._cfg = Config()

    async def check(self, entry):
        if not self._cfg.get('check_{}'.format(type(self).NAME), entry, True):
            return []

        authors = await self.check_one("authors", "Author", entry)
        editors = await self.check_one("editors", "Editor", entry)
        return authors + editors

    async def check_one(self, field, name, entry):
        problems = []
        for author in getattr(entry, field):
            (given, last) = author

            last_lower_count = sum((int(c.islower()) for c in last))
            if last_lower_count == 0:
                problems.append(
                    (type(self).NAME,
                     ("{} '{} {}' seems to have a last name "
                      "that is in abbreviated or all-caps.")
                     .format(name, given, last), ""))
        return problems


