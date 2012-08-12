#!/usr/bin/env python
# coding=utf-8

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import runtime.path
# from runtime import env
from module.base import Base

_engine = None
# db_uri = runtime.path.join(env.get('dir_data'), 'core.db')
db_uri = os.path.abspath(runtime.path.join(os.path.dirname(__file__), 'core.db'))
print db_uri

def get_engine():
    global _engine
    if not _engine:
        _engine = create_engine('sqlite:///%s' % db_uri, echo=False)
    return _engine

Session = sessionmaker(bind=get_engine())

class ContextSession(object):
    _session = None

    def __enter__(self):
        if not self._session:
            self._session = Session()
        return self

    def __exit__(self, type, value, traceback):
        if self._session:
            self._session.close()

    def __getattr__(self, name):
        return getattr(self._session, name)

def get_session(with_context=True):
    if with_context:
        _session = ContextSession()
    else:
        _session = Session()
    return _session

def init():
    Base.metadata.create_all(get_engine())
