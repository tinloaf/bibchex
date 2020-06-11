from datetime import datetime

from dateutil.parser import parse as datetime_parser

from bibchex.strutil import split_at_multiple

# Table shamelessly taken from
# https://stackoverflow.com/a/4580132/4694124
LATEX_ACCENTS = [
    [u"à", "\\`a"],  # Grave accent
    [u"è", "\\`e"],
    [u"ì", "\\`\\i"],
    [u"ò", "\\`o"],
    [u"ù", "\\`u"],
    [u"ỳ", "\\`y"],
    [u"À", "\\`A"],
    [u"È", "\\`E"],
    [u"Ì", "\\`\\I"],
    [u"Ò", "\\`O"],
    [u"Ù", "\\`U"],
    [u"Ỳ", "\\`Y"],
    [u"á", "\\'a"],  # Acute accent
    [u"é", "\\'e"],
    [u"í", "\\'\\i"],
    [u"ó", "\\'o"],
    [u"ú", "\\'u"],
    [u"ý", "\\'y"],
    [u"Á", "\\'A"],
    [u"É", "\\'E"],
    [u"Í", "\\'\\I"],
    [u"Ó", "\\'O"],
    [u"Ú", "\\'U"],
    [u"Ý", "\\'Y"],
    [u"â", "\\^a"],  # Circumflex
    [u"ê", "\\^e"],
    [u"î", "\\^\\i"],
    [u"ô", "\\^o"],
    [u"û", "\\^u"],
    [u"ŷ", "\\^y"],
    [u"Â", "\\^A"],
    [u"Ê", "\\^E"],
    [u"Î", "\\^\\I"],
    [u"Ô", "\\^O"],
    [u"Û", "\\^U"],
    [u"Ŷ", "\\^Y"],
    [u"ä", "\\\"a"],    # Umlaut or dieresis
    [u"ë", "\\\"e"],
    [u"ï", "\\\"\\i"],
    [u"ö", "\\\"o"],
    [u"ü", "\\\"u"],
    [u"ÿ", "\\\"y"],
    [u"Ä", "\\\"A"],
    [u"Ë", "\\\"E"],
    [u"Ï", "\\\"\\I"],
    [u"Ö", "\\\"O"],
    [u"Ü", "\\\"U"],
    [u"Ÿ", "\\\"Y"],
    [u"ç", "\\c{c}"],   # Cedilla
    [u"Ç", "\\c{C}"],
    [u"œ", "{\\oe}"],   # Ligatures
    [u"Œ", "{\\OE}"],
    [u"æ", "{\\ae}"],
    [u"Æ", "{\\AE}"],
    [u"å", "{\\aa}"],
    [u"Å", "{\\AA}"],
    # Dashes are handled separately
    #    [u"–", "--"],   # Dashes
    #    [u"—", "---"],
    [u"ø", "{\\o}"],    # Misc latin-1 letters
    [u"Ø", "{\\O}"],
    [u"ß", "{\\ss}"],
    [u"¡", "{!`}"],
    [u"¿", "{?`}"],
    [u"\\", "\\\\"],    # Characters that should be quoted
    [u"~", "\\~"],
    [u"&", "\\&"],
    [u"$", "\\$"],
    [u"{", "\\{"],
    [u"}", "\\}"],
    [u"%", "\\%"],
    [u"#", "\\#"],
    [u"_", "\\_"],
    [u"≥", "$\\ge$"],   # Math operators
    [u"≤", "$\\le$"],
    [u"≠", "$\\neq$"],
    [u"©", r'\copyright'],  # Misc
    [u"ı", "{\\i}"],
    [u"µ", "$\\mu$"],
    [u"°", "$\\deg$"],
    [u"‘", "`"],  # Quotes
    [u"’", "'"],
    [u"“", "``"],
    [u"”", "''"],
    [u"‚", ","],
    [u"„", ",,"],
]

ACCENT_LOOKUP = {tex: plain for (plain, tex) in LATEX_ACCENTS}


# Technically, this is incorrect, since we're
# missing \-escaping of the backslash
# TODO fix this
# NOTE: Don't do this before unbrace()ing.
# Afterwards, \{ and { cannot be distinguished anymore.
def tranlate_accents(s):
    for tex, plain in ACCENT_LOOKUP.items():
        s = s.replace(tex, plain)

    return s


def count_preceding_backslashes(s, pos):
    count = 0
    i = pos - 1
    while i >= 0:
        if s[i] != '\\':
            return count
        count += 1
        i -= 1
    return count


def unbrace(s):
    index = 0
    while index >= 0:
        index = s.find('{', index)
        if index < 0:
            break

        nback = count_preceding_backslashes(s, index)
        if nback % 2 == 0:
            # Found one. Remove it.
            s = s[:index] + s[index+1:]

    index = 0
    while index >= 0:
        index = s.find('}', index)
        if index < 0:
            break

        nback = count_preceding_backslashes(s, index)
        if nback % 2 == 0:
            # Found one. Remove it.
            s = s[:index] + s[index+1:]

    return s


def unlatexify(s):
    return tranlate_accents(unbrace(s))


def unify_hyphens(s):
    s = s.replace('---', ' - ')
    s = s.replace('--', '-')
    s = s.replace('—', ' - ')

    return s


def parse_datetime(s):
    """We use dateutil.parser to parse dates. However, it has the weird default of
       substituting every missing part of a date with today.
    So, parsing the date '2000' would result in
    <this day>.<this month>.2001 - which is not what we want. """
    # Parse with two different default dates to detect missing info
    # in the string
    def1 = datetime(1970, 1, 1)
    def2 = datetime(1971, 2, 2)

    result1 = datetime_parser(s, default=def1)
    result2 = datetime_parser(s, default=def2)

    res = {}

    if result1.year != def1.year or result2.year != def2.year:
        res["year"] = "{}".format(result1.year)

    if result1.month != def1.month or result2.month != def2.month:
        res["month"] = "{}".format(result1.month)

    if result1.day != def1.day or result2.day != def2.day:
        res["day"] = "{}".format(result1.day)

    return res


def is_abbreviation(s):
    if s.find('.') != -1:
        return True

    uppercount = sum((1 for c in s if c.isupper()))
    lowercount = sum((1 for c in s if c.islower()))

    if uppercount > lowercount:
        return True

    return False


def contains_abbreviation(s):
    words = split_at_multiple(s, ' \t\n')
    return any((is_abbreviation(w) for w in words))

def sorted_pairs(iterable):
    s = sorted(iterable)
    return ((s[i], s[j]) for i in range(0, len(s)) for j in range(i+1, len(s)))
