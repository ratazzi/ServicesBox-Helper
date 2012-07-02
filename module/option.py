#!/usr/bin/env python
# coding=utf-8

from sqlalchemy import Column, Integer, String, Text

import runtime.path
from runtime import env
from base import Base

class Option(Base):
    __tablename__ = 'options'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    addon = Column(Text)
    value = Column(Text)
    description = Column(Text)