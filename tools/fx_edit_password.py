"""Editing restrictions for watermark outputs; viewing needs no password."""

import os
import tempfile
from pathlib import Path


def pdf_edit_encryption(password):
    import pikepdf
    if not password:
        raise ValueError("编辑密码不能为空")
    if len(password.encode("utf-8")) > 127:
        raise ValueError("PDF 编辑密码不能超过 127 个 UTF-8 字节")
    return pikepdf.Encryption(
        owner=password, user="", R=6,
        allow=pikepdf.Permissions(
            accessibility=True, extract=True, print_lowres=True, print_highres=True,
            modify_annotation=False, modify_assembly=False, modify_form=False, modify_other=False,
        ),
    )


def protect_pdf_editing(path, password):
    import pikepdf
    encryption = pdf_edit_encryption(password)
    target = Path(path)
    fd, temp_name = tempfile.mkstemp(prefix="fx_edit_password_", suffix=".pdf", dir=str(target.parent))
    os.close(fd)
    temporary = Path(temp_name)
    try:
        with pikepdf.open(target) as pdf:
            pdf.save(
                temporary,
                encryption=encryption,
            )
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def protect_word_editing(path, password, word_app, open_document):
    if not password:
        raise ValueError("编辑密码不能为空")
    doc = open_document(word_app, Path(path).resolve())
    try:
        # wdAllowOnlyReading: opening/reading stays password-free. Word's
        # Stop Protection action requests this password before editing.
        doc.Protect(Type=3, NoReset=True, Password=password)
        doc.Save()
    finally:
        doc.Close(False)
