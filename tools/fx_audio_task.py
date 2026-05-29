"""Audio task orchestration for Fengxi Toolbox."""

from __future__ import annotations

import concurrent.futures
import os
from dataclasses import dataclass
from typing import Any, Callable


AUDIO_VALID_AUDIO_EXTS = (".mp3", ".wav", ".flac", ".m4a", ".ogg", ".wma", ".aac")
AUDIO_VALID_VIDEO_EXTS = (".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv")
AudioTranscribeArgs = dict[str, Any]


@dataclass
class AudioTaskCallbacks:
    log: Callable[[str], None] | None = None
    stop_requested: Callable[[], bool] | None = None
    on_item_started: Callable[[str, str], None] | None = None
    on_item_finished: Callable[[dict[str, Any]], None] | None = None
    on_item_failed: Callable[[dict[str, Any]], None] | None = None
    on_item_completed: Callable[[int], None] | None = None
    on_transcript_progress: Callable[[str, dict[str, Any]], None] | None = None


def _call(callback, *args):
    if not callable(callback):
        return None
    try:
        return callback(*args)
    except Exception:
        return None


def _log(callbacks: AudioTaskCallbacks | None, message: str) -> None:
    if callbacks is not None:
        _call(callbacks.log, message)


def _stop_requested(callbacks: AudioTaskCallbacks | None) -> bool:
    if callbacks is None or not callable(callbacks.stop_requested):
        return False
    try:
        return bool(callbacks.stop_requested())
    except Exception:
        return False


def collect_audio_files(input_value, collect_input_files=None):
    normalized_input = str(input_value or "").strip()
    if not normalized_input:
        return []
    if os.path.isfile(normalized_input):
        return [normalized_input]
    if callable(collect_input_files):
        try:
            return list(collect_input_files(normalized_input, "audio") or [])
        except Exception:
            return []
    return []


def get_audio_task_args(app):
    try:
        mode = app.audio_mode_var.get()
    except Exception:
        mode = "video2mp3"
    try:
        target_fmt = app.audio_target_fmt.get()
    except Exception:
        target_fmt = "mp3"
    try:
        bitrate = app.audio_bitrate.get()
    except Exception:
        bitrate = "192k"
    try:
        delete_source = bool(app.audio_delete_var.get())
    except Exception:
        delete_source = False
    return str(mode or "video2mp3"), str(target_fmt or "mp3"), str(bitrate or "192k"), delete_source


def get_audio_transcribe_args(app) -> AudioTranscribeArgs:
    def read_var(name, default):
        try:
            return getattr(app, name).get()
        except Exception:
            return default

    return {
        "model_name": str(read_var("audio_transcribe_model", "base") or "base"),
        "language": str(read_var("audio_transcribe_language", "自动识别") or "自动识别"),
        "output_format": str(read_var("audio_transcribe_format", "txt") or "txt"),
        "cache_dir": str(read_var("audio_transcribe_cache_dir", "") or ""),
    }


def build_audio_output_path(src, input_root, output_folder, target_fmt):
    rel = os.path.relpath(src, input_root)
    dst = os.path.join(output_folder, rel)
    dst_dir = os.path.dirname(dst)
    fname = os.path.basename(src)
    new_name = os.path.splitext(fname)[0] + f".{target_fmt}"
    return dst, os.path.join(dst_dir, new_name)


def process_one_audio_file(job, convert_audio_format, copy_file_safe, transcribe_media_file=None):
    src, input_root, output_folder, mode, target_fmt, bitrate, delete_source, *extra = job
    transcribe_args = extra[0] if extra and isinstance(extra[0], dict) else {}
    fname = os.path.basename(src)
    lower_name = fname.lower()
    dst, final_dst = build_audio_output_path(src, input_root, output_folder, target_fmt)
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    is_video = lower_name.endswith(AUDIO_VALID_VIDEO_EXTS)
    is_audio = lower_name.endswith(AUDIO_VALID_AUDIO_EXTS)
    if not is_video and not is_audio:
        copy_file_safe(src, dst)
        return {"src": src, "dst": dst, "output": dst, "status": "copied", "ok": True, "message": "not_audio_video"}

    if mode == "transcribe":
        if not callable(transcribe_media_file):
            copy_file_safe(src, dst)
            return {
                "src": src,
                "dst": dst,
                "output": dst,
                "status": "missing_lib",
                "ok": True,
                "message": "MISSING_LIB:faster_whisper",
            }
        try:
            item = transcribe_media_file(
                src,
                input_root,
                output_folder,
                model_name=transcribe_args.get("model_name", "base"),
                language=transcribe_args.get("language", "自动识别"),
                output_format=transcribe_args.get("output_format", "txt"),
                cache_dir=transcribe_args.get("cache_dir") or None,
                progress_callback=transcribe_args.get("progress_callback")
                if callable(transcribe_args.get("progress_callback"))
                else None,
            )
        except Exception as exc:
            return {"src": src, "dst": dst, "output": "", "status": "failed", "ok": False, "message": str(exc)}
        delete_error = ""
        if delete_source:
            try:
                os.remove(src)
            except Exception as exc:
                delete_error = str(exc)
        item["status"] = "transcribed"
        item["ok"] = True
        item["delete_error"] = delete_error
        return item

    if mode == "video2mp3" and not is_video:
        copy_file_safe(src, dst)
        return {"src": src, "dst": dst, "output": dst, "status": "copied", "ok": True, "message": "not_video"}

    if mode == "convert" and not is_audio:
        copy_file_safe(src, dst)
        return {"src": src, "dst": dst, "output": dst, "status": "copied", "ok": True, "message": "not_audio"}

    status = convert_audio_format(src, final_dst, target_fmt, bitrate)
    if status == "SUCCESS":
        delete_error = ""
        if delete_source:
            try:
                os.remove(src)
            except Exception as exc:
                delete_error = str(exc)
        return {
            "src": src,
            "dst": dst,
            "output": final_dst,
            "status": "success",
            "ok": True,
            "message": status,
            "delete_error": delete_error,
        }

    copy_file_safe(src, dst)
    missing_lib = str(status or "").startswith("MISSING_LIB")
    return {
        "src": src,
        "dst": dst,
        "output": dst,
        "status": "missing_lib" if missing_lib else "failed",
        "ok": missing_lib,
        "message": status,
    }


