"""Task-level orchestration for standalone PDF page rotation normalization."""

from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from tools.fx_pdf_rotation import normalize_pdf_page_rotation
from tools.fx_resume import is_nonempty_file


@dataclass
class PdfRotationTaskOptions:
    password: str = ""
    delete_source: bool = False


@dataclass
class PdfRotationTaskCallbacks:
    stop_requested: Callable[[], bool] | None = None
    on_file_started: Callable[[str, str, int, int], None] | None = None
    on_file_finished: Callable[[str, str, dict[str, Any]], None] | None = None
    on_file_failed: Callable[[str, str, str, Exception], None] | None = None
    on_file_completed: Callable[[str, str, int, int], None] | None = None


def _call(callback, *args):
    if not callable(callback):
        return None
    try:
        return callback(*args)
    except Exception:
        return None


def _stop_requested(callbacks):
    if callbacks is None or not callable(callbacks.stop_requested):
        return False
    try:
        return bool(callbacks.stop_requested())
    except Exception:
        return False


def build_pdf_rotation_output_path(src, input_root, output_folder):
    rel = os.path.relpath(str(src), str(input_root))
    return os.path.join(str(output_folder), rel)


def run_pdf_rotation_task_core(
    pdf_files,
    input_root,
    output_folder,
    options: PdfRotationTaskOptions | None = None,
    callbacks: PdfRotationTaskCallbacks | None = None,
):
    options = options or PdfRotationTaskOptions()
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
        "changed_pages": 0,
        "message": "",
    }
    if total <= 0:
        result.update({"status": "skipped", "skipped_count": 1, "message": "no pdf files"})
        return result

    Path(output_folder).mkdir(parents=True, exist_ok=True)
    for zero_index, src in enumerate(files):
        dst = build_pdf_rotation_output_path(src, input_root, output_folder)
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        rel = os.path.relpath(src, str(input_root))
        _call(callbacks.on_file_started if callbacks else None, src, dst, zero_index, total)
        should_count_completion = True
        try:
            if _stop_requested(callbacks):
                should_count_completion = False
                result["stopped"] = True
                result["status"] = "stopped"
                result["message"] = "stopped by user"
                break

            resumed = is_nonempty_file(dst)
            if not resumed:
                shutil.copy2(src, dst)
            try:
                rotation_result = normalize_pdf_page_rotation(dst, password=options.password)
            except Exception:
                if resumed:
                    shutil.copy2(src, dst)
                    rotation_result = normalize_pdf_page_rotation(dst, password=options.password)
                else:
                    raise
            result["outputs"].append(dst)
            result["success_count"] += 1
            if resumed:
                result["skipped_count"] += 1
            result["changed_pages"] += int(rotation_result.get("changed_pages") or 0)
            if options.delete_source and not resumed:
                os.remove(src)
            _call(
                callbacks.on_file_finished if callbacks else None,
                src,
                dst,
                {"resumed": resumed, "rotation_normalization": rotation_result},
            )
        except Exception as exc:
            result["failed_items"].append(rel)
            result["failed_count"] += 1
            _call(callbacks.on_file_failed if callbacks else None, src, dst, rel, exc)
        finally:
            if should_count_completion:
                result["processed_count"] += 1
                _call(callbacks.on_file_completed if callbacks else None, src, dst, zero_index, total)

    if result["failed_count"]:
        result["status"] = "failed"
        result["message"] = f"{result['failed_count']} pdf files failed"
    elif result["stopped"]:
        result["status"] = "stopped"
        result["message"] = "stopped by user"
    else:
        result["status"] = "success"
        result["message"] = f"{result['success_count']} pdf files normalized"
    result["duration_seconds"] = round(time.time() - started_at, 4)
    return result
