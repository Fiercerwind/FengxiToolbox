"""Format conversion planning helpers for Fengxi Toolbox.

This module keeps the convert page's pure rules together:
mode normalization, file selection, and output-path planning.
It intentionally does not execute Word/PPT/PDF conversion.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable


CONVERT_IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff")

CONVERT_MODE_SPECS = {
    "word2pdf": {
        "label": "Word 转 PDF",
        "input_exts": (".doc", ".docx"),
        "output_ext": ".pdf",
    },
    "pdf2word": {
        "label": "PDF 转 Word",
        "input_exts": (".pdf",),
        "output_ext": ".docx",
    },
    "ppt2pdf": {
        "label": "PPT 转 PDF",
        "input_exts": (".ppt", ".pptx"),
        "output_ext": ".pdf",
    },
    "pdf2ppt": {
        "label": "PDF 转 PPT",
        "input_exts": (".pdf",),
        "output_ext": ".pptx",
    },
    "txt2word": {
        "label": "TXT 转 Word",
        "input_exts": (".txt",),
        "output_ext": ".docx",
    },
    "md2pdf": {
        "label": "Markdown 转 PDF",
        "input_exts": (".md", ".markdown"),
        "output_ext": ".pdf",
    },
    "pdf2md": {
        "label": "PDF 转 Markdown",
        "input_exts": (".pdf",),
        "output_ext": ".md",
    },
    "imgs2pdf": {
        "label": "多图合并 ➔ PDF电子书",
        "input_exts": CONVERT_IMAGE_EXTS,
        "output_ext": ".pdf",
    },
}

CONVERT_MODE_ALIASES = {
    "word_to_pdf": "word2pdf",
    "word to pdf": "word2pdf",
    "pdf_to_word": "pdf2word",
    "pdf to word": "pdf2word",
    "ppt_to_pdf": "ppt2pdf",
    "ppt to pdf": "ppt2pdf",
    "pdf_to_ppt": "pdf2ppt",
    "pdf to ppt": "pdf2ppt",
    "pdf_to_powerpoint": "pdf2ppt",
    "pdf to powerpoint": "pdf2ppt",
    "txt_to_word": "txt2word",
    "txt to word": "txt2word",
    "text_to_word": "txt2word",
    "text to word": "txt2word",
    "md_to_pdf": "md2pdf",
    "md to pdf": "md2pdf",
    "markdown_to_pdf": "md2pdf",
    "markdown to pdf": "md2pdf",
    "pdf_to_md": "pdf2md",
    "pdf to md": "pdf2md",
    "pdf_to_markdown": "pdf2md",
    "pdf to markdown": "pdf2md",
    "images_to_pdf": "imgs2pdf",
    "image_to_pdf": "imgs2pdf",
    "image to pdf": "imgs2pdf",
    "imgs_to_pdf": "imgs2pdf",
    "imgs to pdf": "imgs2pdf",
}


def normalize_convert_mode(mode: object, default: str = "word2pdf") -> str:
    raw = str(mode or "").strip().lower()
    if not raw:
        return default
    compact = raw.replace("-", "_").replace("/", "_")
    if compact in CONVERT_MODE_SPECS:
        return compact
    if compact in CONVERT_MODE_ALIASES:
        return CONVERT_MODE_ALIASES[compact]
    spaced = compact.replace("_", " ")
    if spaced in CONVERT_MODE_ALIASES:
        return CONVERT_MODE_ALIASES[spaced]
    return default if default in CONVERT_MODE_SPECS else "word2pdf"


def get_convert_mode_label(mode: object, fallback: str = "") -> str:
    normalized = normalize_convert_mode(mode)
    spec = CONVERT_MODE_SPECS.get(normalized, {})
    return str(spec.get("label") or fallback or normalized)


def get_convert_mode_exts(mode: object) -> tuple[str, ...]:
    normalized = normalize_convert_mode(mode)
    spec = CONVERT_MODE_SPECS.get(normalized, {})
    return tuple(spec.get("input_exts") or ())


def get_convert_mode_output_ext(mode: object) -> str:
    normalized = normalize_convert_mode(mode)
    spec = CONVERT_MODE_SPECS.get(normalized, {})
    return str(spec.get("output_ext") or "")


def _walk_sorted_files(root: str) -> list[str]:
    files: list[str] = []
    for current, dirs, names in os.walk(root):
        dirs.sort(key=str.lower)
        for name in sorted(names, key=str.lower):
            files.append(str(Path(current) / name))
    return files


def _filter_convert_files(paths, mode: str) -> list[str]:
    valid_exts = {ext.lower() for ext in get_convert_mode_exts(mode)}
    filtered: list[str] = []
    for raw in paths or []:
        path = str(raw or "").strip()
        if not path:
            continue
        suffix = Path(path).suffix.lower()
        if suffix in valid_exts:
            filtered.append(path)
    return filtered


def collect_convert_files(input_value, mode, collect_input_files: Callable[[str, str], list[str]] | None = None):
    normalized_input = str(input_value or "").strip()
    if not normalized_input:
        return []

    normalized_mode = normalize_convert_mode(mode)
    if os.path.isfile(normalized_input):
        return [normalized_input] if Path(normalized_input).suffix.lower() in get_convert_mode_exts(normalized_mode) else []

    if not os.path.isdir(normalized_input):
        return []

    candidates: list[str] = []
    if callable(collect_input_files):
        for task_key in ("convert", "image"):
            if normalized_mode != "imgs2pdf" and task_key == "image":
                continue
            try:
                candidates = list(collect_input_files(normalized_input, task_key) or [])
            except Exception:
                candidates = []
            if candidates:
                break
    if not candidates:
        candidates = _walk_sorted_files(normalized_input)

    filtered = _filter_convert_files(candidates, normalized_mode)
    if normalized_mode == "imgs2pdf":
        return sorted(filtered, key=lambda item: (os.path.basename(item).lower(), item.lower()))
    return filtered


def plan_convert_output_path(src, input_root, output_folder, mode):
    source = Path(str(src or ""))
    normalized_mode = normalize_convert_mode(mode)
    if normalized_mode == "imgs2pdf":
        base_name = Path(str(input_root or source.parent)).name or "images"
        return str(Path(output_folder) / f"{base_name}_图集合并.pdf")

    root = str(input_root or "")
    try:
        rel = os.path.relpath(str(source), root) if root else source.name
    except Exception:
        rel = source.name
    if rel.startswith(".."):
        rel = source.name
    dst = Path(output_folder) / rel
    output_ext = get_convert_mode_output_ext(normalized_mode)
    if output_ext:
        dst = dst.with_suffix(output_ext)
    return str(dst)


def describe_convert_mode(mode, fallback=""):
    return get_convert_mode_label(mode, fallback=fallback)
