from __future__ import annotations

import json
import os
import time
from pathlib import Path


DEFAULT_MAX_ENTRIES = 240


def _coerce_log_path(log_path):
    return Path(log_path).expanduser().resolve()


class FxPerformanceRecorder:
    """Tiny JSONL recorder for startup and UI latency samples."""

    def __init__(self, log_path, app_version="", max_entries=DEFAULT_MAX_ENTRIES):
        self.log_path = _coerce_log_path(log_path)
        self.app_version = str(app_version or "")
        self.max_entries = max(20, int(max_entries or DEFAULT_MAX_ENTRIES))

    @staticmethod
    def now():
        return time.perf_counter()

    def record(self, event, started_at=None, task_name="", details=None):
        elapsed_ms = None
        if started_at is not None:
            elapsed_ms = round(max(0.0, time.perf_counter() - float(started_at)) * 1000.0, 3)
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": str(event or ""),
            "task_name": str(task_name or ""),
            "elapsed_ms": elapsed_ms,
            "details": details if isinstance(details, dict) else {},
            "app_version": self.app_version,
            "pid": os.getpid(),
        }
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.prune()
        return entry

    def prune(self):
        entries = load_performance_entries(self.log_path)
        if len(entries) <= self.max_entries:
            return len(entries)
        kept = entries[-self.max_entries :]
        with self.log_path.open("w", encoding="utf-8") as handle:
            for entry in kept:
                handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")
        return len(kept)


def load_performance_entries(log_path):
    path = _coerce_log_path(log_path)
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            entries.append(payload)
    return entries
