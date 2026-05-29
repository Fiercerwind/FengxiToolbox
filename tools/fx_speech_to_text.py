"""Speech-to-text helpers for Fengxi Toolbox audio workflows."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable


SPEECH_MODEL_OPTIONS = ("tiny", "base", "small", "medium")
SPEECH_LANGUAGE_OPTIONS = {
    "自动识别": None,
    "中文": "zh",
    "英文": "en",
    "日文": "ja",
    "韩文": "ko",
}
SPEECH_OUTPUT_FORMATS = ("txt", "srt", "txt+srt")


def normalize_speech_model(value: str | None) -> str:
    model = str(value or "base").strip()
    return model if model in SPEECH_MODEL_OPTIONS else "base"


def normalize_speech_language(value: str | None) -> str | None:
    raw = str(value or "自动识别").strip()
    if raw in SPEECH_LANGUAGE_OPTIONS:
        return SPEECH_LANGUAGE_OPTIONS[raw]
    if raw.lower() in {"auto", "none", ""}:
        return None
    return raw.lower()


def normalize_speech_output_format(value: str | None) -> str:
    fmt = str(value or "txt").strip().lower()
    return fmt if fmt in SPEECH_OUTPUT_FORMATS else "txt"


def build_transcript_output_paths(src, input_root, output_folder, output_format="txt") -> list[str]:
    src_path = Path(src)
    try:
        rel = Path(os.path.relpath(src_path, input_root))
    except Exception:
        rel = Path(src_path.name)
    rel_parent = rel.parent if str(rel.parent) != "." else Path()
    out_dir = Path(output_folder) / rel_parent
    base = out_dir / src_path.stem
    fmt = normalize_speech_output_format(output_format)
    suffixes = [".txt", ".srt"] if fmt == "txt+srt" else [f".{fmt}"]
    return [str(base.with_suffix(suffix)) for suffix in suffixes]


def format_srt_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(float(seconds or 0) * 1000)))
    ms = total_ms % 1000
    total_seconds = total_ms // 1000
    second = total_seconds % 60
    total_minutes = total_seconds // 60
    minute = total_minutes % 60
    hour = total_minutes // 60
    return f"{hour:02d}:{minute:02d}:{second:02d},{ms:03d}"


def write_transcript_outputs(segments: list[dict[str, Any]], outputs: list[str], *, detected_language: str = "") -> None:
    for output in outputs:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.suffix.lower() == ".srt":
            lines = []
            for index, segment in enumerate(segments, start=1):
                text = str(segment.get("text", "")).strip()
                if not text:
                    continue
                lines.append(str(index))
                lines.append(f"{format_srt_timestamp(segment.get('start', 0))} --> {format_srt_timestamp(segment.get('end', 0))}")
                lines.append(text)
                lines.append("")
            out_path.write_text("\n".join(lines), encoding="utf-8")
        else:
            lines = []
            if detected_language:
                lines.append(f"识别语言: {detected_language}")
                lines.append("")
            lines.extend(str(segment.get("text", "")).strip() for segment in segments if str(segment.get("text", "")).strip())
            out_path.write_text("\n".join(lines).strip() + ("\n" if lines else ""), encoding="utf-8")


def _load_whisper_model(model_name: str, *, cache_dir: str | None = None, model_factory: Callable[..., Any] | None = None):
    if callable(model_factory):
        return model_factory(model_name)
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise RuntimeError("缺少 faster-whisper 后端，请安装 faster-whisper 后再使用语音转文字。") from exc
    kwargs: dict[str, Any] = {
        "device": "auto",
        "compute_type": "int8",
    }
    if cache_dir:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        kwargs["download_root"] = cache_dir
    return WhisperModel(model_name, **kwargs)


def _safe_progress_callback(callback: Callable[[dict[str, Any]], None] | None, payload: dict[str, Any]) -> None:
    if not callable(callback):
        return
    try:
        callback(payload)
    except Exception:
        return


def transcribe_media_file(
    src,
    input_root,
    output_folder,
    *,
    model_name: str = "base",
    language: str | None = None,
    output_format: str = "txt",
    cache_dir: str | None = None,
    model_factory: Callable[..., Any] | None = None,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    src_path = Path(src)
    model = normalize_speech_model(model_name)
    lang = normalize_speech_language(language)
    fmt = normalize_speech_output_format(output_format)
    outputs = build_transcript_output_paths(src_path, input_root, output_folder, fmt)
    _safe_progress_callback(
        progress_callback,
        {"type": "stage", "stage": "load_model", "src": str(src_path), "model": model},
    )
    whisper_model = _load_whisper_model(model, cache_dir=cache_dir, model_factory=model_factory)
    transcribe_kwargs: dict[str, Any] = {
        "vad_filter": True,
        "beam_size": 5,
    }
    if lang:
        transcribe_kwargs["language"] = lang
    _safe_progress_callback(
        progress_callback,
        {"type": "stage", "stage": "transcribe", "src": str(src_path), "model": model},
    )
    segments_iter, info = whisper_model.transcribe(str(src_path), **transcribe_kwargs)
    segments = []
    for segment in segments_iter:
        item = {
            "start": float(getattr(segment, "start", 0.0)),
            "end": float(getattr(segment, "end", 0.0)),
            "text": str(getattr(segment, "text", "")).strip(),
        }
        segments.append(item)
        if item["text"]:
            _safe_progress_callback(
                progress_callback,
                {"type": "segment", "src": str(src_path), "segment": item, "index": len(segments)},
            )
    detected_language = str(getattr(info, "language", "") or lang or "")
    _safe_progress_callback(
        progress_callback,
        {"type": "stage", "stage": "write_outputs", "src": str(src_path), "segments": len(segments)},
    )
    write_transcript_outputs(segments, outputs, detected_language=detected_language)
    _safe_progress_callback(
        progress_callback,
        {
            "type": "done",
            "src": str(src_path),
            "outputs": list(outputs),
            "segments": len(segments),
            "language": detected_language,
        },
    )
    return {
        "src": str(src_path),
        "outputs": outputs,
        "output": outputs[0] if outputs else "",
        "status": "success",
        "ok": True,
        "message": "SUCCESS",
        "segments": len(segments),
        "language": detected_language,
        "model": model,
    }
