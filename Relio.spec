# -*- mode: python ; coding: utf-8 -*-
"""
Relio - PyInstaller 打包配置文件
Relationship Intelligence Orchestrator
生成独立的 macOS 应用程序
"""

import os
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(SPECPATH)

# 收集数据文件
datas = [
    # 资源文件
    (str(PROJECT_ROOT / 'assets'), 'assets'),
    # 配置文件
    (str(PROJECT_ROOT / 'config'), 'config'),
    # 数据目录（初始数据模板）
    (str(PROJECT_ROOT / 'data'), 'data'),
]

# 隐式导入（确保所有模块都被包含）
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtSvg',
    'PySide6.QtSvgWidgets',
    'matplotlib',
    'matplotlib.backends.backend_qtagg',
    'matplotlib.figure',
    'openai',
    'dotenv',
    'json',
    'logging',
    'pathlib',
    'dataclasses',
    'enum',
    'typing',
    'datetime',
    'uuid',
    'hashlib',
    'requests',
    'httpx',
    # 项目模块
    'core',
    'core.config',
    'core.system',
    'core.user_profile',
    'core.relationship_state',
    'core.conversation_analyzer',
    'core.reply_decision',
    'core.llm_client',
    'core.storage',
    'core.history_store',
    'core.intimacy_manager',
    'core.memory_extractor',
    'ui',
    'ui.main_window',
    'ui.dialogs',
    'ui.settings_dialogs',
    'ui.theme_manager',
    'ui.button_styles',
    'ui.store',
]

# 排除不需要的模块（减小体积）
excludes = [
    'tkinter',
    'test',
    'pydoc',
    'doctest',
    'IPython',
    'jupyter',
    'notebook',
    'pytest',
]

a = Analysis(
    ['main.py'],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Relio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示终端窗口
    disable_windowed_traceback=False,
    argv_emulation=True,  # macOS 需要
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
    name='Relio',
)

app = BUNDLE(
    coll,
    name='Relio.app',
    icon='assets/AppIcon.icns' if os.path.exists('assets/AppIcon.icns') else None,
    bundle_identifier='com.ssheep.relio',
    version='1.0.0',
    info_plist={
        'CFBundleDevelopmentRegion': 'en',
        'CFBundleDisplayName': 'Relio',
        'CFBundleName': 'Relio',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1',
        'LSMinimumSystemVersion': '10.15',
        'NSHighResolutionCapable': True,
        'NSPrincipalClass': 'NSApplication',
        'LSUIElement': False,
        # 权限描述
        'NSAppleEventsUsageDescription': 'Relio needs to control other applications to send messages.',
        'NSMicrophoneUsageDescription': 'Relio may need microphone access for voice input features.',
    },
)
