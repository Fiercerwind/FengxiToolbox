# 最近变更

## 2026-05-28 20:36:32 | watermark
- 摘要：watermark color picker and preview
- 文件：Fengxi_Toolbox.py, tools/fx_watermark_core.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md, memory/architecture.md
- 说明：Added selectable #RRGGBB watermark color for PDF and Word output, inline PIL preview UI, and last-settings memory for wm_color_var. Validation: py_compile passed, smoke_test 14/14, full_debug_test 159/159.

## 2026-05-28 18:19:39 | runtime
- 摘要：packaged and opened direct Word watermark visibility build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt and opened the onedir release after fixing direct Word watermark visible rendering. Build completed successfully; PyInstaller warnings were non-blocking optional dependency/cross-platform probe noise.

## 2026-05-28 18:13:06 | watermark
- 摘要：direct Word watermark visible rendering fix
- 文件：tools/fx_watermark_core.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md, memory/architecture.md
- 说明：Fixed direct Word watermark success-but-invisible output by explicitly setting WordArt fill visibility, solid gray fill, no outline, overlap wrapping, and a Word-only minimum visible opacity. Added rendered Word export regressions for helper and app.run_process direct watermark paths. Validation: py_compile passed, smoke_test 14/14, full_debug_test 156/156.

## 2026-05-28 17:45:21 | runtime
- 摘要：packaged and opened watermark real fix build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt the onedir release after the batch watermark direct/convert-PDF fix and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe. Packaging completed successfully; PyInstaller warnings were non-blocking optional dependency and cross-platform probe noise.

## 2026-05-28 17:40:29 | watermark
- 摘要：batch watermark direct and PDF conversion real fix
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md, memory/architecture.md
- 说明：Added loader-layer watermark task runner so single-file Word direct watermark and Word-to-PDF watermark produce real outputs, structured results, and real failures instead of false success. Word-to-PDF conversion now falls back to safe Word ExportAsFixedFormat when runtime conversion fails. Validated with real user document, smoke_test 14/14, full_debug_test 154/154.

## 2026-05-28 16:58:57 | runtime
- 摘要：packaged and opened batch watermark COM fix build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt the onedir release after the Dispatch/DispatchEx Office COM guard and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe. Packaging completed successfully; launched process is running.

## 2026-05-28 16:54:29 | watermark
- 摘要：batch watermark Word COM Dispatch guard
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md, memory/architecture.md
- 说明：Patched both win32com.client.Dispatch and DispatchEx at the loader layer so the runtime batch-watermark .docx branch cannot hit damaged pywin32 gen_py Word wrappers. Added real app.run_process watermark .docx regression; py_compile passed, smoke_test 14/14, full_debug_test 152/152.

## 2026-05-28 16:38:42 | runtime
- 摘要：packaged and opened Office COM fix build
- 文件：dist_release_ascii\fx_toolbox\fx_toolbox.exe,memory\recent-changes.md,memory\changes.jsonl
- 说明：Built the onedir release after the Office COM gen_py safe dispatch fix and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe for manual testing. Build completed successfully; PyInstaller warnings were non-blocking optional dependency/cross-platform probes.
