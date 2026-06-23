"""Core PDF compression helpers for Fengxi Toolbox."""

from __future__ import annotations

import io
import json
import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image as PILImage


PDF_COMPRESS_LEVELS = {
    "轻度": {"garbage": 2, "clean": False, "deflate": True, "use_objstms": False, "compression_effort": 1},
    "标准": {"garbage": 3, "clean": True, "deflate": True, "use_objstms": True, "compression_effort": 6},
    "强力": {"garbage": 4, "clean": True, "deflate": True, "use_objstms": True, "compression_effort": 9},
}

PDF_IMAGE_COMPRESS_LEVELS = {
    "保留原图": {"enabled": False, "quality": 95, "max_side": None, "min_width": None},
    "高清": {"enabled": True, "quality": 82, "max_side": None, "min_width": 1080, "progressive": True},
    "轻度": {"enabled": True, "quality": 85, "max_side": None, "min_width": 1080, "progressive": True},
    "标准": {"enabled": True, "quality": 76, "max_side": 3600, "min_width": 1080, "progressive": True},
    "强力": {"enabled": True, "quality": 66, "max_side": 2800, "min_width": 900, "progressive": True},
    "极限小体积": {"enabled": True, "quality": 55, "max_side": 1800, "min_width": 480, "progressive": True},
}

PDF_COMPRESS_META_VERSION = 1

_GS_PDF_SETTINGS = {
    "轻度": "/printer",
    "标准": "/ebook",
    "强力": "/screen",
    "杞诲害": "/printer",
    "鏍囧噯": "/ebook",
    "寮哄姏": "/screen",
}

_GS_IMAGE_DPI = {
    "保留原图": None,
    "高清": 300,
    "轻度": 300,
    "标准": 150,
    "强力": 120,
    "极限小体积": 72,
    "淇濈暀鍘熷浘": None,
    "楂樻竻": 300,
    "杞诲害": 300,
    "鏍囧噯": 150,
    "寮哄姏": 120,
}

_PDF_COMPRESS_CACHE_NAME = "pdf_compress_cache.json"

_GHOSTSCRIPT_ENV_OVERRIDES = ("FX_GHOSTSCRIPT_EXE", "GHOSTSCRIPT_EXE", "GS_EXECUTABLE")
_GHOSTSCRIPT_RESOURCE_RELS = (
    ("Resource", "Init"),
    ("lib",),
    ("kanji",),
    ("Resource", "Font"),
    ("Resource", "CMap"),
    ("Resource", "CIDFont"),
    ("Resource", "Decoding"),
    ("Resource", "ColorSpace"),
    ("Resource", "SubstCID"),
    ("Resource", "CIDFSubst"),
    ("Resource", "IdiomSet"),
)


def build_pdf_compress_output_path(src, output_folder):
    source = Path(src)
    target_dir = Path(output_folder)
    target = target_dir / f"{source.stem}_压缩{source.suffix}"
    counter = 2
    while target.exists():
        target = target_dir / f"{source.stem}_压缩_{counter}{source.suffix}"
        counter += 1
    return str(target)


def build_pdf_compress_meta_path(dst):
    target = Path(dst)
    override = os.environ.get("FX_PDF_COMPRESS_CACHE_DIR")
    if override:
        cache_dir = Path(override)
    else:
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home())
        cache_dir = root / "FengxiToolbox" / "cache"
    cache_key = hashlib.sha1(str(target.resolve() if target.exists() else target).encode("utf-8", errors="ignore")).hexdigest()
    return str(cache_dir / _PDF_COMPRESS_CACHE_NAME), cache_key


def _build_legacy_pdf_compress_meta_path(dst):
    target = Path(dst)
    return str(target.with_name(f".{target.name}.fx-compress.json"))


def build_pdf_compress_profile_stamp(src, compress_level="标准", image_level="标准", password=""):
    source = Path(src)
    try:
        stat = source.stat()
        source_size = int(stat.st_size)
        source_mtime_ns = int(stat.st_mtime_ns)
    except OSError:
        source_size = 0
        source_mtime_ns = 0
    return {
        "version": PDF_COMPRESS_META_VERSION,
        "source": str(source.resolve()) if source.exists() else str(source),
        "source_size": source_size,
        "source_mtime_ns": source_mtime_ns,
        "compress_level": str(compress_level or "标准"),
        "image_level": str(image_level or "标准"),
        "password_used": bool(password),
    }


