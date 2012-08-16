#!/usr/bin/env python
# coding=utf-8

from UserDict import UserDict
from sqlalchemy import Column, Integer, Text

import storage
from base import Base

class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(Text)
    value = Column(Text)

class Store(UserDict):
    def __getitem__(self, key):
        row = None
        with storage.get_session() as session:
            row = session.query(Settings).filter_by(key=key).first()
        return row

    def __setitem__(self, key, value):
        with storage.get_session() as session:
            row = session.query(Settings).filter_by(key=key).first()
            if not row:
                row = Settings()
                row.key = key
            row.value = value
            session.add(row)
            session.commit()
