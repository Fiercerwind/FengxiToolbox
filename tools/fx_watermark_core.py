"""Core watermark helpers for Fengxi Toolbox.

This module owns the PDF/Word watermark implementation.  The GUI loader keeps
thin wrappers for runtime compatibility and supplies font/COM adapters.
"""

from __future__ import annotations

import io
import hashlib
import os
import random
import secrets
import tempfile
from contextlib import nullcontext
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
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
WATERMARK_RANGE_ALL = "all"
WATERMARK_RANGE_FIRST = "first"
WATERMARK_RANGE_FIRST_RANDOM = "first_random"
COPY_GUARD_METADATA_KEY = "/FXCopyGuard"
COPY_GUARD_METADATA_VALUE = "Fengxi Copy Guard v1"
WORD_COPY_GUARD_VARIABLE = "FXCopyGuard"
WORD_COPY_GUARD_VALUE = "Fengxi Copy Guard v1"
COPY_GUARD_TEXT_PREFIX = "FXCG"
COPY_GUARD_STRENGTH_BLOCKS = {
    "light": 4,
    "standard": 8,
    "strong": 14,
}


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


def normalize_watermark_page_range(value):
    text = str(value or "").strip().lower()
    compact = text.replace(" ", "").replace("-", "_").replace("+", "_")
    if compact in {"first_random", "first_and_random", "first_random_page", "firstplusrandom", "first_one_random", "1_random"}:
        return WATERMARK_RANGE_FIRST_RANDOM
    if compact in {"第一页+随机一页", "第一页_随机一页", "第一页随机一页", "首页+随机一页", "首页_随机一页", "首页随机一页", "仅第一页+随机一页", "仅第一页_随机一页"}:
        return WATERMARK_RANGE_FIRST_RANDOM
    if compact in {"first", "first_page", "1", "第一页", "仅第一页", "首页"}:
        return WATERMARK_RANGE_FIRST
    return WATERMARK_RANGE_ALL


def normalize_copy_guard_strength(value):
    text = str(value or "standard").strip().lower()
    aliases = {
        "轻度": "light",
        "轻量": "light",
        "light": "light",
        "标准": "standard",
        "standard": "standard",
        "normal": "standard",
        "强力": "strong",
        "强": "strong",
        "strong": "strong",
    }
    return aliases.get(text, "standard")


def _select_watermark_page_indexes(page_count, page_range):
    try:
        total = max(0, int(page_count))
    except Exception:
        total = 0
    if total <= 0:
        return set()

    normalized = normalize_watermark_page_range(page_range)
    if normalized == WATERMARK_RANGE_ALL:
        return set(range(total))
    if normalized == WATERMARK_RANGE_FIRST:
        return {0}

    selected = {0}
    if total > 1:
        selected.add(random.randint(1, total - 1))
    return selected


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
    page_size=None,
    scale_font_to_page=False,
    page_rotation=0,
):
    """Build a one-page PDF watermark packet."""

    packet = io.BytesIO()
    try:
        page_width = max(1.0, float(page_size[0]))
        page_height = max(1.0, float(page_size[1]))
    except Exception:
        page_width, page_height = A4
    pdf = canvas.Canvas(packet, pagesize=(page_width, page_height))
    resolved_font = _resolve_reportlab_font(font_name, font_path_resolver=font_path_resolver)
    size = max(1.0, _safe_float(font_size, 36.0))
    normalized_rotation = int(_safe_float(page_rotation, 0.0)) % 360
    if scale_font_to_page:
        visible_width, visible_height = page_width, page_height
        if normalized_rotation in {90, 270}:
            visible_width, visible_height = visible_height, visible_width
        if visible_width > visible_height:
            base_width, base_height = A4[1], A4[0]
        else:
            base_width, base_height = A4
        size *= max(0.01, min(visible_width / base_width, visible_height / base_height))
    alpha = max(0.0, min(1.0, _safe_float(opacity, 0.2)))
    rotation = _safe_float(angle, 45.0) - normalized_rotation
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


