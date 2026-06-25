from pathlib import Path

p = Path('tools/fx_pdf_compress_core.py')
text = p.read_text(encoding='utf-8')

text = text.replace(
    'from PIL import Image as PILImage\n\n\nPDF_COMPRESS_LEVELS = {',
    'from PIL import Image as PILImage\n\n\nWEB_RASTER_IMAGE_LEVEL = "网页式极限压缩"\n\n\nPDF_COMPRESS_LEVELS = {'
)

text = text.replace(
    '    "极限小体积": {"enabled": True, "quality": 55, "max_side": 1800, "min_width": 480, "progressive": True},\n}',
    '    "极限小体积": {"enabled": True, "quality": 55, "max_side": 1800, "min_width": 480, "progressive": True},\n    WEB_RASTER_IMAGE_LEVEL: {\n        "enabled": False,\n        "rasterize_pdf": True,\n        "raster_dpi": 150,\n        "raster_quality": 65,\n        "raster_progressive": True,\n    },\n}'
)

old = '''def _save_pikepdf_candidate(src, dst):
    try:
        import pikepdf
    except Exception as exc:
        return f"SKIP:pikepdf unavailable {exc}"
    try:
        pdf = pikepdf.Pdf.open(src)
        try:
            object_stream_mode = pikepdf.ObjectStreamMode.generate
            pdf.save(
                dst,
                compress_streams=True,
                object_stream_mode=object_stream_mode,
                linearize=False,
            )
        finally:
            pdf.close()
    except Exception as exc:
        return f"SKIP:pikepdf failed {exc}"
    if not os.path.exists(dst) or os.path.getsize(dst) <= 0:
        return "SKIP:pikepdf empty output"
    return "SUCCESS"


'''
new = old + '''def _save_rasterized_web_candidate(src, dst, raster_profile, password=""):
    import fitz

    dpi = int(raster_profile.get("raster_dpi") or 150)
    quality = int(raster_profile.get("raster_quality") or 65)
    progressive = bool(raster_profile.get("raster_progressive", True))
    scale = max(0.5, float(dpi) / 72.0)

    src_doc = fitz.open(src)
    out_doc = fitz.open()
    page_count = 0
    try:
        if src_doc.is_encrypted:
            if not password or not src_doc.authenticate(password):
                return "ERROR:PDF 已加密，密码不正确或未提供密码。", 0
        for page in src_doc:
            rect = page.rect
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            try:
                image = PILImage.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
                buffer = io.BytesIO()
                image.save(
                    buffer,
                    format="JPEG",
                    quality=quality,
                    optimize=True,
                    progressive=progressive,
                    subsampling=1,
                )
                new_page = out_doc.new_page(width=rect.width, height=rect.height)
                new_page.insert_image(rect, stream=buffer.getvalue())
                page_count += 1
            finally:
                pixmap = None
        out_doc.save(dst, garbage=4, clean=True, deflate=True, use_objstms=True)
    except Exception as exc:
        return f"SKIP:rasterized failed {exc}", 0
    finally:
        out_doc.close()
        src_doc.close()
    if not os.path.exists(dst) or os.path.getsize(dst) <= 0:
        return "SKIP:rasterized empty output", 0
    return "SUCCESS", page_count


'''
text = text.replace(old, new)

old2 = '''        gs_candidate = temp_root / "ghostscript.pdf"
        gs_status = _run_ghostscript_candidate(src, str(gs_candidate), compress_level, image_level)
        if gs_status.startswith("SUCCESS") and gs_candidate.exists() and gs_candidate.stat().st_size > 0:
            size = gs_candidate.stat().st_size
            if size < best_size:
                best_path = gs_candidate
                best_size = size
                best_engine = "ghostscript"

        if best_path is None:
'''
new2 = '''        gs_candidate = temp_root / "ghostscript.pdf"
        gs_status = _run_ghostscript_candidate(src, str(gs_candidate), compress_level, image_level)
        if gs_status.startswith("SUCCESS") and gs_candidate.exists() and gs_candidate.stat().st_size > 0:
            size = gs_candidate.stat().st_size
            if size < best_size:
                best_path = gs_candidate
                best_size = size
                best_engine = "ghostscript"

        if image_profile.get("rasterize_pdf"):
            raster_candidate = temp_root / "rasterized_web.pdf"
            raster_status, raster_pages = _save_rasterized_web_candidate(
                src,
                str(raster_candidate),
                image_profile,
                password=password,
            )
            if raster_status.startswith("ERROR"):
                return raster_status
            if raster_status.startswith("SUCCESS") and raster_candidate.exists() and raster_candidate.stat().st_size > 0:
                size = raster_candidate.stat().st_size
                if size < best_size:
                    best_path = raster_candidate
                    best_size = size
                    best_engine = "rasterized"
                    image_changes = max(image_changes, raster_pages)

        if best_path is None:
'''
text = text.replace(old2, new2)

p.write_text(text, encoding='utf-8')
print('patched core')
