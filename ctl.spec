# coding=utf-8

import os
from pprint import pprint

a = Analysis([os.path.join(HOMEPATH,'support/_mountzlib.py'), os.path.join(HOMEPATH,'support/useUnicode.py'), 'ctl.py'], pathex=[''])
pyz = PYZ(a.pure)

def collect_resources():
    items = []
    for root, dir, files in os.walk('resources'):
        for _file in files:
            if _file in ('.DS_Store'):
                continue
            item = os.path.join(root, _file)
            items.append((item, item, 'DATA'))
    return items

a.datas = collect_resources()
pprint(a.datas)

exe = EXE( pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'ctl'),
          debug=False,
          strip=False,
          upx=True,
          console=True )

# vim: ft=python
