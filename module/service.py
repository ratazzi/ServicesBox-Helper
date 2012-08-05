#!/usr/bin/env python
# coding=utf-8

import os
import logging
logger = logging.getLogger(__name__)
import traceback
import json
import psutil
import subprocess
from sqlalchemy import Column, Integer, Text

import storage
import runtime
import runtime.path
from runtime import env
from base import Base

class Service(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    addon = Column(Text)
    description = Column(Text)
    start = Column(Text)
    stop = Column(Text)
    restart = Column(Text)
    env = Column(Text)

    def _start(self):
        if self.name in list_running_services():
            runtime.eerror("service `%s' is already running." % self.name)
            return

        ENV_DICT = env.all_dict()
        ENV_DICT['DIR_ADDON'] = runtime.path.join(env.get('dir_addons'), self.name)
        ENV_DICT['DIR_ADDON_CONFIG'] = runtime.path.join(env.get('dir_config'), self.name)
        ENV_DICT['DIR_ADDON_DATA'] = runtime.path.join(env.get('dir_data'), self.name)
        for name, _dir in ENV_DICT.items():
            if name.startswith('DIR_ADDON') and not os.path.exists(_dir):
                os.makedirs(_dir)
        cmd = self.start.format(**ENV_DICT)
        self.env = json.loads(self.env)
        for key, value in self.env.items():
            self.env[key] = value.format(**ENV_DICT)
        runtime.einfo(cmd)
        logger.debug(cmd)
        runtime.einfo("start service `%s'." % self.name)
        p = subprocess.Popen(cmd.split(), env=self.env)
        runtime.einfo(p.pid)

    def _stop(self):
        if self.name not in list_running_services():
            runtime.eerror("service `%s' is not running." % self.name)
            return

        ENV_DICT = env.all_dict()
        ENV_DICT['DIR_ADDON'] = runtime.path.join(env.get('dir_addons'), self.name)
        _real_exe = self.start.split()[0].format(**ENV_DICT)
        for _p in psutil.process_iter():
            try:
                if _p.exe == _real_exe:
                    runtime.einfo(_p.pid)
                    _p.terminate()
            except psutil.AccessDenied:
                pass
            except IndexError:
                pass
            except Exception, e:
                runtime.eerror(e)
                traceback.print_exc()

        # if not _process:
        #     sys.stderr.write("service `%s' is not running.%s" % (self.name, os.linesep))
        #     sys.stderr.flush()
        runtime.einfo("stop service `%s'." % self.name)
        # print repr(_process.get_children())
        # for _child in _process.get_children():
        #     _exe = _child.cmdline[0].replace(os.path.sep, '/').replace('.exe', '')
        #     print _exe
        #     logger.debug(_exe)
        #     if _exe == _real_exe:
        #         logger.info("terminate child process `%s', pid %d." % (_exe, _child.pid))
        #         _child.terminate()
        # _process.terminate()

    def _restart(self):
        self._stop()
        self._start()

def get(name):
    with storage.get_session() as session:
        return session.query(Service).filter_by(name=name).first()

def list_all():
    with storage.get_session() as session:
        rs = session.query(Service).all()
        return rs

def all_services_exe():
    ENV_DICT = env.all_dict()
    items = {}
    for _service in list_all():
        ENV_DICT['DIR_ADDON'] = runtime.path.join(env.get('dir_addons'), _service.name)
        _exe = _service.start.split()[0]
        _exe = _exe.format(**ENV_DICT)
        items[_service.name] = _exe
    return items

def list_running_services():
    exe2services = dict([(v, k) for k, v in all_services_exe().items()])
    ENV_DICT = env.all_dict()
    rs = []
    _services = []
    for _service in list_all():
        ENV_DICT['DIR_ADDON'] = runtime.path.join(env.get('dir_addons'), _service.name)
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
        except IndexError:
            pass
        except Exception, e:
            runtime.eerror(e)
            traceback.print_exc()
    return rs