def _copy_guard_noise_lines(strength, page_index, document_token, allow_unicode=False):
    block_count = COPY_GUARD_STRENGTH_BLOCKS[normalize_copy_guard_strength(strength)]
    ascii_fragments = ("A9x", "xY7", "Z_9", "Q2", "7K#", "m4@")
    # Keep these as escapes so the source file remains encoding-independent.
    # They intentionally resemble common mojibake, rather than meaningful prose.
    unicode_fragments = (
        "\u951f\u65a4\u62f7",  # 锟斤拷
        "\u70eb\u70eb\u70eb",  # 烫烫烫
        "\u6d63\u20ac",  # 浠€
        "\u93c2\u56e6\u6b22",  # 鏂囦欢
        "\u5bee\u20ac",  # 寮€
        "\u93bb\u612e\u305a",  # 鎻愮ず
    )
    lines = []
    for slot in range(block_count):
        seed = f"{document_token}:{page_index}:{slot}".encode("utf-8")
        first = hashlib.sha256(seed).hexdigest().upper()
        second = hashlib.sha256(seed + b":fx-copy-guard").hexdigest().upper()
        # Alternate families so every strength mixes Chinese mojibake with the
        # existing ASCII/digit/symbol noise. Hashing picks the actual fragment.
        fragments = unicode_fragments if slot % 2 else ascii_fragments
        fragment = fragments[int(first[4:8], 16) % len(fragments)]
        separator = "|#@/"[int(first[2:4], 16) % 4]
        lines.append(f"{COPY_GUARD_TEXT_PREFIX}{slot:02d}{separator}{fragment}{first}{separator}{second[:24]}")
    return lines


def create_copy_guard_packet(page_size, strength="standard", page_index=0, document_token=None):
    """Build an invisible edge-text overlay for whole-page text extraction."""

    try:
        page_width = max(1.0, float(page_size[0]))
        page_height = max(1.0, float(page_size[1]))
    except Exception:
        page_width, page_height = A4
    token = str(document_token or secrets.token_hex(16))
    lines = _copy_guard_noise_lines(strength, page_index, token, allow_unicode=True)

    packet = io.BytesIO()
    pdf = canvas.Canvas(packet, pagesize=(page_width, page_height))
    text_obj = pdf.beginText()
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        guard_font = "STSong-Light"
    except Exception:
        guard_font = "Helvetica"
    text_obj.setFont(guard_font, 1.0)
    text_obj.setTextRenderMode(3)
    top_margin = min(12.0, max(2.0, page_height * 0.02))
    available_height = max(1.0, page_height - (top_margin * 2.0))
    step = available_height / max(1, len(lines) - 1) if len(lines) > 1 else 0.0
    for index, line in enumerate(lines):
        text_obj.setTextOrigin(1.5, top_margin + (index * step))
        text_obj.textLine(line)
    pdf.drawText(text_obj)
    pdf.showPage()
    pdf.save()
    packet.seek(0)
    return packet


def _page_geometry(page):
    """Return raw page width, height and normalized rotation."""

    box = None
    for name in ("mediabox", "MediaBox"):
        try:
            box = getattr(page, name)
        except Exception:
            box = None
        if box is not None:
            break
    if box is None:
        try:
            box = page.obj.get("/MediaBox")
        except Exception:
            box = None
    try:
        left, bottom, right, top = [float(value) for value in box]
        width = max(1.0, abs(right - left))
        height = max(1.0, abs(top - bottom))
    except Exception:
        width, height = A4

    rotation = 0
    for getter in (
        lambda: getattr(page, "rotation"),
        lambda: page.get("/Rotate", 0),
        lambda: page.obj.get("/Rotate", 0),
    ):
        try:
            rotation = int(float(getter() or 0)) % 360
            break
        except Exception:
            continue
    return width, height, rotation


def _is_default_a4_page(width, height, rotation=0):
    if int(rotation or 0) % 360:
        return False
    width_tolerance = max(2.0, A4[0] * 0.01)
    height_tolerance = max(2.0, A4[1] * 0.01)
    return abs(float(width) - A4[0]) <= width_tolerance and abs(float(height) - A4[1]) <= height_tolerance


def _create_adaptive_watermark_packet(watermark_spec, page_size, page_rotation=0, font_path_resolver=None):
    spec = dict(watermark_spec or {})
    return create_watermark_packet(
        spec.get("content", ""),
        spec.get("font_name", ""),
        spec.get("font_size", 36.0),
        spec.get("opacity", 0.2),
        spec.get("angle", 45.0),
        font_path_resolver=font_path_resolver,
        color=spec.get("color"),
        page_size=page_size,
        scale_font_to_page=True,
        page_rotation=page_rotation,
    )


