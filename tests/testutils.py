import json
import pkgutil

from bibchex.data import Entry
from bibchex.ui import SilentUI, UI
from bibchex.checker import Checker
from bibchex.config import Config, ConfigImpl
from bibchex.checks import CCHECKERS


def run_to_checks(path, main_loop):
    UI.select_silent()
    c = Checker(path, '/dev/null')
    c._parse()
    main_loop.run_until_complete(c._check_consistency())

    return (c._problems, c._global_problems)

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


def set_config(options, keep_sub=False, deactivate_checks=True):
    default_options = json.loads(pkgutil.get_data('bibchex',
                                                  'data/default_config.json'))
    if not keep_sub:
        default_options['sub'] = []

    if deactivate_checks:
        for CChecker in CCHECKERS:
            default_options['check_{}'.format(CChecker.NAME)] = False
        
    for (k,v) in options.items():
        default_options[k] = v
    
    Config.instance = ConfigImpl(default_options)
