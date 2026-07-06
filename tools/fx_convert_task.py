"""Format conversion task adapters for Fengxi Toolbox."""

from __future__ import annotations

from dataclasses import dataclass
import html
from pathlib import Path
import re
import shutil
import textwrap
from typing import Any, Callable
import zipfile

from tools.fx_convert_core import collect_convert_files, normalize_convert_mode, plan_convert_output_path
from tools.fx_image_pdf_task import ImagePdfTaskCallbacks, ImagePdfTaskOptions, run_image_pdf_task_core


@dataclass
class ConvertFileContext:
    word_app: Any = None
    ppt_app: Any = None
    skip_complex: bool = False
    convert_doc_to_pdf: Callable[[Any, str, str], str] | None = None
    convert_pdf_to_word: Callable[[str, str], str] | None = None
    convert_ppt_to_pdf: Callable[[Any, str, str], str] | None = None
    convert_pdf_to_ppt: Callable[[Any, str, str], str] | None = None
    convert_txt_to_word: Callable[[str, str], str] | None = None
    convert_md_to_pdf: Callable[[str, str], str] | None = None
    convert_pdf_to_md: Callable[[str, str], str] | None = None
    check_pdf_complexity: Callable[[str], bool] | None = None
    copy_file_safe: Callable[[str, str], Any] | None = None
    log: Callable[[str], None] | None = None


@dataclass
class ConvertImgsToPdfCallbacks:
    log: Callable[[str], None] | None = None
    stop_requested: Callable[[], bool] | None = None
    on_merge_started: Callable[[str, int], None] | None = None
    on_item_finished: Callable[[str, str, dict[str, Any]], None] | None = None
    on_item_failed: Callable[[str, str, str], None] | None = None
    on_item_completed: Callable[[int], None] | None = None


def _call(callback, *args):
    if not callable(callback):
        return None
    try:
        return callback(*args)
    except Exception:
        return None


def _log(callbacks: ConvertImgsToPdfCallbacks | None, message: str) -> None:
    if callbacks is not None:
        _call(callbacks.log, message)


def _context_log(context: ConvertFileContext | None, message: str) -> None:
    if context is not None:
        _call(context.log, message)


def _read_text_file(path: str) -> str:
    data = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _docx_escape_text(value: str) -> str:
    return html.escape(str(value or ""), quote=False)


def _write_simple_docx(paragraphs: list[str], dst: str) -> None:
    dst_path = Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    body_parts = []
    for paragraph in paragraphs or [""]:
        text = _docx_escape_text(paragraph)
        preserve = ' xml:space="preserve"' if text.startswith(" ") or text.endswith(" ") else ""
        body_parts.append(f"<w:p><w:r><w:t{preserve}>{text}</w:t></w:r></w:p>")
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(body_parts)}"
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>'
        "</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    with zipfile.ZipFile(dst_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document_xml)


def convert_txt_to_word_file(src: str, dst: str) -> str:
    try:
        text = _read_text_file(src)
        _write_simple_docx(text.splitlines() or [""], dst)
        return "SUCCESS" if Path(dst).exists() and Path(dst).stat().st_size > 0 else "ERROR:no_output"
    except Exception as exc:
        return f"ERROR:{exc}"


def _strip_markdown_inline(text: str) -> str:
    value = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", str(text or ""))
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = value.replace("**", "").replace("__", "").replace("`", "")
    return value.strip()


def _resolve_reportlab_font():
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        font_path = Path(__file__).resolve().parents[1] / "SmileySans-Oblique.ttf"
        if font_path.exists():
            font_name = "FengxiSmileySans"
            if font_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
            return font_name
    except Exception:
        pass
    return "Helvetica"


def _wrap_pdf_text(text: str, width: int) -> list[str]:
    raw = str(text or "")
    if not raw:
        return [""]
    if len(raw) <= width:
        return [raw]
    lines: list[str] = []
    for chunk in raw.splitlines() or [raw]:
        if len(chunk) <= width:
            lines.append(chunk)
        else:
            lines.extend(textwrap.wrap(chunk, width=width, break_long_words=True, replace_whitespace=False))
    return lines or [raw]


