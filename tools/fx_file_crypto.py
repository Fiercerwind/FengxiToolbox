"""Password encryption and decryption helpers for file-manager workflows."""

from __future__ import annotations

import io
import json
import os
import shutil
import zipfile
from pathlib import Path, PurePosixPath

import pyzipper
from pypdf import PdfReader, PdfWriter


OOXML_EXTS = {".docx", ".docm", ".dotx", ".dotm", ".pptx", ".pptm", ".potx", ".potm", ".ppsx", ".ppsm", ".xlsx", ".xlsm", ".xltx", ".xltm"}
LEGACY_OFFICE_EXTS = {".doc", ".dot", ".ppt", ".pps", ".xls"}
ARCHIVE_EXTS = {".zip"}
MANIFEST_NAME = ".fengxi-encrypted-file.json"


def _require_password(password):
    value = str(password or "")
    if not value:
        raise ValueError("密码不能为空。")
    return value


def encrypted_output_path(src, output_folder):
    source = Path(src)
    root = Path(output_folder)
    if source.suffix.lower() in {".pdf"} | OOXML_EXTS | ARCHIVE_EXTS:
        return str(root / f"{source.stem}_加密{source.suffix}")
    return str(root / f"{source.name}_加密.zip")


def decrypted_output_path(src, output_folder):
    source = Path(src)
    stem = source.stem[:-3] if source.stem.endswith("_加密") else f"{source.stem}_解密"
    return str(Path(output_folder) / f"{stem}{source.suffix}")


def unique_output_path(path):
    candidate = Path(path)
    if not candidate.exists():
        return str(candidate)
    for index in range(2, 10000):
        numbered = candidate.with_name(f"{candidate.stem}_{index}{candidate.suffix}")
        if not numbered.exists():
            return str(numbered)
    raise FileExistsError(f"无法为输出文件生成唯一名称：{candidate}")


def _encrypt_pdf(src, dst, password):
    reader = PdfReader(str(src))
    if reader.is_encrypted:
        if not reader.decrypt(password):
            raise ValueError("PDF 已加密，当前密码无法读取。")
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    if reader.metadata:
        try:
            writer.add_metadata(dict(reader.metadata))
        except Exception:
            pass
    writer.encrypt(password)
    with open(dst, "wb") as output:
        writer.write(output)


def _decrypt_pdf(src, dst, password):
    reader = PdfReader(str(src))
    if not reader.is_encrypted:
        raise ValueError("PDF 未加密，无需解密。")
    if not reader.decrypt(password):
        raise ValueError("PDF 密码不正确。")
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    if reader.metadata:
        try:
            writer.add_metadata(dict(reader.metadata))
        except Exception:
            pass
    with open(dst, "wb") as output:
        writer.write(output)


def _encrypt_ooxml(src, dst, password):
    import msoffcrypto

    with open(src, "rb") as source, open(dst, "wb") as output:
        office = msoffcrypto.OfficeFile(source)
        office.encrypt(password, output)


def _decrypt_ooxml(src, dst, password):
    import msoffcrypto

    with open(src, "rb") as source, open(dst, "wb") as output:
        office = msoffcrypto.OfficeFile(source)
        if not office.is_encrypted():
            raise ValueError("Office 文件未加密，无需解密。")
        office.load_key(password=password, verify_password=True)
        office.decrypt(output)


def _safe_member_name(name):
    normalized = PurePosixPath(str(name or "").replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise ValueError(f"压缩包包含不安全路径：{name}")
    return str(normalized)


def _read_zip_members(src, password):
    members = []
    with pyzipper.AESZipFile(src, "r") as archive:
        archive.pwd = password.encode("utf-8")
        for info in archive.infolist():
            name = _safe_member_name(info.filename)
            data = b"" if info.is_dir() else archive.read(info.filename)
            members.append((name, data, info.is_dir()))
    return members


def _write_aes_zip(dst, members, password):
    with pyzipper.AESZipFile(
        dst,
        "w",
        compression=pyzipper.ZIP_DEFLATED,
        encryption=pyzipper.WZ_AES,
    ) as archive:
        archive.setpassword(password.encode("utf-8"))
        archive.setencryption(pyzipper.WZ_AES, nbits=256)
        for name, data, is_dir in members:
            archive.writestr(name if not is_dir or name.endswith("/") else f"{name}/", data)


def _encrypt_zip(src, dst, password):
    members = _read_zip_members(src, "")
    _write_aes_zip(dst, members, password)


def _encrypt_generic(src, dst, password):
    source = Path(src)
    manifest = json.dumps({"version": 1, "original_name": source.name}, ensure_ascii=False).encode("utf-8")
    members = [(MANIFEST_NAME, manifest, False), (source.name, source.read_bytes(), False)]
    _write_aes_zip(dst, members, password)


def _decrypt_zip(src, dst, output_folder, password):
    members = _read_zip_members(src, password)
    manifest_item = next((item for item in members if item[0] == MANIFEST_NAME), None)
    if manifest_item is not None:
        manifest = json.loads(manifest_item[1].decode("utf-8"))
        original_name = Path(str(manifest.get("original_name") or "restored_file")).name
        payload = next((item for item in members if item[0] == original_name and not item[2]), None)
        if payload is None:
            raise ValueError("加密包缺少原文件内容。")
        restored = Path(output_folder) / original_name
        restored.parent.mkdir(parents=True, exist_ok=True)
        restored.write_bytes(payload[1])
        return str(restored)

    with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data, is_dir in members:
            if is_dir:
                archive.writestr(name if name.endswith("/") else f"{name}/", b"")
            else:
                archive.writestr(name, data)
    return str(dst)


def encrypt_file(src, dst, password):
    password = _require_password(password)
    source = Path(src)
    target = Path(dst)
    target.parent.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix.lower()
    if suffix == ".pdf":
        _encrypt_pdf(source, target, password)
    elif suffix in OOXML_EXTS:
        _encrypt_ooxml(source, target, password)
    elif suffix == ".zip":
        _encrypt_zip(source, target, password)
    else:
        _encrypt_generic(source, target, password)
    return str(target)


def decrypt_file(src, dst, output_folder, password):
    password = _require_password(password)
    source = Path(src)
    target = Path(dst)
    target.parent.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix.lower()
    if suffix == ".pdf":
        _decrypt_pdf(source, target, password)
        return str(target)
    if suffix in OOXML_EXTS:
        _decrypt_ooxml(source, target, password)
        return str(target)
    if suffix == ".zip":
        return _decrypt_zip(source, target, output_folder, password)
    raise ValueError("此文件不是可直接解密的 PDF、Office 或 ZIP；通用加密文件应选择生成的 ZIP 加密包。")
