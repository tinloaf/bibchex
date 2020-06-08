import argparse
import asyncio
import concurrent
import traceback
import os.path
import sys

from bibchex.ui import UI
from bibchex.checker import Checker
from bibchex.config import Config

parser = argparse.ArgumentParser(description="Check BibTex files")


parser.add_argument('--gui', dest='ui_gui', action='store_const',
                    const=True, default=False,
                    help="Enable curses UI (default)")
parser.add_argument('--cli', dest='ui_cli', action='store_const',
                    const=True, default=False,
                    help="Enable CLI as user interface")
parser.add_argument('--silent', dest='ui_silent', action='store_const',
                    const=True, default=False,
                    help="Disable all output")

parser.add_argument('--config', nargs='?', type=str,
                    help="Path to the JSON config file")

parser.add_argument('input_file', nargs=1, type=str,
                    help='Input BibTex file')

parser.add_argument('output_file', nargs=1, type=str,
                    help='Output HTML file')


def main(passed_args=None):
    if passed_args is None:
        passed_args = sys.argv[1:]

    args = parser.parse_args(passed_args)

    if args.ui_gui:
        UI.select_gui()
    elif args.ui_cli:
        UI.select_cli()
    elif args.ui_silent:
        UI.select_silent()

    if args.config:
        Config(args.config)
    else:
        home = os.path.expanduser("~")
        user_cfg = os.path.join(home, '.config', 'bibchex.json')
        if os.path.isfile(user_cfg):
            Config(user_cfg)
        else:
            Config()

    ui = UI()

    loop = asyncio.get_event_loop()
#    loop.set_debug(True)
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(20))

    try:
        c = Checker(args.input_file[0], args.output_file[0])
        loop.run_until_complete(c.run())
    except Exception as e:
        exc_str = traceback.format_exc()
        ui.error("Exception", str(e))
        ui.error("Traceback", exc_str)

    ui.wait()


if __name__ == '__main__':
    main()
