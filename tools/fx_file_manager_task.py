"""File manager task orchestration for Fengxi Toolbox."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from tools.fx_file_manager_core import run_file_dedup_task


@dataclass
class FileDedupTaskCallbacks:
    log: Callable[[str], None] | None = None
    stop_requested: Callable[[], bool] | None = None
    on_progress: Callable[..., None] | None = None


def run_file_dedup_task_core(
    app,
    input_folder,
    *,
    collect_input_files: Callable[[Any, str], list[str]] | None = None,
    progress_tracker=None,
    progress_bar=None,
    get_last_task_result: Callable[[Any], dict | None] | None = None,
    start_task_result: Callable[[Any, Any, str], dict] | None = None,
    set_task_result_output_strategy: Callable[[dict, str, Any], None] | None = None,
    set_task_result_output_root: Callable[[dict, Any], None] | None = None,
    add_task_result_output: Callable[[dict, Any], None] | None = None,
    set_task_result_counts: Callable[..., None] | None = None,
    set_task_result_finished: Callable[..., dict] | None = None,
    normalize_input_path: Callable[[Any], str] | None = None,
    get_task_output_strategy: Callable[[Any, str], Any] | None = None,
    clamp_progress_value: Callable[[Any], float] | None = None,
    set_progress_status: Callable[..., None] | None = None,
    log: Callable[[str], None] | None = None,
) -> dict:
    normalize_input_path = normalize_input_path or (lambda value: str(value or ""))
    normalized_input = normalize_input_path(input_folder)
    result = get_last_task_result(app) if callable(get_last_task_result) else None
    if result is None:
        if not callable(start_task_result):
            raise ValueError("start_task_result callback is required")
        result = start_task_result(app, normalized_input, "file")
    if callable(set_task_result_output_strategy):
        set_task_result_output_strategy(result, "file", get_task_output_strategy(app, "file") if callable(get_task_output_strategy) else "")
    if callable(set_task_result_output_root):
        set_task_result_output_root(result, normalized_input)

    all_files = []
    if callable(collect_input_files):
        try:
            all_files = list(collect_input_files(normalized_input, "file"))
        except Exception:
            all_files = []
    if not all_files and normalized_input and os.path.isfile(normalized_input):
        all_files = [normalized_input]

    if not all_files:
        if callable(log):
            log("⚠️ 未找到可去重的文件。")
        if callable(set_task_result_counts):
            set_task_result_counts(result, processed=0, success=0, failed=0, skipped=1)
        if callable(set_task_result_finished):
            set_task_result_finished(result, "skipped", message="未找到可去重的文件", detail="未找到可去重的文件", skipped=True)
        return result

    tracker = progress_tracker
    progress_status = {"completed": 0, "total": len(all_files)}

    def report_progress(*, completed=0, total=1, current_path="", stage="hashing", fraction=0.0):
        progress_status["completed"] = int(completed or 0)
        progress_status["total"] = max(1, int(total or 1))
        current_name = os.path.basename(str(current_path or "").rstrip("\\/")) or str(current_path or "")
        stage_label = "正在比对" if stage == "hashing" else ("已完成" if stage == "done" else str(stage or "处理中"))
        if tracker is not None:
            try:
                tracker.total_units = max(1, int(total or tracker.total_units or 1))
            except Exception:
                pass
            tracker.set_current_item(current_name, f"文件去重 · {stage_label}")
            if stage == "done":
                tracker.complete_units(1, f"文件去重 · {stage_label}")
            return
        try:
            if progress_bar is not None and callable(getattr(progress_bar, "set", None)):
                progress_bar.set(clamp_progress_value(fraction) if callable(clamp_progress_value) else fraction)
        except Exception:
            pass
        try:
            if callable(set_progress_status):
                set_progress_status(
                    app,
                    current_file=current_name,
                    stage=f"文件去重 · {stage_label}",
                    fraction=clamp_progress_value(fraction) if callable(clamp_progress_value) else fraction,
                    completed=int(completed or 0),
                    total=max(1, int(total or 1)),
                )
        except Exception:
            pass

    def log_message(message):
        if callable(log):
            try:
                log(str(message))
            except Exception:
                pass

    dedup_result = run_file_dedup_task(
        all_files,
        delete_file=os.remove,
        log=log_message,
        stop_requested=lambda: bool(getattr(app, "stop_event", False)),
        progress=report_progress,
    )

    kept = list(dedup_result.get("kept") or [])
    removed = list(dedup_result.get("removed") or [])
    failed_items = list(dedup_result.get("failed_items") or [])
    result["failed_items"] = failed_items
    if callable(add_task_result_output):
        for path in kept:
            add_task_result_output(result, path)
    if callable(set_task_result_output_root):
        set_task_result_output_root(result, os.path.dirname(kept[0]) if kept else normalized_input)
    if callable(set_task_result_counts):
        set_task_result_counts(
            result,
            processed=int(dedup_result.get("processed_count") or len(all_files)),
            success=int(dedup_result.get("kept_count") or len(kept)),
            failed=int(dedup_result.get("failed_count") or len(failed_items)),
            skipped=0,
        )

    status = str(dedup_result.get("status") or "unknown")
    if status == "success":
        log_message(f"✅ [文件去重] 完成，保留 {len(kept)} 个文件，删除 {len(removed)} 个重复文件。")
        if callable(set_task_result_finished):
            set_task_result_finished(
                result,
                "success",
                message=f"文件去重已完成，删除 {len(removed)} 个重复文件",
                detail=f"保留 {len(kept)} 个文件，删除 {len(removed)} 个重复文件",
            )
    elif status == "stopped":
        log_message("⏹️ [文件去重] 已停止。")
        if callable(set_task_result_finished):
            set_task_result_finished(
                result,
                "stopped",
                message="用户停止文件去重任务",
                detail="用户停止文件去重任务",
                stopped=True,
            )
    else:
        log_message(f"❌ [文件去重] 完成但存在失败：{len(failed_items)} 项。")
        if callable(set_task_result_finished):
            set_task_result_finished(
                result,
                "failed",
                message=f"文件去重任务结束，但有 {len(failed_items)} 个文件处理失败。",
                detail=f"失败 {len(failed_items)} 个文件",
                error=f"失败 {len(failed_items)} 个文件",
            )
    return result
