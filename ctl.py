#!/usr/bin/env python
# coding=utf-8

"""Usage:
    ctl service [--start=NAME | --start-all] [-v | --verbose] [-d | --debug]
    ctl service [--stop=NAME | --stop-all] [-v | --verbose] [-d | --debug]
    ctl service [--restart=NAME | --restart-all] [-v | --verbose] [-d | --debug]
    ctl service [--running | --list] [-v | --verbose] [-d | --debug]
    ctl repair  [-v | --verbose] [-d | --debug]
    ctl dylib
    ctl version
    ctl test

"""

import shutil
import yaml
import logging
import logging.handlers
logger = logging.getLogger()
from eventlet.green import os, subprocess
from yaml import Loader, SafeLoader

# force PyYAML to load strings as unicode objects
# http://stackoverflow.com/questions/2890146/how-to-force-pyyaml-to-load-strings-as-unicode-objects
def construct_yaml_str(self, node):
    # Override the default string handling function
    # to always return unicode objects
    return self.construct_scalar(node)
Loader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)
SafeLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)

import traceback
import json
from tornado import template
from docopt import docopt
from pprint import pformat, pprint

import runtime.path
from runtime import env
runtime.path.bootstrap()
import storage
from module import service
from module.schema import Bundle, Option, Service, Directory

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

console = logging.StreamHandler()
console.setFormatter(formatter)
console.setLevel(logging.DEBUG)
logger.addHandler(console)
logger.setLevel(logging.DEBUG)

handler = logging.handlers.TimedRotatingFileHandler(
    filename=runtime.path.join(env.get('dir_log'), 'ctl.log'),
    when='midnight', backupCount=7)
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

logger.debug(pformat(env.all_dict()))

store = storage.get_store()

def _load_bundle(bundle_desc):
    # pprint(bundle_desc)
    print "register bundle `%s'" % bundle_desc['name']
    _bundle = store.find(Bundle, Bundle.name == bundle_desc['name']).one() or Bundle()
    _bundle.name = bundle_desc['name']
    _bundle.description = bundle_desc['description']
    store.add(_bundle)

    if 'options' in bundle_desc:
        for _option_desc in bundle_desc['options']:
            _option = store.find(Option, Option.name == _option_desc['name'], Option.bundle == bundle_desc['name']).one() or Option()
            _option.name = _option_desc['name']
            _option.bundle = bundle_desc['name']
            _option.description = _option_desc.get('description', _option_desc['name'])
            _option.value = unicode(_option_desc['value'])
            store.add(_option)

    if 'service' in bundle_desc:
        _service_desc = bundle_desc['service']
        _service = store.find(Service, Service.name == bundle_desc['name']).one() or Service()
        _service.name = bundle_desc['name']
        _service.bundle = bundle_desc['name']
        _service.description = _service_desc['description']
        _service.start = _service_desc['start']
        _service.stop = _service_desc['stop']
        _service.restart = _service_desc['restart']
        _service.env = _service_desc.get('env', {})
        _service.enable = _service_desc.get('enable', True)
        _service.autostart = _service_desc.get('autostart', True)
        store.add(_service)

    if 'directories' in bundle_desc:
        for _dir_desc in bundle_desc['directories']:
            _dir = store.find(Directory, Directory.name == _dir_desc['name'], Directory.bundle == bundle_desc['name']).one() or Directory()
            _dir.name = _dir_desc['name']
            _dir.bundle = bundle_desc['name']
            _dir.dir = _dir_desc.get('dir', None)
            _dir.permission = _dir_desc.get('permission', u'0755')
            _dir.description = _dir_desc['description']
            store.add(_dir)
    store.commit()

    # copy data
    if 'data' in bundle_desc:
        _env = _bundle.env(True)
        data = bundle_desc['data']
        src = data['src'].format(**_env)
        dst = data['dst'].format(**_env)
        if os.path.exists(dst) and len(os.listdir(dst)) == 0:
            logger.info('remove empty directory %s' % dst)
            shutil.rmtree(dst)
        if not os.path.exists(dst):
            shutil.copytree(src, dst)

    # # bin symlink
    bundle_bin_dir = runtime.path.join(env.get('dir_bundles'), _bundle.name, 'bin')
    if not os.path.exists(env.get('dir_bin')):
        os.makedirs(env.get('dir_bin'))
    if os.path.exists(bundle_bin_dir):
        for item in os.listdir(bundle_bin_dir):
            dst = runtime.path.join(env.get('dir_bin'), item)
            if item in ('.DS_Store'):
                continue
            if os.path.islink(dst) or os.path.isfile(dst):
                os.unlink(dst)
            os.symlink(runtime.path.join(bundle_bin_dir, item), dst)

    # # lib symlink
    bundle_lib_dir = runtime.path.join(env.get('dir_bundles'), _bundle.name, 'lib')
    lib_dir = runtime.path.join(env.get('dir_bundles'), 'lib')
    if not os.path.exists(lib_dir):
        os.makedirs(lib_dir)
    if os.path.exists(bundle_lib_dir):
        for item in os.listdir(bundle_lib_dir):
            src = runtime.path.join(bundle_lib_dir, item)
            dst = runtime.path.join(lib_dir, item)
            if item in ('.DS_Store'):
                continue
            if os.path.islink(dst) or os.path.isfile(dst):
                os.unlink(dst)
            if os.path.isdir(src):
                continue
            os.symlink(src, dst)

