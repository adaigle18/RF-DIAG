# -*- mode: python ; coding: utf-8 -*-
#
# RF_DIAG_Windows.spec — PyInstaller spec for RF-DIAG Windows .exe
#
# Build on a Windows machine with:
#   pip install flask paramiko pyinstaller
#   pyinstaller RF_DIAG_Windows.spec --noconfirm
#
# Result: dist\RF-DIAG\RF-DIAG.exe  (one-folder bundle)

block_cipher = None

a = Analysis(
    ['app_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
    ],
    hiddenimports=[
        # Paramiko (SSH to WLANPi)
        'paramiko',
        'paramiko.transport',
        'paramiko.auth_handler',
        'paramiko.sftp_client',
        'cryptography',
        'cryptography.hazmat.primitives.asymmetric.padding',
        # Flask / Werkzeug / Jinja2
        'flask',
        'flask.templating',
        'jinja2',
        'jinja2.ext',
        'werkzeug',
        'werkzeug.serving',
        'werkzeug.routing',
        'werkzeug.middleware.proxy_fix',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'objc', 'CoreWLAN', 'AppKit', 'Foundation', 'CoreLocation',
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RF-DIAG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,           # keep console window so users can see logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RF-DIAG',
)
