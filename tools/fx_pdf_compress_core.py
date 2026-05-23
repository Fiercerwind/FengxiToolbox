"""Core PDF compression helpers for Fengxi Toolbox."""

from __future__ import annotations

import io
import os
from pathlib import Path

from PIL import Image as PILImage


PDF_COMPRESS_LEVELS = {
    "轻度": {"garbage": 2, "clean": False, "deflate": True, "use_objstms": False, "compression_effort": 1},
    "标准": {"garbage": 3, "clean": True, "deflate": True, "use_objstms": True, "compression_effort": 6},
    "强力": {"garbage": 4, "clean": True, "deflate": True, "use_objstms": True, "compression_effort": 9},
}

PDF_IMAGE_COMPRESS_LEVELS = {
    "保留原图": {"enabled": False, "quality": 95, "max_side": None},
    "轻度": {"enabled": True, "quality": 85, "max_side": 2400},
    "标准": {"enabled": True, "quality": 70, "max_side": 1800},
    "强力": {"enabled": True, "quality": 55, "max_side": 1200},
}


def build_pdf_compress_output_path(src, output_folder):
    source = Path(src)
    target_dir = Path(output_folder)
    target = target_dir / f"{source.stem}_压缩{source.suffix}"
    counter = 2
    while target.exists():
        target = target_dir / f"{source.stem}_压缩_{counter}{source.suffix}"
        counter += 1
    return str(target)


def _jpeg_bytes_from_pixmap(pixmap, quality, max_side):
    if pixmap.alpha:
        with PILImage.open(io.BytesIO(pixmap.tobytes("png"))) as image:
            image = image.convert("RGB")
    else:
        mode = "RGB" if pixmap.n < 4 else "CMYK"
        image = PILImage.frombytes(mode, (pixmap.width, pixmap.height), pixmap.samples)
        if image.mode != "RGB":
            image = image.convert("RGB")

    if max_side and max(image.size) > max_side:
        image.thumbnail((max_side, max_side), PILImage.Resampling.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=int(quality), optimize=True)
    return buffer.getvalue()


def _compress_pdf_images(doc, image_profile):
    import fitz

    if not image_profile.get("enabled"):
        return 0

    seen_xrefs = set()
    changed = 0
    quality = image_profile.get("quality", 70)
    max_side = image_profile.get("max_side")
    for page in doc:
        for image_info in page.get_images(full=True):
            xref = image_info[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            try:
                original = doc.extract_image(xref)
                original_bytes = original.get("image", b"")
                if not original_bytes:
                    continue
                pixmap = fitz.Pixmap(doc, xref)
                if pixmap.width < 96 or pixmap.height < 96:
                    continue
                jpeg_bytes = _jpeg_bytes_from_pixmap(pixmap, quality, max_side)
                if len(jpeg_bytes) >= len(original_bytes) * 0.98:
                    continue
                page.replace_image(xref, stream=jpeg_bytes)
                changed += 1
            except Exception:
                continue
    return changed


def compress_pdf_file(src, dst, compress_level="标准", image_level="标准", password=""):
    import fitz

    pdf_profile = PDF_COMPRESS_LEVELS.get(compress_level, PDF_COMPRESS_LEVELS["标准"])
    image_profile = PDF_IMAGE_COMPRESS_LEVELS.get(image_level, PDF_IMAGE_COMPRESS_LEVELS["标准"])
    doc = fitz.open(src)
    try:
        if doc.is_encrypted:
            if not password or not doc.authenticate(password):
                return "ERROR:PDF 已加密，密码不正确或未提供密码。"

        image_changes = _compress_pdf_images(doc, image_profile)
        save_kwargs = {
            "garbage": pdf_profile["garbage"],
            "clean": pdf_profile["clean"],
            "deflate": pdf_profile["deflate"],
            "deflate_images": True,
            "deflate_fonts": True,
            "use_objstms": pdf_profile["use_objstms"],
            "compression_effort": pdf_profile["compression_effort"],
        }
        doc.save(dst, **save_kwargs)
    finally:
        doc.close()

    if not os.path.exists(dst) or os.path.getsize(dst) <= 0:
        return "ERROR:压缩输出文件未生成。"
    return f"SUCCESS:{image_changes}"

