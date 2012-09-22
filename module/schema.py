#!/usr/bin/env python
# coding=utf-8

import psutil
import eventlet
import logging
import traceback
import json
import signal
from eventlet.green import os
from eventlet.green import subprocess
from storm.locals import Reference, ReferenceSet
from storm.locals import Int, Unicode, JSON, Bool
# from eventlet.green import os, subprocess

import storage
import runtime
from runtime import env

logger = logging.getLogger(__name__)
store = storage.get_store()

def all_services_exe():
    ENV_DICT = env.all_dict()
    items = {}
    for _service in store.find(Service):
        ENV_DICT['DIR_BUNDLE'] = runtime.path.join(env.get('dir_bundles'), _service.name)
        _exe = _service.start.split()[0]
        _exe = _exe.format(**ENV_DICT)
        items[_service.name] = _exe
    return items

def list_running_services():
    exe2services = dict([(v, k) for k, v in all_services_exe().items()])
    ENV_DICT = env.all_dict()
    rs = []
    _services = []
    for _service in store.find(Service):
        ENV_DICT['DIR_BUNDLE'] = runtime.path.join(env.get('dir_bundles'), _service.name)
        _exe = _service.start.split()[0]
        _exe = _exe.format(**ENV_DICT)
        _services.append(_exe)
    for _p in psutil.process_iter():
        try:
            _exe = _p.exe
            if _exe in _services:
                name = exe2services[_exe]
                if name in rs:
                    continue
                rs.append(name)
        except psutil.AccessDenied:
            pass
        except SystemError:
            pass
        except IndexError:
            pass
        except Exception, e:
            runtime.eerror(e)
            traceback.print_exc()
    return rs

class Option(object):
    __storm_table__ = 'options'

    id = Int(primary=True)
    name = Unicode()
    bundle = Unicode()
    value = Unicode()
    description = Unicode()

class Directory(object):
    __storm_table__ = 'directories'

    id = Int(primary=True)
    name = Unicode()
    bundle = Unicode()
    dir = Unicode()
    permission = Unicode()
    description = Unicode()