def run_audio_task_core(
    app,
    input_folder,
    *,
    normalized_input,
    input_root,
    output_folder,
    audio_files,
    result,
    tracker=None,
    is_parallel_enabled=None,
    get_parallel_worker_count=None,
    convert_audio_format=None,
    copy_file_safe=None,
    get_task_result_counts=None,
    set_task_result_counts=None,
    set_task_result_finished=None,
    set_task_result_output_root=None,
    add_task_result_output=None,
    write_failed_report=None,
    log=None,
    progress_bar=None,
    stop_requested=None,
    executor_factory=None,
    get_audio_task_args=None,
    get_audio_transcribe_args=None,
    transcribe_media_file=None,
    callbacks: AudioTaskCallbacks | None = None,
):
    if not callable(convert_audio_format):
        raise ValueError("convert_audio_format callback is required")
    if not callable(copy_file_safe):
        raise ValueError("copy_file_safe callback is required")
    if not callable(get_audio_task_args):
        raise ValueError("get_audio_task_args callback is required")
    if not callable(get_audio_transcribe_args):
        get_audio_transcribe_args = lambda _app: {}
    if not callable(set_task_result_counts) or not callable(set_task_result_finished):
        raise ValueError("task result callbacks are required")
    if not callable(set_task_result_output_root) or not callable(add_task_result_output):
        raise ValueError("output callbacks are required")
    if not callable(write_failed_report):
        raise ValueError("write_failed_report callback is required")
    if not callable(log):
        log = lambda *_args, **_kwargs: None
    if not callable(stop_requested):
        stop_requested = lambda: False
    if not callable(executor_factory):
        executor_factory = concurrent.futures.ThreadPoolExecutor
    if not callable(is_parallel_enabled):
        is_parallel_enabled = lambda *_args, **_kwargs: False
    if not callable(get_parallel_worker_count):
        get_parallel_worker_count = lambda total: 1

    set_task_result_output_root(result, output_folder)
    if not audio_files:
        set_task_result_counts(result, processed=0, success=0, failed=0, skipped=1)
        set_task_result_finished(
            result,
            "skipped",
            message="未找到可处理的音视频文件",
            detail="未找到可处理的音视频文件",
            skipped=True,
        )
        _log(callbacks, "⚠️ [跳过] 未找到可处理的音视频文件")
        return result

    mode, target_fmt, bitrate, delete_source = get_audio_task_args(app)
    transcribe_args = get_audio_transcribe_args(app) if mode == "transcribe" else {}
    if mode == "transcribe":
        target_fmt = str(transcribe_args.get("output_format") or "txt").split("+", 1)[0]
    total = len(audio_files)
    def build_job(src):
        item_transcribe_args = dict(transcribe_args)
        if mode == "transcribe" and callbacks is not None and callable(callbacks.on_transcript_progress):
            item_transcribe_args["progress_callback"] = (
                lambda payload, source=src: _call(callbacks.on_transcript_progress, source, payload)
            )
        return (src, input_root, output_folder, mode, target_fmt, bitrate, delete_source, item_transcribe_args)

    jobs = [build_job(src) for src in audio_files]
    failed_list = []
    success_count = 0
    copied_count = 0

    if mode == "transcribe":
        _log(
            callbacks,
            "📝 [语音转文字] "
            f"共 {total} 个文件，模型：{transcribe_args.get('model_name', 'base')}，"
            f"语言：{transcribe_args.get('language', '自动识别')}，"
            f"输出：{transcribe_args.get('output_format', 'txt')}",
        )
    else:
        _log(callbacks, f"🎧 [音频] 共 {total} 个文件，目标格式：{target_fmt}，码率：{bitrate}")

    def handle_item(item):
        nonlocal success_count, copied_count
        src = item.get("src", "")
        fname = os.path.basename(src)
        status = item.get("status")
        if status in {"success", "transcribed"}:
            success_count += 1
            outputs = item.get("outputs") if isinstance(item.get("outputs"), list) else [item.get("output")]
            for output in outputs:
                add_task_result_output(result, output)
            if status == "transcribed":
                _log(callbacks, f"📝 [语音转文字] 识别成功: {fname}")
            else:
                _log(callbacks, f"🎵 [音频] 转换成功: {fname}")
            if item.get("delete_error"):
                failed_list.append(f"{src}: 删除源文件失败: {item.get('delete_error')}")
                _log(callbacks, f"⚠️ [源文件] 删除失败: {fname}: {item.get('delete_error')}")
        elif status == "missing_lib":
            copied_count += 1
            add_task_result_output(result, item.get("output"))
            _log(callbacks, f"⚠️ [跳过] 缺少 moviepy/ffmpeg 后端: {fname}")
        elif status == "copied":
            copied_count += 1
            add_task_result_output(result, item.get("output"))
            _log(callbacks, f"↪️ [跳过] 已原样复制: {fname}")
        else:
            failed_list.append(f"{src}: {item.get('message')}")
            _log(callbacks, f"❌ [失败] 音频转换错误: {fname}")
        if tracker is not None:
            tracker.complete_units(1)
        else:
            try:
                progress_bar.set(min(1.0, (success_count + copied_count + len(failed_list)) / max(1, total)))
            except Exception:
                pass

    parallel_workers = get_parallel_worker_count(total) if is_parallel_enabled(app) else 1
    if parallel_workers > 1:
        _log(callbacks, f"🚀 [批量并行] 音视频转换启用 {parallel_workers} 个线程。")
        futures = {}
        with executor_factory(max_workers=parallel_workers) as executor:
            for job in jobs:
                if stop_requested():
                    break
                src = job[0]
                if tracker is not None:
                    tracker.set_current_item(src, "音视频转换")
                _call(callbacks.on_item_started if callbacks else None, src, job[2])
                futures[executor.submit(process_one_audio_file, job, convert_audio_format, copy_file_safe, transcribe_media_file)] = job
            for future in concurrent.futures.as_completed(futures):
                src = futures[future][0]
                try:
                    item = future.result()
                except Exception as exc:
                    item = {"src": src, "output": "", "status": "failed", "ok": False, "message": str(exc)}
                _call(callbacks.on_item_finished if callbacks else None, item)
                handle_item(item)
    else:
        for index, job in enumerate(jobs):
            if stop_requested():
                break
            src = job[0]
            if tracker is not None:
                tracker.set_current_item(src, "音视频转换")
            _call(callbacks.on_item_started if callbacks else None, src, job[2])
            try:
                item = process_one_audio_file(job, convert_audio_format, copy_file_safe, transcribe_media_file)
            except Exception as exc:
                item = {"src": src, "output": "", "status": "failed", "ok": False, "message": str(exc)}
            _call(callbacks.on_item_finished if callbacks else None, item)
            handle_item(item)
            if tracker is None:
                try:
                    progress_bar.set((index + 1) / total)
                except Exception:
                    pass

    processed_count = success_count + copied_count + len(failed_list)
    if failed_list:
        result["failed_items"] = list(failed_list)
        set_task_result_counts(result, processed=total, success=success_count + copied_count, failed=len(failed_list), skipped=0)
        report_path = write_failed_report(output_folder, failed_list)
        if report_path:
            add_task_result_output(result, report_path)
            _log(callbacks, f"\n📫 [报告] 已生成失败报告: {report_path}")
        set_task_result_finished(
            result,
            "failed",
            message=f"{'语音转文字' if mode == 'transcribe' else '音视频转换'}完成，但有 {len(failed_list)} 个文件失败",
            detail=f"成功/复制 {success_count + copied_count} 个，失败 {len(failed_list)} 个",
            error=f"失败 {len(failed_list)} 个文件",
        )
    elif stop_requested():
        set_task_result_counts(result, processed=processed_count, success=success_count + copied_count, failed=0, skipped=0)
        set_task_result_finished(
            result,
            "stopped",
            message=f"用户停止{'语音转文字' if mode == 'transcribe' else '音视频转换'}任务",
            detail=f"用户停止{'语音转文字' if mode == 'transcribe' else '音视频转换'}任务",
            stopped=True,
        )
    else:
        set_task_result_counts(result, processed=total, success=success_count + copied_count, failed=0, skipped=0)
        done_label = "语音转文字" if mode == "transcribe" else "音视频转换"
        _log(callbacks, f"\n🎉 [完成] {done_label}已全部完成。")
        set_task_result_finished(
            result,
            "success",
            message=f"{done_label}已全部完成",
            detail=f"{'识别成功' if mode == 'transcribe' else '转换成功'} {success_count} 个，原样复制 {copied_count} 个",
        )
    return result
