"""Core watermark helpers for Fengxi Toolbox.

This module owns the PDF/Word watermark implementation.  The GUI loader keeps
thin wrappers for runtime compatibility and supplies font/COM adapters.
"""

from __future__ import annotations

import io
import os
import tempfile
from contextlib import nullcontext
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


WATERMARK_MARKER = "XMU_DONE"
WATERMARK_CREATOR = "Fengxi Toolbox"
PDF_WATERMARK_DEFAULT_RGB = (115, 115, 115)
WORD_WATERMARK_GRAY_RGB = 0xC0C0C0
WORD_WATERMARK_DEFAULT_RGB = (192, 192, 192)
WORD_WATERMARK_MIN_VISIBLE_OPACITY = 0.18
WORD_WATERMARK_MAX_VISIBLE_OPACITY = 0.85


def _safe_float(value, default):
    try:
        return float(value)
    except Exception:
        return default


def _looks_like_unreadable_word_error(exc):
    text = str(exc or "").lower()
    markers = [
        "word 无法读取",
        "文档可能已损坏",
        "文件似乎已经损坏",
        "cannot read",
        "may be corrupted",
        "appears to be corrupted",
        "损坏",
        "corrupt",
        "-2146823137",
        "-2146822496",
    ]
    if any(marker in text for marker in markers):
        return True
    return "microsoft word" in text and "wdmain11.chm" in text


def _word_visible_opacity(value):
    opacity = max(0.0, min(1.0, _safe_float(value, 0.2)))
    return max(WORD_WATERMARK_MIN_VISIBLE_OPACITY, min(WORD_WATERMARK_MAX_VISIBLE_OPACITY, opacity))


def _coerce_color_channel(value):
    number = _safe_float(value, 0.0)
    if 0.0 <= number <= 1.0 and not isinstance(value, int):
        number *= 255.0
    return max(0, min(255, int(round(number))))


def normalize_watermark_color(value, default=PDF_WATERMARK_DEFAULT_RGB):
    """Return an RGB tuple from #RRGGBB, RRGGBB, or a 3-item sequence."""

    if isinstance(value, str):
        text = value.strip()
        if text.startswith("#"):
            text = text[1:]
        if len(text) == 6:
            try:
                return tuple(int(text[index : index + 2], 16) for index in (0, 2, 4))
            except Exception:
                pass
    elif isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            return tuple(_coerce_color_channel(value[index]) for index in range(3))
        except Exception:
            pass

    if isinstance(default, (list, tuple)) and len(default) >= 3:
        return tuple(_coerce_color_channel(default[index]) for index in range(3))
    return PDF_WATERMARK_DEFAULT_RGB


def watermark_color_to_hex(value, default=PDF_WATERMARK_DEFAULT_RGB):
    red, green, blue = normalize_watermark_color(value, default=default)
    return f"#{red:02X}{green:02X}{blue:02X}"


def _word_rgb_value(value):
    red, green, blue = normalize_watermark_color(value, default=WORD_WATERMARK_DEFAULT_RGB)
    return int(red) + (int(green) << 8) + (int(blue) << 16)


def _resolve_reportlab_font(font_name, font_path_resolver=None):
    raw_name = str(font_name or "").strip() or "Helvetica"
    font_path = ""
    if callable(font_path_resolver):
        try:
            font_path = str(font_path_resolver(raw_name) or "")
        except Exception:
            font_path = ""

    if font_path and os.path.exists(font_path):
        alias = "FengxiWatermark_" + "".join(ch if ch.isalnum() else "_" for ch in Path(font_path).stem)
        try:
            pdfmetrics.registerFont(TTFont(alias, font_path))
            return alias
        except Exception:
            try:
                if alias in pdfmetrics.getRegisteredFontNames():
                    return alias
            except Exception:
                pass

    try:
        if raw_name in pdfmetrics.getRegisteredFontNames():
            return raw_name
    except Exception:
        pass
    return "Helvetica"