def convert_md_to_pdf_file(src: str, dst: str) -> str:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        text = _read_text_file(src)
        dst_path = Path(dst)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        font_name = _resolve_reportlab_font()
        page_width, page_height = A4
        margin = 48
        y = page_height - margin
        pdf = canvas.Canvas(str(dst_path), pagesize=A4)
        in_code = False

        def ensure_space(height: float) -> None:
            nonlocal y
            if y - height < margin:
                pdf.showPage()
                y = page_height - margin

        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if not line.strip():
                y -= 10
                continue
            size = 11
            prefix = ""
            content = line
            if not in_code:
                heading = re.match(r"^(#{1,6})\s+(.*)$", line)
                bullet = re.match(r"^\s*[-*+]\s+(.*)$", line)
                ordered = re.match(r"^\s*(\d+[.)])\s+(.*)$", line)
                if heading:
                    size = max(14, 22 - len(heading.group(1)) * 2)
                    content = heading.group(2)
                elif bullet:
                    prefix = "- "
                    content = bullet.group(1)
                elif ordered:
                    prefix = f"{ordered.group(1)} "
                    content = ordered.group(2)
                content = _strip_markdown_inline(content)
            else:
                prefix = "    "
            pdf.setFont(font_name, size)
            line_height = size + 5
            max_chars = max(24, int((page_width - margin * 2) / max(size * 0.55, 1)))
            for wrapped in _wrap_pdf_text(prefix + content, max_chars):
                ensure_space(line_height)
                pdf.drawString(margin, y, wrapped)
                y -= line_height
            if size >= 16:
                y -= 4
        pdf.save()
        return "SUCCESS" if dst_path.exists() and dst_path.stat().st_size > 0 else "ERROR:no_output"
    except Exception as exc:
        return f"ERROR:{exc}"


def convert_pdf_to_md_file(src: str, dst: str) -> str:
    try:
        source = Path(src)
        dst_path = Path(dst)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        assets_dir = dst_path.with_name(f"{dst_path.stem}_assets")
        if assets_dir.exists() and assets_dir.is_dir():
            shutil.rmtree(assets_dir)
        assets_dir.mkdir(parents=True, exist_ok=True)

        markdown = ""
        try:
            import pymupdf4llm

            markdown = pymupdf4llm.to_markdown(
                str(source),
                write_images=True,
                image_path=str(assets_dir),
                image_format="png",
                page_separators=True,
                show_progress=False,
            )
            if isinstance(markdown, list):
                markdown = "\n\n".join(str(chunk.get("text", chunk)) for chunk in markdown)
            markdown = str(markdown or "")
        except Exception:
            markdown = ""

        if not markdown.strip():
            markdown = _convert_pdf_to_md_fallback(source, assets_dir)

        asset_abs = str(assets_dir.resolve()).replace("\\", "/")
        markdown = markdown.replace(asset_abs + "/", f"{assets_dir.name}/")
        markdown = markdown.replace(str(assets_dir).replace("\\", "/") + "/", f"{assets_dir.name}/")
        if not markdown.lstrip().startswith("#"):
            markdown = f"# {source.stem}\n\n{markdown.lstrip()}"
        dst_path.write_text(markdown.rstrip() + "\n", encoding="utf-8")
        try:
            if assets_dir.exists() and not any(assets_dir.iterdir()):
                assets_dir.rmdir()
        except Exception:
            pass
        return "SUCCESS" if dst_path.exists() and dst_path.stat().st_size > 0 else "ERROR:no_output"
    except Exception as exc:
        return f"ERROR:{exc}"


def _markdown_table_from_rows(rows: list[list[object]]) -> str:
    clean_rows = [["" if cell is None else str(cell).replace("\n", " ").strip() for cell in row] for row in rows if row]
    if not clean_rows:
        return ""
    column_count = max(len(row) for row in clean_rows)
    normalized = [row + [""] * (column_count - len(row)) for row in clean_rows]
    header = normalized[0]
    body = normalized[1:] or [[""] * column_count]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in range(column_count)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


