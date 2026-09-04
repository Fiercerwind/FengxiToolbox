"""PDF page-range deletion helpers."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def normalize_page_delete_range(start, end):
    """Return a validated, inclusive 1-based page range."""

    try:
        start_page = int(str(start).strip())
        end_page = int(str(end).strip())
    except (TypeError, ValueError):
        raise ValueError("请输入有效的页码。")
    if start_page < 1 or end_page < 1:
        raise ValueError("页码从 1 开始。")
    if end_page < start_page:
        raise ValueError("结束页不能小于起始页。")
    return start_page, end_page


def build_page_delete_output_path(source, output_root, start_page, end_page, input_root=None):
    source_path = Path(source)
    root = Path(input_root) if input_root else source_path.parent
    try:
        relative = source_path.relative_to(root)
    except ValueError:
        relative = Path(source_path.name)
    suffix = f"_删除第{start_page}页" if start_page == end_page else f"_删除第{start_page}至{end_page}页"
    return Path(output_root) / relative.parent / f"{source_path.stem}{suffix}{source_path.suffix}"


def delete_pdf_page_range(source, destination, start_page, end_page, password=""):
    """Copy a PDF while omitting an inclusive range of 1-based page numbers."""

    start_page, end_page = normalize_page_delete_range(start_page, end_page)
    source_path = Path(source)
    destination_path = Path(destination)
    reader = PdfReader(str(source_path))
    if reader.is_encrypted and reader.decrypt(str(password or "")) == 0:
        raise ValueError("PDF 已加密，请输入正确的文件密码。")

    page_count = len(reader.pages)
    if end_page > page_count:
        raise ValueError(f"结束页超出文件页数（共 {page_count} 页）。")
    if start_page == 1 and end_page == page_count:
        raise ValueError("不能删除 PDF 的全部页面。")

    writer = PdfWriter()
    for index, page in enumerate(reader.pages, start=1):
        if start_page <= index <= end_page:
            continue
        writer.add_page(page)
    try:
        if reader.metadata:
            writer.add_metadata({str(key): str(value) for key, value in reader.metadata.items() if value is not None})
    except Exception:
        pass

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination_path.stem}_", suffix=".pdf", dir=str(destination_path.parent))
    os.close(fd)
    try:
        with open(temporary_name, "wb") as output_file:
            writer.write(output_file)
        os.replace(temporary_name, destination_path)
    except Exception:
        try:
            os.remove(temporary_name)
        except OSError:
            pass
        raise

    return {
        "source": str(source_path),
        "output": str(destination_path),
        "page_count": page_count,
        "deleted_start": start_page,
        "deleted_end": end_page,
        "remaining_pages": page_count - (end_page - start_page + 1),
    }
