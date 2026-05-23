"""Core ZIP batching implementation for Fengxi Toolbox."""

from __future__ import annotations

import os
import time
import zipfile
from pathlib import Path


ZIP_MODE_TOTAL = "total"
ZIP_MODE_RECURSIVE = "recursive"
ZIP_MODE_SMART_RECURSIVE = "smart_recursive"
ZIP_MODES = {ZIP_MODE_TOTAL, ZIP_MODE_RECURSIVE, ZIP_MODE_SMART_RECURSIVE}


def normalize_zip_mode(mode):
    normalized = str(mode or ZIP_MODE_TOTAL).strip()
    if normalized in ZIP_MODES:
        return normalized
    return ZIP_MODE_TOTAL


def _archive_output_for(source, mode, is_file=False):
    source = Path(source)
    if is_file:
        return source.parent / f"{source.name}_Backup.zip"
    if normalize_zip_mode(mode) == ZIP_MODE_TOTAL:
        return source / f"{source.name}_Backup.zip"
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


def plan_zip_archives(input_path, mode=ZIP_MODE_TOTAL):
    """Return archive jobs without touching the filesystem."""

    source = Path(input_path).resolve()
    mode = normalize_zip_mode(mode)
    if source.is_file():
        return [
            {
                "source": source,
                "output": _archive_output_for(source, mode, is_file=True),
                "kind": "file",
                "mode": mode,
            }
        ]
    if not source.is_dir():
        return []

    if mode == ZIP_MODE_TOTAL:
        return [
            {
                "source": source,
                "output": _archive_output_for(source, mode),
                "kind": "dir",
                "mode": mode,
            }
        ]

    if mode == ZIP_MODE_RECURSIVE:
        folders = [source]
        for current, dirs, _files in os.walk(source):
            dirs[:] = sorted(dirs, key=str.lower)
            current_path = Path(current)
            for dirname in dirs:
                folders.append(current_path / dirname)
        return [
            {
                "source": folder,
                "output": _archive_output_for(folder, mode),
                "kind": "dir",
                "mode": mode,
            }
            for folder in folders
        ]

    jobs = []

    def visit(folder):
        child_dirs = _sorted_child_dirs(folder)
        child_files = _sorted_child_files(folder)
        if child_files or not child_dirs:
            jobs.append(
                {
                    "source": Path(folder),
                    "output": _archive_output_for(folder, mode),
                    "kind": "dir",
                    "mode": mode,
                }
            )
            return
        for child in child_dirs:
            visit(child)

    visit(source)
    return jobs


def estimate_zip_progress_units(input_path, mode=ZIP_MODE_TOTAL):
    return len(plan_zip_archives(input_path, mode))


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
    progress=None,
    stop_requested=None,
    log=None,
    overwrite=True,
):
    """Execute a ZIP task and return a structured result dictionary."""

    started_at = time.time()
    source = Path(input_path).resolve()
    mode = normalize_zip_mode(mode)
    result = {
        "status": "unknown",
        "mode": mode,
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

    jobs = plan_zip_archives(source, mode)
    total = len(jobs)
    if total <= 0:
        result.update({"status": "skipped", "skipped_count": 1, "message": "no archive job"})
        return result

    output_paths = {Path(job["output"]).resolve() for job in jobs}
    if overwrite:
        for output in output_paths:
            if output.exists():
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
