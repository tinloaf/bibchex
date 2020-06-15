import json
import re
import pkgutil
import concurrent.futures
import os


class ConfigurationError(Exception):
    """Exception thrown if the configuration file is erroneous."""


class ConfigImpl(object):
    """Implementation of the config singleton"""

    def __init__(self, data, thread_count=None):
        self._data = data
        self._sub_configs = []
        self._executor = None

        self._parse()
        self._init_executor(thread_count)

    def _init_executor(self, thread_count):
        if thread_count is None:
            if 'threads' in self._data:
                thread_count = int(self._data['threads'])
            else:
                thread_count = len(os.sched_getaffinity(0))

        self._executor = concurrent.futures.ThreadPoolExecutor(thread_count)

    def _parse(self):
        for data in self._data.get('sub', []):
            select_field = data['select_field']
            select_re = data['select_re']
            self._sub_configs.append(
                (select_field, re.compile(select_re), ConfigImpl(data)))

    def get_executor(self):
        return self._executor

    def get(self, key, entry=None, default=None):
        if entry:
            for (sel_field, sel_re, sub_cfg) in self._sub_configs:
                if sel_field in entry.data and \
                   sel_re.match(entry.data[sel_field]):
                    subval = sub_cfg.get(key, entry=entry)
                    if subval:
                        return subval

        return self._data.get(key, default)


class Config(object):
    """Interface to access the JSON configuration"""
    instance = None

    def __init__(self, path=None):
        if path:
            assert not Config.instance
            with open(path, "r") as conffile:
                data = json.load(conffile)
                Config.instance = ConfigImpl(data)
        else:
            if not Config.instance:
                data = json.loads(pkgutil.get_data('bibchex',
                                                   'data/default_config.json'))
                Config.instance = ConfigImpl(data)
            assert Config.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)
