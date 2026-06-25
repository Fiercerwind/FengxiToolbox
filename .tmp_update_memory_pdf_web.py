from pathlib import Path

files = {
    'memory/categories/pdf-file-meta-zip.md': '''

## 2026-06-24 PDF web-style raster compression mode
- New optional image compression profile: `网页式极限压缩`.
- Purpose:
  - Match the kind of strong size reduction users see from web tools such as PDF24 on complex vector/Print-to-PDF documents.
  - Keep existing `保留原图 / 高清 / 轻度 / 标准 / 强力 / 极限小体积` behavior unchanged.
- Behavior:
  - This profile is opt-in only.
  - Fengxi rasterizes each page to a JPEG image and rebuilds the PDF page-by-page.
  - The rasterized result still enters the normal candidate race with optimized/pikepdf/pymupdf/ghostscript outputs.
  - Final safety rule is unchanged: only keep a valid candidate smaller than the source; otherwise keep the original bytes.
- User-visible caution:
  - This mode is for upload/share/web-size reduction.
  - It may lose selectable/searchable text, vector sharpness, links, forms, and editing friendliness because pages are turned into images.
- Implementation:
  - `tools/fx_pdf_compress_core.py` adds `WEB_RASTER_IMAGE_LEVEL = "网页式极限压缩"`.
  - Added `_save_rasterized_web_candidate(...)` using PyMuPDF page rendering + JPEG recomposition.
  - `Fengxi_Toolbox.py` PDF compression success log now labels this engine as `网页式栅格化`.
  - PDF compression panel help text now explains the tradeoff.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\\fx_pdf_compress_core.py full_debug_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 223/223.
''',
    'memory/debug-status.md': '''

## 2026-06-24 PDF web-style raster compression validation
- Added a new opt-in PDF compression profile: `网页式极限压缩`.
- This mode rasterizes PDF pages into JPEG images and rebuilds a new PDF, then lets the normal smallest-valid-candidate selection decide whether it wins.
- Existing non-raster profiles remain unchanged; the new mode does not replace normal optimized/pikepdf/pymupdf/ghostscript behavior.
- Safety rule preserved: if rasterization is not smaller, Fengxi still keeps a smaller non-raster candidate or the original bytes.
- UI/help text now warns that this mode is suitable for upload/share but may lose searchable/editable/vector structure.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\\fx_pdf_compress_core.py full_debug_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 223/223.
'''
}
for path, addition in files.items():
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if addition.strip() not in text:
        p.write_text(text + addition, encoding='utf-8')
print('memory updated')
