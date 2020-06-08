from datetime import datetime
from threading import Lock

import curses


def wrapafter(s, length):
    # Find first space backwards
    if length >= len(s):
        return (s, None)

    i = length
    while i > 0 and not s[i].isspace():
        i -= 1

    if i == 0 and not s[i].isspace():
        # No space before. Do an intra-word wrap
        return (s[:length], s[length:])

    if i < length/2:
        # Would only fill half of this line. Do an intra-word wrap
        return (s[:length], s[length:])

    this_line = s[:i].strip()
    remaining = s[i:].strip()

    # Determine length of the word that the next line would start with.
    # If that would need an intra-word wrap, we can as well do it now.
    # Note that this assumes that the next line has the same length
    # as this one...
    if not any(char.isspace for char in remaining[length:]):
        return ((s[:length]).strip(), (s[length:]).strip())

    return (this_line, remaining)


class Subtask(object):
    def __init__(self, name, total):
        self._name = name
        self._total = total
        self._done = 0


class GUI(object):
    L_DEBUG = 1
    L_MESSAGE = 2
    L_WARN = 3
    L_ERROR = 4

    def __init__(self):
        self._main = curses.initscr()
        curses.noecho()
        curses.start_color()

        self._subtasks = {}
        self._log = []

        self._win_progress = None
        self._win_progress_height = None
        self._win_log = None
        self._win_log_height = None
        self._mutex = Lock()
        self._rebuild_windows = False

        self._init_colors()
        self._build_windows()

        self._refresh()

    def _refresh(self):
        self._mutex.acquire()
        if self._rebuild_windows:
            self._build_windows()

        self._print_log()
        self._print_progress()

        self._win_progress.refresh()
        self._win_log.refresh()
        self._mutex.release()

    def _init_colors(self):
        curses.start_color()
        curses.init_pair(GUI.L_DEBUG, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(GUI.L_MESSAGE, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(GUI.L_WARN, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(GUI.L_ERROR, curses.COLOR_RED, curses.COLOR_BLACK)

    def __del__(self):
        curses.echo()
        curses.endwin()

    def _print_log(self):
        self._win_log.clear()
        self._win_log.border()

        line = 1
        max_line = self._win_log_height - 2

        for (level, when, name, message) in reversed(self._log):
            time_str = when.strftime("%H:%M:%S")
            msg = "{} -- {}".format(name, message)

            msg_line_length = curses.COLS - 5 - len(time_str)

            # First line - print time.
            self._win_log.addstr(line, 2, time_str, curses.color_pair(level))
            # First line - print first part of message
            (line_msg, remaining) = wrapafter(msg, msg_line_length)
            self._win_log.addstr(line, 3 + len(time_str),
                                 line_msg, curses.color_pair(level))
            line += 1
            if line > max_line:
                return
            while remaining:
                (line_msg, remaining) = wrapafter(msg, msg_line_length)
                self._win_log.addstr(
                    line, 3 + len(time_str), line_msg,
                    curses.color_pair(level))
                line += 1
                if line > max_line:
                    return

    def _print_progress(self):
        self._win_progress.clear()
        self._win_progress.border()

        status_strs = []
        status_length = 0
        st_order = []
        for subtask in self._subtasks.values():
            s = "{} [{} / {}]".format(subtask._name,
                                      subtask._done, subtask._total)
            status_strs.append(s)
            status_length = max(status_length, len(s))
            st_order.append(subtask)

        bar_width = curses.COLS - 6 - status_length
        for i in range(0, len(self._subtasks)):
            self._win_progress.addstr(i + 1, 2, status_strs[i])
            st = st_order[i]
            self._win_progress.addstr(
                i + 1, 2 + status_length + 2,
                "#" * int(bar_width * (st._done / st._total)))

    def _build_windows(self):
        self._win_progress_height = len(self._subtasks) + 2
        self._win_log_height = curses.LINES - self._win_progress_height

        if self._win_progress:
            del self._win_progress
        if self._win_log:
            del self._win_log

        self._win_progress = curses.newwin(
            self._win_progress_height, curses.COLS, 0, 0)
        self._win_progress.border()
        self._win_log = curses.newwin(
            self._win_log_height, curses.COLS, self._win_progress_height, 0)
        self._win_log.border()

    def debug(self, name, message):
        self._mutex.acquire()
        self._log.append((GUI.L_DEBUG, datetime.now(), name, message))
        self._mutex.release()
        self._refresh()

    def message(self, name, message):
        self._mutex.acquire()
        self._log.append((GUI.L_MESSAGE, datetime.now(), name, message))
        self._mutex.release()
        self._refresh()

    def warn(self, name, message):
        self._mutex.acquire()
        self._log.append((GUI.L_WARN, datetime.now(), name, message))
        self._mutex.release()
        self._refresh()

    def error(self, name, message):
        self._mutex.acquire()
        self._log.append((GUI.L_ERROR, datetime.now(), name, message))
        self._mutex.release()
        self._refresh()

    def add_subtask(self, name, total):
        self._mutex.acquire()
        self._subtasks[name] = Subtask(name, total)
        self._rebuild_windows = True
        self._mutex.release()
        self._refresh()

    def update_subtask(self, name, done):
        self._mutex.acquire()
        self._subtasks[name]._done = done
        self._mutex.release()
        self._refresh()

    def finish_subtask(self, name):
        self._mutex.acquire()
        self._subtasks[name]._done += 1
        self._mutex.release()
        self._refresh()

    def increase_subtask(self, name):
        self._mutex.acquire()
        if name not in self._subtasks:
            self._subtasks[name] = Subtask(name, 1)
            self._rebuild_windows = True
        else:
            self._subtasks[name]._total += 1
        self._mutex.release()
        self._refresh()

    def wait(self):
        self._win_log.getch()


class CLI(object):
    def __init__(self):
        pass

    def debug(self, name, message):
        print("[D] {} --- {}".format(name, message))

    def message(self, name, message):
        print("[I] {} --- {}".format(name, message))

    def warn(self, name, message):
        print("[W] {} --- {}".format(name, message))

    def error(self, name, message):
        print("[E] {} --- {}".format(name, message))

    def add_subtask(self, name, total):
        pass

    def update_subtask(self, name, done):
        pass

    def finish_subtask(self, name):
        pass

    def increase_subtask(self, name):
        pass

    def wait(self):
        pass  # Don't wait, output is preserved in console


class SilentUI(object):
    def __init__(self):
        pass

    def debug(self, name, message):
        pass

    def message(self, name, message):
        pass

    def warn(self, name, message):
        pass

    def error(self, name, message):
        pass

    def add_subtask(self, name, total):
        pass

    def update_subtask(self, name, done):
        pass

    def finish_subtask(self, name):
        pass

    def increase_subtask(self, name):
        pass

    def wait(self):
        pass


class UI(object):
    instance = None

    def __init__(self):
        if not UI.instance:
            UI.instance = GUI()

    @classmethod
    def select_gui(self):
        UI.instance = GUI()

    @classmethod
    def select_cli(self):
        UI.instance = CLI()

    @classmethod
    def select_silent(self):
        UI.instance = SilentUI()

    def __getattr__(self, name):
        return getattr(self.instance, name)
