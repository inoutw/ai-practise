# -*- mode: python ; coding: utf-8 -*-


block_cipher = None



a = Analysis(
    ['run.py', 'utcode_window.py', 'utcode_action.py', 'cache.py', 'config.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('dict.xls', '.'),
        ('system.txt', '.'),
        ('cache.json', '.'),
        ('sample', 'sample'),
        ('i18n', 'i18n'),
        ('config.toml', '.'),
        ('cache.db', '.')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='UT generator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/robo.ico'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='run',
)