def _copy_guard_text_instruction_blocks(pikepdf, font_name, line, y_position):
    """Return one invisible text block that stays outside normal line selection."""

    return [
        pikepdf.ContentStreamInstruction([], pikepdf.Operator("q")),
        pikepdf.ContentStreamInstruction([], pikepdf.Operator("BT")),
        pikepdf.ContentStreamInstruction([font_name, 1], pikepdf.Operator("Tf")),
        pikepdf.ContentStreamInstruction([3], pikepdf.Operator("Tr")),
        pikepdf.ContentStreamInstruction([1, 0, 0, 1, 1.5, y_position], pikepdf.Operator("Tm")),
        pikepdf.ContentStreamInstruction([pikepdf.String(line)], pikepdf.Operator("Tj")),
        pikepdf.ContentStreamInstruction([], pikepdf.Operator("ET")),
        pikepdf.ContentStreamInstruction([], pikepdf.Operator("Q")),
    ]


def _copy_guard_page_size(page):
    try:
        box = page.MediaBox
        left, bottom, right, top = (float(box[index]) for index in range(4))
        return left, bottom, max(1.0, right - left), max(1.0, top - bottom)
    except Exception:
        return 0.0, 0.0, float(A4[0]), float(A4[1])


def _page_has_direct_text_resources(page):
    """Return whether a page can contain directly selectable text.

    Image-only pages have no text for a customer to copy.  Avoiding a complete
    content-stream parse for them is important for large scanned PDF batches.
    Text inside nested form XObjects was not interleaved by the previous
    implementation either, so this preserves the existing protection scope.
    """

    try:
        resources = page.get("/Resources", None)
        if resources is None:
            return False
        return bool(resources.get("/Font", None))
    except Exception:
        return True


def _inject_copy_guard_into_pikepdf(pdf, pikepdf, strength, document_token):
    """Add guard instructions to an already-open pikepdf document."""

    text_show_operators = {"Tj", "TJ", "'", '"'}
    descendant_font = pikepdf.Dictionary(
        {
            "/Type": pikepdf.Name("/Font"),
            "/Subtype": pikepdf.Name("/CIDFontType0"),
            "/BaseFont": pikepdf.Name("/STSong-Light"),
            "/CIDSystemInfo": pikepdf.Dictionary(
                {
                    "/Registry": pikepdf.String("Adobe"),
                    "/Ordering": pikepdf.String("GB1"),
                    "/Supplement": 4,
                }
            ),
            "/DW": 1000,
        }
    )
    font = pikepdf.Dictionary(
        {
            "/Type": pikepdf.Name("/Font"),
            "/Subtype": pikepdf.Name("/Type0"),
            "/BaseFont": pikepdf.Name("/STSong-Light"),
            "/Encoding": pikepdf.Name("/UniGB-UCS2-H"),
            "/DescendantFonts": pikepdf.Array([descendant_font]),
        }
    )
    for page_index, page in enumerate(pdf.pages):
        if not _page_has_direct_text_resources(page):
            continue
        instructions = list(pikepdf.parse_content_stream(page))
        text_block_indexes = []
        block_has_text = False
        for index, instruction in enumerate(instructions):
            operator = str(instruction.operator)
            if operator == "BT":
                block_has_text = False
            elif operator in text_show_operators:
                block_has_text = True
            elif operator == "ET":
                if block_has_text:
                    # Keep every original BT...ET text block intact, so copying one
                    # paragraph/text block does not cross into a guard block.
                    text_block_indexes.append(index)
                block_has_text = False
        lines = _copy_guard_noise_lines(strength, page_index, document_token, allow_unicode=True)
        left, bottom, _width, height = _copy_guard_page_size(page)
        top_margin = min(12.0, max(2.0, height * 0.02))
        available_height = max(1.0, height - (top_margin * 2.0))
        step = available_height / max(1, len(lines) - 1) if len(lines) > 1 else 0.0
        font_name = page.add_resource(font, pikepdf.Name("/Font"), prefix="FXCopyGuard")
        insertions = {}

        if text_block_indexes:
            for line_index, line in enumerate(lines):
                # Spread blocks through complete text blocks instead of appending them
                # after the page. Duplicate anchors are intentional on short pages.
                block_position = min(
                    len(text_block_indexes) - 1,
                    ((line_index + 1) * len(text_block_indexes)) // (len(lines) + 1),
                )
                anchor = text_block_indexes[block_position]
                y_position = bottom + top_margin + (line_index * step)
                insertions.setdefault(anchor, []).extend(
                    _copy_guard_text_instruction_blocks(
                        pikepdf,
                        font_name,
                        line,
                        y_position,
                    )
                )
        else:
            # Image-only pages have no ordinary text to interleave with, but still
            # receive the guard so their text layer remains consistently protected.
            anchor = len(instructions) - 1
            insertions[anchor] = []
            for line_index, line in enumerate(lines):
                y_position = bottom + top_margin + (line_index * step)
                insertions[anchor].extend(
                    _copy_guard_text_instruction_blocks(
                        pikepdf,
                        font_name,
                        line,
                        y_position,
                    )
                )

        rewritten = []
        for instruction_index, instruction in enumerate(instructions):
            rewritten.append(instruction)
            rewritten.extend(insertions.get(instruction_index, []))
        if not instructions:
            rewritten.extend(insertions.get(-1, []))
        page.Contents = pdf.make_stream(pikepdf.unparse_content_stream(rewritten))


