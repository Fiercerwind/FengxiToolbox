"""User preference storage helpers for Fengxi Toolbox."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping


@dataclass
class UserPrefsContext:
    pref_file: Callable[[], Path]
    output_strategy_values: tuple[str, ...] = ("result_folder", "same_dir", "overwrite")
    output_strategy_default: str = "result_folder"
    remove_wm_values: tuple[str, ...] = ("conservative", "standard", "aggressive")
    remove_wm_default: str = "conservative"
    remove_wm_label_to_value: Mapping[str, str] = field(default_factory=dict)
    filename_rule_positions: tuple[str, ...] = ("开头", "结尾")
    preset_categories: tuple[str, ...] = ("watermark", "ocr", "pdf_compress", "rename")
    preset_category_labels: Mapping[str, str] = field(default_factory=dict)
    preset_category_to_task: Mapping[str, str] = field(default_factory=dict)
    preset_label_to_category: Mapping[str, str] = field(default_factory=dict)
    debug: Callable[[str], None] | None = None


def _debug(context: UserPrefsContext, message: str) -> None:
    try:
        if callable(context.debug):
            context.debug(message)
    except Exception:
        pass


def load_user_prefs(context: UserPrefsContext) -> dict:
    path = Path(context.pref_file())
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception as exc:
        _debug(context, f"user_prefs:load_error:{exc}")
    return {}


def save_user_prefs(data: Any, context: UserPrefsContext) -> None:
    path = Path(context.pref_file())
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        safe_data = data if isinstance(data, dict) else {}
        path.write_text(json.dumps(safe_data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        _debug(context, f"user_prefs:save_error:{exc}")


def coerce_output_strategy(value: Any, context: UserPrefsContext) -> str:
    normalized = str(value or "").strip()
    if normalized in context.output_strategy_values:
        return normalized
    return context.output_strategy_default


def get_saved_output_strategy(context: UserPrefsContext) -> str:
    prefs = load_user_prefs(context)
    return coerce_output_strategy(prefs.get("output_strategy"), context)


def save_output_strategy(value: Any, context: UserPrefsContext) -> None:
    prefs = load_user_prefs(context)
    prefs["output_strategy"] = coerce_output_strategy(value, context)
    save_user_prefs(prefs, context)


def coerce_remove_wm_mode(value: Any, context: UserPrefsContext) -> str:
    normalized = str(value or "").strip()
    if normalized in context.remove_wm_values:
        return normalized
    mapped = context.remove_wm_label_to_value.get(normalized)
    if mapped in context.remove_wm_values:
        return mapped
    return context.remove_wm_default


def get_saved_remove_wm_mode(context: UserPrefsContext) -> str:
    prefs = load_user_prefs(context)
    watermark_prefs = prefs.get("watermark")
    if isinstance(watermark_prefs, dict):
        return coerce_remove_wm_mode(watermark_prefs.get("remove_wm_mode"), context)
    return context.remove_wm_default


def save_remove_wm_mode(value: Any, context: UserPrefsContext) -> None:
    prefs = load_user_prefs(context)
    watermark_prefs = prefs.get("watermark")
    if not isinstance(watermark_prefs, dict):
        watermark_prefs = {}
    watermark_prefs["remove_wm_mode"] = coerce_remove_wm_mode(value, context)
    prefs["watermark"] = watermark_prefs
    save_user_prefs(prefs, context)


def get_saved_watermark_text(context: UserPrefsContext) -> str:
    prefs = load_user_prefs(context)
    watermark_prefs = prefs.get("watermark")
    if isinstance(watermark_prefs, dict):
        value = watermark_prefs.get("text")
        if isinstance(value, str):
            return value
    return ""


def save_watermark_text(value: Any, context: UserPrefsContext) -> None:
    normalized = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    prefs = load_user_prefs(context)
    watermark_prefs = prefs.get("watermark")
    if not isinstance(watermark_prefs, dict):
        watermark_prefs = {}

    if normalized.strip():
        watermark_prefs["text"] = normalized
        prefs["watermark"] = watermark_prefs
    else:
        watermark_prefs.pop("text", None)
        if watermark_prefs:
            prefs["watermark"] = watermark_prefs
        else:
            prefs.pop("watermark", None)

    save_user_prefs(prefs, context)


def get_saved_watermark_filename_rule_settings(context: UserPrefsContext) -> dict:
    prefs = load_user_prefs(context)
    watermark_prefs = prefs.get("watermark")
    if not isinstance(watermark_prefs, dict):
        return {}
    settings = watermark_prefs.get("filename_skip_rule")
    if not isinstance(settings, dict):
        return {}

    saved = {}
    if "enabled" in settings:
        saved["enabled"] = bool(settings.get("enabled"))

    position = settings.get("position")
    if isinstance(position, str) and position in context.filename_rule_positions:
        saved["position"] = position

    marker = settings.get("marker")
    if isinstance(marker, str):
        saved["marker"] = marker
    return saved


def save_watermark_filename_rule_settings(
    context: UserPrefsContext,
    *,
    enabled: Any = False,
    position: Any = "结尾",
    marker: Any = "-",
) -> None:
    normalized_position = str(position or "").strip()
    if normalized_position not in context.filename_rule_positions:
        normalized_position = "结尾"

    prefs = load_user_prefs(context)
    watermark_prefs = prefs.get("watermark")
    if not isinstance(watermark_prefs, dict):
        watermark_prefs = {}

    watermark_prefs["filename_skip_rule"] = {
        "enabled": bool(enabled),
        "position": normalized_position,
        "marker": str(marker or ""),
    }
    prefs["watermark"] = watermark_prefs
    save_user_prefs(prefs, context)


def normalize_pref_category(value: Any, context: UserPrefsContext) -> str:
    normalized = str(value or "").strip()
    if normalized in context.preset_categories:
        return normalized
    mapped = context.preset_label_to_category.get(normalized)
    if mapped in context.preset_categories:
        return mapped
    return "watermark"


def load_last_settings(context: UserPrefsContext) -> dict:
    prefs = load_user_prefs(context)
    data = prefs.get("last_settings")
    if not isinstance(data, dict):
        return {}
    normalized = {}
    for raw_category, entry in data.items():
        category = normalize_pref_category(raw_category, context)
        settings = entry.get("settings") if isinstance(entry, dict) else entry
        if not isinstance(settings, dict):
            continue
        normalized[category] = {
            "category": category,
            "settings": settings,
            "updated_at": float((entry or {}).get("updated_at") or time.time()) if isinstance(entry, dict) else time.time(),
        }
    return normalized


def save_last_settings_entry(
    category: Any,
    settings: Mapping[str, Any] | None,
    context: UserPrefsContext,
    *,
    update_active: bool = True,
) -> dict | None:
    normalized_category = normalize_pref_category(category, context)
    if normalized_category not in context.preset_category_to_task:
        return None

    prefs = load_user_prefs(context)
    last_settings = prefs.get("last_settings")
    if not isinstance(last_settings, dict):
        last_settings = {}
    entry = {
        "category": normalized_category,
        "settings": dict(settings or {}),
        "updated_at": time.time(),
    }
    last_settings[normalized_category] = entry
    prefs["last_settings"] = last_settings

    if update_active:
        active = prefs.get("last_settings_active")
        if not isinstance(active, dict):
            active = {}
        task_type = context.preset_category_to_task.get(normalized_category)
        if task_type:
            active[task_type] = normalized_category
        prefs["last_settings_active"] = active

    save_user_prefs(prefs, context)
    return entry


def get_active_last_settings_category(task_name: Any, context: UserPrefsContext) -> str | None:
    normalized_task = str(task_name or "").strip()
    prefs = load_user_prefs(context)
    active = prefs.get("last_settings_active")
    if not isinstance(active, dict):
        active = {}
    category = normalize_pref_category(active.get(normalized_task), context)
    last_settings = load_last_settings(context)

    if normalized_task == "pdf":
        if category in {"ocr", "pdf_compress"}:
            return category
        if "ocr" in last_settings:
            return "ocr"
        if "pdf_compress" in last_settings:
            return "pdf_compress"
        return None
    if normalized_task == "file":
        return "rename" if "rename" in last_settings else None
    if normalized_task == "watermark":
        return "watermark" if "watermark" in last_settings else None
    return None


def make_preset_id(pid: int | None = None, now: float | None = None) -> str:
    import os

    current_pid = os.getpid() if pid is None else int(pid)
    current_time = time.time() if now is None else float(now)
    return f"preset_{int(current_time * 1000)}_{current_pid}"


def _category_label(category: str, context: UserPrefsContext) -> str:
    return str(context.preset_category_labels.get(category) or category or "预设")


def load_presets(context: UserPrefsContext) -> list[dict]:
    prefs = load_user_prefs(context)
    presets = prefs.get("presets")
    if not isinstance(presets, list):
        return []
    normalized = []
    for entry in presets:
        if not isinstance(entry, dict):
            continue
        category = normalize_pref_category(entry.get("category"), context)
        settings = entry.get("settings")
        if not isinstance(settings, dict):
            settings = {}
        name = str(entry.get("name") or "").strip()
        if not name:
            name = _category_label(category, context)
        normalized.append(
            {
                "id": str(entry.get("id") or make_preset_id()),
                "name": name,
                "category": category,
                "category_label": _category_label(category, context),
                "settings": settings,
                "created_at": float(entry.get("created_at") or time.time()),
                "updated_at": float(entry.get("updated_at") or entry.get("created_at") or time.time()),
            }
        )
    return normalized


def save_presets(presets: Any, context: UserPrefsContext, *, limit: int = 120) -> list[dict]:
    prefs = load_user_prefs(context)
    safe_presets = []
    for entry in list(presets or []):
        if not isinstance(entry, dict):
            continue
        category = normalize_pref_category(entry.get("category"), context)
        safe_presets.append(
            {
                "id": str(entry.get("id") or make_preset_id()),
                "name": str(entry.get("name") or _category_label(category, context)).strip(),
                "category": category,
                "category_label": _category_label(category, context),
                "settings": dict(entry.get("settings") or {}),
                "created_at": float(entry.get("created_at") or time.time()),
                "updated_at": float(entry.get("updated_at") or time.time()),
            }
        )
    prefs["presets"] = safe_presets[-int(limit) :]
    save_user_prefs(prefs, context)
    return prefs["presets"]


def save_preset_entry(
    name: Any,
    category: Any,
    settings: Mapping[str, Any] | None,
    context: UserPrefsContext,
    *,
    default_name_suffix: str = "",
) -> dict:
    normalized_category = normalize_pref_category(category, context)
    normalized_name = str(name or "").strip()
    if not normalized_name:
        suffix = str(default_name_suffix or "").strip()
        normalized_name = _category_label(normalized_category, context)
        if suffix:
            normalized_name = f"{normalized_name} {suffix}"

    presets = load_presets(context)
    now = time.time()
    matched = None
    for entry in presets:
        if entry.get("category") == normalized_category and str(entry.get("name") or "").strip() == normalized_name:
            matched = entry
            break
    if matched is None:
        matched = {
            "id": make_preset_id(now=now),
            "name": normalized_name,
            "category": normalized_category,
            "category_label": _category_label(normalized_category, context),
            "created_at": now,
        }
        presets.append(matched)
    matched["settings"] = dict(settings or {})
    matched["updated_at"] = now
    save_presets(presets, context)
    return dict(matched)


def delete_preset_entry(preset_id: Any, context: UserPrefsContext) -> bool:
    normalized_id = str(preset_id or "")
    presets = load_presets(context)
    kept = [entry for entry in presets if str(entry.get("id") or "") != normalized_id]
    if len(kept) == len(presets):
        return False
    save_presets(kept, context)
    return True


def find_preset_entry(preset_id: Any, context: UserPrefsContext) -> dict | None:
    normalized_id = str(preset_id or "")
    for entry in load_presets(context):
        if str(entry.get("id") or "") == normalized_id:
            return entry
    return None
