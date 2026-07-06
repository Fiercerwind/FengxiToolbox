"""Core ZIP batching implementation for Fengxi Toolbox."""

from __future__ import annotations

import os
import re
import time
import zipfile
from pathlib import Path

from tools.fx_resume import is_valid_zip


ZIP_MODE_TOTAL = "total"
ZIP_MODE_RECURSIVE = "recursive"
ZIP_MODE_SMART_RECURSIVE = "smart_recursive"
ZIP_MODES = {ZIP_MODE_TOTAL, ZIP_MODE_RECURSIVE, ZIP_MODE_SMART_RECURSIVE}
ZIP_ARCHIVE_POLICY_REUSE = "reuse_existing"
ZIP_ARCHIVE_POLICY_REBUILD = "rebuild_existing"
ZIP_ARCHIVE_POLICIES = {ZIP_ARCHIVE_POLICY_REUSE, ZIP_ARCHIVE_POLICY_REBUILD}
ARCHIVE_FILE_EXTS = {
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".zst",
}


def normalize_zip_mode(mode):
    normalized = str(mode or ZIP_MODE_TOTAL).strip()
    if normalized in ZIP_MODES:
        return normalized
    return ZIP_MODE_TOTAL


def normalize_zip_archive_policy(value):
    normalized = str(value or ZIP_ARCHIVE_POLICY_REUSE).strip()
    aliases = {
        "reuse": ZIP_ARCHIVE_POLICY_REUSE,
        "copy": ZIP_ARCHIVE_POLICY_REUSE,
        "copy_existing": ZIP_ARCHIVE_POLICY_REUSE,
        "preserve": ZIP_ARCHIVE_POLICY_REUSE,
        "skip": ZIP_ARCHIVE_POLICY_REUSE,
        "resume": ZIP_ARCHIVE_POLICY_REUSE,
        "rebuild": ZIP_ARCHIVE_POLICY_REBUILD,
        "replace": ZIP_ARCHIVE_POLICY_REBUILD,
        "delete": ZIP_ARCHIVE_POLICY_REBUILD,
        "overwrite": ZIP_ARCHIVE_POLICY_REBUILD,
        "recompress": ZIP_ARCHIVE_POLICY_REBUILD,
    }
    normalized = aliases.get(normalized, normalized)
    if normalized in ZIP_ARCHIVE_POLICIES:
        return normalized
    return ZIP_ARCHIVE_POLICY_REUSE


def normalize_zip_max_depth(value):
    """Return a positive layer count, or None for unlimited."""

    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        depth = int(str(value).strip())
    except Exception:
        return None
    return depth if depth > 0 else None


def normalize_zip_depth_range(value):
    """Return (min_depth, max_depth), where max_depth None means unlimited.

    Backward compatibility: a single number such as "4" keeps the previous
    meaning of layers 1 through 4. A range such as "2-4" means only layers
    2 through 4 are planned.
    """

    if value is None:
        return 1, None
    if isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    if not text:
        return 1, None

    parts = [part.strip() for part in re.split(r"[-~～—–,，\s]+", text) if part.strip()]
    try:
        if len(parts) >= 2:
            min_depth = int(parts[0])
            max_depth = int(parts[1])
        else:
            min_depth = 1
            max_depth = int(parts[0])
    except Exception:
        return 1, None

    min_depth = max(1, min_depth)
    if max_depth <= 0:
        return min_depth, None
    if max_depth < min_depth:
        min_depth, max_depth = max_depth, min_depth
        min_depth = max(1, min_depth)
    return min_depth, max_depth


def _zip_depth_range_label(depth_range):
    min_depth, max_depth = depth_range
    if min_depth <= 1 and max_depth is None:
        return "unlimited"
    if max_depth is None:
        return f"{min_depth}+"
    if min_depth <= 1:
        return str(max_depth)
    return f"{min_depth}-{max_depth}"


def _archive_output_for(source, mode, is_file=False, root_source=None):
    source = Path(source)
    if is_file:
        return source.parent / f"{source.name}_Backup.zip"
    if normalize_zip_mode(mode) == ZIP_MODE_TOTAL:
        return source / f"{source.name}_Backup.zip"
    if root_source is not None:
        try:
            if source.resolve() != Path(root_source).resolve():
                return source.parent / f"{source.name}.zip"
        except Exception:
            pass
    return source / f"{source.name}.zip"