def _pikepdf_docinfo_value(docinfo, key):
    try:
        return str(docinfo.get(key, "") or "")
    except Exception:
        return ""


def _fast_copy_guard_preflight(src_path, check_text):
    """Return watermark state without constructing a pypdf reader.

    Copy-guard work is ultimately performed by pikepdf.  Reusing pikepdf for
    the marker check removes one PDF backend open from the normal path.  MuPDF
    is only used for the legacy first-page text fallback when metadata is absent.
    ``None`` keeps the established pypdf/repair path as a compatibility fallback.
    """

    try:
        import pikepdf
    except Exception:
        return None

    try:
        with pikepdf.Pdf.open(str(src_path)) as pdf:
            keywords = _pikepdf_docinfo_value(pdf.docinfo, "/Keywords")
            creator = _pikepdf_docinfo_value(pdf.docinfo, "/Creator")
            copy_guard_value = _pikepdf_docinfo_value(pdf.docinfo, COPY_GUARD_METADATA_KEY)
            visible_exists = WATERMARK_MARKER in keywords or creator == WATERMARK_CREATOR
            guard_exists = copy_guard_value == COPY_GUARD_METADATA_VALUE
    except Exception:
        return None

    if not visible_exists and check_text:
        try:
            import fitz

            with fitz.open(str(src_path)) as document:
                if document.page_count:
                    visible_exists = str(check_text) in (document[0].get_text("text") or "")
        except Exception:
            return None
    return visible_exists, guard_exists


def _add_interleaved_copy_guard_to_pdf(src_path, dst_path, strength, document_token):
    """Interleave invisible blocks between existing text blocks using pikepdf."""

    try:
        import pikepdf
    except Exception as exc:
        return f"ERROR:copy guard backend unavailable: {exc}"

    try:
        with pikepdf.Pdf.open(str(src_path)) as pdf:
            _inject_copy_guard_into_pikepdf(pdf, pikepdf, strength, document_token)
            pdf.save(str(dst_path))
        return "SUCCESS"
    except Exception as exc:
        return f"ERROR:copy guard interleave failed: {exc}"


def _add_watermark_and_copy_guard_to_pdf(
    src_path,
    dst_path,
    watermark_packet,
    page_range,
    copy_guard_strength,
    document_token,
    adaptive_page_size=False,
    watermark_spec=None,
    font_path_resolver=None,
):
    """Apply the visible overlay and copy guard in one pikepdf write."""

    try:
        import pikepdf
    except Exception as exc:
        return f"ERROR:copy guard backend unavailable: {exc}"

    watermark_pdf = None
    adaptive_watermark_pdfs = {}
    try:
        with pikepdf.Pdf.open(str(src_path)) as pdf:
            watermark_page = None
            if watermark_packet is not None:
                watermark_packet.seek(0)
                watermark_pdf = pikepdf.Pdf.open(watermark_packet)
                watermark_page = watermark_pdf.pages[0]
            target_pages = set(_select_watermark_page_indexes(len(pdf.pages), page_range))
            if watermark_page is not None or (adaptive_page_size and watermark_spec):
                for index, page in enumerate(pdf.pages):
                    if index in target_pages:
                        overlay_page = watermark_page
                        if adaptive_page_size and watermark_spec:
                            width, height, rotation = _page_geometry(page)
                            if not _is_default_a4_page(width, height, rotation):
                                cache_key = (round(width, 3), round(height, 3), rotation)
                                cached = adaptive_watermark_pdfs.get(cache_key)
                                if cached is None:
                                    packet = _create_adaptive_watermark_packet(
                                        watermark_spec,
                                        (width, height),
                                        page_rotation=rotation,
                                        font_path_resolver=font_path_resolver,
                                    )
                                    adaptive_pdf = pikepdf.Pdf.open(packet)
                                    cached = (adaptive_pdf, packet)
                                    adaptive_watermark_pdfs[cache_key] = cached
                                overlay_page = cached[0].pages[0]
                        if overlay_page is not None:
                            page.add_overlay(overlay_page, push_stack=True, shrink=False, expand=False)

            _inject_copy_guard_into_pikepdf(
                pdf,
                pikepdf,
                copy_guard_strength,
                document_token,
            )
            pdf.docinfo[pikepdf.Name("/Keywords")] = WATERMARK_MARKER
            pdf.docinfo[pikepdf.Name("/Creator")] = WATERMARK_CREATOR
            pdf.docinfo[pikepdf.Name(COPY_GUARD_METADATA_KEY)] = COPY_GUARD_METADATA_VALUE
            pdf.save(str(dst_path))
        return "SUCCESS"
    except Exception as exc:
        return f"ERROR:single-pass copy guard failed: {exc}"
    finally:
        for adaptive_pdf, _packet in adaptive_watermark_pdfs.values():
            try:
                adaptive_pdf.close()
            except Exception:
                pass
        if watermark_pdf is not None:
            try:
                watermark_pdf.close()
            except Exception:
                pass


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


