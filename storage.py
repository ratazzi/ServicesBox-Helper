#!/usr/bin/env python
# coding=utf-8

import os
from storm.locals import create_database, Store

import runtime.path
from runtime import env
from module.base import Base

_database = None
_store = None

db_uri = os.path.abspath(runtime.path.join(os.path.dirname(__file__), 'core.db'))
print db_uri

def get_store():
    global _database, _store
    if not _database:
        _database = create_database('sqlite:///%s' % db_uri)
    if not _store:
        _store = Store(_database)

    return _store

def init():
    import sqlite3
    print 'create tables.'
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql')) as fp:
        conn = sqlite3.connect(db_uri)
        conn.executescript(fp.read())