def _sorted_child_dirs(folder):
    try:
        return sorted((item for item in Path(folder).iterdir() if item.is_dir()), key=lambda item: item.name.lower())
    except Exception:
        return []


def _sorted_child_files(folder):
    try:
        return sorted((item for item in Path(folder).iterdir() if item.is_file()), key=lambda item: item.name.lower())
    except Exception:
        return []


def _is_archive_file(path):
    return Path(path).suffix.lower() in ARCHIVE_FILE_EXTS


def _within_depth_range(depth, depth_range):
    min_depth, max_depth = depth_range
    return depth >= min_depth and (max_depth is None or depth <= max_depth)


def _can_descend(depth, depth_range):
    _min_depth, max_depth = depth_range
    return max_depth is None or depth < max_depth


def plan_zip_archives(input_path, mode=ZIP_MODE_TOTAL, max_depth=None):
    """Return archive jobs without touching the filesystem."""

    source = Path(input_path).resolve()
    mode = normalize_zip_mode(mode)
    depth_range = normalize_zip_depth_range(max_depth)
    if source.is_file():
        return [
            {
                "source": source,
                "output": _archive_output_for(source, mode, is_file=True, root_source=source),
                "kind": "file",
                "mode": mode,
                "depth": 1,
            }
        ]
    if not source.is_dir():
        return []

    if mode == ZIP_MODE_TOTAL:
        return [
            {
                "source": source,
                "output": _archive_output_for(source, mode, root_source=source),
                "kind": "dir",
                "mode": mode,
                "depth": 1,
            }
        ]

    if mode == ZIP_MODE_RECURSIVE:
        folders = [(source, 1)]
        for current, dirs, _files in os.walk(source):
            dirs[:] = sorted(dirs, key=str.lower)
            current_path = Path(current)
            try:
                current_depth = len(current_path.relative_to(source).parts) + 1
            except Exception:
                current_depth = 1
            if not _can_descend(current_depth, depth_range):
                dirs[:] = []
                continue
            for dirname in dirs:
                child_depth = current_depth + 1
                if _within_depth_range(child_depth, depth_range):
                    folders.append((current_path / dirname, child_depth))
        return [
            {
                "source": folder,
                "output": _archive_output_for(folder, mode, root_source=source),
                "kind": "dir",
                "mode": mode,
                "depth": depth,
            }
            for folder, depth in folders
            if _within_depth_range(depth, depth_range)
        ]

    jobs = []

    def visit(folder, depth=1):
        if not _can_descend(depth - 1, depth_range):
            return
        child_dirs = _sorted_child_dirs(folder)
        child_files = _sorted_child_files(folder)
        meaningful_files = [item for item in child_files if not _is_archive_file(item)]
        if _within_depth_range(depth, depth_range):
            jobs.append(
                {
                    "source": Path(folder),
                    "output": _archive_output_for(folder, mode, root_source=source),
                    "kind": "dir",
                    "mode": mode,
                    "depth": depth,
                }
            )
        if not child_dirs or not _can_descend(depth, depth_range):
            return
        if meaningful_files:
            return
        for child in child_dirs:
            visit(child, depth + 1)

    visit(source, 1)
    return jobs


def estimate_zip_progress_units(input_path, mode=ZIP_MODE_TOTAL, max_depth=None):
    return len(plan_zip_archives(input_path, mode, max_depth=max_depth))


def _is_excluded(path, exclude_paths):
    try:
        return Path(path).resolve() in exclude_paths
    except Exception:
        return False


def _iter_directory_zip_entries(root, exclude_paths):
    root = Path(root)
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(dirs, key=str.lower)
        files = sorted(files, key=str.lower)
        current_path = Path(current)

        for dirname in dirs:
            dir_path = current_path / dirname
            if _is_excluded(dir_path, exclude_paths):
                continue
            rel_dir = dir_path.relative_to(root).as_posix().rstrip("/") + "/"
            yield dir_path, rel_dir, True

        for filename in files:
            file_path = current_path / filename
            if _is_excluded(file_path, exclude_paths):
                continue
            rel_file = file_path.relative_to(root).as_posix()
            yield file_path, rel_file, False


