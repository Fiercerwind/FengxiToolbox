# 最近变更

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
