# -*- mode: python ; coding: utf-8 -*-

# helpful links:
# https://stackoverflow.com/questions/51312059/kvasers-can-library-has-been-loaded-but-program-executable-outputs-a-no-modul

block_cipher = None

added_files = [
    ('ui/logo.png', 'ui/logo.png')
]

binaries = [
    ('C:\\Windows\\System32\\libusb0.dll', '.'),
    ('C:\\Windows\\System32\\libusb-1.0.dll', '.')
]

paths = []


a = Analysis(['main.py'],
             pathex=paths,
             binaries=binaries,
             datas=added_files,
             hiddenimports=['usb'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='logo.ico')
