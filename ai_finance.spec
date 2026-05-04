# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
    ],
    hiddenimports=[
        'src',
        'src.core', 'src.core.types', 'src.core.account', 'src.core.trade_validator',
        'src.core.trade_executor', 'src.core.risk', 'src.core.risk.rules', 'src.core.wal',
        'src.business', 'src.business.loan', 'src.business.data_fetcher', 'src.business.data_fetcher.sources',
        'src.business.ai_adapter', 'src.business.scheduler', 'src.business.contest',
        'src.auxiliary', 'src.auxiliary.snapshot', 'src.auxiliary.logging_',
        'src.auxiliary.report', 'src.auxiliary.report.charts', 'src.auxiliary.version_control',
        'src.infrastructure', 'src.infrastructure.storage', 'src.infrastructure.crypto_',
        'src.infrastructure.config', 'src.infrastructure.module_manager',
        'src.gui', 'src.gui.views', 'src.gui.widgets',
        'sqlalchemy.dialects.sqlite', 'sqlalchemy.ext.asyncio', 'aiosqlite',
        'cryptography', 'cryptography.fernet',
        'pydantic', 'yaml',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AI-Finance-Simulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
