# -*- mode: python -*-
block_cipher = None

a = Analysis(['test.py'],
             pathex=['C:\\Program Files (x86)\\Python35-32\\Lib\\site-packages\\PyQt5\\Qt\\bin'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

print()
print('######################################################')
print(len(a.pure))
# a.pure.append(('astropy.extern.six.six', 'c:\\program files (x86)\\python35-32\\lib\\site-packages\\astropy\\extern\\bundled\\six.py', 'PYMODULE'))

for i, file in enumerate(a.pure):
    if 'astropy.extern.six' in file:
        print(file)
        a.pure[i] = ('astropy.extern.six', 'c:\\program files (x86)\\python35-32\\lib\\site-packages\\astropy\\extern\\bundled\\six.py', 'PYMODULE')

print()

for pfile in a.pure:
    if 'astropy.extern' in pfile[0]:
        print(pfile)

print('######################################################')

#for pfile in a.zipped_data:
#    if 'astropy.extern' in pfile[0]:
#        print(pfile)
#print('######################################################')

print()

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='test',
          debug=True,
          strip=False,
          upx=False,
          console=True)