def _metadata_has_copy_guard(metadata):
    if not metadata:
        return False
    try:
        return str(metadata.get(COPY_GUARD_METADATA_KEY, "") or "") == COPY_GUARD_METADATA_VALUE
    except Exception:
        return False


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


def _writer_metadata(reader, copy_guard=False):
    metadata = {}
    try:
        for key, value in (reader.metadata or {}).items():
            if key and value is not None:
                metadata[str(key)] = str(value)
    except Exception:
        metadata = {}
    metadata["/Keywords"] = WATERMARK_MARKER
    metadata["/Creator"] = WATERMARK_CREATOR
    if copy_guard:
        metadata[COPY_GUARD_METADATA_KEY] = COPY_GUARD_METADATA_VALUE
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


def add_watermark_to_pdf(
    src,
    dst,
    watermark_packet,
    page_range="all",
    check_text=None,
    force_mode=False,
    copy_guard=False,
    copy_guard_strength="standard",
    adaptive_page_size=False,
    watermark_spec=None,
    font_path_resolver=None,
):
    """Apply the watermark packet to a PDF and return a runtime-compatible status."""

    repair_path = None
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        if not src_path.exists():
            return f"ERROR:source not found: {src_path}"

        reader = None
        preflight_state = _fast_copy_guard_preflight(src_path, check_text) if copy_guard else None
        if preflight_state is not None:
            visible_watermark_exists, copy_guard_exists = preflight_state
        else:
            reader, repair_path, open_status = _open_pdf_reader_for_watermark(src_path)
            if open_status:
                return open_status
            if reader is None:
                return "ERROR:PDF reader unavailable"
            visible_watermark_exists = _metadata_has_marker(reader.metadata)
            if not visible_watermark_exists and check_text:
                visible_watermark_exists = _first_page_contains(reader, check_text)
            copy_guard_exists = _metadata_has_copy_guard(reader.metadata)
        apply_visible_watermark = bool(force_mode or not visible_watermark_exists)
        apply_copy_guard = bool(copy_guard and (force_mode or not copy_guard_exists))
        if not apply_visible_watermark and not apply_copy_guard:
            if copy_guard and copy_guard_exists:
                return "SKIP:already watermarked and copy guard exists"
            if visible_watermark_exists:
                return "SKIP:already watermarked"
            return "SKIP:no watermark change requested"

        copy_guard_token = secrets.token_hex(16) if apply_copy_guard else ""
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        output_path = dst_path
        temp_path = None
        guard_input_path = None
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

        if apply_copy_guard:
            one_pass_source = Path(repair_path) if repair_path is not None else src_path
            one_pass_status = _add_watermark_and_copy_guard_to_pdf(
                one_pass_source,
                output_path,
                watermark_packet if apply_visible_watermark else None,
                page_range,
                copy_guard_strength,
                copy_guard_token,
                adaptive_page_size=adaptive_page_size,
                watermark_spec=watermark_spec,
                font_path_resolver=font_path_resolver,
            )
            if one_pass_status == "SUCCESS":
                if temp_path is not None:
                    os.replace(str(temp_path), str(dst_path))
                return "SUCCESS"

        if reader is None:
            reader, repair_path, open_status = _open_pdf_reader_for_watermark(src_path)
            if open_status:
                return open_status
            if reader is None:
                return "ERROR:PDF reader unavailable"

        watermark_page = None
        watermark_reader = None
        if apply_visible_watermark:
            if hasattr(watermark_packet, "seek"):
                watermark_packet.seek(0)
            watermark_reader = PdfReader(watermark_packet)
            watermark_page = watermark_reader.pages[0]

        writer = PdfWriter()
        target_pages = _select_watermark_page_indexes(len(reader.pages), page_range)
        adaptive_watermark_pages = {}
        for index, page in enumerate(reader.pages):
            if apply_visible_watermark and index in target_pages:
                overlay_page = watermark_page
                if adaptive_page_size and watermark_spec:
                    width, height, rotation = _page_geometry(page)
                    if not _is_default_a4_page(width, height, rotation):
                        cache_key = (round(width, 3), round(height, 3), rotation)
                        cached = adaptive_watermark_pages.get(cache_key)
                        if cached is None:
                            packet = _create_adaptive_watermark_packet(
                                watermark_spec,
                                (width, height),
                                page_rotation=rotation,
                                font_path_resolver=font_path_resolver,
                            )
                            adaptive_reader = PdfReader(packet)
                            cached = (adaptive_reader.pages[0], adaptive_reader, packet)
                            adaptive_watermark_pages[cache_key] = cached
                        overlay_page = cached[0]
                try:
                    page.merge_page(overlay_page)
                except AttributeError:
                    page.mergePage(overlay_page)
            writer.add_page(page)
        writer.add_metadata(_writer_metadata(reader, copy_guard=copy_guard_exists or apply_copy_guard))

        writer_output_path = output_path
        if apply_copy_guard:
            handle = tempfile.NamedTemporaryFile(
                prefix=f"{dst_path.stem}_copy_guard_input_",
                suffix=dst_path.suffix or ".pdf",
                dir=str(dst_path.parent),
                delete=False,
            )
            guard_input_path = Path(handle.name)
            handle.close()
            writer_output_path = guard_input_path

        with open(writer_output_path, "wb") as file_obj:
            writer.write(file_obj)

        if apply_copy_guard:
            guard_status = _add_interleaved_copy_guard_to_pdf(
                guard_input_path,
                output_path,
                copy_guard_strength,
                copy_guard_token,
            )
            if guard_status != "SUCCESS":
                return guard_status

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
        try:
            if 'guard_input_path' in locals() and guard_input_path is not None and Path(guard_input_path).exists():
                Path(guard_input_path).unlink()
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