def create_watermark_packet(
    content,
    font_name,
    font_size,
    opacity,
    angle,
    *,
    font_path_resolver=None,
    color=None,
):
    """Build a one-page PDF watermark packet."""

    packet = io.BytesIO()
    page_width, page_height = A4
    pdf = canvas.Canvas(packet, pagesize=A4)
    resolved_font = _resolve_reportlab_font(font_name, font_path_resolver=font_path_resolver)
    size = max(1.0, _safe_float(font_size, 36.0))
    alpha = max(0.0, min(1.0, _safe_float(opacity, 0.2)))
    rotation = _safe_float(angle, 45.0)
    text = str(content or "")
    lines = text.splitlines() or [""]

    pdf.saveState()
    try:
        pdf.setFillAlpha(alpha)
    except Exception:
        pass
    pdf.setFont(resolved_font, size)
    red, green, blue = normalize_watermark_color(color, default=PDF_WATERMARK_DEFAULT_RGB)
    pdf.setFillColorRGB(red / 255.0, green / 255.0, blue / 255.0)
    pdf.translate(page_width / 2.0, page_height / 2.0)
    pdf.rotate(rotation)
    line_height = size * 1.22
    start_y = ((len(lines) - 1) * line_height) / 2.0
    for index, line in enumerate(lines):
        pdf.drawCentredString(0, start_y - index * line_height, line)
    pdf.restoreState()
    pdf.save()
    packet.seek(0)
    return packet


def _same_path(left, right):
    try:
        return os.path.abspath(str(left)) == os.path.abspath(str(right))
    except Exception:
        return False


def _metadata_has_marker(metadata):
    if not metadata:
        return False
    try:
        keywords = str(metadata.get("/Keywords", "") or "")
        creator = str(metadata.get("/Creator", "") or "")
    except Exception:
        return False
    return WATERMARK_MARKER in keywords or creator == WATERMARK_CREATOR


def _first_page_contains(reader, text):
    needle = str(text or "")
    if not needle:
        return False
    try:
        if not reader.pages:
            return False
        first_text = reader.pages[0].extract_text() or ""
        return needle in first_text
    except Exception:
        return False


def _writer_metadata(reader):
    metadata = {}
    try:
        for key, value in (reader.metadata or {}).items():
            if key and value is not None:
                metadata[str(key)] = str(value)
    except Exception:
        metadata = {}
    metadata["/Keywords"] = WATERMARK_MARKER
    metadata["/Creator"] = WATERMARK_CREATOR
    return metadata


def _repair_pdf_for_watermark(src_path):
    """Return a PyMuPDF-cleaned temporary PDF path, or a status string."""

    try:
        import fitz
    except Exception as exc:
        return None, f"ERROR:PDF repair backend unavailable: {exc}"

    doc = None
    temp_path = None
    try:
        doc = fitz.open(str(src_path))
        if getattr(doc, "needs_pass", False):
            try:
                if not doc.authenticate(""):
                    return None, "SKIP:protected pdf requires password"
            except Exception:
                return None, "SKIP:protected pdf requires password"
        handle = tempfile.NamedTemporaryFile(
            prefix=f"{src_path.stem}_repair_",
            suffix=src_path.suffix or ".pdf",
            dir=str(src_path.parent),
            delete=False,
        )
        temp_path = Path(handle.name)
        handle.close()
        doc.save(str(temp_path), garbage=4, deflate=True, clean=True)
        return temp_path, ""
    except Exception as exc:
        try:
            if temp_path and temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass
        if "encrypted" in str(exc).lower():
            return None, "SKIP:protected pdf requires password"
        return None, f"ERROR:PDF repair failed: {exc}"
    finally:
        try:
            if doc is not None:
                doc.close()
        except Exception:
            pass


def _open_pdf_reader_for_watermark(src_path):
    repair_path = None
    try:
        reader = PdfReader(str(src_path))
        if getattr(reader, "is_encrypted", False):
            try:
                if not reader.decrypt(""):
                    return None, None, "SKIP:protected pdf requires password"
            except Exception:
                return None, None, "SKIP:protected pdf requires password"
        # Force page parsing now so damaged PDFs can fall back to repair.
        len(reader.pages)
        return reader, None, ""
    except Exception as first_exc:
        if "not been decrypted" in str(first_exc).lower():
            return None, None, "SKIP:protected pdf requires password"
        repair_path, repair_status = _repair_pdf_for_watermark(src_path)
        if not repair_path:
            return None, None, repair_status or f"ERROR:{first_exc}"
        try:
            reader = PdfReader(str(repair_path))
            if getattr(reader, "is_encrypted", False):
                try:
                    if not reader.decrypt(""):
                        return None, repair_path, "SKIP:protected pdf requires password"
                except Exception:
                    return None, repair_path, "SKIP:protected pdf requires password"
            len(reader.pages)
            return reader, repair_path, ""
        except Exception as repair_exc:
            return None, repair_path, f"ERROR:{first_exc}; repair read failed: {repair_exc}"


