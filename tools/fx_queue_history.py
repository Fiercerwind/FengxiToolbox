from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping


@dataclass
class QueueHistoryContext:
    history_file: Callable[[], Path]
    retention_days: int
    history_limit: int
    status_labels: Mapping[str, str]
    status_label_to_value: Mapping[str, str]
    task_label_to_value: Mapping[str, str]
    failure_label_to_value: Mapping[str, str]
    classify_failure_reason: Callable[[dict], tuple[str, str]]
    task_result_snapshot: Callable[[dict], dict]
    debug: Callable[[str], None] | None = None


def _debug(context: QueueHistoryContext, message: str) -> None:
    try:
        if callable(context.debug):
            context.debug(message)
    except Exception:
        pass


def queue_status_text(status: Any, context: QueueHistoryContext) -> str:
    return context.status_labels.get(status, status or "")


def queue_history_entry_timestamp(entry: Any) -> float | None:
    if not isinstance(entry, dict):
        return None
    for key in ("finished_at", "created_at", "started_at"):
        try:
            value = entry.get(key)
            if value is not None:
                return float(value)
        except Exception:
            continue
    task_result = entry.get("task_result")
    if isinstance(task_result, dict):
        for key in ("finished_at", "started_at"):
            try:
                value = task_result.get(key)
                if value is not None:
                    return float(value)
            except Exception:
                continue
    return None


def prune_queue_history_entries(
    entries: Any,
    context: QueueHistoryContext,
    *,
    now: float | None = None,
) -> list:
    try:
        cutoff = float(now if now is not None else time.time()) - int(context.retention_days) * 86400
    except Exception:
        cutoff = time.time() - int(context.retention_days) * 86400
    kept = []
    for entry in list(entries or []):
        timestamp = queue_history_entry_timestamp(entry)
        if timestamp is not None and timestamp < cutoff:
            continue
        kept.append(entry)
    if len(kept) > int(context.history_limit):
        kept = kept[-int(context.history_limit) :]
    return kept


def load_queue_history(context: QueueHistoryContext) -> list:
    path = context.history_file()
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                pruned = prune_queue_history_entries(data, context)
                if len(pruned) != len(data):
                    save_queue_history(pruned, context)
                return pruned
    except Exception as exc:
        _debug(context, f"queue:history_load_error:{exc}")
    return []


def save_queue_history(entries: Any, context: QueueHistoryContext) -> None:
    path = context.history_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        safe_entries = prune_queue_history_entries(entries, context)
        path.write_text(json.dumps(safe_entries, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        _debug(context, f"queue:history_save_error:{exc}")


def normalize_queue_history_entry(task: Any, context: QueueHistoryContext) -> dict:
    entry = dict(task or {})
    entry.pop("status_var", None)
    entry.pop("row", None)
    entry.pop("action_button", None)
    entry.pop("index_label", None)
    entry.pop("retry_source_id", None)
    entry.pop("retry_staging_root", None)
    entry.pop("retry_mode", None)
    entry.pop("retry_failed_items", None)
    task_result = entry.get("task_result")
    if isinstance(task_result, dict):
        entry["task_result"] = context.task_result_snapshot(task_result)
    return entry


def build_queue_history_search_blob(entry: Any, context: QueueHistoryContext) -> str:
    item = dict(entry or {})
    parts = [
        item.get("title", ""),
        item.get("input", ""),
        item.get("detail", ""),
        item.get("error", ""),
        item.get("output_root", ""),
        queue_status_text(item.get("status"), context),
    ]
    task_result = item.get("task_result")
    if isinstance(task_result, dict):
        failure_kind, failure_reason = context.classify_failure_reason(item)
        parts.extend(
            [
                task_result.get("message", ""),
                task_result.get("detail", ""),
                task_result.get("error", ""),
                task_result.get("output_root", ""),
                failure_kind,
                failure_reason,
            ]
        )
        parts.extend(list(task_result.get("outputs") or []))
        parts.extend(list(task_result.get("failed_items") or []))
    return " ".join(str(item or "") for item in parts).lower()


def filter_queue_history_entries(
    entries: Any,
    context: QueueHistoryContext,
    *,
    status_filter: str = "全部状态",
    task_filter: str = "全部功能",
    failure_filter: str = "全部失败",
    keyword: str = "",
) -> list:
    status_value = context.status_label_to_value.get(str(status_filter or "").strip(), "")
    task_value = context.task_label_to_value.get(str(task_filter or "").strip(), "")
    failure_value = context.failure_label_to_value.get(str(failure_filter or "").strip(), "")
    normalized_keyword = str(keyword or "").strip().lower()
    filtered = []
    for entry in list(entries or []):
        if status_value and str(entry.get("status") or "") != status_value:
            continue
        if task_value and str(entry.get("task_type") or "") != task_value:
            continue
        if failure_value:
            failure_kind, _failure_reason = context.classify_failure_reason(entry)
            if failure_kind != failure_value:
                continue
        if normalized_keyword and normalized_keyword not in build_queue_history_search_blob(entry, context):
            continue
        filtered.append(entry)
    return filtered
