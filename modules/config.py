#!/usr/bin/env python

import inspect
import os
import sys
import yaml
try:
    import modules.constants
except:
    import constants

DEBUG = True
ERROR = True
VERSION = '2.2 Beta'


def printdebug(mystring):
    if DEBUG is True:
        print("DEBUG config: %s" % mystring)


def printerror(mystring):
    if ERROR is True:
        print("ERROR config: %s" % mystring)


class Settings(object):

    def test(self):
        return "TEST"

    def edacapi(self, item):
        if 'edacapi' in self._cf:
            if item in self._cf['edacapi']:
                return self._cf['edacapi'][item]
            else:
                return None
        else:
            return None

    def getsourceurl(self, url):
        if 'sourceurls' in self._cf:
            if url in self._cf['sourceurls']:
                return self._cf['sourceurls'][url]
            else:
                return None
        else:
            return None

    def getsourcefile(self, filename):
        if 'sourcefiles' in self._cf:
            if filename in self._cf['sourcefiles']:
                return self._cf['sourcefiles'][filename]
            else:
                return None
        else:
            return None

    def __init__(self):
        global __CF__
        self._cf = __CF__

class Environment(object):

    def get_script_dir(follow_symlinks=True):
        if getattr(sys, 'frozen', False):  # py2exe, PyInstaller, cx_Freeze
            path = os.path.abspath(sys.executable)
        else:
            path = inspect.getabsfile(get_script_dir)
        if follow_symlinks:
            path = os.path.realpath(path)
        return os.path.dirname(path)

# Load Configuration File and define objects
configfile = os.path.join(os.path.dirname(__file__),
                          constants.configfile())
with open(configfile, "r") as f:
    __CF__ = yaml.load(f)
printdebug('Loaded settings file: %s' % constants.configfile())
settings = Settings()
env = Environment()
