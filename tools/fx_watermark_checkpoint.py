"""Persistent checkpoints for batch watermark jobs."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path


CHECKPOINT_VERSION = 1
CHECKPOINT_FILENAME = ".fx_watermark_resume.jsonl"


def normalize_path_key(value) -> str:
    try:
        return os.path.normcase(os.path.abspath(os.path.normpath(str(value))))
    except Exception:
        return os.path.normcase(str(value or ""))


def file_signature(path_value) -> dict:
    try:
        stat = Path(path_value).stat()
        return {"size": int(stat.st_size), "mtime_ns": int(stat.st_mtime_ns)}
    except Exception:
        return {}


def build_checkpoint_identity(input_value, actual_strategy, settings) -> str:
    safe_settings = {
        str(key): value
        for key, value in dict(settings or {}).items()
        if not str(key).startswith("_")
    }
    payload = {
        "version": CHECKPOINT_VERSION,
        "input": normalize_path_key(input_value),
        "strategy": str(actual_strategy or ""),
        "settings": safe_settings,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_checkpoint_path(input_value, output_root) -> Path:
    base = Path(output_root or Path(input_value).parent)
    return base / CHECKPOINT_FILENAME


def _empty_checkpoint() -> dict:
    return {"header": None, "state": "", "items": {}}


def load_checkpoint(path_value) -> dict:
    checkpoint = _empty_checkpoint()
    path = Path(path_value)
    try:
        with path.open("r", encoding="utf-8") as stream:
            for raw_line in stream:
                try:
                    event = json.loads(raw_line)
                except Exception:
                    continue
                if not isinstance(event, dict):
                    continue
                event_type = str(event.get("type") or "")
                if event_type == "header":
                    checkpoint["header"] = event
                    checkpoint["state"] = ""
                    checkpoint["items"] = {}
                elif event_type == "item":
                    source_key = str(event.get("source_key") or "")
                    if source_key:
                        checkpoint["items"][source_key] = event
                elif event_type == "state":
                    checkpoint["state"] = str(event.get("state") or "")
    except Exception:
        return _empty_checkpoint()
    return checkpoint


def _append_event(path_value, event, *, sync=False) -> bool:
    path = Path(path_value)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=True, separators=(",", ":")) + "\n")
            stream.flush()
            if sync:
                os.fsync(stream.fileno())
        return True
    except Exception:
        return False


def prepare_checkpoint(path_value, input_value, actual_strategy, identity, total) -> dict:
    path = Path(path_value)
    checkpoint = load_checkpoint(path)
    header = checkpoint.get("header") or {}
    previous_state = str(checkpoint.get("state") or "")
    same_plan = (
        str(header.get("identity") or "") == str(identity or "")
        and int(header.get("version") or 0) == CHECKPOINT_VERSION
    )
    if not same_plan:
        header = {
            "type": "header",
            "version": CHECKPOINT_VERSION,
            "identity": str(identity or ""),
            "input": normalize_path_key(input_value),
            "strategy": str(actual_strategy or ""),
            "created_at": time.time(),
            "total": max(0, int(total or 0)),
        }
        _append_event(path, header, sync=True)
        checkpoint = _empty_checkpoint()
        checkpoint["header"] = header
        previous_state = ""
    checkpoint["previous_state"] = previous_state
    checkpoint["state"] = "running"
    _append_event(
        path,
        {"type": "state", "state": "running", "updated_at": time.time()},
    )
    return checkpoint


def mark_item(path_value, source, output, status) -> bool:
    source_key = normalize_path_key(source)
    if not source_key:
        return False
    output_path = str(output or "")
    output_signature = file_signature(output_path) if output_path else {}
    event = {
        "type": "item",
        "source_key": source_key,
        "source": str(source),
        "source_signature": file_signature(source),
        "output": output_path,
        "output_signature": output_signature,
        "status": str(status or ""),
        "updated_at": time.time(),
    }
    return _append_event(path_value, event)


def mark_state(path_value, state, processed=0, total=0, message="") -> bool:
    return _append_event(
        path_value,
        {
            "type": "state",
            "state": str(state or ""),
            "processed": max(0, int(processed or 0)),
            "total": max(0, int(total or 0)),
            "message": str(message or ""),
            "updated_at": time.time(),
        },
        sync=str(state or "") in {"paused", "completed", "failed", "interrupted"},
    )


def clear_checkpoint(path_value) -> bool:
    try:
        path = Path(path_value)
        if path.exists():
            path.unlink()
        return True
    except Exception:
        return False


def checkpoint_item_reusable(checkpoint, source, output) -> bool:
    source_key = normalize_path_key(source)
    entry = (checkpoint or {}).get("items", {}).get(source_key)
    if not isinstance(entry, dict):
        return False
    if str(entry.get("status") or "") not in {"success", "skipped"}:
        return False
    if normalize_path_key(source) == normalize_path_key(output):
        return False
    if normalize_path_key(entry.get("output")) != normalize_path_key(output):
        return False
    if file_signature(source) != dict(entry.get("source_signature") or {}):
        return False
    current_output_signature = file_signature(output)
    if not current_output_signature or int(current_output_signature.get("size") or 0) <= 0:
        return False
    recorded_output_signature = dict(entry.get("output_signature") or {})
    if recorded_output_signature and current_output_signature != recorded_output_signature:
        return False
    return True


def split_resumable_files(files, checkpoint, output_getter):
    pending = []
    resumed = []
    for source in list(files or []):
        try:
            output = output_getter(source)
        except Exception:
            output = ""
        if output and checkpoint_item_reusable(checkpoint, source, output):
            resumed.append({"source": str(source), "output": str(output)})
        else:
            pending.append(source)
    return pending, resumed


__all__ = [
    "CHECKPOINT_FILENAME",
    "CHECKPOINT_VERSION",
    "build_checkpoint_identity",
    "build_checkpoint_path",
    "checkpoint_item_reusable",
    "clear_checkpoint",
    "file_signature",
    "load_checkpoint",
    "mark_item",
    "mark_state",
    "normalize_path_key",
    "prepare_checkpoint",
    "split_resumable_files",
]
