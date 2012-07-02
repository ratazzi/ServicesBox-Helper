#!/usr/bin/env python
# coding=utf-8

from sqlalchemy import Column, Integer, String, Text

import runtime.path
from runtime import env
from base import Base

class Directory(Base):
    __tablename__ = 'directories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    addon = Column(Text)
    dir = Column(Text)
    permission = Column(String)
    description = Column(Text)