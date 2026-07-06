# 最近变更

## 2026-07-05 21:53:50 | pdf_file
- 摘要：Fix Smart Recursive ZIP mixed-content depth boundary
- 文件：tools/fx_zip_core.py, full_debug_test.py, memory/debug-status.md, memory/categories/pdf-file-meta-zip.md
- 说明：Smart Recursive now stops at folders containing meaningful files even when they are before the selected minimum depth; regression zip_smart_depth_range_stops_at_mixed_boundary; validation py_compile, smoke_test 14/14, full_debug_test 228/228.

## 2026-07-05 20:22:06 | watermark
- 摘要：Parallelize PDF-only batch watermark runs
- 文件：-
- 说明：Validation: py_compile passed, targeted probe workers=[2] success_count=2, smoke_test.py 14/14, full_debug_test.py 227/227.

## 2026-07-05 19:25:39 | runtime
- 摘要：Avoid duplicate default-tab startup initialization
- 文件：-
- 说明：Validated packaged launch: startup_total 2899.965ms, main_create_app 2063.937ms, single lazy_tab_init watermark 579.06ms and no post-show duplicate.

## 2026-07-05 19:10:11 | runtime
- 摘要：Improve startup perceived speed with default-tab lazy init
- 文件：Fengxi_Toolbox.py, tools/fx_startup_patches.py, full_debug_test.py, memory/debug-status.md, memory/architecture.md
- 说明：Diagnosed packaged startup logs showing startup_total around 3.3-3.4s and main_create_app around 2.4-2.5s. tools/fx_startup_patches.py now defers the default startup tab as well as non-default tabs; Fengxi_Toolbox.py shows the window first, then schedules default watermark tab initialization shortly after. Fixed the lazy-init first_random watermark range command to explicitly write wm_range_var. Validation: py_compile passed, smoke_test.py 14/14, full_debug_test.py 226/226.

## 2026-07-05 18:26:46 | convert
- 摘要：Make PDF conversion rich and reorganize convert UI
- 文件：Fengxi_Toolbox.py, tools/fx_convert_task.py, requirements.txt, fx_toolbox.spec, full_debug_test.py, memory/categories/convert-audio-image.md, memory/debug-status.md
- 说明：Converted PDF to PPT from image-backed slides to editable python-pptx text boxes with image shapes; PDF to Markdown now uses PyMuPDF4LLM with extracted assets and PyMuPDF fallback for text/images/tables. Replaced split convert radio layout with one unified 8-mode grid. Validation: py_compile passed, smoke_test.py 14/14, full_debug_test.py 226/226.

## 2026-07-05 17:46:40 | convert
- 摘要：Expand format conversion modes
- 文件：Fengxi_Toolbox.py, tools/fx_convert_core.py, tools/fx_convert_task.py, full_debug_test.py, memory/categories/convert-audio-image.md, memory/debug-status.md
- 说明：Added PDF to PPT, TXT to Word, Markdown to PDF, and PDF to Markdown modes under the existing convert task. New core specs, task helpers, loader UI buttons, extended run_process adapter, and final progress-wrapper interception keep structured counts accurate. Validation: py_compile passed, smoke_test.py 14/14, full_debug_test.py 224/224.

## 2026-06-24 09:50:46 | pdf_file
- 摘要：Add web-style raster PDF compression mode
- 文件：tools\fx_pdf_compress_core.py, Fengxi_Toolbox.py, full_debug_test.py, memory\categories\pdf-file-meta-zip.md, memory\debug-status.md
- 说明：Added a new opt-in PDF image compression profile named 网页式极限压缩. This mode rasterizes PDF pages to JPEG images and rebuilds the PDF, then participates in the normal smallest-valid-candidate selection alongside optimized, pikepdf, pymupdf, and ghostscript outputs. Existing compression profiles were left unchanged. UI help text now explains that this mode is best for upload/share and may lose searchable/editable/vector structure. Validation: py_compile passed, smoke_test.py 14/14, full_debug_test.py 223/223.

## 2026-06-21 09:19:49 | pdf_file
- 摘要：PDF compression Ghostscript TeX Live backend fix
- 文件：tools\fx_pdf_compress_core.py, full_debug_test.py, memory\categories\pdf-file-meta-zip.md, memory\debug-status.md
- 说明：PDF compression now discovers TeX Live bundled Ghostscript and builds GS_LIB with Resource Init, lib, kanji, and font/CMap/CID resource directories. Real sample 01-热力学第一定律.pdf compressed from 3947231 to 3609246 bytes with SUCCESS:2:ghostscript while keeping the no-growth guard. Added regressions for TeX Live GS_LIB env and real Ghostscript candidate execution. Validation: py_compile passed, smoke_test.py 14/14, full_debug_test.py 222/222.

## 2026-06-20 23:24:12 | pdf_file
- 摘要：PDF compression PDF24-inspired candidate optimization and clean cache metadata
- 文件：tools\fx_pdf_compress_core.py, Fengxi_Toolbox.py, full_debug_test.py, memory\categories\pdf-file-meta-zip.md, memory\debug-status.md
- 说明：PDF compression now uses multiple safe candidates inspired by PDF24-style strategy: PyMuPDF optimized save, optional pikepdf object stream optimization, existing PyMuPDF profile path, and optional Ghostscript when installed. The chosen output must be valid and smaller than the source; otherwise the original bytes are copied to avoid growth. Resume/profile metadata is now stored in a local cache file instead of hidden sidecar JSON files beside user outputs. Legacy sidecars are still read for compatibility, but new runs must not create .fx-compress.json files in result folders. Existing old sidecars in external user folders are not deleted without explicit permission. Real sample 01-热力学第一定律.pdf now shrinks slightly instead of growing from about 3.95MB to 12.44MB or producing visible sidecar clutter. Validation: py_compile passed, smoke_test.py 14/14, full_debug_test.py 220/220.

## 2026-06-20 22:54:15 | pdf_file
- 摘要：PDF compression no-growth and profile-aware resume
- 文件：tools\fx_pdf_compress_core.py, Fengxi_Toolbox.py, full_debug_test.py, memory\categories\pdf-file-meta-zip.md, memory\debug-status.md
- 说明：PDF compression now uses candidate selection and never keeps an output larger than the source. Optional Ghostscript is tried when locally available, otherwise PyMuPDF remains the built-in path. If no candidate is smaller, the output keeps the original bytes and logs kept_original. PDF compression resume now requires matching sidecar metadata for source and compression/image levels, so changing settings no longer reuses stale _压缩.pdf outputs. Real user sample no longer grows from 3.95MB to 12.44MB. Validation: py_compile passed, smoke_test.py 14/14, full_debug_test.py 218/218.

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
