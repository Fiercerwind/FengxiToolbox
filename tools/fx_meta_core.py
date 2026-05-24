"""Metadata and file timestamp helpers for Fengxi Toolbox."""

from __future__ import annotations

import os
import shutil
import time
from typing import Callable

from pypdf import PdfReader, PdfWriter


def modify_file_timestamp(src, dst, timestamp, *, copy_file: Callable[[str, str], object] | None = None):
    """Copy a file and set both access/modified time using the runtime timestamp format."""

    try:
        copier = copy_file or shutil.copy2
        copier(src, dst)
        time_struct = time.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        mod_time = time.mktime(time_struct)
        os.utime(dst, (mod_time, mod_time))
        return "SUCCESS"
    except Exception:
        return "ERROR"


def modify_pdf_author(src, dst, author_name, *, reader_cls=PdfReader, writer_cls=PdfWriter, creator="Fengxi Toolbox"):
    """Rewrite PDF metadata while preserving pages."""

    reader = reader_cls(src)
    writer = writer_cls()
    writer.append_pages_from_reader(reader)
    source_meta = getattr(reader, "metadata", None)
    new_meta = {str(key): str(value) for key, value in source_meta.items()} if source_meta else {}
    new_meta["/Author"] = str(author_name or "")
    new_meta["/Creator"] = str(creator or "")
    writer.add_metadata(new_meta)
    with open(dst, "wb") as out:
        writer.write(out)
    return "SUCCESS"


def modify_office_meta(app, src, dst, author_name, app_type="word"):
    """Set Office Author and Last Author properties using an existing COM app instance."""

    doc = None
    pres = None
    try:
        if app_type == "word":
            doc = app.Documents.Open(os.path.abspath(src))
            doc.BuiltInDocumentProperties("Author").Value = author_name
            doc.BuiltInDocumentProperties("Last Author").Value = author_name
            doc.SaveAs(os.path.abspath(dst))
            doc.Close()
        elif app_type == "ppt":
            pres = app.Presentations.Open(os.path.abspath(src), WithWindow=False)
            pres.BuiltInDocumentProperties("Author").Value = author_name
            pres.BuiltInDocumentProperties("Last Author").Value = author_name
            pres.SaveAs(os.path.abspath(dst))
            pres.Close()
        return "SUCCESS"
    except Exception:
        try:
            if doc:
                doc.Close(False)
            if pres:
                pres.Close()
        except Exception:
            pass
        return "ERROR"


def build_meta_output_path(src, input_folder, output_folder):
    fname = os.path.basename(src)
    try:
        rel = os.path.relpath(src, input_folder)
    except Exception:
        rel = fname
    if rel.startswith(".."):
        rel = fname
    dst = os.path.join(output_folder, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    return fname, dst


def process_meta_file(
    src,
    input_folder,
    output_folder,
    args,
    failed_list,
    *,
    copy_file_safe: Callable[[str, str], object] | None = None,
    log: Callable[[str], None] | None = None,
):
    """Process one metadata/privacy file using the legacy runtime-compatible semantics."""

    copy_file_safe = copy_file_safe or shutil.copy2
    fname, dst = build_meta_output_path(src, input_folder, output_folder)
    values = list(args or [])
    meta_mode = values[0] if values else ""
    meta_value = values[1] if len(values) > 1 else ""

    def log_message(message):
        if callable(log):
            try:
                log(str(message))
            except Exception:
                pass

    try:
        if meta_mode == "time":
            status = modify_file_timestamp(src, dst, meta_value)
            if status == "SUCCESS":
                log_message(f"⏱️ [时间] 已修改: {fname}")
            else:
                copy_file_safe(src, dst)
                failed_list.append(fname)
                log_message(f"❌ [失败] 时间修改错误: {fname}")
            return None

        new_author = meta_value
        lower_src = str(src).lower()
        if lower_src.endswith(".pdf"):
            try:
                modify_pdf_author(src, dst, new_author)
                log_message(f"🕵️ [隐私] PDF作者已改: {fname}")
                return None
            except Exception as exc:
                copy_file_safe(src, dst)
                log_message(f"⚠️ PDF元数据失败: {exc}")
                return None
        if not lower_src.endswith((".doc", ".docx", ".ppt", ".pptx")):
            copy_file_safe(src, dst)
            return None
        return None
    except Exception as exc:
        try:
            copy_file_safe(src, dst)
        except Exception:
            pass
        failed_list.append(os.path.basename(src))
        log_message(f"❌ [出错] {os.path.basename(src)}: {exc}")
        return None