def _select_word_header(section, header_index):
    try:
        return _call_collection_item(section.Headers, header_index)
    except Exception:
        return None


def _prepare_first_page_word_header(section):
    try:
        section.PageSetup.DifferentFirstPageHeaderFooter = True
    except Exception:
        pass
    header = _select_word_header(section, 2)
    try:
        if header is not None and hasattr(header, "Exists") and not bool(header.Exists):
            return None
    except Exception:
        pass
    return header


def _iter_word_first_page_headers(doc):
    try:
        sections = doc.Sections
        section_count = int(sections.Count)
    except Exception:
        return

    if section_count <= 0:
        return
    try:
        section = _call_collection_item(sections, 1)
    except Exception:
        return
    header = _prepare_first_page_word_header(section)
    if header is not None:
        yield header, section


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


def _word_has_copy_guard(doc):
    try:
        variable = _call_collection_item(doc.Variables, WORD_COPY_GUARD_VARIABLE)
        return str(getattr(variable, "Value", "") or "") == WORD_COPY_GUARD_VALUE
    except Exception:
        return False


def _mark_word_copy_guard(doc):
    try:
        variable = _call_collection_item(doc.Variables, WORD_COPY_GUARD_VARIABLE)
        variable.Value = WORD_COPY_GUARD_VALUE
        return True
    except Exception:
        pass
    try:
        doc.Variables.Add(WORD_COPY_GUARD_VARIABLE, WORD_COPY_GUARD_VALUE)
        return True
    except Exception:
        return False


def _word_meaningful_paragraph_ranges(doc):
    """Return meaningful body paragraph ranges with one COM text read.

    Accessing every Paragraph.Range property crosses the COM boundary several
    times per paragraph. Word's body text already contains the paragraph marks,
    so the same ranges can be reconstructed locally and the old path kept as a
    fallback for unusual COM implementations.
    """

    try:
        content = doc.Content
        content_start = int(content.Start)
        full_text = str(getattr(content, "Text", "") or "")
        paragraphs = []
        segment_start = 0
        for index, character in enumerate(full_text):
            if character != "\r":
                continue
            segment = full_text[segment_start:index]
            if segment.replace("\r", "").replace("\x07", "").strip():
                paragraphs.append((content_start + segment_start, content_start + index + 1))
            segment_start = index + 1

        if segment_start < len(full_text):
            segment = full_text[segment_start:]
            if segment.replace("\r", "").replace("\x07", "").strip():
                paragraphs.append((content_start + segment_start, content_start + len(full_text)))
        return paragraphs
    except Exception:
        pass

    paragraphs = []
    try:
        collection = doc.Content.Paragraphs
        count = int(collection.Count)
    except Exception:
        return paragraphs

    for index in range(1, count + 1):
        try:
            paragraph = _call_collection_item(collection, index)
            paragraph_range = paragraph.Range.Duplicate
            text = str(getattr(paragraph_range, "Text", "") or "")
            if not text.replace("\r", "").replace("\x07", "").strip():
                continue
            paragraphs.append((int(paragraph_range.Start), int(paragraph_range.End)))
        except Exception:
            continue
    return paragraphs


