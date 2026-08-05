"""PDF page rotation normalization shared by standalone and OCR workflows."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def normalize_pdf_page_rotation(pdf_path, password=""):
    """Bake page /Rotate values into content while preserving the visible page."""
    import fitz

    target = Path(pdf_path).resolve()
    if not target.is_file():
        raise FileNotFoundError(target)

    document = fitz.open(target)
    temporary = None
    rotations_before = {}
    changed_pages = 0
    try:
        if document.is_encrypted and not document.authenticate(password or ""):
            raise ValueError("PDF 已加密，密码不正确或未提供密码。")
        total_pages = document.page_count
        for page in document:
            rotation = int(page.rotation or 0) % 360
            rotations_before[rotation] = rotations_before.get(rotation, 0) + 1
            if rotation:
                page.remove_rotation()
                changed_pages += 1

        if changed_pages == 0:
            document.close()
            return {
                "normalized": False,
                "pages": total_pages,
                "changed_pages": 0,
                "rotations_before": rotations_before,
            }

        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{target.stem}.rotation-",
            suffix=".tmp.pdf",
            dir=target.parent,
        )
        os.close(fd)
        temporary = Path(temporary_name)
        document.save(temporary, garbage=4, deflate=True, use_objstms=1)
    except Exception:
        document.close()
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except Exception:
                pass
        raise
    else:
        document.close()

    try:
        with fitz.open(temporary) as verification:
            if verification.page_count != total_pages:
                raise RuntimeError("页面角度修正后页数发生变化。")
            remaining = [page.number + 1 for page in verification if page.rotation]
            if remaining:
                raise RuntimeError(f"页面角度修正验证失败，仍有旋转页: {remaining[:10]}")
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except Exception:
                pass

    return {
        "normalized": True,
        "pages": total_pages,
        "changed_pages": changed_pages,
        "rotations_before": rotations_before,
    }
