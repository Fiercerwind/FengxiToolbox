"""File manager helpers for Fengxi Toolbox."""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Callable


FILE_RENAME_TYPES = {"add", "replace", "cut", "cut_range"}


class FileRenameSpec:
    def __init__(
        self,
        rename_type: str = "add",
        prefix: str = "",
        suffix: str = "",
        find_text: str = "",
        replace_text: str = "",
        cut_head: int = 0,
        cut_tail: int = 0,
        range_start: int = 1,
        range_end: int = 0,
    ):
        self.rename_type = rename_type
        self.prefix = prefix
        self.suffix = suffix
        self.find_text = find_text
        self.replace_text = replace_text
        self.cut_head = cut_head
        self.cut_tail = cut_tail
        self.range_start = range_start
        self.range_end = range_end


def _safe_int(value, default=0):
    try:
        return max(0, int(str(value).strip() or default))
    except Exception:
        return max(0, int(default or 0))


def normalize_file_rename_spec(args) -> FileRenameSpec:
    values = list(args or [])
    rename_type = str(values[1] if len(values) > 1 else "add" or "add").strip().lower() or "add"
    range_start_value = values[2] if len(values) > 2 else 1
    range_end_value = values[3] if len(values) > 3 else 0
    # The legacy task runner only emits "cut". The UI wrapper encodes the
    # new range operation into its first value so old task paths stay usable.
    if rename_type == "cut" and str(range_start_value).strip().lower().startswith("range:"):
        rename_type = "cut_range"
        range_start_value = str(range_start_value).strip().split(":", 1)[1]
    if rename_type not in FILE_RENAME_TYPES:
        rename_type = "add"
    return FileRenameSpec(
        rename_type=rename_type,
        prefix=str(values[2] if len(values) > 2 else "" or ""),
        suffix=str(values[3] if len(values) > 3 else "" or ""),
        find_text=str(values[2] if len(values) > 2 else "" or ""),
        replace_text=str(values[3] if len(values) > 3 else "" or ""),
        cut_head=_safe_int(values[2] if len(values) > 2 else 0),
        cut_tail=_safe_int(values[3] if len(values) > 3 else 0),
        range_start=max(1, _safe_int(range_start_value, 1)),
        range_end=_safe_int(range_end_value, 0),
    )


def rename_file_name(filename, spec: FileRenameSpec) -> str:
    stem, suffix = os.path.splitext(str(filename or ""))
    rename_type = str(spec.rename_type or "add").strip().lower() or "add"
    if rename_type == "replace":
        if spec.find_text:
            stem = stem.replace(spec.find_text, spec.replace_text)
    elif rename_type == "cut":
        head = max(0, int(spec.cut_head or 0))
        tail = max(0, int(spec.cut_tail or 0))
        if head:
            stem = stem[head:]
        if tail:
            stem = stem[:-tail] if tail < len(stem) else ""
    elif rename_type == "cut_range":
        start = max(1, int(spec.range_start or 1))
        end = int(spec.range_end or 0)
        if end <= 0:
            end = len(stem)
        if start <= len(stem) and end >= start:
            stem = stem[: start - 1] + stem[min(end, len(stem)) :]
    else:
        stem = f"{spec.prefix or ''}{stem}{spec.suffix or ''}"
    stem = stem.strip()
    return f"{stem}{suffix}" if stem else suffix.lstrip(".")


def plan_renamed_output_path(src, output_folder, spec: FileRenameSpec) -> str:
    source = Path(src)
    return str(Path(output_folder) / rename_file_name(source.name, spec))