def write_pdf_compress_meta(dst, stamp, result=None):
    cache_path_str, cache_key = build_pdf_compress_meta_path(dst)
    cache_path = Path(cache_path_str)
    payload = dict(stamp or {})
    if isinstance(result, dict):
        payload["result"] = result
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            cache_data = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
        except Exception:
            cache_data = {}
        if not isinstance(cache_data, dict):
            cache_data = {}
        cache_data[cache_key] = payload
        if len(cache_data) > 500:
            trimmed = dict(list(cache_data.items())[-400:])
            cache_data = trimmed
        cache_path.write_text(json.dumps(cache_data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def pdf_compress_meta_matches(dst, stamp):
    cache_path_str, cache_key = build_pdf_compress_meta_path(dst)
    data = None
    cache_path = Path(cache_path_str)
    if cache_path.exists():
        try:
            cache_data = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(cache_data, dict):
                data = cache_data.get(cache_key)
        except Exception:
            data = None
    if data is None:
        legacy_path = Path(_build_legacy_pdf_compress_meta_path(dst))
        if legacy_path.exists():
            try:
                data = json.loads(legacy_path.read_text(encoding="utf-8"))
            except Exception:
                data = None
    if not isinstance(data, dict):
        return False
    for key in ("version", "source", "source_size", "source_mtime_ns", "compress_level", "image_level", "password_used"):
        if data.get(key) != (stamp or {}).get(key):
            return False
    return True


def _protected_thumbnail_size(size, max_side=None, min_width=None):
    width, height = size
    if not max_side or max(width, height) <= max_side:
        return size

    ratio = float(max_side) / float(max(width, height))
    target_width = max(1, int(round(width * ratio)))
    target_height = max(1, int(round(height * ratio)))

    # Long screenshot PDFs become unreadable if width collapses to a few
    # hundred pixels. Keep at least min_width when the source allows it.
    if min_width and width >= min_width and target_width < min_width:
        width_ratio = float(min_width) / float(width)
        target_width = int(min_width)
        target_height = max(1, int(round(height * width_ratio)))
    return target_width, target_height


def _jpeg_bytes_from_pixmap(pixmap, quality, max_side, min_width=None, progressive=False):
    if pixmap.alpha:
        with PILImage.open(io.BytesIO(pixmap.tobytes("png"))) as image:
            image = image.convert("RGB")
    else:
        mode = "RGB" if pixmap.n < 4 else "CMYK"
        image = PILImage.frombytes(mode, (pixmap.width, pixmap.height), pixmap.samples)
        if image.mode != "RGB":
            image = image.convert("RGB")

    target_size = _protected_thumbnail_size(image.size, max_side=max_side, min_width=min_width)
    if target_size != image.size:
        image = image.resize(target_size, PILImage.Resampling.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=int(quality), optimize=True, progressive=bool(progressive))
    return buffer.getvalue()


def _compress_pdf_images(doc, image_profile):
    import fitz

    if not image_profile.get("enabled"):
        return 0

    seen_xrefs = set()
    changed = 0
    quality = image_profile.get("quality", 70)
    max_side = image_profile.get("max_side")
    min_width = image_profile.get("min_width")
    progressive = image_profile.get("progressive", False)
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
                jpeg_bytes = _jpeg_bytes_from_pixmap(
                    pixmap,
                    quality,
                    max_side,
                    min_width=min_width,
                    progressive=progressive,
                )
                if len(jpeg_bytes) >= len(original_bytes) * 0.98:
                    continue
                page.replace_image(xref, stream=jpeg_bytes)
                changed += 1
            except Exception:
                continue
    return changed


def _save_pymupdf_candidate(src, dst, pdf_profile, image_profile, password=""):
    import fitz

    doc = fitz.open(src)
    try:
        if doc.is_encrypted:
            if not password or not doc.authenticate(password):
                return "ERROR:PDF 已加密，密码不正确或未提供密码。", 0

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
    return "SUCCESS", image_changes


def _save_pymupdf_optimized_candidate(src, dst, image_profile, password=""):
    import fitz

    doc = fitz.open(src)
    try:
        if doc.is_encrypted:
            if not password or not doc.authenticate(password):
                return "ERROR:PDF 已加密，密码不正确或未提供密码。", 0
        image_changes = _compress_pdf_images(doc, image_profile)
        try:
            doc.set_metadata({})
        except Exception:
            pass
        try:
            doc.del_xml_metadata()
        except Exception:
            pass
        try:
            doc.subset_fonts()
        except Exception:
            pass
        doc.ez_save(dst)
    finally:
        doc.close()
    return "SUCCESS", image_changes


def _save_pikepdf_candidate(src, dst):
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


def _iter_ghostscript_candidates():
    for env_name in _GHOSTSCRIPT_ENV_OVERRIDES:
        value = os.environ.get(env_name)
        if value:
            yield Path(value)

    names = ("gswin64c.exe", "gswin32c.exe", "gs")
    for name in names:
        found = shutil.which(name)
        if found:
            yield Path(found)

    if os.name == "nt":
        roots = [
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
        ]
        for root in roots:
            if not root:
                continue
            gs_root = Path(root) / "gs"
            if not gs_root.exists():
                continue
            for exe in sorted(gs_root.glob("gs*\\bin\\gswin64c.exe"), reverse=True):
                yield exe
            for exe in sorted(gs_root.glob("gs*\\bin\\gswin32c.exe"), reverse=True):
                yield exe

        texlive_roots = []
        for env_name in ("TEXLIVE_INSTALL_PREFIX", "TEXLIVE_ROOT"):
            value = os.environ.get(env_name)
            if value:
                texlive_roots.append(Path(value))
        for drive in ("C", "D", "E"):
            texlive_roots.append(Path(f"{drive}:\\texlive"))
        seen_roots = set()
        for root in texlive_roots:
            root_key = str(root).lower()
            if root_key in seen_roots:
                continue
            seen_roots.add(root_key)
            if not root.exists():
                continue
            direct = root / "tlpkg" / "tlgs" / "bin" / "gswin64c.exe"
            if direct.exists():
                yield direct
            for exe in sorted(root.glob("*\\tlpkg\\tlgs\\bin\\gswin64c.exe"), reverse=True):
                yield exe
    return None


def _find_ghostscript_executable():
    seen = set()
    for candidate in _iter_ghostscript_candidates():
        try:
            resolved = candidate.resolve()
        except Exception:
            resolved = candidate
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        if resolved.is_file():
            return str(resolved)
    return None


def _ghostscript_resource_dirs(executable):
    exe = Path(executable)
    if exe.parent.name.lower() != "bin":
        return []
    gs_root = exe.parent.parent
    dirs = []
    for rel in _GHOSTSCRIPT_RESOURCE_RELS:
        path = gs_root.joinpath(*rel)
        if path.exists():
            dirs.append(path)
    return dirs


def _build_ghostscript_env(executable):
    env = os.environ.copy()
    resource_dirs = _ghostscript_resource_dirs(executable)
    if not resource_dirs:
        return env

    parts = []
    seen = set()
    for path in resource_dirs:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            parts.append(str(path))
    existing = env.get("GS_LIB")
    if existing:
        for item in existing.split(os.pathsep):
            if not item:
                continue
            key = item.lower()
            if key not in seen:
                seen.add(key)
                parts.append(item)
    env["GS_LIB"] = os.pathsep.join(parts)
    return env


def _run_ghostscript_candidate(src, dst, compress_level, image_level):
    gs = _find_ghostscript_executable()
    if not gs:
        return "SKIP:ghostscript unavailable"
    env = _build_ghostscript_env(gs)

    pdf_setting = _GS_PDF_SETTINGS.get(str(compress_level), "/ebook")
    dpi = _GS_IMAGE_DPI.get(str(image_level))
    args = [
        gs,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.6",
        f"-dPDFSETTINGS={pdf_setting}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        "-dSubsetFonts=true",
        "-dAutoRotatePages=/None",
    ]
    if dpi:
        args.extend(
            [
                "-dDownsampleColorImages=true",
                "-dDownsampleGrayImages=true",
                "-dDownsampleMonoImages=true",
                "-dColorImageDownsampleType=/Bicubic",
                "-dGrayImageDownsampleType=/Bicubic",
                "-dMonoImageDownsampleType=/Subsample",
                f"-dColorImageResolution={int(dpi)}",
                f"-dGrayImageResolution={int(dpi)}",
                f"-dMonoImageResolution={int(max(150, dpi))}",
            ]
        )
    args.extend([f"-sOutputFile={dst}", str(src)])
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=env,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception as exc:
        return f"SKIP:ghostscript error {exc}"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or b"").decode(errors="ignore").strip()
        return "SKIP:ghostscript failed" + (f" {detail[:160]}" if detail else "")
    if not os.path.exists(dst) or os.path.getsize(dst) <= 0:
        return "SKIP:ghostscript empty output"
    return "SUCCESS"


def compress_pdf_file(src, dst, compress_level="标准", image_level="标准", password=""):
    pdf_profile = PDF_COMPRESS_LEVELS.get(compress_level, PDF_COMPRESS_LEVELS["标准"])
    image_profile = PDF_IMAGE_COMPRESS_LEVELS.get(image_level, PDF_IMAGE_COMPRESS_LEVELS["标准"])
    source_size = os.path.getsize(src)
    best_path = None
    best_size = source_size
    best_engine = "original"
    image_changes = 0
    Path(dst).parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="fx_pdf_compress_") as temp_dir:
        temp_root = Path(temp_dir)

        optimized_candidate = temp_root / "pymupdf_optimized.pdf"
        status, optimized_changes = _save_pymupdf_optimized_candidate(src, str(optimized_candidate), image_profile, password=password)
        if not status.startswith("SUCCESS"):
            return status
        image_changes = max(image_changes, optimized_changes)
        if optimized_candidate.exists() and optimized_candidate.stat().st_size > 0:
            size = optimized_candidate.stat().st_size
            if size < best_size:
                best_path = optimized_candidate
                best_size = size
                best_engine = "optimized"

        pikepdf_candidate = temp_root / "pikepdf.pdf"
        pikepdf_status = _save_pikepdf_candidate(src, str(pikepdf_candidate))
        if pikepdf_status.startswith("SUCCESS") and pikepdf_candidate.exists() and pikepdf_candidate.stat().st_size > 0:
            size = pikepdf_candidate.stat().st_size
            if size < best_size:
                best_path = pikepdf_candidate
                best_size = size
                best_engine = "pikepdf"

        pymupdf_candidate = temp_root / "pymupdf.pdf"
        status, pymupdf_changes = _save_pymupdf_candidate(src, str(pymupdf_candidate), pdf_profile, image_profile, password=password)
        if not status.startswith("SUCCESS"):
            return status
        image_changes = max(image_changes, pymupdf_changes)
        if pymupdf_candidate.exists() and pymupdf_candidate.stat().st_size > 0:
            size = pymupdf_candidate.stat().st_size
            if size < best_size:
                best_path = pymupdf_candidate
                best_size = size
                best_engine = "pymupdf"

        gs_candidate = temp_root / "ghostscript.pdf"
        gs_status = _run_ghostscript_candidate(src, str(gs_candidate), compress_level, image_level)
        if gs_status.startswith("SUCCESS") and gs_candidate.exists() and gs_candidate.stat().st_size > 0:
            size = gs_candidate.stat().st_size
            if size < best_size:
                best_path = gs_candidate
                best_size = size
                best_engine = "ghostscript"

        if best_path is None:
            shutil.copy2(src, dst)
            best_engine = "original"
            best_size = source_size
        else:
            shutil.copy2(best_path, dst)

    if not os.path.exists(dst) or os.path.getsize(dst) <= 0:
        return "ERROR:压缩输出文件未生成。"
    if best_engine == "original":
        return f"SUCCESS:{image_changes}:kept_original"
    return f"SUCCESS:{image_changes}:{best_engine}"
