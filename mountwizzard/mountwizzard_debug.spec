# -*- mode: python -*-

block_cipher = None


a = Analysis(['mountwizzard.py'],
             pathex=['C:\\Program Files (x86)\\Python35-32\\Lib\\site-packages\\PyQt5\\Qt\\bin', 'C:\\Users\\mw\\Projects\\mountwizzard\\mountwizzard'],
             binaries=[],
             datas=[('model001.fit','.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='mountwizzard-console',
          debug=True,
          strip=False,
          upx=True,
          console=True,
          icon='./mountwizzard/mw.ico')
