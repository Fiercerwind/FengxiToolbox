# 最近变更

## 2026-05-30 01:03:15 | runtime
- 摘要：packaged and opened OCR nav fix build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt the onedir release after fixing the PDF OCR nav visibility regression and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe. Launched PID 26164 and confirmed it stayed running after startup wait. PyInstaller optional warnings (pycparser lextab/yacctab, AppKit on Windows) were non-blocking.

## 2026-05-30 01:00:37 | pdf
- 摘要：PDF OCR nav visibility fix
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md
- 说明：Fixed the PDF page left feature list so OCR 搜索版 PDF is no longer clipped after adding realtime preview. PDF mode buttons are compact single-line entries; added pdf_ocr_nav_button_visible regression. Validation: py_compile passed, smoke_test.py 14/14, full_debug_test.py 171/171.

## 2026-05-30 00:19:52 | runtime
- 摘要：packaged and opened OCR preview build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt the onedir release after adding OCR realtime preview and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe. Launched PID 14944 and confirmed it stayed running after startup wait. PyInstaller warnings were non-blocking optional/cross-platform hook noise.
