# 最近变更

## 2026-06-01 08:33:43 | runtime
- 摘要：packaged and opened visible watermark skip-rule UI build
- 文件：dist_release_ascii\fx_toolbox\fx_toolbox.exe
- 说明：Release build completed after moving batch watermark filename-rule controls to the active right-side panel. Started dist_release_ascii\\fx_toolbox\\fx_toolbox.exe successfully with PID 15564. PyInstaller optional pycparser/AppKit warnings were non-blocking.

## 2026-06-01 08:30:40 | watermark
- 摘要：fix visible batch watermark skip-rule controls
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory\categories\watermark-and-remove.md, memory\debug-status.md
- 说明：The prefix/suffix filename skip controls were created on a stale hidden watermark parameter panel. The layout now ensures the active right-side panel contains the controls row and the visible switch is renamed to 按文件名规则跳过. Added active-panel regression. Validation: py_compile, targeted UI probe, smoke_test 14/14, full_debug_test 184/184.

## 2026-06-01 08:17:16 | runtime
- 摘要：packaged and opened watermark skip rule restoration build
- 文件：dist_release_ascii\fx_toolbox\fx_toolbox.exe
- 说明：Release build completed after restoring batch watermark prefix/suffix filename skip rule. Started dist_release_ascii\\fx_toolbox\\fx_toolbox.exe successfully with PID 34844. PyInstaller optional warnings for pycparser/AppKit were non-blocking.

## 2026-06-01 08:13:45 | watermark
- 摘要：restore batch watermark prefix suffix filename skip rule
- 文件：Fengxi_Toolbox.py, tools\fx_user_prefs.py, full_debug_test.py, memory\categories\watermark-and-remove.md, memory\debug-status.md
- 说明：Batch watermark filename skip positions are normalized for Chinese labels and internal English values. Suffix '-' skip is covered by real run_process regression with copy-skipped option. Validation: py_compile, targeted probe, smoke_test 14/14, full_debug_test 183/183.

## 2026-06-01 01:02:26 | runtime
- 摘要：packaged and opened watermark skip-copy build
- 文件：Fengxi_Toolbox.py, tools\fx_user_prefs.py, full_debug_test.py
- 说明：Release build completed and dist_release_ascii\\fx_toolbox\\fx_toolbox.exe launched successfully after batch watermark skip-copy option. Started PID 3000.

## 2026-06-01 00:55:10 | watermark
- 摘要：add copy option for filename-rule skipped watermark files
- 文件：Fengxi_Toolbox.py, tools\fx_user_prefs.py, full_debug_test.py, memory\categories\watermark-and-remove.md, memory\debug-status.md
- 说明：Batch watermark now has wm_copy_skipped_var / 跳过文件复制到输出文件夹. Filename-rule skipped files are not watermarked; when enabled they are copied to the output/result folder preserving relative paths and counted as skipped. Settings persist in local filename_skip_rule.copy_skipped and last-settings. Validation: py_compile, targeted probe, smoke_test 14/14, full_debug_test 181/181.

## 2026-06-01 00:13:31 | runtime
- 摘要：packaged and opened ZIP preview fix build
- 文件：Fengxi_Toolbox.py, full_debug_test.py
- 说明：Release build completed and dist_release_ascii\\fx_toolbox\\fx_toolbox.exe launched successfully after ZIP preview/layout fix. Started PID 34924.

## 2026-06-01 00:09:31 | zip
- 摘要：fix ZIP preview count and move max-depth control right
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory\categories\pdf-file-meta-zip.md, memory\debug-status.md
- 说明：ZIP start preview now uses plan_zip_archives with active mode and max_depth, so folder-based smart/recursive inputs are not blocked as empty. ZIP max-depth control is laid out in the right column beside mode selection. Validation: py_compile, targeted probe, smoke_test 14/14, full_debug_test 179/179.

## 2026-05-31 23:55:13 | runtime
- 摘要：packaged and opened revised ZIP smart mode build
- 文件：-
- 说明：Build completed at dist_release_ascii\\fx_toolbox\\fx_toolbox.exe and launched successfully. ZIP smart mode now follows canonical layer semantics, root package inside root, non-root packages in parent, and max-depth applies to recursive and smart modes.

## 2026-05-31 23:51:32 | zip
- 摘要：ZIP smart mode revised layer semantics and max depth
- 文件：tools/fx_zip_core.py, Fengxi_Toolbox.py, tools/fx_user_prefs.py, full_debug_test.py, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md
- 说明：Changed smart_recursive to the user-canonical layer rule: each visited layer is zipped, mixed ordinary-files-plus-child-folders layers stop descent, child-folder-only layers are zipped and continue, and archive files do not block descent. Non-root folder packages now go to the parent folder while the root package stays inside root. Added max_depth support for recursive and smart modes, a ZIP UI max-depth entry, page documentation, plan logging, and last-settings memory for zip_mode_var/zip_max_depth_var. Read-only probe for the user's modified WeChat folder plans 5 smart archives, or 3 with max_depth=2. Validation: py_compile passed, targeted ZIP probe passed, smoke_test.py 14/14, full_debug_test.py 177/177.

## 2026-05-31 23:06:35 | runtime
- 摘要：packaged and opened ZIP notice build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt the onedir release after adding ZIP smart-mode output planning notices and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe. First package attempt failed because the previous packaged EXE was still running and locking dist_release_ascii; stopped only that project-packaged process (PID 33852), rebuilt successfully, and launched PID 36268. PyInstaller optional warnings (pycparser lextab/yacctab, AppKit on Windows) were non-blocking.

## 2026-05-31 22:59:51 | zip
- 摘要：ZIP smart root-only folder notice
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory\categories\pdf-file-meta-zip.md, memory\debug-status.md
- 说明：Diagnosed the user's WeChat folder as a root-only-subfolders case: total plans 1 root archive, recursive plans 4 archives, smart_recursive plans 2 child-folder archives. Added loader-layer ZIP plan messages so smart mode explains child-folder output and tells users to choose 仅压缩总文件 for one whole-folder zip. Did not modify tools/fx_zip_core.py or ZIP core semantics. Validation: py_compile passed, targeted probe passed, smoke_test.py 14/14, full_debug_test.py 173/173.

## 2026-05-31 22:39:05 | runtime
- 摘要：packaged and opened PDF encrypt password entry build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt the onedir release after adding the visible PDF 加密 password entry and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe. Launched PID 33852 and confirmed it stayed running after startup wait. PyInstaller optional warnings (pycparser lextab/yacctab, AppKit on Windows) were non-blocking.

## 2026-05-30 21:35:51 | pdf
- 摘要：PDF encrypt password entry visibility fix
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md
- 说明：Added a visible password entry directly in the PDF 加密 detail panel. The left shared password entry and right encrypt entry share pdf_pwd_var, and pdf_pwd_entry points to the visible encrypt entry so execution/history paths keep working. Validation: py_compile passed, smoke_test.py 14/14, full_debug_test.py 172/172.

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
