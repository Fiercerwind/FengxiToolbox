# 最近变更

## 2026-06-09 09:15:30 | runtime
- 摘要：Stage startup post-show layout refresh
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory\architecture.md, memory\debug-status.md, memory\recent-changes.md
- 说明：Post-show startup layout refresh now runs as staged callbacks: shell layout, current-tab layout, then visible refresh. This avoids one long layout callback after the window appears. Validation: py_compile passed, smoke_test 14/14, full_debug_test 216/216.

## 2026-06-09 08:57:46 | runtime
- 摘要：Optimize startup layout refresh
- 文件：Fengxi_Toolbox.py, tools\fx_startup_patches.py, full_debug_test.py, memory\architecture.md, memory\debug-status.md, memory\recent-changes.md
- 说明：Startup refresh now tightens only the current visible tab and avoids a synchronous idle flush. Switch-tab refresh keeps one idle flush. Validation: py_compile passed, smoke_test 14/14, full_debug_test 216/216.

## 2026-06-08 20:54:32 | pdf_file
- 摘要：Improve PDF image compression quality for long scanned pages
- 文件：tools/fx_pdf_compress_core.py, full_debug_test.py, memory/categories/pdf-file-meta-zip.md
- 说明：PDF image compression now preserves readable width for scanned long-image PDFs. Added 高清 and 极限小体积 profiles; 标准 keeps 1080px width, 强力 keeps 900px width. Real user PDF probe compressed 19.6MB to about 6.2MB while preserving 1080px width. full_debug_test 214/214.

## 2026-06-08 16:21:16 | watermark
- 摘要：Add first page plus one random page watermark range
- 文件：Fengxi_Toolbox.py, tools/fx_watermark_core.py, full_debug_test.py, memory/categories/watermark-and-remove.md
- 说明：Batch watermark now supports page_range=first_random: watermark page 1 plus exactly one random non-first page when available. Covered by UI, PDF, and Word regressions; full_debug_test 213/213.
