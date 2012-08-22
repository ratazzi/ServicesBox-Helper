#!/usr/bin/env python
# coding=utf-8

from UserDict import UserDict

import storage
from schema import Settings

store = storage.get_store()

class Store(UserDict):
    def __getitem__(self, key):
        row = None
        row = store.find(Settings, Settings.key == unicode(key)).one()
        return row

    def __setitem__(self, key, value):
        row = store.find(Settings, Settings.key == unicode(key)).one()
        if not row:
            row = Settings()
            row.key = unicode(key)
        row.value = unicode(value)
        store.add(row)
        store.commit()
