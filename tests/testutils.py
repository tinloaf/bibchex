from bibchex.data import Entry
from bibchex.ui import SilentUI, UI
from bibchex.checker import Checker

def parse_to_entries(path):
    UI.select_silent()
    c = Checker(path, '/dev/null')
    c._parse()

    return c._entries

def make_entry(fields, entrytype="article", entryid="dummy"):
    data = {
        'ID': entryid,
        'ENTRYTYPE': entrytype}
    data.update(fields)

    return Entry(data, SilentUI())