def _convert_pdf_to_md_fallback(source: Path, assets_dir: Path) -> str:
    parts = [f"# {source.stem}", ""]
    try:
        import fitz

        with fitz.open(str(source)) as doc:
            for page_index, page in enumerate(doc, start=1):
                parts.extend([f"## Page {page_index}", ""])
                text = page.get_text("text").strip()
                if text:
                    parts.extend([text, ""])

                try:
                    tables = page.find_tables()
                    for table_index, table in enumerate(getattr(tables, "tables", []) or [], start=1):
                        table_md = _markdown_table_from_rows(table.extract())
                        if table_md:
                            parts.extend([f"### Table {page_index}.{table_index}", "", table_md, ""])
                except Exception:
                    pass

                image_count = 0
                for image_index, image in enumerate(page.get_images(full=True), start=1):
                    try:
                        xref = int(image[0])
                        extracted = doc.extract_image(xref)
                        ext = str(extracted.get("ext") or "png").lower()
                        if ext == "jpeg":
                            ext = "jpg"
                        image_name = f"page_{page_index:04d}_image_{image_index:02d}.{ext}"
                        image_path = assets_dir / image_name
                        image_path.write_bytes(extracted.get("image") or b"")
                        if image_path.exists() and image_path.stat().st_size > 0:
                            image_count += 1
                            parts.extend([f"![page {page_index} image {image_index}]({assets_dir.name}/{image_name})", ""])
                    except Exception:
                        continue
                if not text and image_count == 0:
                    parts.extend(["_No extractable content found._", ""])
    except Exception:
        from pypdf import PdfReader

        reader = PdfReader(str(source))
        for page_index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            parts.extend([f"## Page {page_index}", "", text or "_No extractable text found._", ""])
    return "\n".join(parts).rstrip() + "\n"


def process_convert_file(src, input_root, output_folder, mode, context: ConvertFileContext | None = None):
    context = context or ConvertFileContext()
    normalized_mode = normalize_convert_mode(mode)
    source = Path(str(src or ""))
    if not source.name:
        return {"src": str(src or ""), "output": "", "status": "failed", "ok": False, "message": "empty source"}

    suffix = source.suffix.lower()
    if normalized_mode == "imgs2pdf":
        return {"src": str(source), "output": "", "status": "skipped", "ok": True, "message": "imgs2pdf handled by task adapter"}

    if normalized_mode == "word2pdf" and suffix in {".doc", ".docx"}:
        produced_path = plan_convert_output_path(str(source), input_root, output_folder, normalized_mode)
        if context.word_app is None:
            message = "Word COM unavailable"
            _context_log(context, f"[依赖异常] Word COM 不可用，无法转换: {source.name}")
            return {"src": str(source), "output": produced_path, "status": "failed", "ok": False, "message": message}
        if not callable(context.convert_doc_to_pdf):
            return {"src": str(source), "output": produced_path, "status": "failed", "ok": False, "message": "convert_doc_to_pdf callback is required"}
        status = context.convert_doc_to_pdf(context.word_app, str(source), produced_path)
        return {"src": str(source), "output": produced_path, "status": status, "ok": status == "SUCCESS", "message": status}

    if normalized_mode == "pdf2word" and suffix == ".pdf":
        if context.skip_complex and callable(context.check_pdf_complexity) and context.check_pdf_complexity(str(source)):
            copied_path = plan_convert_output_path(str(source), input_root, output_folder, "")
            if callable(context.copy_file_safe):
                context.copy_file_safe(str(source), copied_path)
            _context_log(context, f"⚠️ [跳过] 文件过大或复杂，防止乱码: {source.name}")
            return {
                "src": str(source),
                "output": copied_path,
                "status": "skipped_complex",
                "ok": True,
                "message": "complex pdf copied",
                "skipped": True,
            }
        produced_path = plan_convert_output_path(str(source), input_root, output_folder, normalized_mode)
        if not callable(context.convert_pdf_to_word):
            return {"src": str(source), "output": produced_path, "status": "failed", "ok": False, "message": "convert_pdf_to_word callback is required"}
        status = context.convert_pdf_to_word(str(source), produced_path)
        return {"src": str(source), "output": produced_path, "status": status, "ok": status == "SUCCESS", "message": status}

    if normalized_mode == "ppt2pdf" and suffix in {".ppt", ".pptx"}:
        produced_path = plan_convert_output_path(str(source), input_root, output_folder, normalized_mode)
        if context.ppt_app is None:
            message = "PowerPoint COM unavailable"
            _context_log(context, f"[依赖异常] PowerPoint COM 不可用，无法转换: {source.name}")
            return {"src": str(source), "output": produced_path, "status": "failed", "ok": False, "message": message}
        if not callable(context.convert_ppt_to_pdf):
            return {"src": str(source), "output": produced_path, "status": "failed", "ok": False, "message": "convert_ppt_to_pdf callback is required"}
        status = context.convert_ppt_to_pdf(context.ppt_app, str(source), produced_path)
        return {"src": str(source), "output": produced_path, "status": status, "ok": status == "SUCCESS", "message": status}

    if normalized_mode == "pdf2ppt" and suffix == ".pdf":
        produced_path = plan_convert_output_path(str(source), input_root, output_folder, normalized_mode)
        if not callable(context.convert_pdf_to_ppt):
            return {"src": str(source), "output": produced_path, "status": "failed", "ok": False, "message": "convert_pdf_to_ppt callback is required"}
        status = context.convert_pdf_to_ppt(context.ppt_app, str(source), produced_path)
        return {"src": str(source), "output": produced_path, "status": status, "ok": status == "SUCCESS", "message": status}

    if normalized_mode == "txt2word" and suffix == ".txt":
        produced_path = plan_convert_output_path(str(source), input_root, output_folder, normalized_mode)
        converter = context.convert_txt_to_word if callable(context.convert_txt_to_word) else convert_txt_to_word_file
        status = converter(str(source), produced_path)
        return {"src": str(source), "output": produced_path, "status": status, "ok": status == "SUCCESS", "message": status}

    if normalized_mode == "md2pdf" and suffix in {".md", ".markdown"}:
        produced_path = plan_convert_output_path(str(source), input_root, output_folder, normalized_mode)
        converter = context.convert_md_to_pdf if callable(context.convert_md_to_pdf) else convert_md_to_pdf_file
        status = converter(str(source), produced_path)
        return {"src": str(source), "output": produced_path, "status": status, "ok": status == "SUCCESS", "message": status}

    if normalized_mode == "pdf2md" and suffix == ".pdf":
        produced_path = plan_convert_output_path(str(source), input_root, output_folder, normalized_mode)
        converter = context.convert_pdf_to_md if callable(context.convert_pdf_to_md) else convert_pdf_to_md_file
        status = converter(str(source), produced_path)
        return {"src": str(source), "output": produced_path, "status": status, "ok": status == "SUCCESS", "message": status}

    passthrough_path = plan_convert_output_path(str(source), input_root, output_folder, "")
    if callable(context.copy_file_safe):
        context.copy_file_safe(str(source), passthrough_path)
    return {
        "src": str(source),
        "output": passthrough_path,
        "status": "copied",
        "ok": True,
        "message": "not applicable",
        "copied": True,
    }