def _write_file_zip(source, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.write(source, arcname=Path(source).name)


def _write_directory_zip(source, output, exclude_paths):
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path, arcname, is_dir in _iter_directory_zip_entries(source, exclude_paths):
            if is_dir:
                info = zipfile.ZipInfo(arcname)
                archive.writestr(info, b"")
            else:
                archive.write(path, arcname=arcname)


def _emit_progress(progress, completed, total, current_path="", stage="compressing", fraction=None):
    if not callable(progress):
        return
    if fraction is None:
        fraction = completed / max(1, total)
    try:
        progress(
            completed=completed,
            total=total,
            current_path=str(current_path or ""),
            stage=stage,
            fraction=max(0.0, min(1.0, float(fraction))),
        )
    except TypeError:
        try:
            progress(completed, total, str(current_path or ""), stage, fraction)
        except Exception:
            pass
    except Exception:
        pass


def _log(log, message):
    if callable(log):
        try:
            log(message)
        except Exception:
            pass


def run_zip_task(
    input_path,
    mode=ZIP_MODE_TOTAL,
    *,
    max_depth=None,
    archive_policy=ZIP_ARCHIVE_POLICY_REUSE,
    progress=None,
    stop_requested=None,
    log=None,
    overwrite=True,
    resume=True,
):
    """Execute a ZIP task and return a structured result dictionary."""

    started_at = time.time()
    source = Path(input_path).resolve()
    mode = normalize_zip_mode(mode)
    archive_policy = normalize_zip_archive_policy(archive_policy)
    effective_resume = bool(resume) and archive_policy == ZIP_ARCHIVE_POLICY_REUSE
    depth_range = normalize_zip_depth_range(max_depth)
    result = {
        "status": "unknown",
        "mode": mode,
        "archive_policy": archive_policy,
        "max_depth": depth_range[1],
        "min_depth": depth_range[0],
        "depth_range": _zip_depth_range_label(depth_range),
        "input_path": str(source),
        "outputs": [],
        "failed_items": [],
        "processed_count": 0,
        "success_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "duration_seconds": 0.0,
        "message": "",
    }

    if not source.exists():
        result.update(
            {
                "status": "failed",
                "failed_items": [str(source)],
                "failed_count": 1,
                "message": f"path not found: {source}",
            }
        )
        return result

    jobs = plan_zip_archives(source, mode, max_depth=max_depth)
    total = len(jobs)
    if total <= 0:
        result.update({"status": "skipped", "skipped_count": 1, "message": "no archive job"})
        return result

    output_paths = {Path(job["output"]).resolve() for job in jobs}
    if overwrite:
        for output in output_paths:
            if output.exists():
                if effective_resume and is_valid_zip(output):
                    continue
                try:
                    output.unlink()
                except Exception as exc:
                    result["failed_items"].append(f"{output}: {exc}")

    _emit_progress(progress, 0, total, source, "preparing", 0.0)
    for index, job in enumerate(jobs, start=1):
        if callable(stop_requested):
            try:
                if stop_requested():
                    result["status"] = "stopped"
                    result["message"] = "stopped by user"
                    break
            except Exception:
                pass

        source_path = Path(job["source"]).resolve()
        output_path = Path(job["output"]).resolve()
        _log(log, f"[ZIP] {source_path} -> {output_path}")
        _emit_progress(progress, index - 1, total, source_path, "compressing")
        try:
            if effective_resume and is_valid_zip(output_path):
                _log(log, f"[ZIP] resume skip existing archive: {output_path}")
                result["outputs"].append(str(output_path))
                result["success_count"] += 1
                result["skipped_count"] += 1
                continue
            if job["kind"] == "file":
                _write_file_zip(source_path, output_path)
            else:
                _write_directory_zip(source_path, output_path, output_paths)
            result["outputs"].append(str(output_path))
            result["success_count"] += 1
        except Exception as exc:
            result["failed_items"].append(f"{source_path}: {exc}")
            result["failed_count"] += 1
        finally:
            result["processed_count"] += 1
            _emit_progress(progress, index, total, source_path, "done")

    if result["status"] == "stopped":
        pass
    elif result["failed_items"]:
        result["status"] = "failed"
        result["message"] = f"{len(result['failed_items'])} archive(s) failed"
    else:
        result["status"] = "success"
        result["message"] = f"{result['success_count']} archive(s) created"

    result["duration_seconds"] = max(0.0, time.time() - started_at)
    return result
