"""File-level resume helpers for Fengxi Toolbox tasks."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path
from typing import Callable, Iterable


def is_nonempty_file(path_value) -> bool:
    try:
        path = Path(path_value)
        return path.is_file() and path.stat().st_size > 0
    except Exception:
        return False


def is_valid_zip(path_value) -> bool:
    try:
        path = Path(path_value)
        return is_nonempty_file(path) and zipfile.is_zipfile(path)
    except Exception:
        return False


def outputs_are_complete(paths: Iterable, validator: Callable[[object], bool] | None = None) -> bool:
    items = [item for item in paths if item]
    if not items:
        return False
    check = validator or is_nonempty_file
    return all(check(item) for item in items)


def split_completed_jobs(
    jobs: Iterable,
    *,
    output_getter: Callable[[object], object],
    validator: Callable[[object], bool] | None = None,
):
    pending = []
    completed = []
    check = validator or is_nonempty_file
    for job in jobs:
        try:
            output = output_getter(job)
        except Exception:
            output = None
        if output and check(output):
            completed.append(job)
        else:
            pending.append(job)
    return pending, completed


def format_resume_skip_message(label: str, source, output) -> str:
    source_name = os.path.basename(str(source or "")) or str(source or "")
    return f"[{label}] resume skip existing output: {source_name} -> {output}"
