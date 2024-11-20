# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['ej_live.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Add any additional files your app might need
        # Example: ('datafile.json', '.'),
    ],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='ej_live',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Change to False if you don't need the console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='./icon.ico',
    version='./ej_live_version.txt',  # Path to your version information file
    description='ej_live Application for real-time live data processing and management.',
    company_name='Cooperative Bank of Oromia',  # Adjust company name as needed
    copyright='© 2024 Cooperative Bank of Oromia. All rights reserved.',
)