def add_watermark_to_pdf(src, dst, watermark_packet, page_range="all", check_text=None, force_mode=False):
    """Apply the watermark packet to a PDF and return a runtime-compatible status."""

    repair_path = None
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        if not src_path.exists():
            return f"ERROR:source not found: {src_path}"

        reader, repair_path, open_status = _open_pdf_reader_for_watermark(src_path)
        if open_status:
            return open_status
        if reader is None:
            return "ERROR:PDF reader unavailable"
        if not force_mode and _metadata_has_marker(reader.metadata):
            return "SKIP:already watermarked"
        if not force_mode and check_text and _first_page_contains(reader, check_text):
            return "SKIP:watermark text found"

        if hasattr(watermark_packet, "seek"):
            watermark_packet.seek(0)
        watermark_reader = PdfReader(watermark_packet)
        watermark_page = watermark_reader.pages[0]

        writer = PdfWriter()
        only_first = str(page_range or "all").lower() in {"first", "first_page", "1"}
        for index, page in enumerate(reader.pages):
            if not only_first or index == 0:
                try:
                    page.merge_page(watermark_page)
                except AttributeError:
                    page.mergePage(watermark_page)
            writer.add_page(page)
        writer.add_metadata(_writer_metadata(reader))

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        output_path = dst_path
        temp_path = None
        if _same_path(src_path, dst_path):
            handle = tempfile.NamedTemporaryFile(
                prefix=f"{src_path.stem}_watermark_",
                suffix=src_path.suffix or ".pdf",
                dir=str(src_path.parent),
                delete=False,
            )
            temp_path = Path(handle.name)
            handle.close()
            output_path = temp_path

        with open(output_path, "wb") as file_obj:
            writer.write(file_obj)

        if temp_path is not None:
            os.replace(str(temp_path), str(dst_path))
        return "SUCCESS"
    except Exception as exc:
        return f"ERROR:{exc}"
    finally:
        try:
            if repair_path is not None and Path(repair_path).exists():
                Path(repair_path).unlink()
        except Exception:
            pass


def _call_collection_item(collection, index):
    try:
        return collection.Item(index)
    except Exception:
        return collection(index)


def _iter_word_headers(doc):
    try:
        sections = doc.Sections
        section_count = int(sections.Count)
    except Exception:
        return

    for section_index in range(1, section_count + 1):
        try:
            section = _call_collection_item(sections, section_index)
            headers = section.Headers
        except Exception:
            continue
        for header_index in (1, 2, 3):
            try:
                header = _call_collection_item(headers, header_index)
                if hasattr(header, "Exists") and not bool(header.Exists):
                    continue
                yield header, section
            except Exception:
                continue


def _word_has_marker(doc):
    for header, _section in _iter_word_headers(doc):
        try:
            shapes = header.Shapes
            for index in range(1, int(shapes.Count) + 1):
                shape = _call_collection_item(shapes, index)
                if str(getattr(shape, "Name", "") or "") == WATERMARK_MARKER:
                    return True
        except Exception:
            continue
    return False


def _resolve_word_font(font_name, word_font_resolver=None):
    raw_name = str(font_name or "").strip() or "Microsoft YaHei"
    if callable(word_font_resolver):
        try:
            return str(word_font_resolver(raw_name) or raw_name)
        except Exception:
            return raw_name
    return raw_name


def _position_word_shape(shape, section):
    try:
        page_setup = section.PageSetup
        page_width = float(page_setup.PageWidth)
        page_height = float(page_setup.PageHeight)
    except Exception:
        page_width, page_height = 595.0, 842.0

    try:
        shape.RelativeHorizontalPosition = 1
    except Exception:
        pass
    try:
        shape.RelativeVerticalPosition = 1
    except Exception:
        pass
    try:
        shape.Left = (page_width - float(shape.Width)) / 2.0
    except Exception:
        pass
    try:
        shape.Top = (page_height - float(shape.Height)) / 2.0
    except Exception:
        pass
    try:
        shape.WrapFormat.AllowOverlap = True
    except Exception:
        pass
    try:
        shape.WrapFormat.Type = 3
    except Exception:
        pass
    try:
        shape.ZOrder(5)
    except Exception:
        pass


