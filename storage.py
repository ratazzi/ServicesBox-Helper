#!/usr/bin/env python
# coding=utf-8

import logging
from eventlet.green import os
from storm.locals import create_database, Store

import runtime.path
from runtime import env

_database = None
_store = None
logger = logging.getLogger(__name__)

db_uri = os.path.abspath(runtime.path.join(env.get('dir_data'), 'core.db'))
logger.debug("database path: `%s'" % db_uri)

def get_store():
    global _database, _store
    if not _database:
        _database = create_database('sqlite:///%s' % db_uri)
    if not _store:
        _store = Store(_database)

    return _store

def init():
    import sqlite3
    logger.debug('create tables.')
    with open(runtime.path.resources_path('schema.sql')) as fp:
        conn = sqlite3.connect(db_uri)
        conn.executescript(fp.read())
