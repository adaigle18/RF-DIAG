# -*- mode: python ; coding: utf-8 -*-
#
# RF_DIAG.spec — PyInstaller spec for RF-DIAG macOS .app bundle
#
# Build with:
#   pyinstaller RF_DIAG.spec --noconfirm
#
# The resulting bundle is at dist/RF-DIAG.app
# On first launch macOS will ask for Location Services permission (required
# for CoreWLAN to return SSIDs on macOS 14+).

block_cipher = None

a = Analysis(
    ['app_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),   # Flask templates
    ],
    hiddenimports=[
        # PyObjC / CoreWLAN
        'objc',
        'CoreWLAN',
        'AppKit',
        'Foundation',
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
    name='RF-DIAG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,           # keep True so logs appear if launched from Terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file='entitlements.plist',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='RF-DIAG',
)

app = BUNDLE(
    coll,
    name='RF-DIAG.app',
    icon=None,
    bundle_identifier='com.rfdiag.wifi',
    version='9.0.0',
    info_plist={
        # ── Location Services (required for CoreWLAN SSIDs on macOS 14+) ──────
        'NSLocationWhenInUseUsageDescription':
            'RF-DIAG needs Location Services access to read Wi-Fi network names '
            '(SSIDs) on macOS 14 and later.',
        'NSLocationAlwaysAndWhenInUseUsageDescription':
            'RF-DIAG needs Location Services access to read Wi-Fi network names '
            '(SSIDs) on macOS 14 and later.',
        # ── Bundle metadata ───────────────────────────────────────────────────
        'CFBundleDisplayName':        'RF-DIAG',
        'CFBundleName':               'RF-DIAG',
        'CFBundleShortVersionString': '9.0.0',
        'CFBundleVersion':            '9.0.0',
        'NSHighResolutionCapable':    True,
        'NSRequiresAquaSystemAppearance': False,  # support Dark Mode
        'LSBackgroundOnly':           False,       # must be False for Location Services to appear
    },
)
