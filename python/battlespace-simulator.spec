# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all Python files
python_files = [
    'battlespace-simulator.py',
    'tedf-broadcaster.py',
    'entity-simulator.py',
    'config-loader.py',
    'gui-components.py',
    'version_manager.py'
]

# Data files to include
datas = [
    ('simulator_config.json', '.'),
    ('Azure-ttk-theme-main/azure.tcl', 'Azure-ttk-theme-main'),
    ('Azure-ttk-theme-main/theme', 'Azure-ttk-theme-main/theme'),
]

a = Analysis(
    ['battlespace-simulator.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['zmq', 'psutil', 'colorama', 'tkinter', '_tkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add all python modules
for py_file in python_files[1:]:  # Skip the main file
    a.datas.append((py_file, py_file, 'DATA'))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='battlespace-simulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)