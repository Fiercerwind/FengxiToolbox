"""Image to PDF task orchestration for Fengxi Toolbox."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from PIL import Image as PILImage


IMAGE_TO_PDF_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


@dataclass
class ImagePdfTaskOptions:
    merge: bool = False
    delete_source: bool = False
    parallel_workers: int = 1
    input_name: str = "images"
    executor_factory: Callable[..., Any] | None = None
    image_to_pdf: Callable[[str, str], str] | None = None
    merge_images_to_pdf: Callable[[list[str], str], str] | None = None


@dataclass
class ImagePdfTaskCallbacks:
    log: Callable[[str], None] | None = None
    stop_requested: Callable[[], bool] | None = None
    on_item_started: Callable[[str, str, int, int], None] | None = None
    on_item_finished: Callable[[str, str, dict[str, Any]], None] | None = None
    on_item_failed: Callable[[str, str, str], None] | None = None
    on_item_completed: Callable[[int], None] | None = None
    on_merge_started: Callable[[str, int], None] | None = None


def _call(callback, *args):
    if not callable(callback):
        return None
    try:
        return callback(*args)
    except Exception:
        return None


def _log(callbacks: ImagePdfTaskCallbacks | None, message: str) -> None:
    if callbacks is not None:
        _call(callbacks.log, message)


def _stop_requested(callbacks: ImagePdfTaskCallbacks | None) -> bool:
    if callbacks is None or not callable(callbacks.stop_requested):
        return False
    try:
        return bool(callbacks.stop_requested())
    except Exception:
        return False


def collect_image_to_pdf_files(input_value, collect_input_files=None, valid_exts=None):
    normalized_input = str(input_value or "").strip()
    if not normalized_input:
        return []
    valid = set(valid_exts or IMAGE_TO_PDF_EXTS)
    if os.path.isfile(normalized_input):
        suffix = Path(normalized_input).suffix.lower()
        return [normalized_input] if suffix in valid else []

    files = []
    if callable(collect_input_files):
        try:
            files = list(collect_input_files(normalized_input, "image") or [])
        except Exception:
            files = []
    elif os.path.isdir(normalized_input):
        for current, _dirs, names in os.walk(normalized_input):
            for name in names:
                files.append(str(Path(current) / name))

    image_files = [str(path) for path in files if Path(str(path)).suffix.lower() in valid]
    return sorted(image_files, key=lambda item: os.path.basename(str(item)).lower())


def build_image_pdf_output_path(src, output_folder):
    source = Path(src)
    candidate = Path(output_folder) / f"{source.stem}.pdf"
    counter = 2
    while candidate.exists():
        candidate = Path(output_folder) / f"{source.stem}_{counter}.pdf"
        counter += 1
    return str(candidate)


def build_image_merge_pdf_output_path(input_root, normalized_input, output_folder):
    output_name = f"{Path(input_root or normalized_input).name or 'images'}_图集合并.pdf"
    return str(Path(output_folder) / output_name)


def image_file_to_pdf(src, dst):
    image = PILImage.open(src)
    try:
        if image.mode in {"RGBA", "LA"}:
            background = PILImage.new("RGB", image.size, (255, 255, 255))
            alpha = image.getchannel("A") if "A" in image.getbands() else None
            background.paste(image.convert("RGBA"), mask=alpha)
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        image.save(dst, "PDF", resolution=100.0)
    finally:
        try:
            image.close()
        except Exception:
            pass
    if not os.path.exists(dst) or os.path.getsize(dst) <= 0:
        return "ERROR:PDF 输出文件未生成"
    return "SUCCESS"


def _reserve_unique_output_path(src, output_folder, reserved):
    target = Path(build_image_pdf_output_path(src, output_folder))
    target_dir = target.parent
    stem = target.stem
    suffix = target.suffix
    counter = 2
    normalized = os.path.normcase(str(target))
    while normalized in reserved:
        target = target_dir / f"{stem}_{counter}{suffix}"
        normalized = os.path.normcase(str(target))
        counter += 1
    reserved.add(normalized)
    return str(target)


def _delete_source(src, failed_items):
    try:
        os.remove(src)
        return True
    except Exception as exc:
        failed_items.append(f"{src}: 删除源文件失败: {exc}")
        return False


def _process_one_image_pdf(job, image_to_pdf_func):
    src, dst = job
    status = image_to_pdf_func(src, dst)
    return {"src": src, "dst": dst, "ok": status == "SUCCESS", "status": status}


def _finish_result(result, started_at):
    result["duration_seconds"] = round(time.time() - started_at, 4)
    if result["status"] != "unknown":
        return result
    if result["failed_count"]:
        result["status"] = "failed"
        result["message"] = f"{result['failed_count']} image pdf item(s) failed"
    elif result["stopped"]:
        result["status"] = "stopped"
        result["message"] = "stopped by user"
    else:
        result["status"] = "success"
        result["message"] = f"{result['success_count']} image item(s) processed"
    return result


def run_image_pdf_task_core(
    image_files,
    input_root,
    normalized_input,
    output_folder,
    options: ImagePdfTaskOptions | None = None,
    callbacks: ImagePdfTaskCallbacks | None = None,
):
    started_at = time.time()
    options = options or ImagePdfTaskOptions()
    files = [str(path) for path in image_files]
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
        "message": "",
    }
    if total <= 0:
        result.update({"status": "skipped", "skipped_count": 1, "message": "no image files"})
        return _finish_result(result, started_at)

    Path(output_folder).mkdir(parents=True, exist_ok=True)
    if options.merge:
        merge_func = options.merge_images_to_pdf
        if not callable(merge_func):
            raise ValueError("merge_images_to_pdf callback is required for merge mode")
        dst = build_image_merge_pdf_output_path(input_root, normalized_input, output_folder)
        _call(callbacks.on_merge_started if callbacks else None, dst, total)
        status = merge_func(files, dst)
        result["processed_count"] = total
        if status != "SUCCESS" or not os.path.exists(dst):
            result["failed_items"].append(f"{normalized_input}: {status}")
            result["failed_count"] = 1
            _call(callbacks.on_item_failed if callbacks else None, str(normalized_input), dst, status)
        else:
            result["success_count"] = total
            result["outputs"].append(dst)
            _call(callbacks.on_item_finished if callbacks else None, str(normalized_input), dst, {"status": status, "merge": True})
            if options.delete_source:
                for src in files:
                    _delete_source(src, result["failed_items"])
        if callbacks is not None:
            _call(callbacks.on_item_completed, total)
        result["failed_count"] = len(result["failed_items"])
        return _finish_result(result, started_at)

    image_to_pdf_func = options.image_to_pdf or image_file_to_pdf
    reserved_outputs = set()
    jobs = [(src, _reserve_unique_output_path(src, output_folder, reserved_outputs)) for src in files]
    parallel_workers = max(1, int(options.parallel_workers or 1))
    if parallel_workers > 1 and callable(options.executor_factory):
        _log(callbacks, f"🚀 [批量并行] 图片转 PDF 启用 {parallel_workers} 个线程。")
        futures = {}
        with options.executor_factory(max_workers=parallel_workers) as executor:
            for index, job in enumerate(jobs):
                if _stop_requested(callbacks):
                    result["stopped"] = True
                    _log(callbacks, "⏹️ [停止] 图片转 PDF 任务已被用户中止")
                    break
                src, dst = job
                _call(callbacks.on_item_started if callbacks else None, src, dst, index, total)
                futures[executor.submit(_process_one_image_pdf, job, image_to_pdf_func)] = job
            for future in futures:
                src, dst = futures[future]
                try:
                    item = future.result()
                except Exception as exc:
                    item = {"src": src, "dst": dst, "ok": False, "status": str(exc)}
                _record_image_pdf_item(result, item, options, callbacks)
    else:
        for index, job in enumerate(jobs):
            if _stop_requested(callbacks):
                result["stopped"] = True
                _log(callbacks, "⏹️ [停止] 图片转 PDF 任务已被用户中止")
                break
            src, dst = job
            _call(callbacks.on_item_started if callbacks else None, src, dst, index, total)
            try:
                item = _process_one_image_pdf(job, image_to_pdf_func)
            except Exception as exc:
                item = {"src": src, "dst": dst, "ok": False, "status": str(exc)}
            _record_image_pdf_item(result, item, options, callbacks)

    result["failed_count"] = len(result["failed_items"])
    return _finish_result(result, started_at)


def _record_image_pdf_item(result, item, options, callbacks):
    src = str(item.get("src", ""))
    dst = str(item.get("dst", ""))
    if not item.get("ok"):
        message = f"{src}: {item.get('status')}"
        result["failed_items"].append(message)
        _call(callbacks.on_item_failed if callbacks else None, src, dst, item.get("status", ""))
    else:
        result["success_count"] += 1
        result["outputs"].append(dst)
        _call(callbacks.on_item_finished if callbacks else None, src, dst, item)
        if options.delete_source:
            _delete_source(src, result["failed_items"])
    result["processed_count"] += 1
    _call(callbacks.on_item_completed if callbacks else None, 1)
