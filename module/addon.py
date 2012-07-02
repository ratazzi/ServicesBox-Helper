#!/usr/bin/env python
# coding=utf-8

import os
from sqlalchemy import Column, Integer, String, Text

import runtime.path
import storage
from runtime import env
from base import Base
from option import Option
from directory import Directory

class Addon(Base):
    __tablename__ = 'addons'

    name = Column(Text, primary_key=True)
    description = Column(Text)

    def _directories(self):
        with storage.get_session() as session:
            rs = session.query(Directory).filter_by(addon=self.name).all()
            return rs

    def directories_env(self):
        _env = {}
        ENV_DICT = env.all_dict()
        for _dir in self._directories():
            if _dir.dir is None and _dir.name not in runtime.path.DEFAULT_DIRS.keys():
                raise Exception("Invalid default dir: `%s'" % _dir.name)

            if _dir.dir is None:
                _dir_name = 'dir_%s' % _dir.name
                _dst = runtime.path.join(env.get(_dir_name), _dir.addon)
            else:
                _dst = _dir.dir.format(**ENV_DICT)
            _dir_name = 'DIR_ADDON_%s' % _dir.name
            _env[_dir_name.upper()] = _dst
        return _env

    def _options(self):
        with storage.get_session() as session:
            rs = session.query(Option).filter_by(addon=self.name).all()
            return rs

    def options_env(self):
        _env = {}
        for _option in self._options():
            k = '%s_%s' % (self.name, _option.name)
            _env[k.upper()] = _option.value
        return _env

    def env(self):
        _env = {
            'DIR_ADDON': runtime.path.join(env.get('dir_addons'), self.name),
            }
        for _dir in _env.values():
            if not os.path.exists(_dir):
                os.makedirs(_dir)
        _env.update(self.directories_env())
        _env.update(self.options_env())
        return _env

def list_all():
    with storage.get_session() as session:
        rs = session.query(Addon).all()
        return rs

def get(name):
    with storage.get_session() as session:
        row = session.query(Addon).filter_by(name=name).first()
        return row