def _format_word_copy_guard_range(guard_range):
    # Older Word documents can reject individual paragraph-format assignments.
    # Keep the text insertion valid even when one optional style is unsupported.
    for target_name, attribute, value in (
        ("Font", "Hidden", False),
        ("Font", "Size", 1),
        ("Font", "Color", 0xFFFFFF),
        ("ParagraphFormat", "SpaceBefore", 0),
        ("ParagraphFormat", "SpaceAfter", 0),
        ("ParagraphFormat", "LineSpacingRule", 0),
        ("ParagraphFormat", "LineSpacing", 1),
    ):
        try:
            setattr(getattr(guard_range, target_name), attribute, value)
        except Exception:
            pass


def _append_word_copy_guard_paragraphs(range_owner, lines):
    """Append standalone guard paragraphs to a body or text-frame range."""

    if not lines:
        return 0
    try:
        range_owner.InsertAfter("\r".join(lines) + "\r")
    except Exception:
        return 0

    added = 0
    try:
        paragraphs = range_owner.Paragraphs
        for index in range(1, int(paragraphs.Count) + 1):
            paragraph_range = _call_collection_item(paragraphs, index).Range.Duplicate
            paragraph_text = str(getattr(paragraph_range, "Text", "") or "")
            if not any(line in paragraph_text for line in lines):
                continue
            _format_word_copy_guard_range(paragraph_range)
            added += 1
    except Exception:
        pass
    return added


def _add_word_copy_guard_to_text_frame(text_frame, strength, document_token, frame_index):
    try:
        if not bool(text_frame.HasText):
            return 0
        text_range = text_frame.TextRange
        paragraphs = text_range.Paragraphs
        meaningful = []
        for index in range(1, int(paragraphs.Count) + 1):
            paragraph_range = _call_collection_item(paragraphs, index).Range.Duplicate
            paragraph_text = str(getattr(paragraph_range, "Text", "") or "")
            if paragraph_text.replace("\r", "").replace("\x07", "").strip():
                meaningful.append(paragraph_range)
    except Exception:
        return 0

    lines = _copy_guard_noise_lines(
        strength,
        0,
        f"{document_token}:frame:{frame_index}",
        allow_unicode=True,
    )
    if not meaningful:
        return 0
    boundary_positions = [int(item.End) for item in meaningful[:-1]]
    if not boundary_positions:
        return _append_word_copy_guard_paragraphs(text_range, lines)

    placements = []
    for line_index, line in enumerate(lines):
        boundary_index = min(
            len(boundary_positions) - 1,
            ((line_index + 1) * len(boundary_positions)) // (len(lines) + 1),
        )
        placements.append((boundary_positions[boundary_index], line))

    added = 0
    for position, line in sorted(placements, key=lambda item: item[0], reverse=True):
        try:
            guard_range = text_range.Duplicate
            guard_range.SetRange(position, position)
            guard_range.InsertAfter(f"{line}\r")
            guard_range.SetRange(position, position + len(line) + 1)
        except Exception:
            continue
        _format_word_copy_guard_range(guard_range)
        added += 1
    return added


def _add_word_copy_guard_to_shapes(doc, strength, document_token):
    added = 0
    try:
        shapes = doc.Shapes
        shape_count = int(shapes.Count)
    except Exception:
        return 0
    for index in range(1, shape_count + 1):
        try:
            shape = _call_collection_item(shapes, index)
            added += _add_word_copy_guard_to_text_frame(
                shape.TextFrame,
                strength,
                document_token,
                index,
            )
        except Exception:
            continue
    return added