def run_convert_imgs_to_pdf_task_core(
    input_value,
    *,
    input_root,
    output_folder,
    collect_input_files=None,
    merge_images_to_pdf=None,
    callbacks: ConvertImgsToPdfCallbacks | None = None,
):
    if not callable(merge_images_to_pdf):
        raise ValueError("merge_images_to_pdf callback is required")

    image_files = collect_convert_files(input_value, "imgs2pdf", collect_input_files=collect_input_files)
    total = len(image_files)
    if total <= 0:
        return {
            "status": "skipped",
            "outputs": [],
            "failed_items": [],
            "processed_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 1,
            "message": "未找到可合并为 PDF 的图片文件",
        }

    _log(callbacks, f"🧩 [多图合并PDF] 共 {total} 张图片，正在合并...")
    image_callbacks = ImagePdfTaskCallbacks(
        log=callbacks.log if callbacks else None,
        stop_requested=callbacks.stop_requested if callbacks else None,
        on_merge_started=callbacks.on_merge_started if callbacks else None,
        on_item_finished=callbacks.on_item_finished if callbacks else None,
        on_item_failed=callbacks.on_item_failed if callbacks else None,
        on_item_completed=callbacks.on_item_completed if callbacks else None,
    )
    return run_image_pdf_task_core(
        image_files,
        input_root,
        input_value,
        output_folder,
        ImagePdfTaskOptions(merge=True, merge_images_to_pdf=merge_images_to_pdf),
        image_callbacks,
    )
