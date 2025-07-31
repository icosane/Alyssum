# -*- mode: python ; coding: utf-8 -*-
data = []
from PyInstaller.utils.hooks import collect_dynamic_libs
data += collect_dynamic_libs('nvidia')
data += collect_dynamic_libs('torch')
data += collect_dynamic_libs('ctranslate2')
data += collect_dynamic_libs('cv2')
data += collect_dynamic_libs('PyQt5')

a = Analysis(
    ['main.py', './AlyssumResources/config.py', './AlyssumResources/translator.py', './AlyssumResources/argos_utils.py', './AlyssumResources/tesseract.py'],
    pathex=[],
    binaries=data,
    datas=[('AlyssumResources','AlyssumResources')],
    hiddenimports=['PyQt5', 'qfluentwidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Alyssum',
    version="version.txt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    manifest=None,
    icon='./AlyssumResources/assets/icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