def _add_word_copy_guard(doc, strength, document_token):
    """Insert visually neutral guard paragraphs only at body-paragraph boundaries."""

    paragraphs = _word_meaningful_paragraph_ranges(doc)
    if not paragraphs:
        return 0

    lines = _copy_guard_noise_lines(strength, 0, document_token, allow_unicode=True)
    boundary_positions = [end for _start, end in paragraphs[:-1]]
    if not boundary_positions:
        return _append_word_copy_guard_paragraphs(doc.Content, lines)

    placements = []
    for line_index, line in enumerate(lines):
        boundary_index = min(
            len(boundary_positions) - 1,
            ((line_index + 1) * len(boundary_positions)) // (len(lines) + 1),
        )
        placements.append((boundary_positions[boundary_index], line))

    added = 0
    # Insert from the end so original paragraph positions remain valid.
    for position, line in sorted(placements, key=lambda item: item[0], reverse=True):
        try:
            guard_range = doc.Range(position, position)
            guard_range.InsertAfter(f"{line}\r")
            guard_range.SetRange(position, position + len(line) + 1)
        except Exception:
            continue

        _format_word_copy_guard_range(guard_range)
        added += 1
    return added


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


def _add_word_range_watermark(doc, page_number, text, font_name, font_size, opacity, angle, color=None):
    try:
        anchor_range = doc.GoTo(1, 1, int(page_number))
    except Exception:
        return None
    try:
        shape = doc.Shapes.AddTextEffect(
            0,
            str(text or ""),
            str(font_name or "Microsoft YaHei"),
            max(1.0, _safe_float(font_size, 24.0)),
            False,
            False,
            0,
            0,
            anchor_range,
        )
    except Exception:
        try:
            shape = anchor_range.ShapeRange.AddTextEffect(
                0,
                str(text or ""),
                str(font_name or "Microsoft YaHei"),
                max(1.0, _safe_float(font_size, 24.0)),
                False,
                False,
                0,
                0,
            )
        except Exception:
            return None
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
    try:
        page_setup = doc.Sections(1).PageSetup
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
    return shape


def _get_word_page_count(doc):
    try:
        return int(doc.ComputeStatistics(2))
    except Exception:
        try:
            return int(doc.BuiltInDocumentProperties("Number of Pages"))
        except Exception:
            return 1


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
    copy_guard=False,
    copy_guard_strength="standard",
):
    """Apply a header watermark and optional hidden copy guard to a Word document."""

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

            try:
                protection_type = int(doc.ProtectionType)
            except Exception:
                protection_type = -1
            if protection_type != -1:
                return "SKIP:protected Word document requires password"

            visible_watermark_exists = _word_has_marker(doc)
            copy_guard_exists = _word_has_copy_guard(doc)
            apply_visible_watermark = bool(force_mode or not visible_watermark_exists)
            apply_copy_guard = bool(copy_guard and (force_mode or not copy_guard_exists))
            if not apply_visible_watermark and not apply_copy_guard:
                if copy_guard and copy_guard_exists:
                    return "SKIP:already watermarked and copy guard exists"
                return "SKIP:already watermarked"

            added_visible = 0
            if apply_visible_watermark:
                compatible_font = _resolve_word_font(raw_font_name, word_font_resolver=word_font_resolver)
                normalized_range = normalize_watermark_page_range(page_range)
                header_iter = _iter_word_first_page_headers(doc) if normalized_range in {WATERMARK_RANGE_FIRST, WATERMARK_RANGE_FIRST_RANDOM} else _iter_word_headers(doc)
                for header, section in header_iter:
                    try:
                        _add_word_header_watermark(header, section, text, compatible_font, font_size, opacity, angle, color=color)
                        added_visible += 1
                    except Exception:
                        continue
                if normalized_range == WATERMARK_RANGE_FIRST_RANDOM:
                    page_count = _get_word_page_count(doc)
                    target_pages = _select_watermark_page_indexes(page_count, normalized_range)
                    for page_index in sorted(index for index in target_pages if index > 0):
                        try:
                            if _add_word_range_watermark(doc, page_index + 1, text, compatible_font, font_size, opacity, angle, color=color) is not None:
                                added_visible += 1
                        except Exception:
                            continue
                if added_visible <= 0:
                    return "ERROR:no writable Word header found"

            if apply_copy_guard:
                guard_added = _add_word_copy_guard(
                    doc,
                    copy_guard_strength,
                    secrets.token_hex(16),
                )
                guard_added += _add_word_copy_guard_to_shapes(
                    doc,
                    copy_guard_strength,
                    secrets.token_hex(16),
                )
                if guard_added > 0:
                    _mark_word_copy_guard(doc)
                elif not apply_visible_watermark:
                    return "SKIP:copy guard not applicable: no writable Word paragraphs"

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
