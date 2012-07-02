#!/usr/bin/env python
# coding=utf-8

import os

PREFIX = 'X_'

def add(name, value):
    _name = '%s%s' % (PREFIX, name.upper())
    os.environ[_name] = value

def get(name):
    _name = '%s%s' % (PREFIX, name.upper())
    return os.environ[_name].replace(os.path.sep, '/')

def all_dict():
    _data = {}
    for k, v in os.environ.items():
        if k.startswith(PREFIX):
            name = k[len(PREFIX):]
            _data[name] = v.replace(os.path.sep, '/')
    return _data