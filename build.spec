# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs
cuda_binaries = collect_dynamic_libs('nvidia')

a = Analysis(
    ['main.py', './AlyssumResources/config.py', './AlyssumResources/translator.py', './AlyssumResources/argos_utils.py'],
    pathex=[],
    binaries=cuda_binaries,
    datas=[('AlyssumResources','AlyssumResources')],
    hiddenimports=['PyQt5', 'winrt.windows.ui.viewmanagement', 'qfluentwidgets', 'nvidia.cuda_runtime-cu12', 'nvidia.cublas-cu12', 'nvidia.cudnn-cu12'],
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
    disable_windowed_traceback=True,
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
