#!/usr/bin/env python
# coding=utf-8

import sys

def einfo(output, newline=True):
    sys.stdout.write('%s%s' % (output, newline and '\n' or ''))
    sys.stdout.flush()

def eerror(output, newline=True):
    sys.stderr.write('%s%s' % (output, newline and '\n' or ''))
    sys.stderr.flush()