class Service(object):
    __storm_table__ = 'services'

    id = Int(primary=True)
    name = Unicode()
    bundle = Unicode()
    description = Unicode()
    start = Unicode()
    stop = Unicode()
    restart = Unicode()
    env = JSON()
    enable = Bool()
    autostart = Bool()
    directories = ReferenceSet(bundle, Directory.bundle)

    def _start(self, **kwargs):
        if self.name in list_running_services():
            runtime.eerror("service `%s' is already running." % self.name)
            return

        if not self.enable:
            runtime.eerror("service `%s' is disabled." % self.name)
            return

        ENV_DICT = env.all_dict()
        ENV_DICT['DIR_BUNDLE'] = runtime.path.join(env.get('dir_bundles'), self.name)
        ENV_DICT['DIR_BUNDLE_CONFIG'] = runtime.path.join(env.get('dir_config'), self.name)
        for _dir in self.directories:
            if _dir.dir is None and _dir.name not in runtime.path.DEFAULT_DIRS.keys():
                raise Exception("Invalid default dir: `%s'" % _dir.name)

            if _dir.dir is None:
                _dir_name = 'dir_%s' % _dir.name
                _dst = runtime.path.join(env.get(_dir_name), _dir.bundle)
            else:
                _dst = _dir.dir.format(**ENV_DICT)
            _dir_name = 'DIR_BUNDLE_%s' % _dir.name.upper()
            ENV_DICT[_dir_name] = _dst
            if not os.path.exists(_dst):
                os.makedirs(_dst)
        for name, _dir in ENV_DICT.items():
            if name.startswith('DIR_BUNDLE') and not os.path.exists(_dir):
                os.makedirs(_dir)
        cmd = self.start.format(**ENV_DICT)
        _env = self.env
        for key, value in _env.items():
            _env[key] = value.format(**ENV_DICT)
        runtime.einfo(cmd)
        logger.debug(cmd)
        runtime.einfo("start service `%s'." % self.name)
        kwargs = {
            'env': _env,
        }
        logger.debug(kwargs)
        p = subprocess.Popen(cmd.split(), **kwargs)
        runtime.einfo(p.pid)

    def _stop(self, **kwargs):
        if self.name not in list_running_services():
            runtime.eerror("service `%s' is not running." % self.name)
            return

        ENV_DICT = env.all_dict()
        ENV_DICT['DIR_BUNDLE'] = runtime.path.join(env.get('dir_bundles'), self.name)
        _real_exe = self.start.split()[0].format(**ENV_DICT)

        # for normal services
        for _p in psutil.process_iter():
            try:
                # logger.debug('%d %s' % (_p.pid, _p.exe))
                if _p.exe == _real_exe:
                    runtime.einfo(_p.pid)
                    logger.debug('kill %d [%s]' % (_p.pid, self.name))
                    _p.terminate()
                    _p.wait()
                    logger.info(_p.status)
            except (psutil.error.NoSuchProcess, psutil.AccessDenied, IndexError):
                pass
            except Exception, e:
                runtime.eerror(e)
                logger.error(traceback.format_exc())

        # for setuid services
        logger.debug("find process via `ps ax'")
        for line in subprocess.check_output(['ps', 'ax']).split(os.linesep):
            try:
                parts = line.strip().split()
                if len(parts) > 4 and parts[4] == _real_exe:
                    logger.debug(parts)
                    logger.debug('kill %s [%s]' % (parts[0], self.name))
                    os.kill(int(parts[0]), signal.SIGTERM)
            except Exception, e:
                logger.error(e)

        runtime.einfo("stop service `%s'." % self.name)

    def _restart(self, **kwargs):
        self._stop()
        eventlet.sleep(3)
        self._start()

    def _toggle_enable(self, **kwargs):
        self.enable = kwargs['enable']
        store.add(self)
        store.commit()
        logger.debug('after toggle enable: %s' % str(self.enable))

    def _toggle_autostart(self, **kwargs):
        self.autostart = kwargs['autostart']
        store.add(self)
        store.commit()
        logger.debug('after toggle autostart: %s' % str(self.autostart))

class Settings(object):
    __storm_table__ = 'settings'

    id = Int(primary=True)
    key = Unicode()
    value = Unicode()

class Bundle(object):
    __storm_table__ = 'bundles'

    name = Unicode(primary=True)
    description = Unicode()
    directories = ReferenceSet(name, Directory.bundle)
    options = ReferenceSet(name, Option.bundle)

    def directories_env(self):
        _env = {}
        ENV_DICT = env.all_dict()
        for _dir in self.directories:
            if _dir.dir is None and _dir.name not in runtime.path.DEFAULT_DIRS.keys():
                raise Exception("Invalid default dir: `%s'" % _dir.name)

            if _dir.dir is None:
                _dir_name = 'dir_%s' % _dir.name
                _dst = runtime.path.join(env.get(_dir_name), _dir.bundle)
            else:
                _dst = _dir.dir.format(**ENV_DICT)
            _dir_name = 'DIR_BUNDLE_%s' % _dir.name
            _env[_dir_name.upper()] = _dst
        return _env

    def options_env(self):
        _env = {}
        for _option in self.options:
            k = '%s_%s' % (self.name, _option.name)
            _env[k.upper()] = _option.value
        return _env

    def env(self, additional=False):
        _env = {
            'DIR_BUNDLE': runtime.path.join(env.get('dir_bundles'), self.name),
        }
        for k, v in os.environ.items():
            if k.startswith(env.PREFIX):
                k = k.replace(env.PREFIX, '')
                _env[k] = v
        for _dir in _env.values():
            if not os.path.exists(_dir):
                os.makedirs(_dir)
        _env.update(self.directories_env())
        _env.update(self.options_env())
        return _env
