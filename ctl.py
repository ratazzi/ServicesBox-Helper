#!/usr/bin/env python
# coding=utf-8

"""Usage:
    ctl.py service [--start=NAME | --start-all] [-v | --verbose] [-d | --debug]
    ctl.py service [--stop=NAME | --stop-all] [-v | --verbose] [-d | --debug]
    ctl.py service [--restart=NAME | --restart-all] [-v | --verbose] [-d | --debug]
    ctl.py service [--running | --list] [-v | --verbose] [-d | --debug]
    ctl.py repair  [-v | --verbose] [-d | --debug]
    ctl.py version
    ctl.py test

"""

import os
import yaml
import logging
import logging.handlers
logger = logging.getLogger()

import traceback
import json
from tornado import template
from docopt import docopt

import storage
import runtime.path
from runtime import env
from module import addon, option, service, directory

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

console = logging.StreamHandler()
console.setFormatter(formatter)
console.setLevel(logging.WARNING)
logger.addHandler(console)
logger.setLevel(logging.DEBUG)

runtime.path.bootstrap()
handler = logging.handlers.TimedRotatingFileHandler(
    filename=runtime.path.join(env.get('dir_log'), 'ctl.log'),
    when='midnight', backupCount=7)
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

def _load_addon(addon_desc):
    # pprint(addon_desc)
    print "register addon `%s'" % addon_desc['name']
    with storage.get_session() as session:
        _addon = addon.Addon()
        _addon.name = addon_desc['name']
        _addon.description = addon_desc['description']
        session.add(_addon)

        if 'options' in addon_desc:
            for _option_desc in addon_desc['options']:
                _option = option.Option()
                _option.name = _option_desc['name']
                _option.addon = addon_desc['name']
                _option.description = _option_desc.get('description', _option_desc['name'])
                _option.value = _option_desc['value']
                session.add(_option)

        if 'service' in addon_desc:
            _service_desc = addon_desc['service']
            _service = service.Service()
            _service.name = addon_desc['name']
            _service.addon = addon_desc['name']
            _service.description = _service_desc['description']
            _service.start = _service_desc['start']
            _service.stop = _service_desc['stop']
            _service.restart = _service_desc['restart']
            _service.env = json.dumps(_service_desc.get('env', {}))
            session.add(_service)

        if 'directories' in addon_desc:
            for _dir_desc in addon_desc['directories']:
                _dir = directory.Directory()
                _dir.name = _dir_desc['name']
                _dir.addon = addon_desc['name']
                _dir.dir = _dir_desc.get('dir', None)
                _dir.permission = _dir_desc.get('permission', '0755')
                _dir.description = _dir_desc['description']
                session.add(_dir)
        session.commit()

def load_addons():
    for addon_desc in runtime.path.all_addons_desc():
        print "processing `%s'" % addon_desc
        with open(addon_desc, 'r') as fp:
            _addon_desc = yaml.load(fp.read())
            _load_addon(_addon_desc)

def gen_config():
    for addon_desc in runtime.path.all_addons_desc():
        ENV_DICT = env.all_dict()
        with open(addon_desc, 'r') as fp:
            _addon_desc = yaml.load(fp.read())
            _addon = addon.get(_addon_desc['name'])
            ENV_DICT.update(_addon.env())
            for _conf in _addon_desc['conf']:
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
            # exit(0)

def do_service(options):
    if options['--start-all']:
        for _service in service.list_all():
            _service._start()
    elif options['--start']:
        _service = service.get(options['--start'])
        _service._start()
    elif options['--stop-all']:
        for _service in service.list_all():
            _service._stop()
    elif options['--stop']:
        _service = service.get(options['--stop'])
        _service._stop()
    elif options['--restart-all']:
        for _service in service.list_all():
            _service._restart()
    elif options['--restart']:
        _service = service.get(options['--restart'])
        _service._restart()
    elif options['--running']:
        for _service in service.list_running_services():
            print _service
    elif options['--list']:
        for _service in service.list_all():
            print _service.name
    else:
        print 'do nothing.'

def do_repair(options):
    load_addons()
    for _addon in addon.list_all():
        runtime.path.process_addon_dirs(_addon)
    gen_config()

def main():
    storage.init()

    options = docopt(__doc__, version='0.1.0')

    if options['service']:
        do_service(options)
    elif options['repair']:
        do_repair(options)
    elif options['test']:
        from pprint import pprint
        from core import activity
        pprint(activity.services_activity())
        exit(0)

if __name__ == '__main__':
    main()