def _add_word_header_watermark(header, section, text, font_name, font_size, opacity, angle, color=None):
    shape = header.Shapes.AddTextEffect(
        0,
        str(text or ""),
        str(font_name or "Microsoft YaHei"),
        max(1.0, _safe_float(font_size, 24.0)),
        False,
        False,
        0,
        0,
    )
    try:
        shape.Name = WATERMARK_MARKER
    except Exception:
        pass
    try:
        shape.Rotation = _safe_float(angle, 45.0)
    except Exception:
        pass
    try:
        shape.TextEffect.NormalizedHeight = False
    except Exception:
        pass
    try:
        shape.Fill.Visible = True
    except Exception:
        pass
    try:
        shape.Fill.Solid()
    except Exception:
        pass
    try:
        shape.Fill.ForeColor.RGB = _word_rgb_value(color if color is not None else WORD_WATERMARK_DEFAULT_RGB)
    except Exception:
        pass
    try:
        shape.Fill.Transparency = 1.0 - _word_visible_opacity(opacity)
    except Exception:
        pass
    try:
        shape.Line.Visible = False
    except Exception:
        pass
    _position_word_shape(shape, section)
    return shape


def open_word_document_safely(word_app, src_path):
    """Open a Word document with repair fallbacks for damaged files."""

    src_value = str(Path(src_path).resolve())
    attempts = [
        lambda: word_app.Documents.Open(src_value, False, False, False),
        lambda: word_app.Documents.Open(src_value),
        lambda: word_app.Documents.Open(src_value, False, False, False, "", "", False, "", "", 0, 0, False, False, True),
        lambda: word_app.Documents.Open(src_value, False, True, False, "", "", False, "", "", 0, 0, False, False, True),
    ]
    last_exc = None
    for attempt in attempts:
        try:
            return attempt()
        except Exception as exc:
            last_exc = exc
    if last_exc is not None:
        raise last_exc
    raise RuntimeError(f"unable to open Word document: {src_value}")


def add_watermark_to_word(
    word_app,
    src,
    dst,
    text,
    raw_font_name,
    font_size,
    opacity,
    angle,
    page_range="all",
    force_mode=False,
    *,
    word_font_resolver=None,
    com_context_factory=None,
    color=None,
):
    """Apply a header watermark to a Word document."""

    src_path = Path(src).resolve()
    dst_path = Path(dst).resolve()
    if not src_path.exists():
        return f"ERROR:source not found: {src_path}"

    context = com_context_factory() if callable(com_context_factory) else nullcontext()
    doc = None
    previous_alerts = None
    try:
        with context:
            try:
                previous_alerts = word_app.DisplayAlerts
                word_app.DisplayAlerts = 0
            except Exception:
                previous_alerts = None

            doc = open_word_document_safely(word_app, src_path)

            if not force_mode and _word_has_marker(doc):
                try:
                    doc.Close(False)
                except Exception:
                    pass
                doc = None
                return "SKIP:already watermarked"

            compatible_font = _resolve_word_font(raw_font_name, word_font_resolver=word_font_resolver)
            added = 0
            only_first = str(page_range or "all").lower() in {"first", "first_page", "1"}
            for header, section in _iter_word_headers(doc):
                try:
                    _add_word_header_watermark(header, section, text, compatible_font, font_size, opacity, angle, color=color)
                    added += 1
                    if only_first:
                        break
                except Exception:
                    continue

            if added <= 0:
                return "ERROR:no writable Word header found"

            dst_path.parent.mkdir(parents=True, exist_ok=True)
            if _same_path(src_path, dst_path):
                doc.Save()
            else:
                if dst_path.exists():
                    try:
                        dst_path.unlink()
                    except Exception:
                        pass
                try:
                    doc.SaveAs2(str(dst_path))
                except Exception:
                    doc.SaveAs(str(dst_path))
            return "SUCCESS"
    except Exception as exc:
        if _looks_like_unreadable_word_error(exc):
            return "SKIP:damaged word source"
        return f"ERROR:{exc}"
    finally:
        if doc is not None:
            try:
                doc.Close(False)
            except Exception:
                pass
        if previous_alerts is not None:
            try:
                word_app.DisplayAlerts = previous_alerts
            except Exception:
                pass
