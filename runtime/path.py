#!/usr/bin/env python
# coding=utf-8

import sys
import glob
import biplist
import plistlib
from eventlet.green import os

import env

DEFAULT_DIRS = {'bundles': '0755', 'config': '0755', 'bin': '0755', 'tmp': '0777',
                'data': '0755', 'log': '0755', 'run': '0755'}

def join(*args):
    return os.path.normpath(os.path.join(*args)).replace(os.path.sep, '/')

def bootstrap():
    defaults_path = os.path.expanduser('~/Library/Preferences/org.ratazzi.ServicesBox.plist')
    defaults = dict()
    if os.path.isfile(defaults_path):
        try:
            defaults = biplist.readPlist(defaults_path)
        except (biplist.InvalidPlistException, biplist.NotBinaryPlistException):
            defaults = plistlib.readPlist(defaults_path)

    if 'dir_library' in defaults:
        env.add('dir_library', defaults['dir_library'])
    else:
        # development environment
        env.add('dir_library', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

    bundles = 'darwin' in sys.platform and 'bundles' or 'bundle'

    env.add('dir_bundles', os.path.join(env.get('dir_library'), bundles))
    env.add('dir_config', os.path.join(env.get('dir_library'), 'etc'))
    env.add('dir_bin', os.path.join(env.get('dir_library'), 'bin'))
    env.add('dir_tmp', os.path.join(env.get('dir_library'), 'tmp'))
    env.add('dir_data', os.path.join(env.get('dir_library'), 'data'))
    env.add('dir_log', os.path.join(env.get('dir_library'), 'var', 'log'))
    env.add('dir_run', os.path.join(env.get('dir_library'), 'var', 'run'))

    # custom data path
    for item in DEFAULT_DIRS.keys():
        key = 'dir_%s' % item
        if defaults.get(key):
            env.add(key, defaults[key])

    for k, _dir in os.environ.items():
        if k.startswith('%sDIR_' % env.PREFIX):
            if not os.path.exists(_dir):
                os.makedirs(_dir)

def all_bundles_desc():
    return glob.glob('%s/*/bundle.y*ml' % env.get('dir_bundles'))

def process_bundle_dirs(bundle):
    ENV_DICT = env.all_dict()
    for _dir in bundle.directories:
        if _dir.dir is None and _dir.name not in DEFAULT_DIRS.keys():
            raise Exception("Invalid default dir: `%s'" % _dir.name)

        if _dir.dir is None:
            _dir_name = 'dir_%s' % _dir.name
            _dst = join(env.get(_dir_name), _dir.bundle)
        else:

            _dst = _dir.dir.format(**ENV_DICT)
        if not os.path.exists(_dst):
            os.makedirs(_dst)

def resources_path(relative, is_dir=False):
    if getattr(sys, 'frozen', None):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
    return join(base_dir, 'resources', relative)
