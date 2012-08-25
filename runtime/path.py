#!/usr/bin/env python
# coding=utf-8

import sys
import glob
import biplist
import plistlib
from eventlet.green import os

import env

DEFAULT_DIRS = {'config': '0755', 'tmp': '0777', 'data': '0755', 'log': '0755', 'run': '0755'}

def join(*args):
    return os.path.normpath(os.path.join(*args)).replace(os.path.sep, '/')

def bootstrap():
    plist_path = os.path.expanduser('~/Library/Preferences/org.ratazzi.ServicesBox.plist')
    if os.path.isfile(plist_path):
        try:
            defaults = biplist.readPlist(plist_path)
        except (biplist.InvalidPlistException, biplist.NotBinaryPlistException):
            defaults = plistlib.readPlist(plist_path)
        except:
            defaults = dict()
    if 'dir_library' in defaults:
        base_dir = defaults['dir_library']
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    # print base_dir
    if 'darwin' in sys.platform:
        addons = 'bundles'
    else:
        addons = 'addons'
    env.add('dir_library', base_dir)
    env.add('dir_addons', os.path.join(base_dir, addons))
    env.add('dir_config', os.path.join(base_dir, 'etc'))
    env.add('dir_bin', os.path.join(base_dir, 'bin'))
    env.add('dir_tmp', os.path.join(base_dir, 'tmp'))
    env.add('dir_data', os.path.join(base_dir, 'var', 'lib'))
    env.add('dir_log', os.path.join(base_dir, 'var', 'log'))
    env.add('dir_run', os.path.join(base_dir, 'var', 'run'))

    for k, _dir in os.environ.items():
        if k.startswith('%sDIR_' % env.PREFIX):
            if not os.path.exists(_dir):
                os.makedirs(_dir)

    # from pprint import pprint
    # pprint(os.environ)

def all_addons_desc():
    return glob.glob('%s/*/addon.y*ml' % env.get('dir_addons'))

def process_addon_dirs(addon):
    ENV_DICT = env.all_dict()
    for _dir in addon.directories:
        if _dir.dir is None and _dir.name not in DEFAULT_DIRS.keys():
            raise Exception("Invalid default dir: `%s'" % _dir.name)

        if _dir.dir is None:
            _dir_name = 'dir_%s' % _dir.name
            _dst = join(env.get(_dir_name), _dir.addon)
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