def load_bundles():
    for bundle_desc in runtime.path.all_bundles_desc():
        print "processing `%s'" % bundle_desc
        with open(bundle_desc, 'r') as fp:
            _bundle_desc = yaml.load(fp.read())
            _load_bundle(_bundle_desc)

def gen_config():
    for item in os.listdir(env.get('dir_config')):
        _path = runtime.path.join(env.get('dir_config'), item)
        if os.path.isfile(_path):
            os.remove(_path)
        else:
            shutil.rmtree(_path)
    for bundle_desc in runtime.path.all_bundles_desc():
        ENV_DICT = env.all_dict()
        with open(bundle_desc, 'r') as fp:
            _bundle_desc = yaml.load(fp.read())
            _bundle = store.find(Bundle, Bundle.name == _bundle_desc['name']).one()
            # _bundle = bundle.get(_bundle_desc['name'])
            ENV_DICT.update(_bundle.env())
            for _conf in _bundle_desc.get('conf', []):
                src = _conf['src'].format(**ENV_DICT)
                dst = _conf['dst'].format(**ENV_DICT)
                dst_dir = os.path.dirname(dst)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                content = None
                with open(src, 'r') as fp:
                    try:
                        content = template.Template(fp.read()).generate(**ENV_DICT)
                    except Exception, e:
                        print e
                        print traceback.format_exc()
                with open(dst, 'w') as fp:
                    fp.write(content)
                    # print dst
                    logger.info('genrate config file %s' % dst)
            # exit(0)

def start_all_services(only_autostart=False):
    for _service in store.find(Service):
        if not _service.autostart and only_autostart:
            continue
        _service._start()

def stop_all_services():
    for _service in service.store.find(Service):
        _service._stop()

def restart_all_services():
    for _service in service.store.find(Service):
        _service._restart()

def do_service(options):
    if options['--start-all']:
        start_all_services()
    elif options['--start']:
        _service = service.get(options['--start'])
        _service._start()
    elif options['--stop-all']:
        stop_all_services()
    elif options['--stop']:
        _service = service.get(options['--stop'])
        _service._stop()
    elif options['--restart-all']:
        restart_all_services()
    elif options['--restart']:
        _service = service.get(options['--restart'])
        _service._restart()
    elif options['--running']:
        for _service in service.list_running_services():
            print _service
    elif options['--list']:
        for _service in service.store.find(Service)():
            print _service.name
    else:
        print 'do nothing.'

def do_repair(options=dict()):
    load_bundles()
    # virtaul env
    shutil.copy(runtime.path.resources_path('activate'), runtime.path.join(env.get('dir_bin'), 'activate'))
    for _bundle in store.find(Bundle):
        runtime.path.process_bundle_dirs(_bundle)
    gen_config()

def fixed_dylib(dylibs, environ):
    for _dylib in dylibs:
        _dylib = _dylib.format(**environ)
        logger.debug("fixed dylib `%s'" % _dylib)
        cmd = ['otool', '-L', _dylib]
        for line in subprocess.check_output(cmd).replace('\t', '').split(os.linesep):
            if line.startswith('@rpath'):
                logger.debug('dylib info: %s' % line)
                old_rpath = line.split()[0]
                filename = old_rpath.split(os.path.sep)[-1]
                new_rpath = os.path.join(environ['DIR_BUNDLES'], 'lib', filename)
                logger.debug('old rpath: %s' % old_rpath)
                logger.debug('new rpath: %s' % new_rpath)
                logger.debug('verify new rpath: %s' % os.path.isfile(new_rpath))
                cmd = ['install_name_tool', '-change', old_rpath, new_rpath, _dylib]
                logger.debug('run command: %s' % ' '.join(cmd))
                logger.debug(subprocess.check_output(cmd))

def do_dylib(options=dict()):
    for bundle_desc in runtime.path.all_bundles_desc():
        with open(bundle_desc, 'r') as fp:
            _bundle_desc = yaml.load(fp.read())
            _bundle = store.find(Bundle, Bundle.name == _bundle_desc['name']).one()
            dylibs = _bundle_desc.get('fixed_dylib', [])
            if len(dylibs):
                _environ = _bundle.env()
                fixed_dylib(dylibs, _environ)

def main():
    storage.init()

    options = docopt(__doc__, version='0.1.0')

    if options['service']:
        do_service(options)
    elif options['repair']:
        do_repair(options)
    elif options['dylib']:
        do_dylib(options)

if __name__ == '__main__':
    main()
