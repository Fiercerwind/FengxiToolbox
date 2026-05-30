"""Task-level OCR PDF orchestration for Fengxi Toolbox."""

from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from tools.fx_pdf_ocr import FengxiPdfOcrEngine, write_pdf_ocr_comparison_report


@dataclass
class PdfOcrTaskOptions:
    model_root: Any
    profile_key: str
    backend_key: str
    extraction_mode: str = "mixed"
    cls: bool = False
    compare_report: bool = False
    password: str = ""
    limit_side_len: int = 2880
    cpu_threads: int = 4
    preprocess_mode: str = "auto"
    layered: bool = True


@dataclass
class PdfOcrTaskCallbacks:
    log: Callable[[str], None] | None = None
    stop_requested: Callable[[], bool] | None = None
    on_engine_ready: Callable[[str], None] | None = None
    on_file_started: Callable[[str, str, int, int], None] | None = None
    on_page_progress: Callable[[str, int, int, int, int], None] | None = None
    on_page_preview: Callable[[str, int, int, dict[str, Any]], None] | None = None
    on_file_finished: Callable[[str, str, dict[str, Any]], None] | None = None
    on_file_failed: Callable[[str, str, str, Exception], None] | None = None
    on_file_completed: Callable[[str, str, int, int], None] | None = None
    on_compare_report: Callable[[str, str, dict[str, Any]], None] | None = None
    on_compare_report_failed: Callable[[str, Exception], None] | None = None


def _call(callback, *args):
    if not callable(callback):
        return None
    try:
        return callback(*args)
    except Exception:
        return None


def _stop_requested(callbacks: PdfOcrTaskCallbacks | None) -> bool:
    if callbacks is None or not callable(callbacks.stop_requested):
        return False
    try:
        return bool(callbacks.stop_requested())
    except Exception:
        return False


def build_pdf_ocr_output_path(src, input_root, output_folder):
    rel = os.path.relpath(str(src), str(input_root))
    return os.path.join(str(output_folder), rel)


def build_pdf_ocr_compare_report_path(src, output_folder):
    report_dir = Path(output_folder) / "_ocr_compare_reports"
    return str(report_dir / f"{Path(src).stem}.ocr_compare.md")


def _run_compare_report(src, report_path, options: PdfOcrTaskOptions):
    return write_pdf_ocr_comparison_report(
        src=src,
        report_path=report_path,
        profile_key=options.profile_key,
        model_root=options.model_root,
        cls=options.cls,
        password=options.password,
        page_index=0,
        cpu_threads=options.cpu_threads,
        limit_side_len=options.limit_side_len,
        preprocess_mode=options.preprocess_mode,
    )


def run_pdf_ocr_task_core(
    pdf_files,
    input_root,
    output_folder,
    options: PdfOcrTaskOptions,
    callbacks: PdfOcrTaskCallbacks | None = None,
):
    """Run OCR for already-collected PDF files and return task-level facts."""

    started_at = time.time()
    files = [str(path) for path in pdf_files]
    total = len(files)
    result = {
        "status": "unknown",
        "outputs": [],
        "failed_items": [],
        "processed_count": 0,
        "success_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "stopped": False,
        "duration_seconds": 0.0,
        "backend_usage": {},
        "engine_backend": "",
        "message": "",
    }
    if total <= 0:
        result.update({"status": "skipped", "skipped_count": 1, "message": "no pdf files"})
        return result

    Path(output_folder).mkdir(parents=True, exist_ok=True)
    engine = FengxiPdfOcrEngine(
        model_root=options.model_root,
        profile_key=options.profile_key,
        backend_key=options.backend_key,
        cls=options.cls,
        limit_side_len=options.limit_side_len,
        cpu_threads=max(1, int(options.cpu_threads or 1)),
        preprocess_mode=options.preprocess_mode,
    )
    result["engine_backend"] = engine.backend_key
    _call(callbacks.on_engine_ready if callbacks else None, engine.backend_key)

    try:
        for zero_index, src in enumerate(files):
            if _stop_requested(callbacks):
                result["stopped"] = True
                result["status"] = "stopped"
                result["message"] = "stopped by user"
                break

            rel = os.path.relpath(src, str(input_root))
            dst = build_pdf_ocr_output_path(src, input_root, output_folder)
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            _call(callbacks.on_file_started if callbacks else None, src, dst, zero_index, total)

            should_count_completion = True
            try:
                if options.compare_report:
                    report_path = build_pdf_ocr_compare_report_path(src, output_folder)
                    try:
                        report_result = _run_compare_report(src, report_path, options)
                    except Exception as report_exc:
                        _call(callbacks.on_compare_report_failed if callbacks else None, src, report_exc)
                    else:
                        _call(callbacks.on_compare_report if callbacks else None, src, report_path, report_result)

                def _page_progress(page_done, total_pages, page_payload=None):
                    _call(callbacks.on_page_progress if callbacks else None, src, zero_index, total, page_done, total_pages)
                    if page_payload:
                        _call(callbacks.on_page_preview if callbacks else None, src, page_done, total_pages, page_payload)

                ocr_result = engine.ocr_pdf_to_searchable_pdf(
                    src,
                    dst,
                    extraction_mode=options.extraction_mode,
                    password=options.password,
                    layered=options.layered,
                    progress_callback=_page_progress,
                    stop_checker=lambda: _stop_requested(callbacks),
                )
            except KeyboardInterrupt:
                should_count_completion = False
                result["stopped"] = True
                result["status"] = "stopped"
                result["message"] = "stopped by user"
                break
            except Exception as exc:
                result["failed_items"].append(rel)
                result["failed_count"] += 1
                try:
                    shutil.copy2(src, dst)
                except Exception:
                    pass
                _call(callbacks.on_file_failed if callbacks else None, src, dst, rel, exc)
            else:
                result["success_count"] += 1
                result["outputs"].append(dst)
                for key, value in dict(ocr_result.get("backend_usage") or {}).items():
                    result["backend_usage"][key] = result["backend_usage"].get(key, 0) + value
                _call(callbacks.on_file_finished if callbacks else None, src, dst, ocr_result)
            finally:
                if should_count_completion:
                    result["processed_count"] += 1
                    _call(callbacks.on_file_completed if callbacks else None, src, dst, zero_index, total)
    finally:
        result["engine_backend"] = getattr(engine, "backend_key", result.get("engine_backend", ""))
        try:
            engine.close()
        finally:
            result["duration_seconds"] = round(time.time() - started_at, 4)

    if result["status"] == "unknown":
        if result["failed_count"]:
            result["status"] = "failed"
            result["message"] = f"{result['failed_count']} pdf files failed"
        elif result["stopped"]:
            result["status"] = "stopped"
            result["message"] = "stopped by user"
        else:
            result["status"] = "success"
            result["message"] = f"{result['success_count']} pdf files processed"
    return result
