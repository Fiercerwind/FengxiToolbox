from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping


@dataclass
class TaskHistoryExportContext:
    normalize_path: Callable[[Any], str]
    export_task_result: Callable[[dict, str], bool]
    sanitize_filename_component: Callable[[Any, str], str]
    format_queue_time: Callable[[Any], str]
    get_feature_label: Callable[..., str]
    queue_status_text: Callable[[Any], str]
    classify_failure_reason: Callable[[dict], tuple[str, str]]
    failure_value_to_label: Mapping[str, str]
    project_root: Path
    user_home: Path
    probe_environment: Callable[[], dict]
    load_queue_history: Callable[[], list]
    debug: Callable[[str], None] | None = None


def _debug(context: TaskHistoryExportContext, message: str) -> None:
    try:
        if callable(context.debug):
            context.debug(message)
    except Exception:
        pass


def _item(entry: Any) -> dict:
    return dict(entry or {})


def _task_result(item: dict) -> dict:
    result = item.get("task_result")
    return result if isinstance(result, dict) else {}


def _feature_label(context: TaskHistoryExportContext, task_type: Any, fallback: str) -> str:
    try:
        return context.get_feature_label(task_type, fallback=fallback)
    except TypeError:
        return context.get_feature_label(task_type)


def _history_filename(
    entry: Any,
    context: TaskHistoryExportContext,
    *,
    prefix: str,
    extension: str,
) -> str:
    item = _item(entry)
    task_type = _feature_label(context, item.get("task_type"), item.get("task_type") or "task")
    task_slug = context.sanitize_filename_component(task_type, fallback="task")
    title_slug = context.sanitize_filename_component(
        item.get("title") or item.get("input") or "history",
        fallback="history",
    )
    timestamp = context.sanitize_filename_component(
        context.format_queue_time(item.get("finished_at") or item.get("created_at")),
        fallback="time",
    )
    return f"{prefix}_{task_slug}_{title_slug}_{timestamp}.{extension}"


def build_task_history_export_filename(entry: Any, context: TaskHistoryExportContext) -> str:
    return _history_filename(entry, context, prefix="fengxi_task_result", extension="json")


def export_task_history_entry(
    entry: Any,
    output_path: Any,
    context: TaskHistoryExportContext,
) -> tuple[bool, str]:
    item = _item(entry)
    task_result = _task_result(item)
    if not task_result:
        return False, "当前历史记录没有可导出的结构化结果。"
    normalized_output = context.normalize_path(output_path)
    if not normalized_output:
        return False, "未选择导出位置。"
    ok = context.export_task_result(task_result, normalized_output)
    if not ok:
        return False, f"导出失败：{normalized_output}"
    return True, normalized_output


def build_task_history_log_export_text(entry: Any, context: TaskHistoryExportContext) -> str:
    item = _item(entry)
    task_result = _task_result(item)
    logs = list(item.get("logs") or task_result.get("logs") or task_result.get("log_lines") or [])
    lines = [
        f"标题：{item.get('title', '')}",
        f"功能：{_feature_label(context, item.get('task_type'), '未知任务')}",
        f"状态：{context.queue_status_text(item.get('status'))}",
        f"输入：{item.get('input', '')}",
        f"创建时间：{context.format_queue_time(item.get('created_at'))}",
        f"结束时间：{context.format_queue_time(item.get('finished_at') or item.get('created_at'))}",
        "",
        "日志：",
    ]
    if logs:
        lines.extend(f"- {text}" for text in logs)
    else:
        lines.append("- (empty)")
    return "\n".join(lines)


def build_task_history_log_export_filename(entry: Any, context: TaskHistoryExportContext) -> str:
    return _history_filename(entry, context, prefix="fengxi_task_log", extension="txt")


