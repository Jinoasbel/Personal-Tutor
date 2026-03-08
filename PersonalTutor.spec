# -*- mode: python ; coding: utf-8 -*-
# PersonalTutor.spec — PyInstaller build specification
#
# Run:  pyinstaller PersonalTutor.spec --noconfirm --clean
# Output: dist\Ur Personal Tutor\Ur Personal Tutor.exe

import sys
import os
from pathlib import Path

ROOT = Path(SPECPATH)
block_cipher = None

# ── Helper: find a package's directory from the active Python environment ─────
def pkg_dir(name):
    """Return Path to an installed package's directory, or None if not found."""
    import importlib.util
    spec = importlib.util.find_spec(name)
    if spec and spec.submodule_search_locations:
        return Path(list(spec.submodule_search_locations)[0])
    if spec and spec.origin:
        return Path(spec.origin).parent
    return None

def collect_pkg_data(pkg_name, dest_name=None):
    """
    Return a (src, dest) tuple for PyInstaller datas if the package exists.
    Includes the entire package directory so all data files are bundled.
    """
    d = pkg_dir(pkg_name)
    if d and d.exists():
        return (str(d), dest_name or pkg_name)
    return None

# ── Collect data-heavy packages ───────────────────────────────────────────────
_data_packages = [
    'language_tags',    # needs data/json/
    'csvw',             # needs datasets/
    'segments',         # needs data files
    'phonemizer',       # needs share/ and backends
    'misaki',           # needs data files
    'kokoro',           # needs voices/ config
    'espeakng_loader',  # needs espeak-ng-data/
    'paddle',           # PaddlePaddle runtime data
    'paddleocr',        # OCR models and configs
]

extra_datas = []
for pkg in _data_packages:
    entry = collect_pkg_data(pkg)
    if entry:
        extra_datas.append(entry)
        print(f'  + Bundling data: {pkg} -> {entry[0]}')
    else:
        print(f'  ! Package not found: {pkg}')

# ── Also find espeak-ng DLL (Windows) ────────────────────────────────────────
_espeak_binaries = []
try:
    import espeakng_loader
    import os
    _esp_dir = Path(espeakng_loader.__file__).parent
    for _dll in _esp_dir.rglob("*.dll"):
        _espeak_binaries.append((str(_dll), "espeakng_loader"))
    for _dll in _esp_dir.rglob("*.so"):
        _espeak_binaries.append((str(_dll), "espeakng_loader"))
    print(f"  + espeak binaries found: {len(_espeak_binaries)}")
except Exception as e:
    print(f"  ! espeak binary detection failed: {e}")

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[] + _espeak_binaries,
    datas=[
        # ── Local packages ────────────────────────────────────────────────────
        (str(ROOT / 'pt_theme'),        'pt_theme'),
        (str(ROOT / 'icons'),           'icons'),
        (str(ROOT / 'ui'),              'ui'),
        (str(ROOT / 'core'),            'core'),
        (str(ROOT / 'assets'),          'assets'),
        (str(ROOT / 'app_config.py'),   '.'),
        (str(ROOT / 'main_window.py'),  '.'),
    ] + extra_datas,
    hiddenimports=[
        # ── App modules ───────────────────────────────────────────────────────
        'app_config',
        'main_window',
        'core',
        'core.paths',
        'core.audio_generator',
        'core.key_store',
        'core.lesson_writer',
        'core.link_extractor',
        'core.ocr_engine',
        'core.qa_engine',
        'core.question_generator',
        'core.summarizer',
        'core.workers',
        'core.app_state',
        'ui',
        'ui.ask_panel',
        'ui.audio_panel',
        'ui.link_row',
        'ui.panels',
        'ui.settings_panel',
        'ui.sidebar',
        'ui.upload_dialog',
        'pt_theme',
        'icons',
        'icons.icon_loader',
        # ── PySide6 ───────────────────────────────────────────────────────────
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        # ── Kokoro chain ──────────────────────────────────────────────────────
        'kokoro',
        'misaki',
        'misaki.espeak',
        'phonemizer',
        'phonemizer.backend',
        'phonemizer.backend.espeak',
        'phonemizer.backend.espeak.espeak',
        'phonemizer.backend.segments',
        'segments',
        'csvw',
        'csvw.metadata',
        'language_tags',
        'language_tags.tags',
        'loguru',
        'espeakng_loader',
        'soundfile',
        'numpy',
        # ── PaddleOCR ─────────────────────────────────────────────────────────
        'paddleocr',
        'paddle',
        'PIL',
        'PIL._tkinter_finder',
        # ── YouTube ───────────────────────────────────────────────────────────
        'youtube_transcript_api',
        # ── stdlib ────────────────────────────────────────────────────────────
        'urllib.request',
        'urllib.error',
        'json',
        'base64',
        'logging',
        'logging.handlers',
        'pathlib',
        're',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(ROOT / 'installer' / 'rthook_streams.py')],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
    ],
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
    name='Ur Personal Tutor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'assets' / 'icons' / 'app.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Ur Personal Tutor',
)
