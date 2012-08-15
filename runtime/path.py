#!/usr/bin/env python
# coding=utf-8

import sys
import glob
from eventlet.green import os

import env

DEFAULT_DIRS = {'config': '0755', 'tmp': '0777', 'data': '0755', 'log': '0755', 'run': '0755'}

def join(*args):
    return os.path.join(*args).replace(os.path.sep, '/')

def bootstrap():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    # print base_dir
    if 'darwin' in sys.platform:
        addons = 'bundles'
    else:
        addons = 'addons'
    env.add('dir_addons', os.path.join(base_dir, addons))
    env.add('dir_config', os.path.join(base_dir, 'etc'))
    env.add('dir_tmp', os.path.join(base_dir, 'tmp'))
    env.add('dir_data', os.path.join(base_dir, 'var', 'lib'))
    env.add('dir_log', os.path.join(base_dir, 'var', 'log'))
    env.add('dir_run', os.path.join(base_dir, 'var', 'run'))
    env.add('dir_resources', os.path.join(base_dir, 'resources'))

    for k, _dir in os.environ.items():
        if k.startswith('X_DIR_'):
            if not os.path.exists(_dir):
                os.makedirs(_dir)

def all_addons_desc():
    return glob.glob('%s/*/addon.yaml' % env.get('dir_addons'))

def process_addon_dirs(addon):
    ENV_DICT = env.all_dict()
    for _dir in addon._directories():
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
    _path = join(env.get('dir_resources'), relative)
    if is_dir and os.path.exists(_path):
        return _path
    if not is_dir and os.path.isfile(_path):
        return _path
