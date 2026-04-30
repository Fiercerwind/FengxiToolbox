# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('fengxi_runtime.bin', '.')]
datas += collect_data_files('customtkinter')


a = Analysis(
    ['Fengxi_Toolbox.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['PyInstaller.archive.readers', 'customtkinter', 'pdf2docx', 'PIL', 'imageio', 'imageio_ffmpeg', 'moviepy', 'moviepy.editor', 'pypdf', 'pythoncom', 'pywinstyles', 'reportlab.lib.pagesizes', 'reportlab.pdfbase', 'reportlab.pdfbase.ttfonts', 'reportlab.pdfgen', 'tkinter', 'tkinter.filedialog', 'tkinter.font', 'tkinter.messagebox', 'tkinter.ttk', 'windnd', 'win32com.client'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='fx_toolbox_diag',
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
)