def _unique_renamed_output_path(path: Path) -> Path:
    """Avoid overwriting another source when a rename rule produces a collision."""

    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    index = 2
    while True:
        candidate = path.with_name(f"{stem} ({index}){suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def apply_rename_to_file(
    src,
    input_folder,
    output_folder,
    args,
    *,
    copy_file_safe: Callable[[str, str], None],
    log: Callable[[str], None] | None = None,
):
    spec = normalize_file_rename_spec(args)
    source_path = Path(src)
    dst = _unique_renamed_output_path(Path(plan_renamed_output_path(src, output_folder, spec)))
    dst.parent.mkdir(parents=True, exist_ok=True)
    copy_file_safe(str(source_path), str(dst))
    if callable(log):
        try:
            log(f"[文件管家] 重命名完成: {source_path.name} -> {dst.name}")
        except Exception:
            pass
    return {
        "src": str(source_path),
        "dst": str(dst),
        "output": str(dst),
        "status": "success",
        "ok": True,
        "message": "SUCCESS",
    }


def md5_of_file(path, chunk_size=1024 * 1024):
    digest = hashlib.md5()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def deduplicate_files(
    paths,
    *,
    delete_file: Callable[[str], None] | None = None,
    log: Callable[[str], None] | None = None,
    stop_requested: Callable[[], bool] | None = None,
    progress: Callable[..., None] | None = None,
):
    seen = {}
    kept = []
    removed = []
    failed = []
    stopped = False
    file_paths = [str(path or "") for path in (paths or []) if str(path or "")]
    total = len(file_paths)
    for index, path in enumerate(file_paths, start=1):
        if callable(stop_requested):
            try:
                if stop_requested():
                    stopped = True
                    break
            except Exception:
                pass
        _emit_file_progress(progress, index - 1, total, path, "hashing")
        normalized = str(path or "")
        if not normalized or not os.path.isfile(normalized):
            continue
        try:
            signature = md5_of_file(normalized)
            if signature in seen:
                if callable(delete_file):
                    delete_file(normalized)
                removed.append(normalized)
                if callable(log):
                    try:
                        log(f"[文件去重] 删除重复文件: {os.path.basename(normalized)}")
                    except Exception:
                        pass
                continue
            seen[signature] = os.path.basename(normalized)
            kept.append(normalized)
        except Exception as exc:
            failed.append(f"{normalized}: {exc}")
            if callable(log):
                try:
                    log(f"[文件去重] 处理失败: {os.path.basename(normalized)}: {exc}")
                except Exception:
                    pass
        finally:
            _emit_file_progress(progress, index, total, path, "done")
    return {
        "kept": kept,
        "removed": removed,
        "kept_count": len(kept),
        "removed_count": len(removed),
        "failed_items": failed,
        "failed_count": len(failed),
        "processed_count": len(kept) + len(removed) + len(failed),
        "status": "stopped" if stopped else ("failed" if failed else "success"),
        "stopped": stopped,
    }


def _emit_file_progress(progress, completed, total, current_path="", stage="processing"):
    if not callable(progress):
        return
    try:
        fraction = completed / max(1, total)
        progress(
            completed=completed,
            total=total,
            current_path=str(current_path or ""),
            stage=stage,
            fraction=max(0.0, min(1.0, float(fraction))),
        )
    except TypeError:
        try:
            progress(completed, total, str(current_path or ""), stage)
        except Exception:
            pass
    except Exception:
        pass


def run_file_dedup_task(
    paths,
    *,
    delete_file: Callable[[str], None] | None = None,
    log: Callable[[str], None] | None = None,
    stop_requested: Callable[[], bool] | None = None,
    progress: Callable[..., None] | None = None,
):
    """Delete duplicate files by MD5 while keeping the first occurrence."""

    started_at = time.time()
    result = deduplicate_files(
        paths,
        delete_file=delete_file or os.remove,
        log=log,
        stop_requested=stop_requested,
        progress=progress,
    )
    stopped = False
    if callable(stop_requested):
        try:
            stopped = bool(stop_requested())
        except Exception:
            stopped = False
    if stopped and result.get("status") != "failed":
        result["status"] = "stopped"
    result["success_count"] = int(result.get("kept_count") or 0) + int(result.get("removed_count") or 0)
    result["skipped_count"] = 0
    result["duration_seconds"] = max(0.0, time.time() - started_at)
    result["message"] = (
        f"removed {result.get('removed_count', 0)} duplicate file(s)"
        if result.get("status") == "success"
        else result.get("status", "unknown")
    )
    return result
