"""Format conversion task adapters for Fengxi Toolbox."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

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