def export_task_history_log(
    entry: Any,
    output_path: Any,
    context: TaskHistoryExportContext,
) -> tuple[bool, str]:
    text = build_task_history_log_export_text(entry, context)
    normalized_output = context.normalize_path(output_path)
    if not normalized_output:
        return False, "未选择导出位置。"
    try:
        path = Path(normalized_output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return True, normalized_output
    except Exception as exc:
        _debug(context, f"queue:history_log_export_error:{exc}")
        return False, f"导出失败：{normalized_output}"


def build_task_history_report_export_filename(entry: Any, context: TaskHistoryExportContext) -> str:
    return _history_filename(entry, context, prefix="fengxi_task_report", extension="md")


def _safe_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except Exception:
        return 0


def build_task_history_report_text(entry: Any, context: TaskHistoryExportContext) -> str:
    item = _item(entry)
    task_result = _task_result(item)
    outputs = list(task_result.get("outputs") or item.get("outputs") or [])
    failed_items = list(task_result.get("failed_items") or item.get("failed_items") or [])
    logs = [
        str(text).strip()
        for text in (item.get("logs") or task_result.get("logs") or task_result.get("log_lines") or [])
        if str(text).strip()
    ]
    has_content = bool(
        task_result
        or outputs
        or failed_items
        or logs
        or any(item.get(key) for key in ("title", "task_type", "status", "input", "detail", "error", "output_root"))
    )
    if not has_content:
        return ""

    duration_seconds = task_result.get("duration_seconds", item.get("duration_seconds", 0.0))
    try:
        duration_seconds = float(duration_seconds or 0.0)
    except Exception:
        duration_seconds = 0.0

    processed_count = _safe_int(task_result.get("processed_count", item.get("processed_count", 0)))
    success_count = _safe_int(task_result.get("success_count", item.get("success_count", 0)))
    failed_count = _safe_int(task_result.get("failed_count", item.get("failed_count", 0)))
    skipped_count = _safe_int(task_result.get("skipped_count", item.get("skipped_count", 0)))
    output_root = task_result.get("output_root") or item.get("output_root", "")
    output_strategy_label = task_result.get("output_strategy_label") or item.get("output_strategy_label", "")
    output_strategy = task_result.get("output_strategy") or item.get("output_strategy", "")
    error_text = str(task_result.get("error") or item.get("error") or "").strip()
    detail_text = str(task_result.get("detail") or item.get("detail") or "").strip()
    message_text = str(task_result.get("message") or item.get("message") or "").strip()
    failure_kind, failure_reason = context.classify_failure_reason(item)
    failure_label = context.failure_value_to_label.get(failure_kind, failure_kind or "未知失败")
    failed_log_lines = [
        text
        for text in logs
        if any(marker in text.lower() for marker in ("❌", "🔥", "错误", "失败", "error", "failed", "traceback"))
    ]

    lines = [
        "# 风兮工具箱任务报告",
        "",
        "## 基本信息",
        f"- 标题：{item.get('title', '')}",
        f"- 功能：{_feature_label(context, item.get('task_type'), '未知任务')}",
        f"- 状态：{context.queue_status_text(item.get('status'))}",
        f"- 输入：{item.get('input', '')}",
        f"- 创建时间：{context.format_queue_time(item.get('created_at'))}",
        f"- 结束时间：{context.format_queue_time(item.get('finished_at') or item.get('created_at'))}",
    ]
    if duration_seconds > 0:
        lines.append(f"- 耗时：{duration_seconds:.3f}s")

    lines.extend(
        [
            "",
            "## 结果统计",
            f"- 处理总数：{processed_count}",
            f"- 成功数：{success_count}",
            f"- 失败数：{failed_count}",
            f"- 跳过数：{skipped_count}",
        ]
    )
    if message_text:
        lines.append(f"- 结果消息：{message_text}")
    if detail_text:
        lines.append(f"- 结果详情：{detail_text}")
    if error_text:
        lines.append(f"- 错误信息：{error_text}")

    lines.extend(["", "## 输出位置"])
    if output_strategy_label:
        lines.append(f"- 输出策略：{output_strategy_label}")
    elif output_strategy:
        lines.append(f"- 输出策略：{output_strategy}")
    if output_root:
        lines.append(f"- 输出目录：{output_root}")
    else:
        lines.append("- 输出目录：")
    if outputs:
        lines.append("- 输出文件：")
        lines.extend(f"  - {path}" for path in outputs)
    else:
        lines.append("- 输出文件：无")

    if item.get("status") == "failed" or error_text or failed_items or failed_log_lines:
        lines.extend(["", "## 失败分析", f"- 失败分类：{failure_label}"])
        if failure_reason:
            lines.append(f"- 失败原因：{failure_reason}")
        if failed_items:
            lines.append(f"- 失败项数量：{len(failed_items)}")
            lines.append("- 失败项：")
            lines.extend(f"  - {path}" for path in failed_items)

    lines.extend(["", "## 关键日志"])
    if failed_log_lines:
        lines.extend(f"- {text}" for text in failed_log_lines[-8:])
    elif logs:
        lines.extend(f"- {text}" for text in logs[-12:])
    else:
        lines.append("- (empty)")

    lines.extend(["", "## 结构化结果摘要"])
    if task_result:
        lines.append("```json")
        lines.append(json.dumps(task_result, ensure_ascii=False, indent=2))
        lines.append("```")
    else:
        lines.append("- 无结构化结果。")
    return "\n".join(lines)


def export_task_history_report(
    entry: Any,
    output_path: Any,
    context: TaskHistoryExportContext,
) -> tuple[bool, str]:
    text = build_task_history_report_text(entry, context)
    if not text:
        return False, "当前历史记录为空，无法导出任务报告。"
    normalized_output = context.normalize_path(output_path)
    if not normalized_output:
        return False, "未选择导出位置。"
    try:
        path = Path(normalized_output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return True, str(path.resolve())
    except Exception as exc:
        _debug(context, f"queue:history_report_export_error:{exc}")
        return False, f"导出失败：{normalized_output}"


def build_task_history_diagnostic_filename(entry: Any, context: TaskHistoryExportContext) -> str:
    return _history_filename(entry, context, prefix="fengxi_diagnostic", extension="zip")


def diagnostic_path_replacements(context: TaskHistoryExportContext) -> list[tuple[str, str]]:
    replacements = []
    for label, value in (
        ("<PROJECT_ROOT>", context.project_root),
        ("<USER_HOME>", context.user_home),
    ):
        try:
            normalized = str(Path(value).resolve())
        except Exception:
            normalized = str(value or "")
        if normalized:
            replacements.append((normalized, label))
            replacements.append((normalized.replace("\\", "/"), label))
    replacements.sort(key=lambda item: len(item[0]), reverse=True)
    return replacements


def redact_diagnostic_text(value: Any, context: TaskHistoryExportContext) -> str:
    text = str(value)
    for raw, replacement in diagnostic_path_replacements(context):
        if raw:
            text = text.replace(raw, replacement)
    return text


def redact_diagnostic_payload(value: Any, context: TaskHistoryExportContext) -> Any:
    if isinstance(value, dict):
        return {str(key): redact_diagnostic_payload(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_diagnostic_payload(item, context) for item in value]
    if isinstance(value, tuple):
        return [redact_diagnostic_payload(item, context) for item in value]
    if isinstance(value, str):
        return redact_diagnostic_text(value, context)
    return value


def diagnostic_write_json(zip_file: zipfile.ZipFile, arcname: str, payload: Any, context: TaskHistoryExportContext) -> None:
    text = json.dumps(redact_diagnostic_payload(payload, context), ensure_ascii=False, indent=2)
    zip_file.writestr(arcname, text)


def diagnostic_write_text(zip_file: zipfile.ZipFile, arcname: str, text: str, context: TaskHistoryExportContext) -> None:
    zip_file.writestr(arcname, redact_diagnostic_text(text or "", context))


def build_diagnostic_summary(
    entry: Any,
    environment: Mapping[str, Any],
    context: TaskHistoryExportContext,
) -> str:
    item = _item(entry)
    task_result = _task_result(item)
    failure_kind, failure_reason = context.classify_failure_reason(item)
    lines = [
        "# 风兮工具箱诊断包",
        "",
        "## 说明",
        "- 此诊断包用于排查任务失败或异常表现。",
        "- 包内不包含原始输入文件，只包含任务摘要、日志、结构化结果和环境探测。",
        "- 路径已做基础脱敏：项目目录显示为 <PROJECT_ROOT>，用户目录显示为 <USER_HOME>。",
        "",
        "## 当前任务",
        f"- 标题：{item.get('title', '')}",
        f"- 功能：{_feature_label(context, item.get('task_type'), '未知任务')}",
        f"- 状态：{context.queue_status_text(item.get('status'))}",
        f"- 失败分类：{context.failure_value_to_label.get(failure_kind, failure_kind or '未知失败')}",
    ]
    if failure_reason:
        lines.append(f"- 失败原因：{failure_reason}")
    if task_result:
        lines.extend(
            [
                f"- 处理总数：{task_result.get('processed_count', 0)}",
                f"- 成功数：{task_result.get('success_count', 0)}",
                f"- 失败数：{task_result.get('failed_count', 0)}",
                f"- 跳过数：{task_result.get('skipped_count', 0)}",
                f"- 输出策略：{task_result.get('output_strategy_label') or task_result.get('output_strategy') or ''}",
            ]
        )
    lines.extend(
        [
            "",
            "## 环境摘要",
            f"- 软件版本：{environment.get('app', {}).get('display_version', '')} ({environment.get('app', {}).get('release_version', '')})",
            f"- 系统：{environment.get('system', {}).get('platform', '')}",
            f"- Python：{environment.get('system', {}).get('python', '').splitlines()[0]}",
            f"- ffmpeg：{'可用' if environment.get('dependencies', {}).get('ffmpeg', {}).get('available') else '不可用'}",
        ]
    )
    office = environment.get("dependencies", {}).get("office", {})
    lines.append(f"- Word COM：{'可用' if office.get('word', {}).get('available') else '不可用'}")
    lines.append(f"- PowerPoint COM：{'可用' if office.get('powerpoint', {}).get('available') else '不可用'}")
    return "\n".join(lines)


def build_recent_history_diagnostic_snapshot(
    entry: Any,
    context: TaskHistoryExportContext,
    *,
    limit: int = 12,
) -> list[dict]:
    selected = _item(entry)
    try:
        history = context.load_queue_history()
    except Exception:
        history = []
    if not isinstance(history, list):
        history = []
    recent = history[-limit:]
    selected_id = selected.get("id")
    if selected and selected_id and all(item.get("id") != selected_id for item in recent if isinstance(item, dict)):
        recent.append(selected)
    snapshot = []
    for item in recent:
        if not isinstance(item, dict):
            continue
        task_result = _task_result(item)
        failure_kind, failure_reason = context.classify_failure_reason(item)
        snapshot.append(
            {
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "task_type": item.get("task_type", ""),
                "status": item.get("status", ""),
                "created_at": item.get("created_at"),
                "finished_at": item.get("finished_at"),
                "input": item.get("input", ""),
                "output_root": task_result.get("output_root") or item.get("output_root", ""),
                "error": task_result.get("error") or item.get("error", ""),
                "failure_kind": failure_kind,
                "failure_reason": failure_reason,
            }
        )
    return snapshot


def export_task_history_diagnostic_package(
    entry: Any,
    output_path: Any,
    context: TaskHistoryExportContext,
) -> tuple[bool, str]:
    item = _item(entry)
    if not item:
        return False, "当前历史记录为空，无法导出诊断包。"
    normalized_output = context.normalize_path(output_path)
    if not normalized_output:
        return False, "未选择导出位置。"
    if not normalized_output.lower().endswith(".zip"):
        normalized_output += ".zip"
    try:
        output = Path(normalized_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        task_result = _task_result(item)
        environment = context.probe_environment()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            diagnostic_write_text(archive, "README.md", build_diagnostic_summary(item, environment, context), context)
            diagnostic_write_json(archive, "task_history_entry.json", item, context)
            diagnostic_write_json(archive, "task_result.json", task_result, context)
            diagnostic_write_text(archive, "task_report.md", build_task_history_report_text(item, context), context)
            diagnostic_write_text(archive, "task_log.txt", build_task_history_log_export_text(item, context), context)
            diagnostic_write_json(archive, "environment.json", environment, context)
            diagnostic_write_json(
                archive,
                "recent_history.json",
                build_recent_history_diagnostic_snapshot(item, context),
                context,
            )
        return True, str(output.resolve())
    except Exception as exc:
        _debug(context, f"queue:diagnostic_export_error:{exc}")
        return False, f"导出失败：{normalized_output}"
