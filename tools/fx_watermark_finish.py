"""Finish watermark content before encryption, and publish verified outputs."""

import io
import os
import tempfile
from pathlib import Path

from tools.fx_edit_password import pdf_edit_encryption


INSERT_MARKER = "Fengxi Toolbox"


def finish_pikepdf(pdf, *, insert_page_pdf_bytes=None, insert_page_position="end", edit_password=None):
    import pikepdf

    if insert_page_pdf_bytes and str(pdf.docinfo.get("/FXInsertedWatermarkPage", "")) != INSERT_MARKER:
        with pikepdf.open(io.BytesIO(insert_page_pdf_bytes)) as template:
            if not len(template.pages):
                raise ValueError("水印页模板没有可用页面")
            if insert_page_position == "start":
                pdf.pages.insert(0, template.pages[0])
            else:
                pdf.pages.append(template.pages[0])
        pdf.docinfo["/FXInsertedWatermarkPage"] = INSERT_MARKER
        pdf.docinfo["/FXInsertedWatermarkPagePosition"] = insert_page_position
    return {"encryption": pdf_edit_encryption(edit_password)} if edit_password is not None else {}


def finish_pypdf(writer, *, insert_page_pdf_bytes=None, insert_page_position="end", edit_password=None):
    from pypdf import PdfReader
    from pypdf.constants import UserAccessPermissions as Permission

    if insert_page_pdf_bytes and str((writer.metadata or {}).get("/FXInsertedWatermarkPage", "")) != INSERT_MARKER:
        template = PdfReader(io.BytesIO(insert_page_pdf_bytes))
        if not template.pages:
            raise ValueError("水印页模板没有可用页面")
        if insert_page_position == "start":
            writer.insert_page(template.pages[0], 0)
        else:
            writer.add_page(template.pages[0])
        writer.add_metadata({"/FXInsertedWatermarkPage": INSERT_MARKER,
                             "/FXInsertedWatermarkPagePosition": insert_page_position})
    if edit_password is not None:
        pdf_edit_encryption(edit_password)  # Validate the shared password limits.
        denied = Permission.MODIFY | Permission.ADD_OR_MODIFY | Permission.FILL_FORM_FIELDS | Permission.ASSEMBLE_DOC
        writer.encrypt("", owner_password=edit_password, algorithm="AES-256",
                       permissions_flag=Permission(0xFFFFFFFC & ~int(denied)))


def verify_pdf_output(path, edit_password=None):
    import pikepdf

    with pikepdf.open(path) as pdf:
        if not len(pdf.pages):
            raise ValueError("输出 PDF 没有页面")
        if edit_password is not None:
            if not pdf.is_encrypted or any((pdf.allow.modify_other, pdf.allow.modify_annotation,
                                           pdf.allow.modify_assembly, pdf.allow.modify_form)):
                raise ValueError("PDF 编辑密码保护验证失败")
    if edit_password is not None:
        with pikepdf.open(path, password=edit_password) as pdf:
            if not pdf.owner_password_matched:
                raise ValueError("PDF 编辑密码验证失败")


def verify_word_output(path, edit_password=None):
    import zipfile
    from xml.etree import ElementTree

    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("Word 输出文件为空")
    if path.suffix.lower() in {".docx", ".docm"}:
        with zipfile.ZipFile(path) as package:
            # Reading the XML also checks CRC and detects a truncated package.
            ElementTree.fromstring(package.read("word/document.xml"))
            if edit_password is not None:
                settings = ElementTree.fromstring(package.read("word/settings.xml"))
                ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
                protection = settings.find(ns + "documentProtection")
                if (protection is None or protection.get(ns + "edit") != "readOnly"
                        or protection.get(ns + "enforcement") not in {"1", "true", "on"}):
                    raise ValueError("Word 只读保护验证失败")
    else:
        import olefile
        with olefile.OleFileIO(str(path)) as package:
            if not package.exists("WordDocument"):
                raise ValueError("Word 输出结构无效")


def publish_watermark_output(destination, process, verify):
    """Only a successfully processed and verified staging file replaces output."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="fx_wm_pending_", suffix=destination.suffix, dir=str(destination.parent))
    os.close(fd)
    staging = Path(name)
    try:
        status = process(staging)
        if str(status).strip().upper().startswith("SUCCESS"):
            verify(staging)
            os.replace(staging, destination)
        return status
    except Exception:
        return "ERROR:输出处理或验证失败，未提交结果"
    finally:
        staging.unlink(missing_ok=True)
