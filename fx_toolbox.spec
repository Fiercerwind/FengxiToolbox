# -*- mode: python ; coding: utf-8 -*-
import importlib.util
import os

from PyInstaller.building.datastruct import TOC
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules


CONFLICTING_RUNTIME_DLLS = {
    "msvcp140.dll",
    "msvcp140_1.dll",
    "ucrtbase.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll",
}


def _is_conflicting_runtime_binary(entry):
    names = []
    try:
        names.append(os.path.basename(str(entry[0])).lower())
    except Exception:
        pass
    try:
        names.append(os.path.basename(str(entry[1])).lower())
    except Exception:
        pass
    return any(name.startswith("api-ms-win-crt-") or name in CONFLICTING_RUNTIME_DLLS for name in names)


def _module_exists(module_name):
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False

datas = [('fengxi_runtime.bin', '.')]
datas += collect_data_files('customtkinter')
datas += collect_data_files('rapidocr')
binaries = collect_dynamic_libs('onnxruntime')
hiddenimports = [
    'PyInstaller.archive.readers', 'customtkinter', 'pdf2docx', 'PIL', 'imageio',
    'imageio_ffmpeg', 'pypdf', 'pythoncom',
    'pywinstyles', 'rapidocr', 'reportlab.lib.pagesizes', 'reportlab.pdfbase',
    'reportlab.pdfbase.ttfonts', 'reportlab.pdfgen', 'tkinter', 'tkinter.filedialog',
    'tkinter.font', 'tkinter.messagebox', 'tkinter.ttk', 'windnd',
    'win32com.client'
]
for module_name in (
    'moviepy',
    'moviepy.editor',
    'moviepy.audio.io.AudioFileClip',
    'moviepy.video.io.VideoFileClip',
):
    if _module_exists(module_name):
        hiddenimports.append(module_name)
hiddenimports += collect_submodules(
    'rapidocr',
    filter=lambda name: not name.startswith('rapidocr.inference_engine.tensorrt'),
    on_error='ignore',
)


a = Analysis(
    ['Fengxi_Toolbox.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
a.binaries = TOC([entry for entry in a.binaries if not _is_conflicting_runtime_binary(entry)])
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='fx_toolbox',
    icon='assets\\fengxi_app_icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
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
    upx=False,
    upx_exclude=[],
    name='fx_toolbox',
)
