import io
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

from PIL import Image
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from tools.fx_task_history_exports import (
    TaskHistoryExportContext,
    build_task_history_export_filename,
    build_task_history_report_text,
)
from tools.fx_user_prefs import (
    UserPrefsContext,
    delete_preset_entry as delete_preset_entry_module,
    find_preset_entry as find_preset_entry_module,
    get_saved_output_strategy as get_saved_output_strategy_module,
    get_saved_remove_wm_mode as get_saved_remove_wm_mode_module,
    get_saved_watermark_filename_rule_settings as get_saved_watermark_filename_rule_settings_module,
    get_saved_watermark_text as get_saved_watermark_text_module,
    get_active_last_settings_category as get_active_last_settings_category_module,
    load_last_settings as load_last_settings_module,
    load_presets as load_presets_module,
    load_user_prefs as load_user_prefs_module,
    normalize_filename_rule_position as normalize_filename_rule_position_module,
    save_last_settings_entry as save_last_settings_entry_module,
    save_output_strategy as save_output_strategy_module,
    save_preset_entry as save_preset_entry_module,
    save_presets as save_presets_module,
    save_remove_wm_mode as save_remove_wm_mode_module,
    save_watermark_filename_rule_settings as save_watermark_filename_rule_settings_module,
    save_watermark_text as save_watermark_text_module,
)
from tools.fx_queue_history import (
    QueueHistoryContext,
    build_queue_history_search_blob,
    filter_queue_history_entries,
    load_queue_history as load_queue_history_module,
    normalize_queue_history_entry as normalize_queue_history_entry_module,
    prune_queue_history_entries as prune_queue_history_entries_module,
    queue_history_entry_timestamp as queue_history_entry_timestamp_module,
    queue_status_text as queue_status_text_module,
    save_queue_history as save_queue_history_module,
)
from tools.fx_resume import (
    is_nonempty_file as is_nonempty_file_module,
    outputs_are_complete as outputs_are_complete_module,
)
from tools.fx_watermark_core import (
    COPY_GUARD_METADATA_KEY as COPY_GUARD_METADATA_KEY_MODULE,
    COPY_GUARD_METADATA_VALUE as COPY_GUARD_METADATA_VALUE_MODULE,
    COPY_GUARD_TEXT_PREFIX as COPY_GUARD_TEXT_PREFIX_MODULE,
    WORD_COPY_GUARD_VALUE as WORD_COPY_GUARD_VALUE_MODULE,
    WORD_COPY_GUARD_VARIABLE as WORD_COPY_GUARD_VARIABLE_MODULE,
    _copy_guard_noise_lines as copy_guard_noise_lines_module,
    add_watermark_to_pdf as add_watermark_to_pdf_module,
    add_watermark_to_word as add_watermark_to_word_module,
    create_watermark_packet as create_watermark_packet_module,
    normalize_copy_guard_strength as normalize_copy_guard_strength_module,
    normalize_watermark_page_range as normalize_watermark_page_range_module,
)
from tools.fx_zip_core import (
    estimate_zip_progress_units as estimate_zip_progress_units_module,
    normalize_zip_archive_policy as normalize_zip_archive_policy_module,
    normalize_zip_depth_range as normalize_zip_depth_range_module,
    normalize_zip_max_depth as normalize_zip_max_depth_module,
    normalize_zip_mode as normalize_zip_mode_module,
    plan_zip_archives as plan_zip_archives_module,
    run_zip_task as run_zip_task_module,
)
from tools.fx_pdf_compress_core import (
    PDF_COMPRESS_LEVELS as PDF_COMPRESS_LEVELS_MODULE,
    PDF_IMAGE_COMPRESS_LEVELS as PDF_IMAGE_COMPRESS_LEVELS_MODULE,
    _build_ghostscript_env as build_ghostscript_env_module,
    _find_ghostscript_executable as find_ghostscript_executable_module,
    _run_ghostscript_candidate as run_ghostscript_candidate_module,
    build_pdf_compress_meta_path as build_pdf_compress_meta_path_module,
    build_pdf_compress_profile_stamp as build_pdf_compress_profile_stamp_module,
    build_pdf_compress_output_path as build_pdf_compress_output_path_module,
    compress_pdf_file as compress_pdf_file_module,
    pdf_compress_meta_matches as pdf_compress_meta_matches_module,
    write_pdf_compress_meta as write_pdf_compress_meta_module,
)
from tools.fx_file_manager_core import (
    apply_rename_to_file as apply_rename_to_file_module,
    deduplicate_files as deduplicate_files_module,
    normalize_file_rename_spec as normalize_file_rename_spec_module,
    plan_renamed_output_path as plan_renamed_output_path_module,
    rename_file_name as rename_file_name_module,
    run_file_dedup_task as run_file_dedup_task_module,
)
from tools.fx_file_manager_task import run_file_dedup_task_core as run_file_dedup_task_core_module
from tools.fx_audio_task import (
    AudioTaskCallbacks as AudioTaskCallbacksModule,
    build_audio_output_path as build_audio_output_path_module,
    collect_audio_files as collect_audio_files_module,
    get_audio_transcribe_args as get_audio_transcribe_args_module,
    get_audio_task_args as get_audio_task_args_module,
    process_one_audio_file as process_one_audio_file_module,
    run_audio_task_core as run_audio_task_core_module,
)
from tools.fx_speech_to_text import (
    build_transcript_output_paths as build_transcript_output_paths_module,
    transcribe_media_file as transcribe_media_file_module,
)
from tools.fx_convert_core import (
    CONVERT_MODE_SPECS as CONVERT_MODE_SPECS_MODULE,
    collect_convert_files as collect_convert_files_module,
    describe_convert_mode as describe_convert_mode_module,
    normalize_convert_mode as normalize_convert_mode_module,
    plan_convert_output_path as plan_convert_output_path_module,
)
from tools.fx_convert_task import (
    ConvertFileContext,
    ConvertImgsToPdfCallbacks,
    convert_md_to_pdf_file as convert_md_to_pdf_file_module,
    convert_pdf_to_md_file as convert_pdf_to_md_file_module,
    convert_txt_to_word_file as convert_txt_to_word_file_module,
    process_convert_file as process_convert_file_module,
    run_convert_imgs_to_pdf_task_core as run_convert_imgs_to_pdf_task_core_module,
)
from tools.fx_meta_core import (
    build_meta_output_path as build_meta_output_path_module,
    modify_file_timestamp as modify_file_timestamp_module,
    modify_office_meta as modify_office_meta_module,
    modify_pdf_author as modify_pdf_author_module,
    process_meta_file as process_meta_file_module,
)
from tools.fx_pdf_ocr_task import (
    PdfOcrTaskCallbacks,
    PdfOcrTaskOptions,
    build_pdf_ocr_compare_report_path,
    build_pdf_ocr_output_path,
    run_pdf_ocr_task_core,
)
import tools.fx_pdf_ocr_task as pdf_ocr_task_module
from tools.fx_image_pdf_task import (
    ImagePdfTaskCallbacks,
    ImagePdfTaskOptions,
    build_image_merge_pdf_output_path,
    build_image_pdf_output_path,
    collect_image_to_pdf_files,
    image_file_to_pdf,
    run_image_pdf_task_core,
)


def load_module():
    spec = importlib.util.spec_from_file_location("fengxi_toolbox", "Fengxi_Toolbox.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.messagebox.showinfo = lambda *args, **kwargs: None
    module.messagebox.showwarning = lambda *args, **kwargs: None
    module.messagebox.showerror = lambda *args, **kwargs: None
    module.messagebox.askokcancel = lambda *args, **kwargs: True
    return module


class DummyApp:
    stop_event = False

    def __init__(self):
        self.logs = []

    def log(self, msg):
        self.logs.append(msg)


class AttrBox:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def make_pdf(path, lines):
    pdf = canvas.Canvas(str(path))
    for index, line in enumerate(lines):
        pdf.drawString(100, 700, line)
        if index != len(lines) - 1:
            pdf.showPage()
    pdf.save()


def make_long_image_pdf(path, image_path, width=1080, height=6976):
    pdf = canvas.Canvas(str(path), pagesize=(width, height))
    pdf.drawImage(ImageReader(str(image_path)), 0, 0, width=width, height=height)
    pdf.save()


def first_pdf_image_size(path):
    import fitz

    with fitz.open(str(path)) as document:
        for page in document:
            images = page.get_images(full=True)
            if images:
                info = document.extract_image(images[0][0])
                return int(info.get("width", 0)), int(info.get("height", 0))
    return 0, 0


def rendered_pdf_nonwhite_pixels(path):
    import fitz

    with fitz.open(str(path)) as document:
        pixmap = document[0].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    image = Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")
    width, height = image.size
    crop = image.crop((int(width * 0.05), int(height * 0.15), int(width * 0.95), int(height * 0.9)))
    return sum(1 for red, green, blue in crop.getdata() if min(red, green, blue) < 245)


def rendered_pdf_page_nonwhite_pixels(path, page_index):
    import fitz

    with fitz.open(str(path)) as document:
        pixmap = document[page_index].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    image = Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")
    width, height = image.size
    crop = image.crop((int(width * 0.05), int(height * 0.15), int(width * 0.95), int(height * 0.9)))
    return sum(1 for red, green, blue in crop.getdata() if min(red, green, blue) < 245)


def rendered_pdf_redish_pixels(path):
    import fitz

    with fitz.open(str(path)) as document:
        pixmap = document[0].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    image = Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")
    width, height = image.size
    crop = image.crop((int(width * 0.05), int(height * 0.15), int(width * 0.95), int(height * 0.9)))
    return sum(1 for red, green, blue in crop.getdata() if red > green + 20 and red > blue + 20 and red > 120)


def wait_for(condition, timeout=15, interval=0.2):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return True
        time.sleep(interval)
    return condition()


def office_available(progid, mod=None):
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    try:
        if mod is not None and progid == "Word.Application":
            app = mod._create_hidden_word_app()
        else:
            app = win32com.client.DispatchEx(progid)
        version = getattr(app, "Version", None)
        app.Quit()
        return True, version
    except Exception as exc:
        return False, str(exc)
    finally:
        pythoncom.CoUninitialize()


def main():
    mod = load_module()
    root = Path(tempfile.mkdtemp(prefix="tmp_full_debug_", dir=Path.cwd())).resolve()
    os.environ["FX_PDF_COMPRESS_CACHE_DIR"] = str(root / "pdf_compress_cache")
    original_pref_root = mod._get_user_pref_root
    mod._get_user_pref_root = lambda: root / "user_prefs"
    dummy = DummyApp()
    results = []

    def record(name, ok, detail="", skipped=False):
        payload = {"case": name, "ok": bool(ok), "detail": str(detail), "skipped": bool(skipped)}
        results.append(payload)
        print(json.dumps(payload, ensure_ascii=True), flush=True)

    runtime_run_process = mod._unwrap_runtime_run_process(mod.FengxiToolboxApp.run_process)
    runtime_progress_map = mod._build_runtime_progress_site_map(runtime_run_process)
    record(
        "runtime_progress_site_map",
        bool(runtime_progress_map["before_process_single"])
        and bool(runtime_progress_map["direct_pre"])
        and bool(runtime_progress_map["pass_through"]),
        runtime_progress_map,
    )

    tracker_values = []
    fake_app = type("FakeProgressApp", (), {"stop_event": False})()
    tracker = mod._FxRunProgressTracker(
        fake_app,
        total_units=2,
        original_progress_set=lambda value: tracker_values.append(round(float(value), 4)),
        runtime_run_process=runtime_run_process,
        site_map=runtime_progress_map,
    )
    direct_offset = min(runtime_progress_map["direct_pre"])
    tracker.handle_runtime_progress_call(direct_offset, 0.5)
    tracker.handle_runtime_progress_call(direct_offset, 1.0)
    tracker.finalize_pending()
    record("progress_tracker_direct_loop", tracker_values == [0.0, 0.5, 1.0], tracker_values)

    tracker_values = []
    tracker = mod._FxRunProgressTracker(
        fake_app,
        total_units=2,
        original_progress_set=lambda value: tracker_values.append(round(float(value), 4)),
        runtime_run_process=runtime_run_process,
        site_map=runtime_progress_map,
    )
    process_offset = min(runtime_progress_map["before_process_single"])
    tracker.handle_runtime_progress_call(process_offset, 0.5)
    tracker.note_process_single_complete()
    tracker.handle_runtime_progress_call(process_offset, 1.0)
    tracker.note_process_single_complete()
    record("progress_tracker_process_single", tracker_values == [0.0, 0.5, 0.5, 1.0], tracker_values)

    progress_status_values = []

    class ProgressStatusVar:
        def set(self, value):
            progress_status_values.append(value)

    status_app = type("FakeProgressStatusApp", (), {"stop_event": False})()
    status_app._fx_progress_status_var = ProgressStatusVar()
    tracker = mod._FxRunProgressTracker(
        status_app,
        total_units=2,
        original_progress_set=lambda value: None,
        runtime_run_process=runtime_run_process,
        site_map=runtime_progress_map,
    )
    tracker.started_at = time.time() - 30
    tracker.set_current_item("D:/probe/scan.pdf", "OCR 准备")
    tracker.set_current_item_fraction(0.5, stage="OCR 第 1/2 页", current_file="D:/probe/scan.pdf")
    latest_progress_status = getattr(status_app, "_fx_last_progress_status", "")
    record(
        "progress_tracker_status_text",
        "当前：scan.pdf" in latest_progress_status
        and "阶段：OCR 第 1/2 页" in latest_progress_status
        and "文件：0/2" in latest_progress_status
        and "总进度：25%" in latest_progress_status
        and "预计剩余：" in latest_progress_status,
        latest_progress_status,
    )
    record(
        "progress_eta_format",
        mod._format_progress_eta(None) == "--"
        and mod._format_progress_eta(0.2) == "<1秒"
        and mod._format_progress_eta(65) == "01:05",
        {
            "none": mod._format_progress_eta(None),
            "short": mod._format_progress_eta(0.2),
            "minute": mod._format_progress_eta(65),
        },
    )

    history_path = mod._get_queue_history_file()
    history_path.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    old_entry = {
        "id": "old_history",
        "title": "old history",
        "status": "success",
        "task_type": "pdf",
        "finished_at": now - (mod.QUEUE_HISTORY_RETENTION_DAYS + 2) * 86400,
    }
    recent_entry = {
        "id": "recent_history",
        "title": "recent history",
        "status": "failed",
        "task_type": "zip",
        "finished_at": now - 3600,
    }
    undated_entry = {
        "id": "undated_history",
        "title": "undated history",
        "status": "skipped",
        "task_type": "file",
    }
    history_path.write_text(
        json.dumps([old_entry, recent_entry, undated_entry], ensure_ascii=False),
        encoding="utf-8",
    )
    loaded_history = mod._load_queue_history()
    persisted_history = json.loads(history_path.read_text(encoding="utf-8"))
    record(
        "queue_history_auto_prune_old",
        [item.get("id") for item in loaded_history] == ["recent_history", "undated_history"]
        and [item.get("id") for item in persisted_history] == ["recent_history", "undated_history"],
        persisted_history,
    )
    module_history_path = root / "queue_history_module.json"
    module_context = QueueHistoryContext(
        history_file=lambda: module_history_path,
        retention_days=mod.QUEUE_HISTORY_RETENTION_DAYS,
        history_limit=2,
        status_labels=mod.QUEUE_STATUS_LABELS,
        status_label_to_value=mod.QUEUE_HISTORY_STATUS_LABEL_TO_VALUE,
        task_label_to_value=mod.QUEUE_HISTORY_TASK_LABEL_TO_VALUE,
        failure_label_to_value=mod.QUEUE_HISTORY_FAILURE_LABEL_TO_VALUE,
        classify_failure_reason=mod._classify_failure_reason,
        task_result_snapshot=mod._task_result_snapshot,
        debug=lambda message: None,
    )
    noisy_task = {
        "id": "queued",
        "status": "queued",
        "status_var": object(),
        "row": object(),
        "retry_mode": "failed_subset",
        "task_result": {
            "task_type": "pdf",
            "status": "failed",
            "outputs": [str(root / "out.pdf")],
            "finished_at": now,
        },
    }
    normalized_module_entry = normalize_queue_history_entry_module(noisy_task, module_context)
    module_history_entries = [
        old_entry,
        {"id": "middle", "status": "success", "task_type": "pdf", "finished_at": now - 10},
        recent_entry,
        undated_entry,
    ]
    save_queue_history_module(module_history_entries, module_context)
    loaded_module_history = load_queue_history_module(module_context)
    module_blob = build_queue_history_search_blob(
        {
            "title": "PDF 工具 · 失败样本",
            "status": "failed",
            "task_type": "pdf",
            "error": "路径不存在: probe.pdf",
            "task_result": {"error": "路径不存在: probe.pdf", "failed_items": ["probe.pdf"]},
        },
        module_context,
    )
    module_filtered = filter_queue_history_entries(
        [
            {"title": "ok", "status": "success", "task_type": "pdf"},
            {
                "title": "missing",
                "status": "failed",
                "task_type": "pdf",
                "error": "路径不存在: probe.pdf",
                "task_result": {"error": "路径不存在: probe.pdf"},
            },
        ],
        module_context,
        status_filter="仅失败",
        task_filter="PDF 工具",
        failure_filter="路径缺失",
        keyword="路径不存在",
    )
    record(
        "queue_history_module_context",
        normalized_module_entry.get("status_var") is None
        and normalized_module_entry.get("retry_mode") is None
        and isinstance(normalized_module_entry.get("task_result"), dict)
        and [item.get("id") for item in loaded_module_history] == ["recent_history", "undated_history"]
        and queue_status_text_module("failed", module_context) == "失败"
        and queue_history_entry_timestamp_module({"task_result": {"finished_at": now}}) == now
        and "path_missing" in module_blob
        and len(module_filtered) == 1
        and module_filtered[0].get("title") == "missing",
        {
            "normalized_keys": sorted(normalized_module_entry.keys()),
            "loaded": loaded_module_history,
            "blob": module_blob,
            "filtered": module_filtered,
            "pruned": prune_queue_history_entries_module(module_history_entries, module_context, now=now),
        },
    )
    mod._save_queue_history([])

    perf_path = mod._get_performance_log_file()
    record(
        "performance_log_path_under_user_prefs",
        perf_path == root / "user_prefs" / "performance.jsonl",
        perf_path,
    )
    mod._FX_PERFORMANCE_RECORDER = None
    performance_entry = mod._record_performance(
        "debug_probe",
        started_at=mod.FxPerformanceRecorder.now() - 0.01,
        task_name="pdf",
        details={"status": "success"},
    )
    recent_performance_entries = mod._load_recent_performance_entries(limit=5)
    record(
        "performance_record_helper_jsonl",
        perf_path.exists()
        and performance_entry.get("event") == "debug_probe"
        and performance_entry.get("task_name") == "pdf"
        and isinstance(performance_entry.get("elapsed_ms"), float)
        and recent_performance_entries[-1].get("event") == "debug_probe",
        {
            "entry": performance_entry,
            "recent": recent_performance_entries[-2:],
        },
    )

    prune_path = root / "perf_prune.jsonl"
    recorder = mod.FxPerformanceRecorder(prune_path, app_version="test", max_entries=25)
    for index in range(35):
        recorder.record("probe", details={"index": index})
    pruned_entries = mod.load_performance_entries(prune_path)
    record(
        "performance_recorder_prune",
        len(pruned_entries) == 25
        and pruned_entries[0].get("details", {}).get("index") == 10
        and pruned_entries[-1].get("details", {}).get("index") == 34,
        [item.get("details", {}).get("index") for item in pruned_entries[:3] + pruned_entries[-3:]],
    )

    class WrapProbe:
        def ping(self, value):
            return value + 1

    wrap_logs = []
    wrap_ok = mod.wrap_callable(WrapProbe, "ping", label="wrap_probe", debug=wrap_logs.append)
    wrap_result = WrapProbe().ping(4)
    record(
        "runtime_patch_wrap_callable_module",
        wrap_ok
        and wrap_result == 5
        and wrap_logs == ["wrap_probe:start", "wrap_probe:done"],
        {"ok": wrap_ok, "result": wrap_result, "logs": wrap_logs},
    )

    class FakeCtk:
        def __init__(self):
            self.ctk_ready = True

        def withdraw(self):
            self.withdrawn = True

    class FakeStartupApp:
        def __init__(self):
            self.events = []
            self.pdf_init_count = 0

        def init_watermark_ui(self):
            self.events.append("init_watermark")

        def init_pdf_ui(self):
            self.pdf_init_count += 1
            self.events.append("init_pdf")

        def setup_main_area(self):
            self.init_watermark_ui()
            self.init_pdf_ui()
            return "main_ready"

        def switch_tab(self, task_name, btn_obj):
            self.events.append(f"switch:{task_name}")
            return "switched"

        def update_idletasks(self):
            self.events.append("idle")

    startup_patch_logs = []
    startup_patch_perf = []
    startup_patch_lazy = []
    startup_patch_refresh = []
    startup_context = mod.StartupPatchContext(
        app_class=FakeStartupApp,
        ctk_class=FakeCtk,
        lazy_tab_specs={"watermark": {"init": "init_watermark_ui"}, "pdf": {"init": "init_pdf_ui"}},
        default_startup_tab="watermark",
        debug=startup_patch_logs.append,
        get_internal_attr=lambda obj, name, default=None: getattr(obj, name, default),
        ensure_lazy_tab_initialized=lambda app_obj, task_name: startup_patch_lazy.append(task_name) or True,
        show_inline_help=lambda app_obj: "help_inline",
        show_inline_donate=lambda app_obj: "donate_inline",
        set_help_button_selected=lambda app_obj, selected: startup_patch_refresh.append(("help", selected)),
        set_donate_button_selected=lambda app_obj, selected: startup_patch_refresh.append(("donate", selected)),
        set_help_action_state=lambda app_obj, selected: startup_patch_refresh.append(("help_action", selected)),
        refresh_output_strategy_hint=lambda app_obj: startup_patch_refresh.append(("output", True)),
        refresh_parallel_mode_hint=lambda app_obj: startup_patch_refresh.append(("parallel", True)),
        refresh_visible_tab_layout=lambda app_obj, task_name: startup_patch_refresh.append(("layout", task_name)),
        guess_lazy_tab_for_attr=lambda name: "pdf" if str(name).startswith("pdf_") else None,
        record_performance=lambda event, **kwargs: startup_patch_perf.append((event, kwargs)),
    )
    startup_installed = mod.install_startup_performance_patch(startup_context)
    startup_installed_again = mod.install_startup_performance_patch(startup_context)
    fake_window = FakeCtk()
    fake_startup_app = FakeStartupApp()
    setup_main_result = fake_startup_app.setup_main_area()
    fake_startup_app._fx_lazy_tabs_initializing.add("pdf")
    try:
        getattr(fake_startup_app, "pdf_probe")
        reentrant_getattr_blocked = False
    except AttributeError:
        reentrant_getattr_blocked = True
    fake_startup_app._fx_lazy_tabs_initializing.clear()
    switch_result = fake_startup_app.switch_tab("pdf", None)
    help_result = fake_startup_app.show_readme()
    donate_result = fake_startup_app.show_donate_window()
    record(
        "startup_patch_installer_module",
        startup_installed
        and not startup_installed_again
        and getattr(fake_window, "_fx_start_hidden", False)
        and setup_main_result == "main_ready"
        and "init_watermark" not in fake_startup_app.events
        and fake_startup_app.pdf_init_count == 0
        and fake_startup_app._fx_lazy_tabs_initializing == set()
        and fake_startup_app._fx_lazy_tabs_state == {"watermark": False, "pdf": False}
        and reentrant_getattr_blocked
        and switch_result == "switched"
        and startup_patch_lazy == ["pdf"]
        and startup_patch_perf[-1][0] == "switch_tab"
        and help_result == "help_inline"
        and donate_result == "donate_inline",
        {
            "installed": startup_installed,
            "installed_again": startup_installed_again,
            "window_hidden": getattr(fake_window, "_fx_start_hidden", False),
            "setup": setup_main_result,
            "events": fake_startup_app.events,
            "pdf_init_count": fake_startup_app.pdf_init_count,
            "reentrant_getattr_blocked": reentrant_getattr_blocked,
            "lazy": startup_patch_lazy,
            "perf": startup_patch_perf[-1:] if startup_patch_perf else [],
            "refresh": startup_patch_refresh,
            "logs": startup_patch_logs,
        },
    )

    class StartupLayoutProbe:
        current_task = "watermark"

        def __init__(self):
            self._fx_startup_layout_refreshed = False
            self.tightened = []
            self.refreshed = []
            self.idle_count = 0

        def after(self, _delay_ms, callback):
            callback()

        def update_idletasks(self):
            self.idle_count += 1

    layout_probe = StartupLayoutProbe()
    original_apply_shell_layout_tightening = mod._apply_shell_layout_tightening
    original_tighten_single_tab_layout = mod._tighten_single_tab_layout
    original_refresh_visible = mod._refresh_visible_tab_layout
    try:
        mod._apply_shell_layout_tightening = lambda app_obj: app_obj.tightened.append("shell")
        mod._tighten_single_tab_layout = lambda app_obj, task_name: app_obj.tightened.append(task_name)
        mod._refresh_visible_tab_layout = lambda app_obj, task_name: app_obj.refreshed.append(task_name)
        mod._run_startup_layout_refresh(layout_probe)
    finally:
        mod._apply_shell_layout_tightening = original_apply_shell_layout_tightening
        mod._tighten_single_tab_layout = original_tighten_single_tab_layout
        mod._refresh_visible_tab_layout = original_refresh_visible
    record(
        "startup_layout_refresh_current_tab_only",
        layout_probe.tightened == ["shell", "watermark"]
        and layout_probe.refreshed == ["watermark"]
        and layout_probe.idle_count == 0,
        {
            "tightened": layout_probe.tightened,
            "refreshed": layout_probe.refreshed,
            "idle_count": layout_probe.idle_count,
        },
    )

    record(
        "startup_switch_tab_single_idle_refresh",
        fake_startup_app.events.count("idle") == 1,
        fake_startup_app.events,
    )

    app = mod.FengxiToolboxApp()
    app.withdraw()
    app._fx_disable_fast_close_force_exit = True
    record("app_init", True, "current_task=" + str(getattr(app, "current_task", None)))

    resume_probe = root / "resume_probe.txt"
    resume_probe.write_text("done", encoding="utf-8")
    record(
        "resume_helper_outputs_complete",
        is_nonempty_file_module(resume_probe)
        and outputs_are_complete_module([resume_probe])
        and not outputs_are_complete_module([resume_probe, root / "missing_resume_probe.txt"]),
        resume_probe,
    )

    background_calls = []

    def fake_guard_begin(self, reason):
        background_calls.append(("begin", reason))
        self._fx_background_guard_count = int(getattr(self, "_fx_background_guard_count", 0) or 0) + 1
        return True

    def fake_guard_end(self, reason):
        background_calls.append(("end", reason))
        self._fx_background_guard_count = max(0, int(getattr(self, "_fx_background_guard_count", 0) or 0) - 1)
        return True

    original_guard_begin = mod._fx_background_guard_begin
    original_guard_end = mod._fx_background_guard_end
    mod._fx_background_guard_begin = fake_guard_begin
    mod._fx_background_guard_end = fake_guard_end
    try:
        app.current_task = "meta"
        app.run_process(str(root / "empty_meta_probe"), "meta")
    finally:
        mod._fx_background_guard_begin = original_guard_begin
        mod._fx_background_guard_end = original_guard_end
    record(
        "background_guard_wrapped_run_process",
        background_calls == [("begin", "run_process:meta"), ("end", "run_process:meta")]
        and getattr(app, "_fx_background_guard_count", None) == 0,
        background_calls,
    )

    expected_feature_tasks = {
        "watermark",
        "remove_wm",
        "convert",
        "audio",
        "zip",
        "pdf",
        "image",
        "meta",
        "file",
    }
    record(
        "feature_registry_core_tasks",
        expected_feature_tasks.issubset(set(mod.FEATURE_REGISTRY))
        and not mod._get_feature_registry_errors()
        and set(mod.QUEUE_TASK_LABELS) == set(mod.FEATURE_REGISTRY),
        {
            "tasks": sorted(mod.FEATURE_REGISTRY),
            "errors": mod._get_feature_registry_errors(),
            "labels": mod.QUEUE_TASK_LABELS,
        },
    )
    record(
        "feature_registry_derived_policy_sets",
        mod.OUTPUT_STRATEGY_SUPPORTED_TASKS
        == {task for task, spec in mod.FEATURE_REGISTRY.items() if spec.get("output_strategy", {}).get("supported")}
        and mod.OUTPUT_STRATEGY_FORCE_RESULT_FOLDER_TASKS
        == {task for task, spec in mod.FEATURE_REGISTRY.items() if spec.get("output_strategy", {}).get("force_result_folder")}
        and "pdf" in mod.PARALLEL_SAFE_TASKS
        and "remove_wm" in mod.PARALLEL_FORCED_SINGLE_TASKS,
        {
            "output_supported": sorted(mod.OUTPUT_STRATEGY_SUPPORTED_TASKS),
            "output_forced": sorted(mod.OUTPUT_STRATEGY_FORCE_RESULT_FOLDER_TASKS),
            "parallel_safe": sorted(mod.PARALLEL_SAFE_TASKS),
            "parallel_forced": sorted(mod.PARALLEL_FORCED_SINGLE_TASKS),
        },
    )
    record(
        "feature_registry_preview_labels",
        mod._get_feature_preview_mode_label("pdf", "ocr") == "OCR 搜索版 PDF"
        and mod._get_feature_preview_mode_label("image", "merge_pdf") == "多图合并 PDF"
        and mod._get_feature_preview_mode_label("convert", "imgs2pdf") == "多图合并 ➔ PDF电子书"
        and mod._get_feature_label("remove_wm") == "去除水印",
        {
            "pdf_ocr": mod._get_feature_preview_mode_label("pdf", "ocr"),
            "image_merge": mod._get_feature_preview_mode_label("image", "merge_pdf"),
            "convert_imgs": mod._get_feature_preview_mode_label("convert", "imgs2pdf"),
            "remove_wm": mod._get_feature_label("remove_wm"),
        },
    )

    help_blob = "\n".join(
        "\n".join((title, *lines))
        for title, lines in mod.INLINE_HELP_SECTIONS
    )
    help_required_terms = [
        "任务预览",
        "OCR 搜索版 PDF",
        "图像增强",
        "质量回退",
        "任务队列",
        "历史详情",
        "输出策略",
        "覆盖原文件",
        "保守（推荐）",
        "批量并行",
        "复制干扰层",
        "局部拖选一行正文",
        "截图后重新 OCR",
    ]
    record(
        "inline_help_workflow_sections",
        all(term in help_blob for term in help_required_terms)
        and len(mod.INLINE_HELP_SECTIONS) >= 10,
        {
            "sections": [title for title, _lines in mod.INLINE_HELP_SECTIONS],
            "missing": [term for term in help_required_terms if term not in help_blob],
        },
    )

    zip_help_lines = dict(mod.INLINE_HELP_SECTIONS).get("批量压缩", ())
    zip_help_blob = "\n".join(zip_help_lines)
    zip_help_required_terms = [
        "空目录",
        "混合边界早于所选起始层",
        "zip、rar、7z、tar、gz、bz2、xz、zst",
        ".DS_Store",
        "本次计划生成的 ZIP",
        "根目录名.zip",
        "原文件名_Backup.zip",
        "结构有效的 ZIP",
        "ZIP Deflate",
        "单线程逐包执行",
        "两个压缩包之间响应",
        "不会删除普通源文件",
    ]
    record(
        "zip_help_documents_complete_implementation_rules",
        tuple(zip_help_lines) == tuple(mod.ZIP_IMPLEMENTATION_HELP_LINES)
        and all(term in zip_help_blob for term in zip_help_required_terms)
        and all(term in mod.ZIP_MODE_DESCRIPTION_TEXT for term in zip_help_required_terms)
        and mod.ZIP_MODE_DESCRIPTION_TEXT.startswith("功能说明：新版智能压缩完整实现规则"),
        {
            "line_count": len(zip_help_lines),
            "missing_inline": [term for term in zip_help_required_terms if term not in zip_help_blob],
            "missing_panel": [term for term in zip_help_required_terms if term not in mod.ZIP_MODE_DESCRIPTION_TEXT],
        },
    )

    sidebar_preset_button = getattr(app, "btn_preset_center_sidebar", None)
    bottom_preset_button = getattr(app, "btn_preset_center", None)
    record(
        "last_settings_no_dedicated_preset_center",
        sidebar_preset_button is None
        and bottom_preset_button is None
        and not callable(getattr(mod, "_show_preset_center", None)),
        {
            "exists": sidebar_preset_button is not None,
            "text": sidebar_preset_button.cget("text") if sidebar_preset_button is not None else "",
            "bottom_exists": bottom_preset_button is not None,
            "window_func": callable(getattr(mod, "_show_preset_center", None)),
        },
    )

    progress_label = getattr(app, "_fx_progress_status_label", None)
    action_rows = [
        child
        for child in app.bottom_bar.winfo_children()
        if isinstance(child, mod.customtkinter.CTkFrame) and child.winfo_children()
    ]
    progress_grid = progress_label.grid_info() if progress_label is not None else {}
    progress_pack = {}
    try:
        progress_pack = progress_label.pack_info() if progress_label is not None else {}
    except Exception:
        progress_pack = {}
    record(
        "progress_status_separate_from_action_row",
        progress_label is not None
        and progress_label.winfo_manager() == "grid"
        and progress_label.master is app.bottom_bar
        and progress_grid.get("row") == 0
        and progress_grid.get("column") == 1
        and not progress_pack
        and all(progress_label not in row.winfo_children() for row in action_rows),
        {
            "manager": progress_label.winfo_manager() if progress_label is not None else None,
            "grid": progress_grid,
            "pack": progress_pack,
            "master_is_bottom": progress_label.master is app.bottom_bar if progress_label is not None else False,
            "action_rows": len(action_rows),
        },
    )

    def collect_widget_texts(widget):
        texts = []
        stack = [widget]
        while stack:
            current = stack.pop()
            try:
                text = current.cget("text")
            except Exception:
                text = None
            if isinstance(text, str) and text:
                texts.append(text)
            try:
                stack.extend(current.winfo_children())
            except Exception:
                pass
        return texts

    donate_toplevel_calls = []
    original_ctk_toplevel = mod.customtkinter.CTkToplevel

    def forbidden_donate_toplevel(*args, **kwargs):
        donate_toplevel_calls.append(True)
        raise AssertionError("donate should render inline, not open a popup")

    mod.customtkinter.CTkToplevel = forbidden_donate_toplevel
    try:
        app.show_donate_window()
        selected_tab = app.main_panel.get()
        donate_texts = "\n".join(collect_widget_texts(getattr(app, "tab_donate", app)))
        run_button_text = app.btn_run.cget("text")
    finally:
        mod.customtkinter.CTkToplevel = original_ctk_toplevel
    record(
        "inline_donate_page_no_popup",
        not donate_toplevel_calls
        and getattr(app, "current_task", None) == "donate"
        and selected_tab == mod.DONATE_TAB_TITLE
        and mod.DONATE_SUPPORT_SENTENCE in donate_texts
        and run_button_text == "查看赞助作者中",
        {
            "toplevel_calls": len(donate_toplevel_calls),
            "current_task": getattr(app, "current_task", None),
            "selected_tab": selected_tab,
            "has_sentence": mod.DONATE_SUPPORT_SENTENCE in donate_texts,
            "run_button": run_button_text,
        },
    )

    donate_toplevel_calls = []
    mod.customtkinter.CTkToplevel = forbidden_donate_toplevel
    try:
        app.switch_tab("watermark", app.btn_nav_wm)
        app.btn_donate.invoke()
        button_selected_tab = app.main_panel.get()
    finally:
        mod.customtkinter.CTkToplevel = original_ctk_toplevel
    record(
        "inline_donate_sidebar_button",
        not donate_toplevel_calls
        and getattr(app, "current_task", None) == "donate"
        and button_selected_tab == mod.DONATE_TAB_TITLE,
        {
            "toplevel_calls": len(donate_toplevel_calls),
            "current_task": getattr(app, "current_task", None),
            "selected_tab": button_selected_tab,
        },
    )
    app.switch_tab("watermark", app.btn_nav_wm)

    parallel_switch_text = ""
    try:
        parallel_switch_text = app.chk_multithread.cget("text")
    except Exception:
        pass
    record(
        "parallel_mode_label_truthful",
        parallel_switch_text == mod.PARALLEL_SWITCH_TEXT
        and "极速模式" not in parallel_switch_text
        and "可提速" in mod._get_parallel_mode_message(app, "watermark"),
        {
            "switch": parallel_switch_text,
            "watermark": mod._get_parallel_mode_message(app, "watermark"),
        },
    )
    mod._ensure_lazy_tab_initialized(app, "pdf")
    app.pdf_mode_var.set("ocr")
    record(
        "parallel_mode_forced_single_hints",
        "稳定单线程" in mod._get_parallel_mode_message(app, "pdf")
        and "OCR" in mod._get_parallel_mode_message(app, "pdf"),
        mod._get_parallel_mode_message(app, "pdf"),
    )
    app.pdf_mode_var.set("compress")
    record(
        "parallel_mode_pdf_compress_available",
        "可提速" in mod._get_parallel_mode_message(app, "pdf")
        and "压缩" in mod._get_parallel_mode_message(app, "pdf"),
        mod._get_parallel_mode_message(app, "pdf"),
    )
    mod._ensure_lazy_tab_initialized(app, "image")
    app.img_mode_var.set("to_pdf")
    record(
        "parallel_mode_image_to_pdf_available",
        "可提速" in mod._get_parallel_mode_message(app, "image")
        and "转 PDF" in mod._get_parallel_mode_message(app, "image"),
        mod._get_parallel_mode_message(app, "image"),
    )
    record(
        "parallel_hint_removed_queue_actions_kept",
        getattr(app, "_fx_parallel_hint_label", None) is None
        and getattr(app, "_fx_parallel_hint_var", None).get() == ""
        and hasattr(app, "btn_queue_add")
        and hasattr(app, "btn_queue_panel"),
        {
            "parallel_label": str(getattr(app, "_fx_parallel_hint_label", None)),
            "parallel_hint": getattr(app, "_fx_parallel_hint_var", None).get()
            if getattr(app, "_fx_parallel_hint_var", None) is not None
            else None,
            "queue_add": hasattr(app, "btn_queue_add"),
            "queue_panel": hasattr(app, "btn_queue_panel"),
        },
    )

    mod._save_output_strategy("overwrite")
    app._fx_output_strategy_memory_ready = False
    mod._install_output_strategy_memory(app)
    record(
        "output_strategy_memory_save_load",
        mod._get_saved_output_strategy() == "overwrite"
        and getattr(app, "output_strategy_var", None).get() == mod.OUTPUT_STRATEGY_VALUE_TO_LABEL["overwrite"],
        {
            "saved": mod._get_saved_output_strategy(),
            "ui": getattr(app, "output_strategy_var", None).get(),
        },
    )
    mod._save_output_strategy("result_folder")
    app._fx_output_strategy_memory_ready = False
    mod._install_output_strategy_memory(app)

    user_prefs_module_path = root / "user_prefs_module" / "user_prefs.json"
    user_prefs_context = UserPrefsContext(
        pref_file=lambda: user_prefs_module_path,
        output_strategy_values=mod.OUTPUT_STRATEGY_VALUES,
        output_strategy_default=mod.OUTPUT_STRATEGY_DEFAULT,
        remove_wm_values=mod.REMOVE_WM_MODE_VALUES,
        remove_wm_default=mod.REMOVE_WM_MODE_DEFAULT,
        remove_wm_label_to_value=mod.REMOVE_WM_MODE_LABEL_TO_VALUE,
        preset_categories=tuple(mod.PRESET_CATEGORY_LABELS.keys()),
        preset_category_labels=mod.PRESET_CATEGORY_LABELS,
        preset_category_to_task=mod.PRESET_CATEGORY_TO_TASK,
        preset_label_to_category=mod.PRESET_LABEL_TO_CATEGORY,
    )
    save_output_strategy_module("overwrite", user_prefs_context)
    save_remove_wm_mode_module(mod.REMOVE_WM_MODE_VALUE_TO_LABEL["standard"], user_prefs_context)
    save_watermark_text_module("Line1\r\nLine2", user_prefs_context)
    save_watermark_filename_rule_settings_module(
        user_prefs_context,
        enabled=True,
        position="开头",
        marker="FX",
        copy_skipped=True,
    )
    user_prefs_payload = load_user_prefs_module(user_prefs_context)
    record(
        "user_prefs_module_context",
        get_saved_output_strategy_module(user_prefs_context) == "overwrite"
        and get_saved_remove_wm_mode_module(user_prefs_context) == "standard"
        and get_saved_watermark_text_module(user_prefs_context) == "Line1\nLine2"
        and get_saved_watermark_filename_rule_settings_module(user_prefs_context)
        == {"enabled": True, "position": "开头", "marker": "FX", "copy_skipped": True},
        user_prefs_payload,
    )
    record(
        "watermark_filename_rule_position_normalization",
        normalize_filename_rule_position_module("prefix", user_prefs_context) == "开头"
        and normalize_filename_rule_position_module("start", user_prefs_context) == "开头"
        and normalize_filename_rule_position_module("末尾", user_prefs_context) == "结尾"
        and normalize_filename_rule_position_module("suffix", user_prefs_context) == "结尾",
        {
            "prefix": normalize_filename_rule_position_module("prefix", user_prefs_context),
            "start": normalize_filename_rule_position_module("start", user_prefs_context),
            "end_label": normalize_filename_rule_position_module("末尾", user_prefs_context),
            "suffix": normalize_filename_rule_position_module("suffix", user_prefs_context),
        },
    )
    saved_last_settings_entry = save_last_settings_entry_module(
        "ocr",
        {"category": "ocr", "pdf_ocr_backend": "auto"},
        user_prefs_context,
        update_active=True,
    )
    loaded_last_settings_module = load_last_settings_module(user_prefs_context)
    record(
        "user_prefs_last_settings_module_context",
        isinstance(saved_last_settings_entry, dict)
        and loaded_last_settings_module.get("ocr", {}).get("settings", {}).get("pdf_ocr_backend") == "auto"
        and get_active_last_settings_category_module("pdf", user_prefs_context) == "ocr",
        {
            "entry": saved_last_settings_entry,
            "loaded": loaded_last_settings_module,
            "active_pdf": get_active_last_settings_category_module("pdf", user_prefs_context),
        },
    )
    saved_preset_entry = save_preset_entry_module(
        "",
        "pdf_compress",
        {"pdf_compress_level_var": "强力"},
        user_prefs_context,
        default_name_suffix="debug",
    )
    loaded_presets_module = load_presets_module(user_prefs_context)
    found_preset_module = find_preset_entry_module(saved_preset_entry.get("id"), user_prefs_context)
    delete_preset_ok = delete_preset_entry_module(saved_preset_entry.get("id"), user_prefs_context)
    record(
        "user_prefs_presets_module_context",
        isinstance(saved_preset_entry, dict)
        and saved_preset_entry.get("name") == "PDF 压缩 debug"
        and len(loaded_presets_module) == 1
        and found_preset_module is not None
        and delete_preset_ok
        and load_presets_module(user_prefs_context) == [],
        {
            "saved": saved_preset_entry,
            "loaded": loaded_presets_module,
            "found": found_preset_module,
            "deleted": delete_preset_ok,
        },
    )
    save_presets_module([], user_prefs_context)

    preview_root = root / "start_preview"
    preview_root.mkdir()
    make_pdf(preview_root / "a.pdf", ["preview a"])
    make_pdf(preview_root / "b.pdf", ["preview b"])
    (preview_root / "note.txt").write_text("ignore", encoding="utf-8")
    app.current_task = "pdf"
    app.pdf_mode_var.set("compress")
    app.pdf_delete_var.set(True)
    preview = mod._build_start_preview(app, str(preview_root), "pdf")
    record(
        "start_preview_counts_and_risks",
        preview["effective_count"] == 2
        and preview["total_count"] == 2
        and preview["mode_detail"] == "PDF 压缩"
        and "删除源文件" in " ".join(preview["risks"]),
        preview,
    )

    preview_messages = []
    original_askokcancel = mod.tkinter.messagebox.askokcancel
    mod.tkinter.messagebox.askokcancel = lambda title, message, **kwargs: preview_messages.append((title, message)) or False
    try:
        confirm_result = mod._confirm_start_preview(app, str(preview_root), "pdf")
    finally:
        mod.tkinter.messagebox.askokcancel = original_askokcancel
    record(
        "start_preview_confirmation_cancel",
        confirm_result is False
        and preview_messages
        and "将处理：2 个文件" in preview_messages[0][1]
        and "PDF 处理完成后会删除源文件" in preview_messages[0][1],
        preview_messages[0][1] if preview_messages else "",
    )

    queue_preview_messages = []
    mod.tkinter.messagebox.askokcancel = lambda *args, **kwargs: queue_preview_messages.append(args) or False
    app._fx_start_via_queue = True
    try:
        queue_confirm_result = mod._confirm_start_preview(app, str(preview_root), "pdf")
    finally:
        app._fx_start_via_queue = False
        mod.tkinter.messagebox.askokcancel = original_askokcancel
        app.pdf_delete_var.set(False)
    record(
        "start_preview_skips_queue_worker",
        queue_confirm_result is True and not queue_preview_messages,
        queue_preview_messages,
    )

    mod._save_remove_wm_mode("aggressive")
    remove_mode_probe = type("RemoveWmModeProbe", (), {})()
    remove_mode_probe.rm_wm_mode_var = mod.tkinter.StringVar(master=app, value="")
    remove_mode_probe.rm_wm_mode_hint_var = mod.tkinter.StringVar(master=app, value="")
    mod._install_remove_wm_mode_memory(remove_mode_probe)
    record(
        "remove_wm_mode_memory_save_load",
        mod._get_saved_remove_wm_mode() == "aggressive"
        and remove_mode_probe.rm_wm_mode_var.get() == mod.REMOVE_WM_MODE_VALUE_TO_LABEL["aggressive"]
        and "强力模式" in remove_mode_probe.rm_wm_mode_hint_var.get(),
        {
            "saved": mod._get_saved_remove_wm_mode(),
            "ui": remove_mode_probe.rm_wm_mode_var.get(),
            "hint": remove_mode_probe.rm_wm_mode_hint_var.get(),
        },
    )
    remove_mode_probe.rm_wm_mode_var.set(mod.REMOVE_WM_MODE_VALUE_TO_LABEL["standard"])
    record(
        "remove_wm_mode_memory_trace_save",
        mod._get_saved_remove_wm_mode() == "standard",
        mod._get_saved_remove_wm_mode(),
    )
    mod._save_remove_wm_mode("conservative")

    standard_shape_candidate = AttrBox(
        Name="",
        AlternativeText="",
        Title="",
        TextEffect=AttrBox(Text=""),
        TextFrame=AttrBox(HasText=False),
        Width=360,
        Height=210,
        Left=320,
        Top=395,
        Rotation=15,
        Fill=AttrBox(Transparency=0.16),
    )
    shape_mode_checks = {
        mode: mod._shape_looks_like_watermark(standard_shape_candidate, 1000, 1000, mode=mode)
        for mode in ("conservative", "standard", "aggressive")
    }
    record(
        "remove_wm_mode_shape_thresholds",
        shape_mode_checks == {"conservative": False, "standard": True, "aggressive": True},
        shape_mode_checks,
    )

    standard_inline_candidate = AttrBox(
        AlternativeText="",
        Title="",
        Range=AttrBox(Text=""),
        Width=500,
        Height=170,
    )
    inline_mode_checks = {
        mode: mod._inline_shape_looks_like_watermark(standard_inline_candidate, 1000, 1000, mode=mode)
        for mode in ("conservative", "standard", "aggressive")
    }
    record(
        "remove_wm_mode_inline_thresholds",
        inline_mode_checks == {"conservative": False, "standard": True, "aggressive": True},
        inline_mode_checks,
    )

    mod._install_watermark_last_settings_memory(app)
    app.selected_font.set("AutoMemoryFont")
    app.wm_range_var.set("first")
    app.wm_overwrite_var.set("force")
    app.allow_simsun.set(True)
    app.wm_delete_var.set(True)
    app.wm_convert_pdf.set(True)
    app.wm_skip_hyphen_var.set(True)
    app.wm_skip_name_position_var.set("开头")
    app.wm_skip_name_text_var.set("AUTO")
    app.wm_copy_skipped_var.set(True)
    app.wm_skip_pdf_type_var.set(True)
    app.wm_skip_word_type_var.set(False)
    app.wm_skip_ppt_type_var.set(True)
    app.wm_color_var.set("#336699")
    for slider_name, slider_value in (("slider_size", 66), ("slider_opacity", 0.31), ("slider_angle", 27)):
        mod._safe_named_widget_set(app, slider_name, slider_value)
        slider = getattr(app, slider_name, None)
        command = getattr(slider, "_command", None)
        if callable(command):
            command(slider.get())
    app.update()
    time.sleep(0.45)
    app.update()
    auto_watermark_settings = (mod._load_last_settings().get("watermark") or {}).get("settings", {})
    record(
        "watermark_parameters_auto_memory",
        auto_watermark_settings.get("selected_font") == "AutoMemoryFont"
        and auto_watermark_settings.get("wm_range_var") == "first"
        and auto_watermark_settings.get("wm_overwrite_var") == "force"
        and auto_watermark_settings.get("allow_simsun") is True
        and auto_watermark_settings.get("wm_delete_var") is True
        and auto_watermark_settings.get("wm_convert_pdf") is True
        and auto_watermark_settings.get("wm_skip_hyphen_var") is True
        and auto_watermark_settings.get("wm_skip_name_position_var") == "开头"
        and auto_watermark_settings.get("wm_skip_name_text_var") == "AUTO"
        and auto_watermark_settings.get("wm_copy_skipped_var") is True
        and auto_watermark_settings.get("wm_skip_pdf_type_var") is True
        and auto_watermark_settings.get("wm_skip_word_type_var") is False
        and auto_watermark_settings.get("wm_skip_ppt_type_var") is True
        and auto_watermark_settings.get("wm_color_var") == "#336699"
        and abs(float(auto_watermark_settings.get("slider_size", 0)) - float(app.slider_size.get())) < 0.01
        and abs(float(auto_watermark_settings.get("slider_opacity", 0)) - float(app.slider_opacity.get())) < 0.01
        and abs(float(auto_watermark_settings.get("slider_angle", 0)) - float(app.slider_angle.get())) < 0.01,
        auto_watermark_settings,
    )

    mod._safe_named_widget_set(app, "wm_text", "Preset Watermark\nCONFIDENTIAL")
    app.selected_font.set("SmileySans-Oblique")
    app.wm_range_var.set("first")
    app.wm_overwrite_var.set("force")
    app.wm_skip_hyphen_var.set(True)
    app.wm_skip_name_position_var.set("开头")
    app.wm_skip_name_text_var.set("FX")
    app.wm_copy_skipped_var.set(True)
    app.wm_skip_pdf_type_var.set(False)
    app.wm_skip_word_type_var.set(True)
    app.wm_skip_ppt_type_var.set(False)
    app.wm_color_var.set("#2A7FFF")
    app.wm_copy_guard_enabled_var.set(True)
    app.wm_copy_guard_strength_var.set("强力")
    mod._safe_named_widget_set(app, "slider_size", 72)
    mod._safe_named_widget_set(app, "slider_opacity", 0.22)
    mod._safe_named_widget_set(app, "slider_angle", 30)
    watermark_last = mod._save_last_settings_category(app, "watermark")
    saved_slider_size = float(watermark_last["settings"]["slider_size"])
    mod._safe_named_widget_set(app, "wm_text", "changed")
    app.wm_range_var.set("all")
    app.wm_skip_name_text_var.set("ZZ")
    app.wm_copy_skipped_var.set(False)
    app.wm_skip_pdf_type_var.set(True)
    app.wm_skip_word_type_var.set(False)
    app.wm_skip_ppt_type_var.set(True)
    app.wm_color_var.set("#C0C0C0")
    app.wm_copy_guard_enabled_var.set(False)
    app.wm_copy_guard_strength_var.set("轻度")
    mod._safe_named_widget_set(app, "slider_size", 20)
    apply_ok, apply_message = mod._restore_last_settings_category(app, "watermark")
    loaded_last = mod._load_last_settings().get("watermark")
    record(
        "last_settings_watermark_save_restore",
        apply_ok
        and isinstance(loaded_last, dict)
        and mod._read_watermark_text_widget(app) == "Preset Watermark\nCONFIDENTIAL"
        and app.wm_range_var.get() == "first"
        and app.wm_skip_name_text_var.get() == "FX"
        and app.wm_copy_skipped_var.get() is True
        and app.wm_skip_pdf_type_var.get() is False
        and app.wm_skip_word_type_var.get() is True
        and app.wm_skip_ppt_type_var.get() is False
        and app.wm_color_var.get() == "#2A7FFF"
        and app.wm_copy_guard_enabled_var.get() is True
        and app.wm_copy_guard_strength_var.get() == "强力"
        and abs(float(app.slider_size.get()) - saved_slider_size) < 0.01,
        {
            "message": apply_message,
            "loaded": loaded_last,
            "slider_size": app.slider_size.get(),
            "saved_slider_size": saved_slider_size,
        },
    )

    wm_preview_frame = getattr(app, "_fx_wm_color_preview_frame", None)
    wm_text_widget = getattr(app, "wm_text", None)
    try:
        app.update_idletasks()
    except Exception:
        pass
    wm_text_panel = getattr(wm_text_widget, "master", None)
    try:
        wm_left_children = list(wm_text_panel.pack_slaves()) if wm_text_panel is not None else []
    except Exception:
        wm_left_children = list(wm_text_panel.winfo_children()) if wm_text_panel is not None else []
    try:
        preview_index = wm_left_children.index(wm_preview_frame)
    except Exception:
        preview_index = -1
    try:
        text_index = wm_left_children.index(wm_text_widget)
    except Exception:
        text_index = -1
    preview_before_text = preview_index >= 0 and text_index >= 0 and preview_index < text_index
    preview_frames = []
    try:
        stack = list(app.tab_wm.winfo_children())
        while stack:
            widget = stack.pop()
            if getattr(widget, "_fx_wm_color_preview_controls", False):
                preview_frames.append(widget)
            stack.extend(widget.winfo_children())
    except Exception:
        preview_frames = []
    record(
        "watermark_color_preview_ui",
        hasattr(app, "wm_color_var")
        and hasattr(app, "wm_preview_label")
        and wm_preview_frame is not None
        and wm_preview_frame.master == wm_text_panel
        and wm_preview_frame.winfo_manager() == "pack"
        and preview_before_text
        and len(preview_frames) == 1
        and mod._refresh_watermark_preview(app)
        and app.wm_color_var.get() == "#2A7FFF",
        {
            "color": getattr(app, "wm_color_var", None).get() if hasattr(app, "wm_color_var") else None,
            "parent_is_text_panel": wm_preview_frame.master == wm_text_panel
            if wm_preview_frame is not None
            else False,
            "manager": wm_preview_frame.winfo_manager() if wm_preview_frame is not None else None,
            "preview_index": preview_index,
            "text_index": text_index,
            "preview_before_text": preview_before_text,
            "preview_count": len(preview_frames),
        },
    )
    wm_copy_guard_frame = getattr(app, "_fx_wm_copy_guard_frame", None)
    wm_copy_guard_hint = getattr(app, "wm_copy_guard_hint_label", None)
    try:
        copy_guard_index = wm_left_children.index(wm_copy_guard_frame)
    except Exception:
        copy_guard_index = -1
    wm_copy_guard_settings = mod._get_watermark_settings(app)
    wm_copy_guard_preview = mod._get_preview_mode_detail(app, "watermark")
    record(
        "watermark_copy_guard_module_ui_and_settings",
        wm_copy_guard_frame is not None
        and wm_copy_guard_frame.master == wm_text_panel
        and wm_copy_guard_frame.winfo_manager() == "pack"
        and 0 <= copy_guard_index < text_index
        and 0 <= preview_index < text_index
        and app.wm_copy_guard_enabled_var.get() is True
        and app.wm_copy_guard_strength_var.get() == "强力"
        and wm_copy_guard_settings.get("copy_guard_enabled") is True
        and wm_copy_guard_settings.get("copy_guard_strength") == "strong"
        and "复制干扰层" in wm_copy_guard_preview
        and str(getattr(app.wm_copy_guard_strength_control, "_state", "")) == "normal"
        and "全选整页/整份" in str(wm_copy_guard_hint.cget("text") if wm_copy_guard_hint is not None else "")
        and "截图后重新 OCR 不受影响" in str(wm_copy_guard_hint.cget("text") if wm_copy_guard_hint is not None else ""),
        {
            "manager": wm_copy_guard_frame.winfo_manager() if wm_copy_guard_frame is not None else None,
            "copy_guard_index": copy_guard_index,
            "text_index": text_index,
            "settings": wm_copy_guard_settings,
            "preview": wm_copy_guard_preview,
        },
    )
    wm_range_random_radio = getattr(app, "_fx_wm_range_random_radio", None)
    try:
        wm_range_random_text = wm_range_random_radio.cget("text") if wm_range_random_radio is not None else ""
    except Exception:
        wm_range_random_text = ""
    random_range_label = getattr(mod, "WATERMARK_RANGE_UI_LABELS", {}).get("first_random", "")
    if wm_range_random_radio is not None:
        try:
            wm_range_random_radio.invoke()
        except Exception:
            mod._set_watermark_range_var(app, "first_random")
    record(
        "watermark_range_first_random_option_visible",
        wm_range_random_radio is not None
        and str(wm_range_random_radio.cget("value")) == "first_random"
        and wm_range_random_text == random_range_label
        and app.wm_range_var.get() == "first_random"
        and mod._watermark_core_normalize_page_range(random_range_label) == "first_random",
        {
            "text": wm_range_random_text,
            "value": str(wm_range_random_radio.cget("value")) if wm_range_random_radio is not None else None,
            "label": random_range_label,
            "range": app.wm_range_var.get(),
        },
    )

    mod._ensure_lazy_tab_initialized(app, "pdf")
    backend_values = list(getattr(app, "_fx_pdf_ocr_backend_map", {}).keys())
    lang_values = list(getattr(app, "_fx_pdf_ocr_lang_map", {}).keys())
    mode_values = list(getattr(app, "_fx_pdf_ocr_mode_map", {}).keys())
    preprocess_values = list(getattr(app, "_fx_pdf_ocr_preprocess_map", {}).keys())
    chosen_backend = backend_values[-1] if backend_values else app.pdf_ocr_backend.get()
    chosen_lang = lang_values[-1] if lang_values else app.pdf_ocr_language.get()
    chosen_mode = mode_values[-1] if mode_values else app.pdf_ocr_mode.get()
    chosen_preprocess = preprocess_values[-1] if preprocess_values else app.pdf_ocr_preprocess.get()
    app.pdf_ocr_backend.set(chosen_backend)
    app.pdf_ocr_language.set(chosen_lang)
    app.pdf_ocr_mode.set(chosen_mode)
    app.pdf_ocr_preprocess.set(chosen_preprocess)
    app.pdf_ocr_model_root.set(str(root / "ocr_models_probe"))
    app.pdf_ocr_cls.set(True)
    app.pdf_ocr_compare_report.set(True)
    ocr_last = mod._save_last_settings_category(app, "ocr")
    app.pdf_ocr_backend.set(backend_values[0] if backend_values else chosen_backend)
    app.pdf_ocr_preprocess.set(preprocess_values[0] if preprocess_values else chosen_preprocess)
    app.pdf_ocr_model_root.set("")
    app.pdf_ocr_cls.set(False)
    app.pdf_ocr_compare_report.set(False)
    ocr_apply_ok, _ocr_apply_message = mod._restore_last_settings_category(app, "ocr")
    record(
        "last_settings_ocr_save_restore",
        ocr_apply_ok
        and isinstance(ocr_last, dict)
        and app.pdf_mode_var.get() == "ocr"
        and app.pdf_ocr_backend.get() == chosen_backend
        and app.pdf_ocr_language.get() == chosen_lang
        and app.pdf_ocr_mode.get() == chosen_mode
        and app.pdf_ocr_preprocess.get() == chosen_preprocess
        and app.pdf_ocr_model_root.get() == str(root / "ocr_models_probe")
        and bool(app.pdf_ocr_cls.get())
        and bool(app.pdf_ocr_compare_report.get()),
        {
            "backend": app.pdf_ocr_backend.get(),
            "language": app.pdf_ocr_language.get(),
            "mode": app.pdf_ocr_mode.get(),
            "preprocess": app.pdf_ocr_preprocess.get(),
        },
    )

    pdf_nav_debug = {}
    try:
        app.deiconify()
        app.geometry("1180x760+80+80")
        app.update_idletasks()
        app.update()
        app.switch_tab("pdf", getattr(app, "btn_nav_pdf", None))
        for _ in range(6):
            app.update_idletasks()
            app.update()
            time.sleep(0.05)

        expected_pdf_modes = [
            "合并成一个 PDF (Merge)",
            "拆分为单页 PDF (Split)",
            "PDF 加密 (Encrypt)",
            "PDF 压缩",
            "OCR 搜索版 PDF",
        ]
        pdf_mode_buttons = {}

        def collect_pdf_mode_buttons(widget):
            for child in widget.winfo_children():
                try:
                    text = str(child.cget("text"))
                except Exception:
                    text = ""
                text_lines = text.splitlines()
                label = text_lines[0].strip() if text_lines else ""
                if child.__class__.__name__ == "CTkButton" and label in expected_pdf_modes:
                    pdf_mode_buttons[label] = child
                collect_pdf_mode_buttons(child)

        collect_pdf_mode_buttons(app)
        parents = {button.master for button in pdf_mode_buttons.values()}
        if len(parents) == 1:
            parent_height = int(next(iter(parents)).winfo_height())
        else:
            parent_height = -1
        pdf_nav_debug = {
            label: {
                "found": label in pdf_mode_buttons,
                "mapped": bool(pdf_mode_buttons[label].winfo_ismapped()) if label in pdf_mode_buttons else False,
                "y": int(pdf_mode_buttons[label].winfo_y()) if label in pdf_mode_buttons else None,
                "height": int(pdf_mode_buttons[label].winfo_height()) if label in pdf_mode_buttons else None,
                "bottom": int(pdf_mode_buttons[label].winfo_y() + pdf_mode_buttons[label].winfo_height())
                if label in pdf_mode_buttons
                else None,
            }
            for label in expected_pdf_modes
        }
        pdf_nav_debug["parent_height"] = parent_height
        pdf_nav_debug["same_parent"] = len(parents) == 1
        pdf_nav_visible_ok = (
            set(pdf_mode_buttons) == set(expected_pdf_modes)
            and len(parents) == 1
            and all(button.winfo_ismapped() for button in pdf_mode_buttons.values())
            and all(button.winfo_height() >= 30 for button in pdf_mode_buttons.values())
            and all(button.winfo_y() + button.winfo_height() <= parent_height for button in pdf_mode_buttons.values())
        )
    except Exception as exc:
        pdf_nav_visible_ok = False
        pdf_nav_debug = {"error": str(exc)}
    finally:
        try:
            app.withdraw()
        except Exception:
            pass
    record("pdf_ocr_nav_button_visible", pdf_nav_visible_ok, pdf_nav_debug)

    encrypt_pwd_debug = {}
    try:
        app.deiconify()
        app.geometry("1180x760+80+80")
        app.switch_tab("pdf", getattr(app, "btn_nav_pdf", None))
        if callable(getattr(app, "_fx_select_pdf_mode", None)):
            app._fx_select_pdf_mode("encrypt")
        else:
            app.pdf_mode_var.set("encrypt")
        for _ in range(4):
            app.update_idletasks()
            app.update()
            time.sleep(0.05)
        encrypt_entry = getattr(app, "_fx_pdf_encrypt_pwd_entry", None)
        shared_entry = getattr(app, "_fx_pdf_shared_pwd_entry", None)
        if encrypt_entry is not None:
            encrypt_entry.delete(0, "end")
            encrypt_entry.insert(0, "visible-pass")
        encrypt_pwd_debug = {
            "mode": app.pdf_mode_var.get(),
            "encrypt_exists": encrypt_entry is not None,
            "encrypt_mapped": bool(encrypt_entry.winfo_ismapped()) if encrypt_entry is not None else False,
            "encrypt_value": encrypt_entry.get() if encrypt_entry is not None else "",
            "shared_value": shared_entry.get() if shared_entry is not None else "",
            "active_value": app.pdf_pwd_entry.get() if getattr(app, "pdf_pwd_entry", None) is not None else "",
        }
        encrypt_pwd_visible_ok = (
            app.pdf_mode_var.get() == "encrypt"
            and encrypt_entry is not None
            and bool(encrypt_entry.winfo_ismapped())
            and encrypt_entry.get() == "visible-pass"
            and shared_entry is not None
            and shared_entry.get() == "visible-pass"
            and app.pdf_pwd_entry is encrypt_entry
        )
    except Exception as exc:
        encrypt_pwd_visible_ok = False
        encrypt_pwd_debug = {"error": str(exc)}
    finally:
        try:
            app.withdraw()
        except Exception:
            pass
    record("pdf_encrypt_password_entry_visible", encrypt_pwd_visible_ok, encrypt_pwd_debug)

    app.pdf_compress_level_var.set("强力")
    app.pdf_image_compress_level_var.set("轻度")
    compress_last = mod._save_last_settings_category(app, "pdf_compress")
    app.pdf_compress_level_var.set("轻度")
    app.pdf_image_compress_level_var.set("保留原图")
    compress_apply_ok, _compress_apply_message = mod._restore_last_settings_category(app, "pdf_compress")
    record(
        "last_settings_pdf_compress_save_restore",
        compress_apply_ok
        and isinstance(compress_last, dict)
        and app.pdf_mode_var.get() == "compress"
        and app.pdf_compress_level_var.get() == "强力"
        and app.pdf_image_compress_level_var.get() == "轻度",
        {
            "pdf": app.pdf_compress_level_var.get(),
            "image": app.pdf_image_compress_level_var.get(),
        },
    )

    mod._ensure_lazy_tab_initialized(app, "file")
    app.rename_type_var.set("replace")
    mod._safe_named_widget_set(app, "rename_prefix", "PRE_")
    mod._safe_named_widget_set(app, "rename_suffix", "_SUF")
    mod._safe_named_widget_set(app, "rename_find", "old")
    mod._safe_named_widget_set(app, "rename_rep", "new")
    mod._safe_named_widget_set(app, "rename_cut_head", "1")
    mod._safe_named_widget_set(app, "rename_cut_tail", "2")
    rename_last = mod._save_last_settings_category(app, "rename")
    app.rename_type_var.set("add")
    mod._safe_named_widget_set(app, "rename_prefix", "")
    mod._safe_named_widget_set(app, "rename_find", "")
    rename_apply_ok, _rename_apply_message = mod._restore_last_settings_category(app, "rename")
    record(
        "last_settings_rename_save_restore",
        rename_apply_ok
        and isinstance(rename_last, dict)
        and app.rename_type_var.get() == "replace"
        and app.rename_prefix.get() == "PRE_"
        and app.rename_suffix.get() == "_SUF"
        and app.rename_find.get() == "old"
        and app.rename_rep.get() == "new"
        and app.rename_cut_head.get() == "1"
        and app.rename_cut_tail.get() == "2",
        {
            "type": app.rename_type_var.get(),
            "prefix": app.rename_prefix.get(),
            "find": app.rename_find.get(),
        },
    )

    app.wm_skip_hyphen_var.set(True)
    app.wm_skip_name_position_var.set("开头")
    app.wm_skip_name_text_var.set("FX")
    app.wm_copy_skipped_var.set(True)
    mod._flush_watermark_filename_rule_persistence(app)
    saved_rule = mod._get_saved_watermark_filename_rule_settings()
    record(
        "watermark_filename_rule_memory_save",
        saved_rule == {"enabled": True, "position": "开头", "marker": "FX", "copy_skipped": True},
        saved_rule,
    )

    reload_probe = type("WatermarkRuleProbe", (), {})()
    reload_probe.wm_skip_hyphen_var = mod.tkinter.BooleanVar(master=app, value=False)
    reload_probe.wm_skip_name_position_var = mod.tkinter.StringVar(master=app, value="结尾")
    reload_probe.wm_skip_name_text_var = mod.tkinter.StringVar(master=app, value="-")
    reload_probe.wm_copy_skipped_var = mod.tkinter.BooleanVar(master=app, value=False)
    reload_probe.after = app.after
    reload_probe.after_cancel = app.after_cancel
    mod._install_watermark_filename_rule_memory(reload_probe)
    record(
        "watermark_filename_rule_memory_load",
        reload_probe.wm_skip_hyphen_var.get()
        and reload_probe.wm_skip_name_position_var.get() == "开头"
        and reload_probe.wm_skip_name_text_var.get() == "FX"
        and reload_probe.wm_copy_skipped_var.get() is True,
        {
            "enabled": reload_probe.wm_skip_hyphen_var.get(),
            "position": reload_probe.wm_skip_name_position_var.get(),
            "marker": reload_probe.wm_skip_name_text_var.get(),
            "copy_skipped": reload_probe.wm_copy_skipped_var.get(),
        },
    )

    controls_row = getattr(getattr(app, "wm_skip_name_entry", None), "master", None)
    controls_row = getattr(controls_row, "master", None)
    candidate_controls = []
    try:
        stack = [getattr(app, "tab_wm", None)]
        while stack:
            widget = stack.pop()
            if widget is None:
                continue
            if getattr(widget, "_fx_wm_filename_rule_controls", False):
                candidate_controls.append(widget)
            try:
                stack.extend(widget.winfo_children())
            except Exception:
                pass
    except Exception:
        pass
    if controls_row not in candidate_controls and controls_row is not None:
        candidate_controls.append(controls_row)

    def collect_widget_texts(widget):
        texts = []
        stack = [widget]
        while stack:
            item = stack.pop()
            try:
                text = str(item.cget("text") or "")
                if text:
                    texts.append(text)
            except Exception:
                pass
            try:
                stack.extend(item.winfo_children())
            except Exception:
                pass
        return texts

    all_rule_texts = []
    for candidate in candidate_controls:
        all_rule_texts.extend(collect_widget_texts(candidate))
    hint_marker = "\u7559\u7a7a\u9ed8\u8ba4"
    hint_detail_marker = "\u4efb\u610f\u5f00\u5934\u6216\u7ed3\u5c3e\u5b57\u7b26"
    copy_option_marker = "\u8df3\u8fc7\u6587\u4ef6\u590d\u5236\u5230\u8f93\u51fa\u6587\u4ef6\u5939"
    hint_text = next((text for text in all_rule_texts if hint_marker in text), "")
    copy_option_text = next((text for text in all_rule_texts if copy_option_marker in text), "")
    record(
        "watermark_filename_rule_hint_layout",
        bool(candidate_controls)
        and hint_marker in hint_text
        and hint_detail_marker in hint_text,
        {"hint": hint_text, "texts": all_rule_texts},
    )
    record(
        "watermark_copy_skipped_option_visible",
        bool(candidate_controls)
        and copy_option_marker in copy_option_text,
        {"hint": hint_text, "copy_option": copy_option_text, "texts": all_rule_texts},
    )
    active_skip_switch = mod._find_watermark_skip_switch(getattr(app, "tab_wm", None))
    active_controls_row = getattr(getattr(app, "wm_skip_name_entry", None), "master", None)
    active_controls_row = getattr(active_controls_row, "master", None)
    active_pack_slaves = []
    try:
        if active_skip_switch is not None:
            active_pack_slaves = list(active_skip_switch.master.pack_slaves())
    except Exception:
        active_pack_slaves = []
    record(
        "watermark_filename_rule_controls_on_active_panel",
        active_skip_switch is not None
        and active_controls_row is not None
        and getattr(active_controls_row, "master", None) is getattr(active_skip_switch, "master", None),
        {
            "switch": str(active_skip_switch),
            "controls": str(active_controls_row),
            "switch_text": active_skip_switch.cget("text") if active_skip_switch is not None else "",
            "controls_parent": str(getattr(active_controls_row, "master", "")),
            "switch_parent": str(getattr(active_skip_switch, "master", "")),
        },
    )
    record(
        "watermark_filename_rule_controls_below_switch",
        active_skip_switch in active_pack_slaves
        and active_controls_row in active_pack_slaves
        and active_pack_slaves.index(active_controls_row) == active_pack_slaves.index(active_skip_switch) + 1,
        {
            "switch_index": active_pack_slaves.index(active_skip_switch) if active_skip_switch in active_pack_slaves else None,
            "controls_index": active_pack_slaves.index(active_controls_row) if active_controls_row in active_pack_slaves else None,
            "order": [
                {
                    "class": child.__class__.__name__,
                    "text": child.cget("text") if hasattr(child, "cget") and "text" in getattr(child, "_keys", set()) else "",
                    "rule_controls": bool(getattr(child, "_fx_wm_filename_rule_controls", False)),
                }
                for child in active_pack_slaves
            ],
        },
    )
    active_type_skip_controls = None
    try:
        for child in getattr(active_controls_row, "master", None).winfo_children():
            if getattr(child, "_fx_wm_type_skip_controls", False):
                active_type_skip_controls = child
                break
    except Exception:
        active_type_skip_controls = None
    type_skip_texts = collect_widget_texts(active_type_skip_controls) if active_type_skip_controls is not None else []
    record(
        "watermark_type_skip_options_visible",
        active_type_skip_controls is not None
        and getattr(active_type_skip_controls, "master", None) is getattr(active_controls_row, "master", None)
        and "PDF" in type_skip_texts
        and "Word" in type_skip_texts
        and "PPT" in type_skip_texts,
        {"texts": type_skip_texts, "controls": str(active_type_skip_controls)},
    )

    wm_skip_copy_root = root / "watermark_skip_copy"
    wm_skip_copy_root.mkdir()
    wm_keep_pdf = wm_skip_copy_root / "normal.pdf"
    wm_skip_pdf = wm_skip_copy_root / "FX_skip.pdf"
    make_pdf(wm_keep_pdf, ["normal watermark target"])
    make_pdf(wm_skip_pdf, ["skip copy target"])
    mod._safe_named_widget_set(app, "wm_text", "SKIP COPY WATERMARK")
    mod._safe_var_set(app, "output_strategy_var", mod.OUTPUT_STRATEGY_VALUE_TO_LABEL["result_folder"])
    mod._safe_var_set(app, "wm_delete_var", False)
    mod._safe_var_set(app, "wm_convert_pdf", False)
    mod._safe_var_set(app, "wm_skip_hyphen_var", True)
    mod._safe_var_set(app, "wm_skip_name_position_var", "开头")
    mod._safe_var_set(app, "wm_skip_name_text_var", "FX")
    mod._safe_var_set(app, "wm_copy_skipped_var", True)
    mod._safe_var_set(app, "wm_range_var", "all")
    mod._safe_var_set(app, "wm_overwrite_var", "force")
    app.run_process(str(wm_skip_copy_root), "watermark")
    wm_skip_copy_result = mod._get_last_task_result(app)
    wm_skip_copy_folder = wm_skip_copy_root / mod.RESULT_FOLDER_NAME
    wm_skip_copied = wm_skip_copy_folder / "FX_skip.pdf"
    wm_watermarked_outputs = [
        Path(item)
        for item in wm_skip_copy_result.get("outputs", [])
        if Path(item).name != "FX_skip.pdf" and Path(item).suffix.lower() == ".pdf"
    ]
    record(
        "watermark_copy_rule_skipped_files_to_result_folder",
        wm_skip_copy_result.get("status") == "success"
        and wm_skip_copy_result.get("success_count") == 1
        and wm_skip_copy_result.get("skipped_count") == 1
        and wm_skip_copied.exists()
        and wm_skip_copied.read_bytes() == wm_skip_pdf.read_bytes()
        and any(path.exists() and "normal" in path.name for path in wm_watermarked_outputs),
        {
            "result": wm_skip_copy_result,
            "copied": str(wm_skip_copied),
            "outputs": [str(path) for path in wm_watermarked_outputs],
        },
    )

    wm_unsupported_copy_root = root / "watermark_unsupported_copy"
    wm_unsupported_copy_root.mkdir()
    wm_unsupported_pdf = wm_unsupported_copy_root / "normal.pdf"
    wm_unsupported_txt = wm_unsupported_copy_root / "notes.txt"
    wm_unsupported_zip = wm_unsupported_copy_root / "data.zip"
    make_pdf(wm_unsupported_pdf, ["normal unsupported-copy target"])
    wm_unsupported_txt.write_text("plain text should be copied\n", encoding="utf-8")
    with zipfile.ZipFile(wm_unsupported_zip, "w") as zf:
        zf.writestr("inside.txt", "zip payload")
    mod._safe_named_widget_set(app, "wm_text", "UNSUPPORTED COPY WATERMARK")
    mod._safe_var_set(app, "output_strategy_var", mod.OUTPUT_STRATEGY_VALUE_TO_LABEL["result_folder"])
    mod._safe_var_set(app, "wm_delete_var", False)
    mod._safe_var_set(app, "wm_convert_pdf", False)
    mod._safe_var_set(app, "wm_skip_hyphen_var", False)
    mod._safe_var_set(app, "wm_skip_name_position_var", "缁撳熬")
    mod._safe_var_set(app, "wm_skip_name_text_var", "")
    mod._safe_var_set(app, "wm_copy_skipped_var", True)
    mod._safe_var_set(app, "wm_range_var", "all")
    mod._safe_var_set(app, "wm_overwrite_var", "force")
    app.run_process(str(wm_unsupported_copy_root), "watermark")
    wm_unsupported_copy_result = mod._get_last_task_result(app)
    wm_unsupported_copy_folder = wm_unsupported_copy_root / mod.RESULT_FOLDER_NAME
    wm_unsupported_copied_txt = wm_unsupported_copy_folder / "notes.txt"
    wm_unsupported_copied_zip = wm_unsupported_copy_folder / "data.zip"
    record(
        "watermark_copy_unsupported_files_to_result_folder",
        wm_unsupported_copy_result.get("status") == "success"
        and wm_unsupported_copy_result.get("success_count") == 1
        and wm_unsupported_copy_result.get("skipped_count") == 2
        and wm_unsupported_copied_txt.exists()
        and wm_unsupported_copied_txt.read_bytes() == wm_unsupported_txt.read_bytes()
        and wm_unsupported_copied_zip.exists()
        and wm_unsupported_copied_zip.read_bytes() == wm_unsupported_zip.read_bytes(),
        {
            "result": wm_unsupported_copy_result,
            "copied_txt": str(wm_unsupported_copied_txt),
            "copied_zip": str(wm_unsupported_copied_zip),
            "outputs": list(wm_unsupported_copy_result.get("outputs", [])),
        },
    )

    wm_type_skip_root = root / "watermark_type_skip"
    wm_type_skip_root.mkdir()
    wm_type_pdf = wm_type_skip_root / "skip_pdf.pdf"
    wm_type_word = wm_type_skip_root / "keep_word.docx"
    make_pdf(wm_type_pdf, ["pdf should be copied without watermark"])
    from docx import Document

    doc = Document()
    doc.add_paragraph("word should still receive watermark")
    doc.save(wm_type_word)
    mod._safe_named_widget_set(app, "wm_text", "TYPE SKIP WATERMARK")
    mod._safe_var_set(app, "output_strategy_var", mod.OUTPUT_STRATEGY_VALUE_TO_LABEL["result_folder"])
    mod._safe_var_set(app, "wm_delete_var", False)
    mod._safe_var_set(app, "wm_convert_pdf", False)
    mod._safe_var_set(app, "wm_skip_hyphen_var", False)
    mod._safe_var_set(app, "wm_copy_skipped_var", True)
    mod._safe_var_set(app, "wm_skip_pdf_type_var", True)
    mod._safe_var_set(app, "wm_skip_word_type_var", False)
    mod._safe_var_set(app, "wm_skip_ppt_type_var", False)
    app.wm_copy_guard_enabled_var.set(False)
    mod._safe_var_set(app, "wm_range_var", "all")
    mod._safe_var_set(app, "wm_overwrite_var", "force")
    app.run_process(str(wm_type_skip_root), "watermark")
    wm_type_skip_result = mod._get_last_task_result(app)
    wm_type_skip_folder = wm_type_skip_root / mod.RESULT_FOLDER_NAME
    wm_type_copied_pdf = wm_type_skip_folder / "skip_pdf.pdf"
    wm_type_word_outputs = [
        Path(item)
        for item in wm_type_skip_result.get("outputs", [])
        if Path(item).suffix.lower() == ".docx" and "keep_word" in Path(item).name
    ]
    record(
        "watermark_type_skip_pdf_copies_and_word_processes",
        wm_type_skip_result.get("status") == "success"
        and wm_type_skip_result.get("success_count") == 1
        and wm_type_skip_result.get("skipped_count") == 1
        and wm_type_copied_pdf.exists()
        and wm_type_copied_pdf.read_bytes() == wm_type_pdf.read_bytes()
        and any(path.exists() for path in wm_type_word_outputs),
        {
            "result": wm_type_skip_result,
            "copied_pdf": str(wm_type_copied_pdf),
            "word_outputs": [str(path) for path in wm_type_word_outputs],
        },
    )
    mod._safe_var_set(app, "wm_skip_pdf_type_var", False)
    mod._safe_var_set(app, "wm_skip_word_type_var", False)
    mod._safe_var_set(app, "wm_skip_ppt_type_var", False)

    wm_suffix_skip_root = root / "watermark_suffix_skip"
    wm_suffix_skip_root.mkdir()
    wm_suffix_keep_pdf = wm_suffix_skip_root / "normal.pdf"
    wm_suffix_skip_pdf = wm_suffix_skip_root / "skip-.pdf"
    make_pdf(wm_suffix_keep_pdf, ["normal suffix target"])
    make_pdf(wm_suffix_skip_pdf, ["suffix skip target"])
    mod._safe_named_widget_set(app, "wm_text", "SUFFIX SKIP WATERMARK")
    mod._safe_var_set(app, "output_strategy_var", mod.OUTPUT_STRATEGY_VALUE_TO_LABEL["result_folder"])
    mod._safe_var_set(app, "wm_delete_var", False)
    mod._safe_var_set(app, "wm_convert_pdf", False)
    mod._safe_var_set(app, "wm_skip_hyphen_var", True)
    mod._safe_var_set(app, "wm_skip_name_position_var", "结尾")
    mod._safe_var_set(app, "wm_skip_name_text_var", "-")
    mod._safe_var_set(app, "wm_copy_skipped_var", True)
    mod._safe_var_set(app, "wm_range_var", "all")
    mod._safe_var_set(app, "wm_overwrite_var", "force")
    app.run_process(str(wm_suffix_skip_root), "watermark")
    wm_suffix_skip_result = mod._get_last_task_result(app)
    wm_suffix_skip_folder = wm_suffix_skip_root / mod.RESULT_FOLDER_NAME
    wm_suffix_copied = wm_suffix_skip_folder / "skip-.pdf"
    record(
        "watermark_suffix_dash_rule_skips_files",
        mod._get_watermark_filename_rule(app) == ("suffix", "-")
        and wm_suffix_skip_result.get("status") == "success"
        and wm_suffix_skip_result.get("success_count") == 1
        and wm_suffix_skip_result.get("skipped_count") == 1
        and wm_suffix_copied.exists()
        and wm_suffix_copied.read_bytes() == wm_suffix_skip_pdf.read_bytes(),
        {
            "rule": mod._get_watermark_filename_rule(app),
            "result": wm_suffix_skip_result,
            "copied": str(wm_suffix_copied),
        },
    )

    wm_bad_path_root = root / "watermark_bad_output_path"
    wm_bad_path_root.mkdir()
    wm_bad_first = wm_bad_path_root / "bad.pdf"
    wm_bad_second = wm_bad_path_root / "good.pdf"
    make_pdf(wm_bad_first, ["bad output path"])
    make_pdf(wm_bad_second, ["good output path"])
    mod._safe_named_widget_set(app, "wm_text", "BAD PATH WATERMARK")
    mod._safe_var_set(app, "output_strategy_var", mod.OUTPUT_STRATEGY_VALUE_TO_LABEL["result_folder"])
    mod._safe_var_set(app, "wm_delete_var", False)
    mod._safe_var_set(app, "wm_convert_pdf", False)
    mod._safe_var_set(app, "wm_skip_hyphen_var", False)
    mod._safe_var_set(app, "wm_range_var", "all")
    mod._safe_var_set(app, "wm_overwrite_var", "force")
    original_wm_output_path = mod._build_watermark_output_path

    def fake_wm_output_path(src, input_root, output_root, strategy, convert_to_pdf=False, single_input=False):
        src_path = Path(src)
        if src_path.name == "bad.pdf":
            return str(Path(output_root) / "bad\0parent" / src_path.name)
        return original_wm_output_path(src, input_root, output_root, strategy, convert_to_pdf=convert_to_pdf, single_input=single_input)

    mod._build_watermark_output_path = fake_wm_output_path
    try:
        app.run_process(str(wm_bad_path_root), "watermark")
    finally:
        mod._build_watermark_output_path = original_wm_output_path
    wm_bad_path_result = mod._get_last_task_result(app)
    wm_bad_path_logs = list(getattr(app, "_fx_last_task_logs", []) or [])
    record(
        "watermark_output_path_failure_does_not_abort_batch",
        wm_bad_path_result.get("failed_count") == 1
        and wm_bad_path_result.get("success_count") == 1
        and wm_bad_path_result.get("processed_count") == 2
        and any("输出路径准备失败" in str(item) for item in wm_bad_path_logs)
        and not any("严重错误" in str(item) for item in wm_bad_path_logs),
        {"result": wm_bad_path_result, "logs": wm_bad_path_logs[-8:]},
    )

    wm_trailing_space_src = Path("D:/probe/root/医学药学公卫资料试卷/系解人体结构神经系统资料试卷 /人体结构神经系统系解复习资料/试题.pdf")
    wm_trailing_space_out = Path(
        mod._build_watermark_output_path(
            wm_trailing_space_src,
            "D:/probe/root",
            "D:/probe/root/【处理完成】结果文件夹",
            "result_folder",
        )
    )
    record(
        "watermark_result_path_strips_trailing_space_dirs",
        "系解人体结构神经系统资料试卷 " not in wm_trailing_space_out.parts
        and "系解人体结构神经系统资料试卷" in wm_trailing_space_out.parts
        and wm_trailing_space_out.name == "试题.pdf",
        str(wm_trailing_space_out),
    )

    wm_resolve_root = root / "watermark_resolve_spaces"
    wm_resolve_dir = wm_resolve_root / "数字逻辑期中卷"
    wm_resolve_dir.mkdir(parents=True)
    wm_resolve_pdf = wm_resolve_dir / "space.pdf"
    make_pdf(wm_resolve_pdf, ["resolve spaces"])
    wm_resolved = mod._resolve_watermark_source_path(wm_resolve_root / " 数字逻辑期中卷 " / " space.pdf ", wm_resolve_root)
    record(
        "watermark_resolves_trimmed_retry_paths",
        wm_resolved == wm_resolve_pdf,
        str(wm_resolved),
    )

    import tools.fx_watermark_core as wm_core_module

    wm_repair_pdf = root / "watermark_repair_source.pdf"
    wm_repair_out = root / "watermark_repair_output.pdf"
    make_pdf(wm_repair_pdf, ["repair fallback target"])
    wm_repair_pkt = mod.create_watermark_packet("REPAIR TEST", "SmileySans-Oblique", 28, 0.2, 45)
    original_core_reader = wm_core_module.PdfReader
    original_core_repair = wm_core_module._repair_pdf_for_watermark

    def fake_broken_pdf_reader(target, *args, **kwargs):
        if str(target) == str(wm_repair_pdf):
            raise RuntimeError("Could not read Boolean object")
        return original_core_reader(target, *args, **kwargs)

    def fake_pdf_repair(src_path):
        repaired = Path(tempfile.mkstemp(prefix="fx_repair_probe_", suffix=".pdf", dir=root)[1])
        shutil.copy2(src_path, repaired)
        return repaired, ""

    wm_core_module.PdfReader = fake_broken_pdf_reader
    wm_core_module._repair_pdf_for_watermark = fake_pdf_repair
    try:
        repair_status = mod.add_watermark_to_pdf(
            str(wm_repair_pdf),
            str(wm_repair_out),
            wm_repair_pkt,
            page_range="all",
            check_text="REPAIR TEST",
            force_mode=True,
        )
    finally:
        wm_core_module.PdfReader = original_core_reader
        wm_core_module._repair_pdf_for_watermark = original_core_repair
    record(
        "pdf_watermark_repair_fallback",
        repair_status == "SUCCESS"
        and wm_repair_out.exists()
        and "REPAIR TEST" in "\n".join(page.extract_text() or "" for page in PdfReader(str(wm_repair_out)).pages),
        repair_status,
    )

    class FakeRepairDocuments:
        def __init__(self):
            self.calls = []
            self.doc = object()

        def Open(self, *args):
            self.calls.append(args)
            if len(args) >= 14 and bool(args[13]):
                return self.doc
            raise RuntimeError("open failed")

    fake_repair_docs = FakeRepairDocuments()
    fake_repair_word = type("FakeRepairWord", (), {"Documents": fake_repair_docs})()
    repair_doc = wm_core_module.open_word_document_safely(fake_repair_word, root / "repair_probe.docx")
    record(
        "word_open_repair_fallback",
        repair_doc is fake_repair_docs.doc
        and len(fake_repair_docs.calls) >= 3
        and len(fake_repair_docs.calls[0]) == 4
        and len(fake_repair_docs.calls[1]) == 1
        and len(fake_repair_docs.calls[2]) >= 14
        and bool(fake_repair_docs.calls[2][13]),
        [len(args) for args in fake_repair_docs.calls],
    )

    wm_protected_root = root / "watermark_protected_preserve"
    wm_protected_root.mkdir()
    wm_protected_pdf = wm_protected_root / "protected.pdf"
    make_pdf(wm_protected_pdf, ["protected original"])
    mod._safe_named_widget_set(app, "wm_text", "PROTECTED WATERMARK")
    mod._safe_var_set(app, "output_strategy_var", mod.OUTPUT_STRATEGY_VALUE_TO_LABEL["result_folder"])
    mod._safe_var_set(app, "wm_delete_var", False)
    mod._safe_var_set(app, "wm_convert_pdf", False)
    mod._safe_var_set(app, "wm_skip_hyphen_var", False)
    mod._safe_var_set(app, "wm_range_var", "all")
    mod._safe_var_set(app, "wm_overwrite_var", "force")
    original_process_pdf = mod._watermark_process_pdf
    mod._watermark_process_pdf = lambda src, dst, settings: "SKIP:protected pdf requires password"
    try:
        app.run_process(str(wm_protected_root), "watermark")
    finally:
        mod._watermark_process_pdf = original_process_pdf
    wm_protected_result = mod._get_last_task_result(app)
    wm_protected_copy = wm_protected_root / mod.RESULT_FOLDER_NAME / "protected.pdf"
    record(
        "watermark_protected_pdf_preserves_original",
        wm_protected_result.get("status") == "success"
        and wm_protected_result.get("failed_count") == 0
        and wm_protected_result.get("skipped_count") == 1
        and wm_protected_copy.exists()
        and wm_protected_copy.read_bytes() == wm_protected_pdf.read_bytes(),
        {"result": wm_protected_result, "copy": str(wm_protected_copy)},
    )

    wm_damaged_word_root = root / "watermark_damaged_word_preserve"
    wm_damaged_word_root.mkdir()
    wm_damaged_word_docx = wm_damaged_word_root / "damaged.docx"
    wm_damaged_word_docx.write_bytes(b"not-a-real-docx")
    mod._safe_named_widget_set(app, "wm_text", "DAMAGED WORD WATERMARK")
    mod._safe_var_set(app, "output_strategy_var", mod.OUTPUT_STRATEGY_VALUE_TO_LABEL["result_folder"])
    mod._safe_var_set(app, "wm_delete_var", False)
    mod._safe_var_set(app, "wm_convert_pdf", False)
    mod._safe_var_set(app, "wm_skip_hyphen_var", False)
    mod._safe_var_set(app, "wm_range_var", "all")
    mod._safe_var_set(app, "wm_overwrite_var", "force")
    original_process_word = mod._watermark_process_word
    mod._watermark_process_word = lambda src, dst, settings, word_app: "SKIP:damaged word source"
    try:
        app.run_process(str(wm_damaged_word_root), "watermark")
    finally:
        mod._watermark_process_word = original_process_word
    wm_damaged_word_result = mod._get_last_task_result(app)
    wm_damaged_word_copy = wm_damaged_word_root / mod.RESULT_FOLDER_NAME / "damaged.docx"
    record(
        "watermark_damaged_word_preserves_original",
        wm_damaged_word_result.get("status") == "success"
        and wm_damaged_word_result.get("failed_count") == 0
        and wm_damaged_word_result.get("skipped_count") == 1
        and wm_damaged_word_copy.exists()
        and wm_damaged_word_copy.read_bytes() == wm_damaged_word_docx.read_bytes(),
        {"result": wm_damaged_word_result, "copy": str(wm_damaged_word_copy)},
    )

    wm_progress_values = []
    original_progress_bar = getattr(app, "progress_bar", None)

    class WatermarkProgressProbe:
        def set(self, value):
            wm_progress_values.append(round(float(value), 4))

    app.progress_bar = WatermarkProgressProbe()
    wm_progress_root = root / "watermark_progress_sync"
    wm_progress_root.mkdir()
    wm_progress_a = wm_progress_root / "a.pdf"
    wm_progress_b = wm_progress_root / "b.pdf"
    make_pdf(wm_progress_a, ["progress a"])
    make_pdf(wm_progress_b, ["progress b"])
    mod._safe_named_widget_set(app, "wm_text", "PROGRESS WATERMARK")
    mod._safe_var_set(app, "output_strategy_var", mod.OUTPUT_STRATEGY_VALUE_TO_LABEL["result_folder"])
    mod._safe_var_set(app, "wm_delete_var", False)
    mod._safe_var_set(app, "wm_convert_pdf", False)
    mod._safe_var_set(app, "wm_skip_hyphen_var", False)
    mod._safe_var_set(app, "wm_range_var", "all")
    mod._safe_var_set(app, "wm_overwrite_var", "force")
    try:
        app.run_process(str(wm_progress_root), "watermark")
    finally:
        app.progress_bar = original_progress_bar
    wm_progress_result = mod._get_last_task_result(app)
    record(
        "watermark_progress_bar_syncs_with_status",
        wm_progress_result.get("status") == "success"
        and wm_progress_values
        and wm_progress_values[0] == 0.0
        and wm_progress_values[-1] == 1.0
        and any(0.0 < value < 1.0 for value in wm_progress_values),
        {"values": wm_progress_values, "result": wm_progress_result},
    )

    queue_root = root / "queue_probe"
    queue_root.mkdir()
    queue_pdf = queue_root / "queue.pdf"
    make_pdf(queue_pdf, ["queue probe"])
    app.current_task = "pdf"
    _ = app.pdf_mode_var
    app.pdf_mode_var.set("encrypt")
    app.pdf_pwd_entry.delete(0, "end")
    app.pdf_pwd_entry.insert(0, "2468")
    app.input_path.set(str(queue_pdf))
    queue_task = mod._queue_add_current_task(app)
    record(
        "task_queue_snapshot",
        queue_task is not None
        and queue_task["snapshot"]["variables"].get("pdf_mode_var") == "encrypt"
        and queue_task["snapshot"]["widgets"].get("pdf_pwd_entry") == "2468"
        and hasattr(app, "btn_queue_add")
        and hasattr(app, "btn_queue_panel"),
        queue_task["title"] if queue_task else "missing",
    )

    queue_run_calls = []
    original_queue_run_process = app.run_process

    def fake_queue_run_process(input_value, task_type):
        queue_run_calls.append((input_value, task_type, app.pdf_mode_var.get(), app.pdf_pwd_entry.get()))
        app.log("queue fake success")

    app.run_process = fake_queue_run_process
    mod._run_task_queue_worker(app)
    app.run_process = original_queue_run_process
    success_history = [item for item in getattr(app, "_fx_task_history", []) if item.get("title") == queue_task["title"] and item.get("status") == "success"]
    record(
        "task_queue_success_history",
        queue_run_calls
        and queue_run_calls[-1][1:] == ("pdf", "encrypt", "2468")
        and bool(success_history),
        queue_run_calls,
    )
    success_result = success_history[-1].get("task_result") if success_history else {}
    record(
        "task_queue_structured_result",
        isinstance(success_result, dict)
        and success_result.get("status") == "success"
        and success_result.get("task_type") == "pdf"
        and success_result.get("input") == str(queue_pdf)
        and "duration_seconds" in success_result,
        success_result,
    )
    filtered_failed = mod._filter_queue_history_entries(
        getattr(app, "_fx_task_history", []),
        status_filter="仅完成",
        task_filter="PDF 工具",
        keyword="queue",
    )
    record(
        "task_history_filter_success_pdf_keyword",
        len(filtered_failed) >= 1
        and all(item.get("status") == "success" for item in filtered_failed)
        and all(item.get("task_type") == "pdf" for item in filtered_failed),
        filtered_failed[:2],
    )
    app._fx_history_filter_status_var.set("仅完成")
    app._fx_history_filter_task_var.set("PDF 工具")
    app._fx_history_search_var.set("queue")
    filtered_via_app = mod._get_filtered_queue_history(app)
    record(
        "task_history_filter_state_vars",
        len(filtered_via_app) == len(filtered_failed)
        and bool(filtered_via_app)
        and "显示 1/1 条" in app._fx_history_summary_var.get(),
        {
            "count": len(filtered_via_app),
            "summary": app._fx_history_summary_var.get(),
        },
    )
    detail_text = mod._build_task_history_detail_text(success_history[-1] if success_history else {})
    record(
        "task_history_detail_text",
        "任务历史详情" not in detail_text
        and "结构化结果 JSON" in detail_text
        and "标题：" in detail_text
        and "功能：" in detail_text,
        detail_text[:240],
    )
    module_context = TaskHistoryExportContext(
        normalize_path=lambda value: str(Path(value).resolve()) if value else "",
        export_task_result=lambda result, output_path: Path(output_path).write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        >= 0,
        sanitize_filename_component=mod._sanitize_filename_component,
        format_queue_time=mod._format_queue_time,
        get_feature_label=mod._get_feature_label,
        queue_status_text=mod._queue_status_text,
        classify_failure_reason=mod._classify_failure_reason,
        failure_value_to_label=mod.QUEUE_HISTORY_FAILURE_VALUE_TO_LABEL,
        project_root=root,
        user_home=root.parent,
        probe_environment=lambda: {"app": {}, "system": {}, "dependencies": {}, "performance": {}},
        load_queue_history=lambda: success_history,
        debug=lambda message: None,
    )
    module_report_text = build_task_history_report_text(success_history[-1] if success_history else {}, module_context)
    module_export_filename = build_task_history_export_filename(success_history[-1] if success_history else {}, module_context)
    record(
        "task_history_exports_module_context",
        "# 风兮工具箱任务报告" in module_report_text
        and "queue fake success" in module_report_text
        and module_export_filename.endswith(".json")
        and "fengxi_task_result_" in module_export_filename,
        {
            "filename": module_export_filename,
            "report": module_report_text[:240],
        },
    )
    export_filename = mod._build_task_history_export_filename(success_history[-1] if success_history else {})
    record(
        "task_history_export_filename",
        export_filename.endswith(".json")
        and "fengxi_task_result_" in export_filename
        and all(char not in export_filename for char in '<>:"/\\\\|?*'),
        export_filename,
    )
    export_path = root / "task_result_export.json"
    export_ok, export_payload = mod._export_task_history_entry(success_history[-1] if success_history else {}, str(export_path))
    exported_json = json.loads(export_path.read_text(encoding="utf-8")) if export_ok and export_path.exists() else {}
    record(
        "task_history_export_result",
        export_ok
        and export_payload == str(export_path.resolve())
        and exported_json.get("task_type") == "pdf"
        and exported_json.get("input") == str(queue_pdf)
        and "status" in exported_json
        and "outputs" in exported_json
        and "output_root" in exported_json
        and "failed_items" in exported_json,
        exported_json,
    )
    export_missing_ok, export_missing_payload = mod._export_task_history_entry({"title": "empty"}, str(root / "empty_export.json"))
    record(
        "task_history_export_missing_result",
        (not export_missing_ok) and ("没有可导出的结构化结果" in export_missing_payload),
        export_missing_payload,
    )
    log_filename = mod._build_task_history_log_export_filename(success_history[-1] if success_history else {})
    record(
        "task_history_log_export_filename",
        log_filename.endswith(".txt")
        and "fengxi_task_log_" in log_filename
        and all(char not in log_filename for char in '<>:"/\\\\|?*'),
        log_filename,
    )
    log_path = root / "task_history_log.txt"
    log_ok, log_payload = mod._export_task_history_log(success_history[-1] if success_history else {}, str(log_path))
    log_text = log_path.read_text(encoding="utf-8") if log_ok and log_path.exists() else ""
    record(
        "task_history_log_export_result",
        log_ok
        and log_payload == str(log_path.resolve())
        and "日志：" in log_text
        and "queue fake success" in log_text,
        log_text[:240],
    )
    empty_log_ok, empty_log_payload = mod._export_task_history_log({"title": "empty"}, str(root / "empty_log.txt"))
    record(
        "task_history_log_export_empty",
        empty_log_ok
        and "日志：" in (root / "empty_log.txt").read_text(encoding="utf-8"),
        empty_log_payload,
    )
    report_filename = mod._build_task_history_report_export_filename(success_history[-1] if success_history else {})
    record(
        "task_history_report_export_filename",
        report_filename.endswith(".md")
        and "fengxi_task_report_" in report_filename
        and all(char not in report_filename for char in '<>:\"/\\\\|?*'),
        report_filename,
    )
    report_path = root / "task_history_report.md"
    report_ok, report_payload = mod._export_task_history_report(success_history[-1] if success_history else {}, str(report_path))
    report_text = report_path.read_text(encoding="utf-8") if report_ok and report_path.exists() else ""
    record(
        "task_history_report_export_result",
        report_ok
        and report_payload == str(report_path.resolve())
        and "# 风兮工具箱任务报告" in report_text
        and "## 基本信息" in report_text
        and "## 结果统计" in report_text
        and "queue fake success" in report_text,
        report_text[:500],
    )
    empty_report_ok, empty_report_payload = mod._export_task_history_report({}, str(root / "empty_report.md"))
    record(
        "task_history_report_export_empty",
        (not empty_report_ok) and ("无法导出任务报告" in empty_report_payload),
        empty_report_payload,
    )
    diagnostic_filename = mod._build_task_history_diagnostic_filename(success_history[-1] if success_history else {})
    record(
        "task_history_diagnostic_filename",
        diagnostic_filename.endswith(".zip")
        and "fengxi_diagnostic_" in diagnostic_filename
        and all(char not in diagnostic_filename for char in '<>:"/\\\\|?*'),
        diagnostic_filename,
    )
    original_probe_diagnostic_environment = mod._probe_diagnostic_environment
    mod._probe_diagnostic_environment = lambda: {
        "app": {
            "release_version": mod.APP_RELEASE_VERSION,
            "display_version": mod.APP_DISPLAY_VERSION,
            "frozen": False,
        },
        "system": {
            "platform": "test-platform",
            "python": "test-python",
            "executable": str(root / "python.exe"),
            "cwd": str(root),
        },
        "dependencies": {
            "ffmpeg": {"available": True, "path": str(root / "ffmpeg.exe")},
            "ocr": {"rapidocr": {"available": True, "reason": "ok"}},
            "office": {
                "word": {"available": True, "version": "16.0", "error": ""},
                "powerpoint": {"available": False, "version": "", "error": "not installed"},
            },
        },
        "performance": {
            "log_path": str(mod._get_performance_log_file()),
            "recent": mod._load_recent_performance_entries(limit=5),
        },
    }
    try:
        diagnostic_path = root / "task_history_diagnostic.zip"
        diagnostic_ok, diagnostic_payload = mod._export_task_history_diagnostic_package(
            success_history[-1] if success_history else {},
            str(diagnostic_path),
        )
        diagnostic_members = []
        readme_text = ""
        diagnostic_task_result = {}
        diagnostic_environment = {}
        if diagnostic_ok and diagnostic_path.exists():
            with zipfile.ZipFile(diagnostic_path, "r") as diagnostic_zip:
                diagnostic_members = sorted(diagnostic_zip.namelist())
                readme_text = diagnostic_zip.read("README.md").decode("utf-8")
                diagnostic_task_result = json.loads(diagnostic_zip.read("task_result.json").decode("utf-8"))
                diagnostic_environment = json.loads(diagnostic_zip.read("environment.json").decode("utf-8"))
        record(
            "task_history_diagnostic_export_package",
            diagnostic_ok
            and diagnostic_payload == str(diagnostic_path.resolve())
            and {
                "README.md",
                "task_history_entry.json",
                "task_result.json",
                "task_report.md",
                "task_log.txt",
                "environment.json",
                "recent_history.json",
            }.issubset(set(diagnostic_members))
            and "# 风兮工具箱诊断包" in readme_text
            and "<PROJECT_ROOT>" in readme_text
            and str(root) not in readme_text
            and diagnostic_task_result.get("task_type") == "pdf"
            and diagnostic_environment.get("dependencies", {}).get("ffmpeg", {}).get("available") is True
            and isinstance(diagnostic_environment.get("performance", {}).get("recent"), list),
            {
                "payload": diagnostic_payload,
                "members": diagnostic_members,
                "readme": readme_text[:300],
                "task_result": diagnostic_task_result,
                "environment": diagnostic_environment,
            },
        )
        empty_diag_ok, empty_diag_payload = mod._export_task_history_diagnostic_package({}, str(root / "empty_diag.zip"))
        record(
            "task_history_diagnostic_export_empty",
            (not empty_diag_ok) and ("无法导出诊断包" in empty_diag_payload),
            empty_diag_payload,
        )
    finally:
        mod._probe_diagnostic_environment = original_probe_diagnostic_environment
    open_dir = root / "history_open_output"
    open_dir.mkdir(exist_ok=True)
    open_calls = []
    original_startfile = getattr(mod.os, "startfile", None)
    mod.os.startfile = lambda path: open_calls.append(str(path))
    try:
        open_ok, open_payload = mod._open_task_history_output({"output_root": str(open_dir)})
        record(
            "task_history_open_output_root",
            open_ok and open_payload == str(open_dir.resolve()) and open_calls[-1] == str(open_dir.resolve()),
            {"payload": open_payload, "calls": open_calls},
        )
        output_file = open_dir / "from_output_file.pdf"
        output_file.write_text("probe", encoding="utf-8")
        open_ok_file, open_payload_file = mod._open_task_history_output({"outputs": [str(output_file)]})
        record(
            "task_history_open_output_file_parent",
            open_ok_file and open_payload_file == str(open_dir.resolve()) and open_calls[-1] == str(open_dir.resolve()),
            {"payload": open_payload_file, "calls": open_calls},
        )
        open_missing_ok, open_missing_payload = mod._open_task_history_output({"title": "empty"})
        record(
            "task_history_open_output_missing",
            (not open_missing_ok) and ("没有可打开的输出位置" in open_missing_payload),
            open_missing_payload,
        )
    finally:
        if original_startfile is None:
            try:
                delattr(mod.os, "startfile")
            except Exception:
                pass
        else:
            mod.os.startfile = original_startfile
    mod._reset_queue_history_filters(app)
    record(
        "task_history_filter_reset",
        app._fx_history_filter_status_var.get() == "全部状态"
        and app._fx_history_filter_task_var.get() == "全部功能"
        and app._fx_history_search_var.get() == "",
        {
            "status": app._fx_history_filter_status_var.get(),
            "task": app._fx_history_filter_task_var.get(),
            "keyword": app._fx_history_search_var.get(),
        },
    )
    app._fx_task_queue = []
    replay_task = mod._queue_replay_history_task(app, success_history[-1]) if success_history else None
    record(
        "task_history_replay_success",
        replay_task is not None
        and replay_task.get("input") == str(queue_pdf)
        and replay_task.get("task_type") == "pdf"
        and any(item.get("id") == replay_task.get("id") for item in getattr(app, "_fx_task_queue", [])),
        replay_task or "missing",
    )
    app._fx_task_queue = []

    failed_source = {
        "id": "failed-probe",
        "input": str(queue_pdf),
        "task_type": "pdf",
        "title": "PDF 工具 · 失败样本",
        "snapshot": queue_task["snapshot"],
        "status": "failed",
        "created_at": time.time(),
        "finished_at": time.time(),
        "detail": "probe failed",
        "logs": ["❌ probe failed"],
        "task_result": {
            "task_type": "pdf",
            "input": str(queue_root),
            "status": "failed",
            "failed_items": [str(queue_pdf)],
            "failed_count": 1,
        },
    }
    retry_failed_paths = mod._resolve_retry_failed_item_paths(failed_source)
    record(
        "task_queue_retry_failed_item_paths",
        retry_failed_paths == [str(queue_pdf)],
        retry_failed_paths,
    )
    retry_subset = mod._build_retry_subset_input(app, failed_source)
    record(
        "task_queue_retry_failed_subset",
        isinstance(retry_subset, dict)
        and retry_subset.get("mode") in {"single_file", "staging_dir"}
        and bool(retry_subset.get("input")),
        retry_subset,
    )
    app._fx_task_history.append(failed_source)
    mod._queue_retry_failed_history(app)
    retry_tasks = list(getattr(app, "_fx_task_queue", []))
    retry_titles = [item.get("title") for item in retry_tasks]
    targeted_retry = next((item for item in retry_tasks if item.get("title") == failed_source["title"]), None)
    record(
        "task_queue_retry_failed",
        failed_source["title"] in retry_titles
        and targeted_retry is not None
        and targeted_retry.get("retry_mode") in {"single_file", "staging_dir"}
        and bool(targeted_retry.get("retry_failed_items")),
        targeted_retry or retry_titles,
    )
    app._fx_task_queue = []
    failed_detail_text = mod._build_task_history_detail_text(failed_source)
    record(
        "task_history_failed_detail_groups",
        "失败概览：" in failed_detail_text
        and "失败原因：" in failed_detail_text
        and "失败项：" in failed_detail_text
        and "关键日志：" in failed_detail_text
        and str(queue_pdf) in failed_detail_text
        and "probe failed" in failed_detail_text,
        failed_detail_text[:500],
    )
    failed_report_text = mod._build_task_history_report_text(failed_source)
    record(
        "task_history_failed_report_sections",
        "## 失败分析" in failed_report_text
        and "失败分类：" in failed_report_text
        and "部分失败" in failed_report_text
        and str(queue_pdf) in failed_report_text
        and "## 关键日志" in failed_report_text,
        failed_report_text[:600],
    )
    mod._show_task_history_detail(app, failed_source)
    detail_window = getattr(app, "_fx_history_detail_window", None)
    detail_box = getattr(detail_window, "_fx_detail_box", None) if detail_window is not None else None
    fail_header_ranges = detail_box.tag_ranges("fx_history_fail_header") if detail_box is not None else ()
    fail_text_ranges = detail_box.tag_ranges("fx_history_fail_text") if detail_box is not None else ()
    fail_item_ranges = detail_box.tag_ranges("fx_history_fail_item") if detail_box is not None else ()
    fail_log_ranges = detail_box.tag_ranges("fx_history_log_error") if detail_box is not None else ()
    record(
        "task_history_failed_detail_highlight_tags",
        bool(fail_header_ranges) and bool(fail_text_ranges) and bool(fail_item_ranges) and bool(fail_log_ranges),
        {
            "header": len(fail_header_ranges),
            "text": len(fail_text_ranges),
            "item": len(fail_item_ranges),
            "log": len(fail_log_ranges),
        },
    )
    if detail_window is not None:
        try:
            detail_window.destroy()
        except Exception:
            pass
    classified_failed_source = dict(failed_source)
    classified_failed_source["error"] = "路径不存在: probe.pdf"
    classified_failed_source["task_result"] = dict(failed_source["task_result"])
    classified_failed_source["task_result"]["error"] = "路径不存在: probe.pdf"
    failure_kind, failure_reason = mod._classify_failure_reason(classified_failed_source)
    record(
        "task_history_failure_reason_classification",
        failure_kind == "path_missing" and "路径不存在" in failure_reason,
        {"kind": failure_kind, "reason": failure_reason},
    )
    failed_history_blob = mod._build_queue_history_search_blob(classified_failed_source)
    record(
        "task_history_failure_reason_search_blob",
        "path_missing" in failed_history_blob and "路径不存在" in failed_history_blob,
        failed_history_blob,
    )
    failed_path_entry = dict(classified_failed_source)
    failed_path_entry["status"] = "failed"
    failed_path_entry["task_type"] = "pdf"
    path_filtered = mod._filter_queue_history_entries(
        [failed_source, failed_path_entry],
        status_filter="仅失败",
        task_filter="PDF 工具",
        failure_filter="路径缺失",
        keyword="路径不存在",
    )
    record(
        "task_history_failure_filter_path_missing",
        len(path_filtered) == 1 and path_filtered[0].get("error") == "路径不存在: probe.pdf",
        path_filtered,
    )
    app._fx_task_history = [failed_source, failed_path_entry]
    app._fx_history_filter_status_var.set("仅失败")
    app._fx_history_filter_task_var.set("PDF 工具")
    app._fx_history_filter_failure_var.set("路径缺失")
    app._fx_history_search_var.set("路径不存在")
    filtered_via_failure_app = mod._get_filtered_queue_history(app)
    record(
        "task_history_failure_filter_state_vars",
        len(filtered_via_failure_app) == 1
        and filtered_via_failure_app[0].get("error") == "路径不存在: probe.pdf",
        filtered_via_failure_app,
    )
    mod._reset_queue_history_filters(app)
    app._fx_task_history = []

    close_probe = type("FastCloseProbe", (), {})()
    close_destroy_called = []
    close_withdraw_called = []
    close_quit_called = []
    close_probe.stop_event = False
    close_probe._fx_disable_fast_close_force_exit = True
    close_probe.withdraw = lambda: close_withdraw_called.append(True)
    close_probe.update_idletasks = lambda: None
    close_probe.quit = lambda: close_quit_called.append(True)
    close_probe.destroy = lambda: close_destroy_called.append(True)
    close_probe.after = lambda delay, callback=None, *args: callback(*args) if callback else None
    close_start = time.perf_counter()
    mod._request_fast_close(close_probe)
    close_elapsed = time.perf_counter() - close_start
    record(
        "app_fast_close_hides_first",
        close_elapsed < 0.2
        and close_probe.stop_event
        and bool(close_withdraw_called)
        and bool(close_quit_called)
        and bool(close_destroy_called),
        f"{close_elapsed:.4f}s",
    )

    pdf_src = root / "sample.pdf"
    make_pdf(pdf_src, ["hello fengxi"])
    pkt = mod.create_watermark_packet("CONFIDENTIAL", "SmileySans-Oblique", 36, 0.2, 45)
    pdf_out = root / "sample_wm.pdf"
    status = mod.add_watermark_to_pdf(str(pdf_src), str(pdf_out), pkt, page_range="all", check_text="CONFIDENTIAL")
    watermark_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_out)).pages)
    record("pdf_watermark", status == "SUCCESS" and "CONFIDENTIAL" in watermark_text, status)
    red_pdf_out = root / "sample_wm_red.pdf"
    red_pkt = mod.create_watermark_packet("RED WATERMARK", "SmileySans-Oblique", 46, 0.55, 35, color="#FF2020")
    red_status = mod.add_watermark_to_pdf(str(pdf_src), str(red_pdf_out), red_pkt, page_range="all", check_text="RED WATERMARK", force_mode=True)
    red_pixels = rendered_pdf_redish_pixels(red_pdf_out)
    record(
        "pdf_watermark_custom_color",
        red_status == "SUCCESS" and red_pixels > 1000,
        {"status": red_status, "red_pixels": red_pixels},
    )
    pdf_random_src = root / "sample_first_random.pdf"
    make_pdf(pdf_random_src, ["page one", "page two", "page three"])
    pdf_random_out = root / "sample_first_random_wm.pdf"
    random_pkt = mod.create_watermark_packet("FIRST RANDOM", "SmileySans-Oblique", 42, 0.45, 35)
    import tools.fx_watermark_core as wm_core_for_random

    original_random_randint = wm_core_for_random.random.randint
    wm_core_for_random.random.randint = lambda start, end: 2
    try:
        random_status = mod.add_watermark_to_pdf(
            str(pdf_random_src),
            str(pdf_random_out),
            random_pkt,
            page_range="first_random",
            check_text="FIRST RANDOM",
            force_mode=True,
        )
    finally:
        wm_core_for_random.random.randint = original_random_randint
    random_page_pixels = [rendered_pdf_page_nonwhite_pixels(pdf_random_out, index) for index in range(3)]
    record(
        "pdf_watermark_first_random_two_pages",
        random_status == "SUCCESS"
        and random_page_pixels[0] > random_page_pixels[1] + 5000
        and random_page_pixels[2] > random_page_pixels[1] + 5000,
        {"status": random_status, "pixels": random_page_pixels},
    )

    copy_guard_pdf_noise = copy_guard_noise_lines_module("strong", 0, "pdf-noise-probe", allow_unicode=False)
    copy_guard_word_noise = copy_guard_noise_lines_module("strong", 0, "word-noise-probe", allow_unicode=True)
    record(
        "copy_guard_mixed_noise_character_families",
        all(line.startswith(COPY_GUARD_TEXT_PREFIX_MODULE) for line in copy_guard_pdf_noise + copy_guard_word_noise)
        and any(any(character.isdigit() for character in line) for line in copy_guard_pdf_noise)
        and any(any(character.isalpha() for character in line) for line in copy_guard_pdf_noise)
        and any(any(character in "|#@/" for character in line) for line in copy_guard_pdf_noise)
        and any(any("\u4e00" <= character <= "\u9fff" for character in line) for line in copy_guard_word_noise)
        and any("�" in line or "æ" in line for line in copy_guard_word_noise),
        {"pdf_noise": copy_guard_pdf_noise[:3], "word_noise": copy_guard_word_noise[:6]},
    )

    copy_guard_src = root / "copy_guard_source.pdf"
    copy_guard_source_pdf = canvas.Canvas(str(copy_guard_src))
    for copy_guard_line_index in range(12):
        copy_guard_source_pdf.drawString(
            100,
            740 - (copy_guard_line_index * 45),
            f"NORMAL CUSTOMER VISIBLE LINE {copy_guard_line_index + 1:02d}",
        )
    copy_guard_source_pdf.save()
    copy_guard_out = root / "copy_guard_output.pdf"
    import fitz as fitz_copy_guard

    with fitz_copy_guard.open(str(copy_guard_src)) as document:
        copy_guard_before_pixels = [page.get_pixmap(alpha=False).samples for page in document]
    copy_guard_status = mod.add_watermark_to_pdf(
        str(copy_guard_src),
        str(copy_guard_out),
        mod.create_watermark_packet("", "Helvetica", 12, 0.0, 0),
        page_range="first",
        check_text="",
        copy_guard=True,
        copy_guard_strength="standard",
    )
    copy_guard_reader = PdfReader(str(copy_guard_out))
    copy_guard_texts = [page.extract_text() or "" for page in copy_guard_reader.pages]
    copy_guard_text_lines = copy_guard_texts[0].splitlines() if copy_guard_texts else []
    copy_guard_first_noise_index = next(
        (
            index
            for index, line in enumerate(copy_guard_text_lines)
            if len(line) >= 80 and line.startswith(COPY_GUARD_TEXT_PREFIX_MODULE)
        ),
        -1,
    )
    copy_guard_last_visible_index = max(
        (
            index
            for index, line in enumerate(copy_guard_text_lines)
            if line == "NORMAL CUSTOMER VISIBLE LINE 12"
        ),
        default=-1,
    )
    with fitz_copy_guard.open(str(copy_guard_out)) as document:
        copy_guard_after_pixels = [page.get_pixmap(alpha=False).samples for page in document]
        copy_guard_local_line = document[0].get_text(
            clip=fitz_copy_guard.Rect(80, 300, 520, 350)
        ).strip()
    record(
        "pdf_copy_guard_whole_copy_noise_local_line_clean_visual_unchanged",
        copy_guard_status == "SUCCESS"
        and len(copy_guard_texts) == 1
        and all(len(text) > 500 for text in copy_guard_texts)
        and "NORMAL CUSTOMER VISIBLE LINE 01" in copy_guard_texts[0]
        and "NORMAL CUSTOMER VISIBLE LINE 12" in copy_guard_texts[0]
        and 0 < copy_guard_first_noise_index < copy_guard_last_visible_index
        and copy_guard_local_line == "NORMAL CUSTOMER VISIBLE LINE 06"
        and copy_guard_before_pixels == copy_guard_after_pixels
        and copy_guard_reader.metadata.get(COPY_GUARD_METADATA_KEY_MODULE) == COPY_GUARD_METADATA_VALUE_MODULE
        and normalize_copy_guard_strength_module("强力") == "strong",
        {
            "status": copy_guard_status,
            "text_lengths": [len(text) for text in copy_guard_texts],
            "local_line": copy_guard_local_line,
            "first_noise_index": copy_guard_first_noise_index,
            "last_visible_index": copy_guard_last_visible_index,
            "pixels_equal": copy_guard_before_pixels == copy_guard_after_pixels,
            "metadata": copy_guard_reader.metadata.get(COPY_GUARD_METADATA_KEY_MODULE),
        },
    )

    copy_guard_upgrade_out = root / "copy_guard_upgrade_existing_watermark.pdf"
    copy_guard_upgrade_status = mod.add_watermark_to_pdf(
        str(pdf_out),
        str(copy_guard_upgrade_out),
        pkt,
        page_range="all",
        check_text="CONFIDENTIAL",
        copy_guard=True,
        copy_guard_strength="light",
    )
    copy_guard_upgrade_reader = PdfReader(str(copy_guard_upgrade_out))
    copy_guard_upgrade_text = "\n".join(page.extract_text() or "" for page in copy_guard_upgrade_reader.pages)
    record(
        "pdf_copy_guard_upgrades_existing_watermark_without_duplicate_visible_text",
        copy_guard_upgrade_status == "SUCCESS"
        and copy_guard_upgrade_text.count("CONFIDENTIAL") == 1
        and len(copy_guard_upgrade_text) > len(watermark_text) + 200
        and copy_guard_upgrade_reader.metadata.get(COPY_GUARD_METADATA_KEY_MODULE) == COPY_GUARD_METADATA_VALUE_MODULE,
        {
            "status": copy_guard_upgrade_status,
            "visible_count": copy_guard_upgrade_text.count("CONFIDENTIAL"),
            "text_length": len(copy_guard_upgrade_text),
        },
    )
    record(
        "watermark_core_module_exports",
        callable(create_watermark_packet_module)
        and callable(add_watermark_to_pdf_module)
        and callable(add_watermark_to_word_module)
        and callable(normalize_copy_guard_strength_module)
        and callable(normalize_watermark_page_range_module)
        and getattr(mod._watermark_core_create_watermark_packet, "__module__", "") == "tools.fx_watermark_core",
        {
            "packet_module": getattr(create_watermark_packet_module, "__module__", ""),
            "pdf_module": getattr(add_watermark_to_pdf_module, "__module__", ""),
            "word_module": getattr(add_watermark_to_word_module, "__module__", ""),
        },
    )
    record(
        "pdf_compress_core_module_exports",
        callable(compress_pdf_file_module)
        and callable(build_pdf_compress_output_path_module)
        and "标准" in PDF_COMPRESS_LEVELS_MODULE
        and "标准" in PDF_IMAGE_COMPRESS_LEVELS_MODULE
        and "高清" in PDF_IMAGE_COMPRESS_LEVELS_MODULE
        and "极限小体积" in PDF_IMAGE_COMPRESS_LEVELS_MODULE
        and "图片化压缩" in PDF_IMAGE_COMPRESS_LEVELS_MODULE
        and getattr(mod.compress_pdf_file, "__module__", "") == "fengxi_toolbox",
        {
            "module": getattr(compress_pdf_file_module, "__module__", ""),
            "output_module": getattr(build_pdf_compress_output_path_module, "__module__", ""),
        },
    )
    ocr_task_src = root / "ocr_task_module" / "nested" / "scan.pdf"
    ocr_task_out_root = root / "ocr_task_out"
    ocr_task_src.parent.mkdir(parents=True)
    ocr_task_src.write_text("probe", encoding="utf-8")
    ocr_task_output = build_pdf_ocr_output_path(ocr_task_src, root / "ocr_task_module", ocr_task_out_root)
    ocr_task_report = build_pdf_ocr_compare_report_path(ocr_task_src, ocr_task_out_root)
    record(
        "pdf_ocr_task_module_exports",
        PdfOcrTaskOptions(model_root=root, profile_key="general", backend_key="auto").extraction_mode == "mixed"
        and isinstance(PdfOcrTaskCallbacks(), PdfOcrTaskCallbacks)
        and hasattr(PdfOcrTaskCallbacks(), "on_page_preview")
        and callable(run_pdf_ocr_task_core)
        and Path(ocr_task_output) == ocr_task_out_root / "nested" / "scan.pdf"
        and Path(ocr_task_report) == ocr_task_out_root / "_ocr_compare_reports" / "scan.ocr_compare.md",
        {
            "output": ocr_task_output,
            "report": ocr_task_report,
        },
    )
    Path(ocr_task_output).parent.mkdir(parents=True, exist_ok=True)
    Path(ocr_task_output).write_bytes(b"%PDF-resume-probe")

    class RaisingOcrEngine:
        def __init__(self, *args, **kwargs):
            raise AssertionError("OCR engine should not load for completed resume outputs")

    original_resume_ocr_engine = pdf_ocr_task_module.FengxiPdfOcrEngine
    pdf_ocr_task_module.FengxiPdfOcrEngine = RaisingOcrEngine
    try:
        ocr_resume_result = run_pdf_ocr_task_core(
            [str(ocr_task_src)],
            root / "ocr_task_module",
            ocr_task_out_root,
            PdfOcrTaskOptions(model_root=root, profile_key="general", backend_key="auto"),
            PdfOcrTaskCallbacks(),
        )
    finally:
        pdf_ocr_task_module.FengxiPdfOcrEngine = original_resume_ocr_engine
    record(
        "pdf_ocr_resume_skips_existing_output",
        ocr_resume_result.get("status") == "success"
        and ocr_resume_result.get("success_count") == 1
        and ocr_resume_result.get("skipped_count") == 1
        and ocr_resume_result.get("outputs") == [str(ocr_task_output)],
        ocr_resume_result,
    )

    img1 = root / "1.png"
    img2 = root / "2.png"
    Image.new("RGB", (100, 100), "red").save(img1)
    Image.new("RGB", (100, 100), "blue").save(img2)
    merged = root / "images.pdf"
    status = mod.merge_images_to_pdf([str(img1), str(img2)], str(merged))
    record("images_to_pdf", status == "SUCCESS" and merged.exists(), status)

    single_img_pdf = root / "single_image.pdf"
    status = mod._image_file_to_pdf(str(img1), str(single_img_pdf))
    record("image_to_pdf_helper", status == "SUCCESS" and single_img_pdf.exists(), status)
    image_task_probe_dir = root / "image_task_module"
    image_task_probe_dir.mkdir()
    Image.new("RGBA", (40, 30), (0, 120, 255, 128)).save(image_task_probe_dir / "probe.png")
    (image_task_probe_dir / "ignore.txt").write_text("no", encoding="utf-8")
    image_task_out = root / "image_task_out"
    image_task_name_out = root / "image_task_name_out"
    image_task_single_out = image_task_out / "probe.pdf"
    image_task_status = image_file_to_pdf(str(image_task_probe_dir / "probe.png"), str(image_task_single_out))
    image_task_result = run_image_pdf_task_core(
        [str(image_task_probe_dir / "probe.png")],
        image_task_probe_dir,
        image_task_probe_dir,
        image_task_out / "core",
        ImagePdfTaskOptions(image_to_pdf=image_file_to_pdf),
        ImagePdfTaskCallbacks(),
    )
    record(
        "image_pdf_task_module_exports",
        image_task_status == "SUCCESS"
        and image_task_single_out.exists()
        and collect_image_to_pdf_files(image_task_probe_dir) == [str(image_task_probe_dir / "probe.png")]
        and Path(build_image_pdf_output_path(image_task_probe_dir / "probe.png", image_task_name_out)) == image_task_name_out / "probe.pdf"
        and Path(build_image_merge_pdf_output_path(image_task_probe_dir, image_task_probe_dir, image_task_out)) == image_task_out / "image_task_module_图集合并.pdf"
        and image_task_result.get("status") == "success"
        and callable(run_image_pdf_task_core),
        {
            "status": image_task_status,
            "result": image_task_result,
            "single": str(image_task_single_out),
        },
    )
    image_resume_out = root / "image_task_resume_out"
    image_resume_pdf = image_resume_out / "probe.pdf"
    image_resume_pdf.parent.mkdir(parents=True)
    image_resume_pdf.write_bytes(b"existing-image-pdf")
    image_resume_result = run_image_pdf_task_core(
        [str(image_task_probe_dir / "probe.png")],
        image_task_probe_dir,
        image_task_probe_dir,
        image_resume_out,
        ImagePdfTaskOptions(image_to_pdf=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("image pdf should resume"))),
        ImagePdfTaskCallbacks(),
    )
    record(
        "image_pdf_resume_skips_existing_output",
        image_resume_result.get("status") == "success"
        and image_resume_result.get("success_count") == 1
        and image_resume_result.get("skipped_count") == 1
        and image_resume_result.get("outputs") == [str(image_resume_pdf)],
        image_resume_result,
    )

    src = root / "stamp.txt"
    dst = root / "stamp_out.txt"
    src.write_text("abc", encoding="utf-8")
    status = mod.modify_file_timestamp(str(src), str(dst), "2024-01-02 03:04:05")
    record("modify_timestamp", status == "SUCCESS" and dst.exists(), status)

    inp = root / "pdf_in"
    out = root / "pdf_out"
    inp.mkdir()
    out.mkdir()
    src = inp / "multi.pdf"
    make_pdf(src, ["p1", "p2"])
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "pdf", ("split", "", False), [])
    split_folder = out / "multi"
    record("pdf_split", split_folder.exists() and len(list(split_folder.glob("*.pdf"))) == 2, "ok")
    split_outputs = sorted(split_folder.glob("*.pdf"))
    if split_outputs:
        split_outputs[0].write_bytes(b"existing split resume marker")
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "pdf", ("split", "", False), [])
    record(
        "pdf_split_resume_skips_complete_outputs",
        bool(split_outputs)
        and split_outputs[0].read_bytes() == b"existing split resume marker"
        and any("resume skip existing output" in str(item) or "断点续跑" in str(item) for item in dummy.logs),
        dummy.logs[-4:],
    )

    inp = root / "pdf_enc_in"
    out = root / "pdf_enc_out"
    inp.mkdir()
    out.mkdir()
    src = inp / "enc.pdf"
    make_pdf(src, ["secret"])
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "pdf", ("encrypt", "1234", False), [])
    enc = out / "enc.pdf"
    reader = PdfReader(str(enc))
    record("pdf_encrypt", enc.exists() and reader.is_encrypted, "encrypted=" + str(reader.is_encrypted))

    inp = root / "pdf_compress_in"
    out = root / "pdf_compress_out"
    inp.mkdir()
    out.mkdir()
    src = inp / "compress.pdf"
    make_pdf(src, ["compress me"])
    compressed = out / "compress_out.pdf"
    status = mod.compress_pdf_file(str(src), str(compressed), "强力", "保留原图")
    compressed_text = ""
    try:
        compressed_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(compressed)).pages)
    except Exception:
        compressed_text = ""
    record(
        "pdf_compress_helper",
        status.startswith("SUCCESS") and compressed.exists() and "compress me" in compressed_text,
        status,
    )
    record(
        "pdf_compress_core_helper",
        compress_pdf_file_module(str(src), str(root / "pdf_compress_out_core.pdf"), "强力", "保留原图").startswith("SUCCESS"),
        "core_helper",
    )
    no_growth_src = inp / "no_growth_vector.pdf"
    make_pdf(no_growth_src, ["vector text"] * 80)
    no_growth_out = out / "no_growth_vector_compressed.pdf"
    no_growth_status = compress_pdf_file_module(str(no_growth_src), str(no_growth_out), "标准", "保留原图")
    record(
        "pdf_compress_never_outputs_larger_file",
        no_growth_status.startswith("SUCCESS")
        and no_growth_out.exists()
        and no_growth_out.stat().st_size <= no_growth_src.stat().st_size,
        {
            "status": no_growth_status,
            "source_size": no_growth_src.stat().st_size,
            "output_size": no_growth_out.stat().st_size if no_growth_out.exists() else 0,
        },
    )
    resume_stamp = build_pdf_compress_profile_stamp_module(str(no_growth_src), "标准", "保留原图")
    write_pdf_compress_meta_module(str(no_growth_out), resume_stamp, {"status": "probe"})
    mismatched_stamp = build_pdf_compress_profile_stamp_module(str(no_growth_src), "强力", "保留原图")
    record(
        "pdf_compress_resume_requires_matching_profile",
        pdf_compress_meta_matches_module(str(no_growth_out), resume_stamp)
        and not pdf_compress_meta_matches_module(str(no_growth_out), mismatched_stamp),
        {
            "matching": pdf_compress_meta_matches_module(str(no_growth_out), resume_stamp),
            "mismatched": pdf_compress_meta_matches_module(str(no_growth_out), mismatched_stamp),
        },
    )
    cache_meta_path, cache_meta_key = build_pdf_compress_meta_path_module(str(no_growth_out))
    legacy_sidecar = no_growth_out.with_name(f".{no_growth_out.name}.fx-compress.json")
    record(
        "pdf_compress_meta_stored_outside_output_folder",
        Path(cache_meta_path).name == "pdf_compress_cache.json"
        and Path(cache_meta_path).parent != no_growth_out.parent
        and not legacy_sidecar.exists()
        and bool(cache_meta_key),
        {
            "cache_meta_path": str(cache_meta_path),
            "output_parent": str(no_growth_out.parent),
            "legacy_sidecar_exists": legacy_sidecar.exists(),
        },
    )
    record(
        "pdf_compress_reports_engine_candidate",
        any(token in no_growth_status for token in (":optimized", ":pikepdf", ":pymupdf", ":ghostscript", ":kept_original")),
        no_growth_status,
    )
    fake_tlgs = root / "fake_texlive" / "2024" / "tlpkg" / "tlgs"
    fake_gs = fake_tlgs / "bin" / "gswin64c.exe"
    for rel in (
        ("Resource", "Init"),
        ("lib",),
        ("kanji",),
        ("Resource", "Font"),
        ("Resource", "CMap"),
        ("Resource", "CIDFont"),
    ):
        fake_tlgs.joinpath(*rel).mkdir(parents=True, exist_ok=True)
    fake_gs.parent.mkdir(parents=True, exist_ok=True)
    fake_gs.write_text("fake", encoding="utf-8")
    old_gs_lib = os.environ.get("GS_LIB")
    os.environ["GS_LIB"] = str(root / "already_in_gs_lib")
    try:
        gs_env = build_ghostscript_env_module(str(fake_gs))
        gs_lib_parts = gs_env.get("GS_LIB", "").split(os.pathsep)
    finally:
        if old_gs_lib is None:
            os.environ.pop("GS_LIB", None)
        else:
            os.environ["GS_LIB"] = old_gs_lib
    record(
        "pdf_compress_ghostscript_texlive_env",
        str(fake_tlgs / "Resource" / "Init") in gs_lib_parts
        and str(fake_tlgs / "lib") in gs_lib_parts
        and str(fake_tlgs / "kanji") in gs_lib_parts
        and str(root / "already_in_gs_lib") in gs_lib_parts,
        {"GS_LIB": gs_env.get("GS_LIB", "")},
    )
    real_gs = find_ghostscript_executable_module()
    if real_gs:
        gs_probe = out / "ghostscript_probe.pdf"
        gs_probe_status = run_ghostscript_candidate_module(
            str(no_growth_src),
            str(gs_probe),
            "强力",
            "强力",
        )
        record(
            "pdf_compress_ghostscript_candidate_runs_when_available",
            gs_probe_status.startswith("SUCCESS") and gs_probe.exists() and gs_probe.stat().st_size > 0,
            {"status": gs_probe_status, "gs": real_gs, "size": gs_probe.stat().st_size if gs_probe.exists() else 0},
        )
    else:
        record(
            "pdf_compress_ghostscript_candidate_runs_when_available",
            True,
            "skipped: ghostscript unavailable",
        )
    long_image = inp / "long_scan.jpg"
    long_img = Image.new("RGB", (1080, 6976), "white")
    for y in range(80, 6900, 180):
        for x in range(80, 1000, 24):
            long_img.putpixel((x, y), (0, 0, 0))
            long_img.putpixel((x + 1, y), (0, 0, 0))
            long_img.putpixel((x, y + 1), (0, 0, 0))
    long_img.save(long_image, "JPEG", quality=96)
    long_pdf = inp / "long_scan.pdf"
    make_long_image_pdf(long_pdf, long_image)
    long_standard = out / "long_scan_standard.pdf"
    long_tiny = out / "long_scan_tiny.pdf"
    standard_status = mod.compress_pdf_file(str(long_pdf), str(long_standard), "标准", "标准")
    tiny_status = mod.compress_pdf_file(str(long_pdf), str(long_tiny), "标准", "极限小体积")
    standard_image_size = first_pdf_image_size(long_standard)
    tiny_image_size = first_pdf_image_size(long_tiny)
    record(
        "pdf_compress_long_scan_keeps_readable_width",
        standard_status.startswith("SUCCESS")
        and long_standard.exists()
        and standard_image_size[0] >= 1080
        and standard_image_size[1] >= 6000
        and tiny_status.startswith("SUCCESS")
        and tiny_image_size[0] < standard_image_size[0],
        {
            "standard_status": standard_status,
            "tiny_status": tiny_status,
            "standard_size": standard_image_size,
            "tiny_size": tiny_image_size,
            "standard_bytes": long_standard.stat().st_size if long_standard.exists() else 0,
            "tiny_bytes": long_tiny.stat().st_size if long_tiny.exists() else 0,
        },
    )

    vector_raster_pdf = inp / "vector_raster_source.pdf"
    vec_canvas = canvas.Canvas(str(vector_raster_pdf))
    for page_index in range(12):
        vec_canvas.setFont("Helvetica", 8)
        for row in range(85):
            y = 812 - row * 9
            vec_canvas.drawString(22, y, f"Vector row {page_index+1:02d}-{row+1:02d} | " + ("ABCD1234 xyz " * 22))
            vec_canvas.line(20, y - 1, 585, y - 1)
            vec_canvas.line(20, y + 2, 585, y + 2)
            vec_canvas.rect(20 + (row % 15) * 12, y - 7, 160, 8, stroke=1, fill=0)
            vec_canvas.circle(520 - (row % 8) * 14, y - 3, 4, stroke=1, fill=0)
        vec_canvas.showPage()
    vec_canvas.save()
    vector_raster_out = out / "vector_rasterized.pdf"
    vector_pike_out = out / "vector_pike.pdf"
    vector_raster_status = mod.compress_pdf_file(str(vector_raster_pdf), str(vector_raster_out), "标准", "图片化压缩")
    vector_pike_status = mod.compress_pdf_file(str(vector_raster_pdf), str(vector_pike_out), "标准", "保留原图")
    vector_raster_img_size = first_pdf_image_size(vector_raster_out)
    record(
        "pdf_compress_web_raster_mode",
        vector_raster_status.startswith("SUCCESS")
        and vector_pike_status.startswith("SUCCESS")
        and vector_raster_out.exists()
        and vector_pike_out.exists()
        and vector_raster_out.stat().st_size <= vector_raster_pdf.stat().st_size
        and (
            ":rasterized" in vector_raster_status
            or vector_raster_out.stat().st_size == vector_pike_out.stat().st_size
        ),
        {
            "status": vector_raster_status,
            "pike_status": vector_pike_status,
            "source_bytes": vector_raster_pdf.stat().st_size,
            "raster_bytes": vector_raster_out.stat().st_size if vector_raster_out.exists() else 0,
            "pike_bytes": vector_pike_out.stat().st_size if vector_pike_out.exists() else 0,
            "first_image_size": vector_raster_img_size,
        },
    )

    single_pdf = root / "single_input_encrypt.pdf"
    make_pdf(single_pdf, ["single file input"])
    app.current_task = "pdf"
    app.pdf_mode_var.set("encrypt")
    app.pdf_pwd_entry.delete(0, "end")
    app.pdf_pwd_entry.insert(0, "4321")
    app.run_process(str(single_pdf), "pdf")
    single_pdf_out = root / "【处理完成】结果文件夹" / "single_input_encrypt.pdf"
    single_pdf_ok = wait_for(lambda: single_pdf_out.exists()) and PdfReader(str(single_pdf_out)).is_encrypted
    record("single_file_input_pdf_encrypt", single_pdf_ok, single_pdf_out)

    single_compress_pdf = root / "single_input_compress.pdf"
    make_pdf(single_compress_pdf, ["single compress input"])
    app.current_task = "pdf"
    app.pdf_mode_var.set("compress")
    if hasattr(app, "pdf_compress_level_var"):
        app.pdf_compress_level_var.set("标准")
    if hasattr(app, "pdf_image_compress_level_var"):
        app.pdf_image_compress_level_var.set("保留原图")
    app.run_process(str(single_compress_pdf), "pdf")
    single_compress_out = root / "【处理完成】结果文件夹" / "single_input_compress_压缩.pdf"
    single_compress_result = getattr(app, "_fx_last_task_result", {})
    single_compress_text = ""
    if wait_for(lambda: single_compress_out.exists()):
        single_compress_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(single_compress_out)).pages)
    record(
        "single_file_input_pdf_compress",
        single_compress_out.exists() and "single compress input" in single_compress_text,
        single_compress_out,
    )
    record(
        "single_file_input_pdf_compress_result_model",
        isinstance(single_compress_result, dict)
        and single_compress_result.get("status") == "success"
        and single_compress_result.get("output_strategy_requested") == "result_folder"
        and single_compress_result.get("output_strategy") == "result_folder"
        and str(single_compress_result.get("output_root", "")).endswith("【处理完成】结果文件夹")
        and str(single_compress_out) in list(single_compress_result.get("outputs") or [])
        and float(single_compress_result.get("duration_seconds") or 0.0) >= 0.0,
        single_compress_result,
    )

    parallel_pdf_root = root / "parallel_pdf_compress"
    parallel_pdf_root.mkdir()
    make_pdf(parallel_pdf_root / "a.pdf", ["parallel a"])
    make_pdf(parallel_pdf_root / "b.pdf", ["parallel b"])
    app.current_task = "pdf"
    app.pdf_mode_var.set("compress")
    if hasattr(app, "pdf_compress_level_var"):
        app.pdf_compress_level_var.set("标准")
    if hasattr(app, "pdf_image_compress_level_var"):
        app.pdf_image_compress_level_var.set("保留原图")
    app.enable_multithread.set(True)
    pdf_executor_workers = []
    original_executor = mod.concurrent.futures.ThreadPoolExecutor

    class RecordingExecutor(original_executor):
        def __init__(self, *args, **kwargs):
            pdf_executor_workers.append(kwargs.get("max_workers") if "max_workers" in kwargs else (args[0] if args else None))
            super().__init__(*args, **kwargs)

    mod.concurrent.futures.ThreadPoolExecutor = RecordingExecutor
    try:
        app.run_process(str(parallel_pdf_root), "pdf")
    finally:
        mod.concurrent.futures.ThreadPoolExecutor = original_executor
        app.enable_multithread.set(False)
    record(
        "pdf_compress_parallel_executor",
        bool(pdf_executor_workers) and max(value or 0 for value in pdf_executor_workers) > 1,
        pdf_executor_workers,
    )

    parallel_wm_root = root / "parallel_watermark_pdf"
    parallel_wm_root.mkdir()
    make_pdf(parallel_wm_root / "a.pdf", ["watermark parallel a"])
    make_pdf(parallel_wm_root / "b.pdf", ["watermark parallel b"])
    mod._ensure_lazy_tab_initialized(app, "watermark")
    try:
        app.wm_text.delete("1.0", "end")
        app.wm_text.insert("1.0", "PARALLEL WM")
    except Exception:
        pass
    app.wm_copy_guard_enabled_var.set(True)
    app.wm_copy_guard_strength_var.set("强力")
    app.current_task = "watermark"
    app.enable_multithread.set(True)
    watermark_executor_workers = []
    original_executor = mod.concurrent.futures.ThreadPoolExecutor

    class RecordingWatermarkExecutor(original_executor):
        def __init__(self, *args, **kwargs):
            watermark_executor_workers.append(kwargs.get("max_workers") if "max_workers" in kwargs else (args[0] if args else None))
            super().__init__(*args, **kwargs)

    mod.concurrent.futures.ThreadPoolExecutor = RecordingWatermarkExecutor
    try:
        app.run_process(str(parallel_wm_root), "watermark")
    finally:
        mod.concurrent.futures.ThreadPoolExecutor = original_executor
        app.enable_multithread.set(False)
    parallel_wm_out_a = parallel_wm_root / mod.RESULT_FOLDER_NAME / "a.pdf"
    parallel_wm_out_b = parallel_wm_root / mod.RESULT_FOLDER_NAME / "b.pdf"
    parallel_wm_result = dict(getattr(app, "_fx_last_task_result", {}) or {})
    parallel_wm_logs = list(getattr(app, "_fx_last_task_logs", []) or [])
    try:
        parallel_wm_reader_a = PdfReader(str(parallel_wm_out_a))
        parallel_wm_guard_text_a = "\n".join(page.extract_text() or "" for page in parallel_wm_reader_a.pages)
        parallel_wm_guard_metadata_a = parallel_wm_reader_a.metadata.get(COPY_GUARD_METADATA_KEY_MODULE)
    except Exception:
        parallel_wm_guard_text_a = ""
        parallel_wm_guard_metadata_a = ""
    record(
        "watermark_pdf_parallel_executor",
        bool(watermark_executor_workers)
        and max(value or 0 for value in watermark_executor_workers) > 1
        and wait_for(lambda: parallel_wm_out_a.exists() and parallel_wm_out_b.exists())
        and parallel_wm_result.get("status") == "success"
        and parallel_wm_result.get("success_count") == 2
        and len(parallel_wm_guard_text_a) > 800
        and parallel_wm_guard_metadata_a == COPY_GUARD_METADATA_VALUE_MODULE
        and any("[复制干扰层] 已开启（强力）" in item for item in parallel_wm_logs),
        {
            "workers": watermark_executor_workers,
            "result": parallel_wm_result,
            "outputs": [str(parallel_wm_out_a), str(parallel_wm_out_b)],
            "guard_text_length": len(parallel_wm_guard_text_a),
            "guard_metadata": parallel_wm_guard_metadata_a,
            "logs": parallel_wm_logs,
        },
    )
    app.wm_copy_guard_enabled_var.set(False)

    inp = root / "img_in"
    out = root / "img_out"
    inp.mkdir()
    out.mkdir()
    src = inp / "pic.png"
    Image.new("RGBA", (120, 80), (0, 255, 0, 255)).save(src)
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "image", ("convert", False, "jpg", 1.0), [])
    record("image_convert", (out / "pic.jpg").exists(), "ok")

    inp = root / "img_cmp_in"
    out = root / "img_cmp_out"
    inp.mkdir()
    out.mkdir()
    src = inp / "big.jpg"
    Image.new("RGB", (200, 100), "yellow").save(src)
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "image", ("compress", False, "jpg", 0.5), [])
    record("image_compress", (out / "big.jpg").exists(), "ok")

    img_pdf_root = root / "image_to_pdf_workflow"
    img_pdf_root.mkdir()
    Image.new("RGB", (80, 60), "red").save(img_pdf_root / "one.png")
    Image.new("RGB", (80, 60), "blue").save(img_pdf_root / "two.jpg")
    app.current_task = "image"
    app.img_mode_var.set("to_pdf")
    app.run_process(str(img_pdf_root), "image")
    image_to_pdf_out = img_pdf_root / "【处理完成】结果文件夹" / "one.pdf"
    image_to_pdf_out_2 = img_pdf_root / "【处理完成】结果文件夹" / "two.pdf"
    record(
        "image_to_pdf_workflow",
        wait_for(lambda: image_to_pdf_out.exists() and image_to_pdf_out_2.exists()),
        image_to_pdf_out,
    )

    img_pdf_parallel_root = root / "image_to_pdf_parallel"
    img_pdf_parallel_root.mkdir()
    Image.new("RGB", (80, 60), "purple").save(img_pdf_parallel_root / "p1.png")
    Image.new("RGB", (80, 60), "orange").save(img_pdf_parallel_root / "p2.jpg")
    app.current_task = "image"
    app.img_mode_var.set("to_pdf")
    app.enable_multithread.set(True)
    image_executor_workers = []
    original_executor = mod.concurrent.futures.ThreadPoolExecutor

    class RecordingImageExecutor(original_executor):
        def __init__(self, *args, **kwargs):
            image_executor_workers.append(kwargs.get("max_workers") if "max_workers" in kwargs else (args[0] if args else None))
            super().__init__(*args, **kwargs)

    mod.concurrent.futures.ThreadPoolExecutor = RecordingImageExecutor
    try:
        app.run_process(str(img_pdf_parallel_root), "image")
    finally:
        mod.concurrent.futures.ThreadPoolExecutor = original_executor
        app.enable_multithread.set(False)
    record(
        "image_to_pdf_parallel_executor",
        bool(image_executor_workers) and max(value or 0 for value in image_executor_workers) > 1,
        image_executor_workers,
    )

    img_merge_root = root / "image_merge_pdf_workflow"
    img_merge_root.mkdir()
    Image.new("RGB", (80, 60), "green").save(img_merge_root / "1.png")
    Image.new("RGB", (80, 60), "yellow").save(img_merge_root / "2.jpg")
    app.current_task = "image"
    app.img_mode_var.set("merge_pdf")
    app.run_process(str(img_merge_root), "image")
    image_merge_pdf_out = img_merge_root / "【处理完成】结果文件夹" / "image_merge_pdf_workflow_图集合并.pdf"
    record(
        "image_merge_pdf_workflow",
        wait_for(lambda: image_merge_pdf_out.exists()),
        image_merge_pdf_out,
    )

    for name, args, expected in [
        ("file_rename_add", ("rename", "add", "pre_", "_suf"), "pre_demo_suf.txt"),
        ("file_rename_replace", ("rename", "replace", "demo", "sample"), "sample.txt"),
        ("file_rename_cut", ("rename", "cut", "2", "1"), "m.txt"),
    ]:
        inp = root / f"{name}_in"
        out = root / f"{name}_out"
        inp.mkdir()
        out.mkdir()
        src = inp / "demo.txt"
        src.write_text("x", encoding="utf-8")
        mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "file", args, [])
        record(name, (out / expected).exists(), expected)

    resume_rename_in = root / "file_rename_resume_in"
    resume_rename_out = root / "file_rename_resume_out"
    resume_rename_in.mkdir()
    resume_rename_out.mkdir()
    resume_rename_src = resume_rename_in / "demo.txt"
    resume_rename_dst = resume_rename_out / "pre_demo_suf.txt"
    resume_rename_src.write_text("new-source", encoding="utf-8")
    resume_rename_dst.write_text("existing-output", encoding="utf-8")
    mod.FengxiToolboxApp.process_single_file(
        dummy,
        str(resume_rename_src),
        str(resume_rename_in),
        str(resume_rename_out),
        "file",
        ("rename", "add", "pre_", "_suf"),
        [],
    )
    record(
        "process_single_file_resume_rename",
        resume_rename_dst.read_text(encoding="utf-8") == "existing-output"
        and any("resume skip existing output" in str(item) or "断点续跑" in str(item) for item in dummy.logs),
        dummy.logs[-3:],
    )

    file_core_out = root / "file_core_out"
    file_core_out.mkdir()
    rename_spec = normalize_file_rename_spec_module(("rename", "add", "pre_", "_suf"))
    rename_plan = plan_renamed_output_path_module(root / "demo.txt", file_core_out, rename_spec)
    file_core_target = file_core_out / "demo.txt"
    file_core_target.write_text("x", encoding="utf-8")
    file_core_result = apply_rename_to_file_module(
        str(file_core_target),
        str(file_core_out),
        str(file_core_out),
        ("rename", "replace", "demo", "sample"),
        copy_file_safe=mod.copy_file_safe,
        log=lambda *_args, **_kwargs: None,
    )
    record(
        "file_manager_core_module_exports",
        callable(rename_file_name_module)
        and callable(plan_renamed_output_path_module)
        and callable(apply_rename_to_file_module)
        and callable(deduplicate_files_module)
        and callable(run_file_dedup_task_module)
        and rename_spec.rename_type == "add"
        and Path(rename_plan).name == "pre_demo_suf.txt"
        and Path(file_core_result.get("output", "")).name == "sample.txt"
        and (file_core_out / "sample.txt").exists()
        and getattr(mod.FengxiToolboxApp.process_single_file, "__fx_file_manager_core_patch__", False),
        {
            "plan": rename_plan,
            "result": file_core_result,
            "outputs": sorted(p.name for p in file_core_out.iterdir()),
        },
    )

    file_task_root = root / "file_task_module"
    file_task_root.mkdir()
    (file_task_root / "keep.txt").write_text("same", encoding="utf-8")
    (file_task_root / "dup.txt").write_text("same", encoding="utf-8")
    file_task_app = type("FileTaskModuleApp", (), {"stop_event": False})()
    file_task_result = {}
    file_task_logs = []

    def file_task_start(_app, input_value, task_type):
        file_task_result.update({"task_type": task_type, "input": str(input_value), "outputs": []})
        return file_task_result

    def file_task_output(result, path):
        result.setdefault("outputs", []).append(str(path))

    def file_task_counts(result, **counts):
        result.update(counts)

    def file_task_finish(result, status, **kwargs):
        result["status"] = status
        result.update(kwargs)
        return result

    file_task_module_result = run_file_dedup_task_core_module(
        file_task_app,
        str(file_task_root),
        collect_input_files=lambda _input, _task: [str(file_task_root / "keep.txt"), str(file_task_root / "dup.txt")],
        get_last_task_result=lambda _app: None,
        start_task_result=file_task_start,
        set_task_result_output_strategy=lambda *_args, **_kwargs: None,
        set_task_result_output_root=lambda result, path: result.update({"output_root": str(path)}),
        add_task_result_output=file_task_output,
        set_task_result_counts=file_task_counts,
        set_task_result_finished=file_task_finish,
        normalize_input_path=str,
        get_task_output_strategy=lambda *_args: "same_dir",
        clamp_progress_value=lambda value: float(value),
        set_progress_status=lambda *_args, **_kwargs: None,
        log=lambda message: file_task_logs.append(str(message)),
    )
    record(
        "file_manager_task_module_exports",
        callable(run_file_dedup_task_core_module)
        and file_task_module_result.get("status") == "success"
        and file_task_module_result.get("processed") == 2
        and file_task_module_result.get("success") == 1
        and sorted(p.name for p in file_task_root.glob("*.txt")) == ["keep.txt"]
        and any("文件去重" in item for item in file_task_logs),
        {
            "result": file_task_module_result,
            "logs": file_task_logs,
            "remaining": sorted(p.name for p in file_task_root.glob("*.txt")),
        },
    )

    inp = root / "meta_in"
    out = root / "meta_out"
    inp.mkdir()
    out.mkdir()
    src = inp / "a.txt"
    src.write_text("meta", encoding="utf-8")
    failed = []
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "meta", ("time", "2024-05-06 07:08:09"), failed)
    record("meta_time", (out / "a.txt").exists() and not failed, str(failed))

    meta_core_time_src = root / "meta_core_time_src.txt"
    meta_core_time_src.write_text("meta core time", encoding="utf-8")
    meta_core_time_dst = root / "meta_core_time_dst.txt"
    meta_core_time_status = modify_file_timestamp_module(str(meta_core_time_src), str(meta_core_time_dst), "2024-05-06 07:08:09")
    record(
        "meta_core_module_exports",
        callable(build_meta_output_path_module)
        and callable(modify_file_timestamp_module)
        and callable(modify_pdf_author_module)
        and callable(modify_office_meta_module)
        and callable(process_meta_file_module)
        and meta_core_time_status == "SUCCESS"
        and meta_core_time_dst.exists(),
        meta_core_time_status,
    )

    inp = root / "meta_pdf_in"
    out = root / "meta_pdf_out"
    inp.mkdir()
    out.mkdir()
    src = inp / "m.pdf"
    make_pdf(src, ["meta pdf"])
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "meta", ("author", "Tester"), [])
    meta_reader = PdfReader(str(out / "m.pdf"))
    record("meta_author_pdf", meta_reader.metadata.get("/Author") == "Tester", meta_reader.metadata)

    meta_core_pdf_in = root / "meta_core_pdf_in"
    meta_core_pdf_out = root / "meta_core_pdf_out"
    meta_core_pdf_in.mkdir()
    meta_core_pdf_out.mkdir()
    meta_core_pdf_src = meta_core_pdf_in / "core.pdf"
    make_pdf(meta_core_pdf_src, ["meta core pdf"])
    meta_core_failures = []
    process_meta_file_module(
        str(meta_core_pdf_src),
        str(meta_core_pdf_in),
        str(meta_core_pdf_out),
        ("author", "CoreTester"),
        meta_core_failures,
        copy_file_safe=mod.copy_file_safe,
        log=lambda *_args, **_kwargs: None,
    )
    meta_core_reader = PdfReader(str(meta_core_pdf_out / "core.pdf"))
    record(
        "meta_core_process_file",
        meta_core_reader.metadata.get("/Author") == "CoreTester" and not meta_core_failures,
        meta_core_reader.metadata,
    )

    convert_core_root = root / "convert_core"
    convert_core_root.mkdir()
    (convert_core_root / "doc.docx").write_text("doc", encoding="utf-8")
    (convert_core_root / "slides.pptx").write_text("ppt", encoding="utf-8")
    make_pdf(convert_core_root / "scan.pdf", ["convert core"])
    (convert_core_root / "notes.txt").write_text("hello txt\n第二行", encoding="utf-8")
    (convert_core_root / "article.md").write_text("# 标题\n\n- item", encoding="utf-8")
    Image.new("RGB", (20, 20), "red").save(convert_core_root / "b.jpg")
    Image.new("RGB", (20, 20), "blue").save(convert_core_root / "a.png")
    (convert_core_root / "note.txt").write_text("ignore", encoding="utf-8")
    convert_output_root = convert_core_root / "out"
    convert_output_root.mkdir()
    word_files = collect_convert_files_module(str(convert_core_root), "word2pdf")
    img_files = collect_convert_files_module(str(convert_core_root), "imgs2pdf")
    txt_files = collect_convert_files_module(str(convert_core_root), "txt2word")
    md_files = collect_convert_files_module(str(convert_core_root), "md2pdf")
    record(
        "convert_core_module_exports",
        normalize_convert_mode_module("pdf_to_word") == "pdf2word"
        and normalize_convert_mode_module("pdf_to_ppt") == "pdf2ppt"
        and normalize_convert_mode_module("markdown_to_pdf") == "md2pdf"
        and describe_convert_mode_module("ppt2pdf") == "PPT 转 PDF"
        and describe_convert_mode_module("pdf2md") == "PDF 转 Markdown"
        and "imgs2pdf" in CONVERT_MODE_SPECS_MODULE
        and "pdf2ppt" in CONVERT_MODE_SPECS_MODULE
        and [Path(path).name for path in word_files] == ["doc.docx"]
        and [Path(path).name for path in img_files] == ["a.png", "b.jpg"]
        and [Path(path).name for path in txt_files] == ["note.txt", "notes.txt"]
        and [Path(path).name for path in md_files] == ["article.md"]
        and Path(plan_convert_output_path_module(str(convert_core_root / "scan.pdf"), str(convert_core_root), str(convert_output_root), "pdf2word")).name == "scan.docx"
        and Path(plan_convert_output_path_module(str(convert_core_root / "scan.pdf"), str(convert_core_root), str(convert_output_root), "pdf2ppt")).name == "scan.pptx"
        and Path(plan_convert_output_path_module(str(convert_core_root / "notes.txt"), str(convert_core_root), str(convert_output_root), "txt2word")).name == "notes.docx"
        and Path(plan_convert_output_path_module(str(convert_core_root / "article.md"), str(convert_core_root), str(convert_output_root), "md2pdf")).name == "article.pdf"
        and Path(plan_convert_output_path_module(str(convert_core_root / "scan.pdf"), str(convert_core_root), str(convert_output_root), "pdf2md")).name == "scan.md"
        and Path(plan_convert_output_path_module("", str(convert_core_root), str(convert_output_root), "imgs2pdf")).name == "convert_core_图集合并.pdf",
        {
            "word": [Path(path).name for path in word_files],
            "images": [Path(path).name for path in img_files],
            "txt": [Path(path).name for path in txt_files],
            "md": [Path(path).name for path in md_files],
            "pdf_out": plan_convert_output_path_module(str(convert_core_root / "scan.pdf"), str(convert_core_root), str(convert_output_root), "pdf2word"),
            "imgs_out": plan_convert_output_path_module("", str(convert_core_root), str(convert_output_root), "imgs2pdf"),
        },
    )

    convert_task_root = root / "convert_task_imgs"
    convert_task_root.mkdir()
    Image.new("RGB", (18, 18), "green").save(convert_task_root / "one.png")
    Image.new("RGB", (18, 18), "yellow").save(convert_task_root / "two.jpg")
    convert_task_out = root / "convert_task_out"
    convert_task_logs = []
    convert_task_result = run_convert_imgs_to_pdf_task_core_module(
        str(convert_task_root),
        input_root=str(convert_task_root),
        output_folder=str(convert_task_out),
        merge_images_to_pdf=mod.merge_images_to_pdf,
        callbacks=ConvertImgsToPdfCallbacks(log=lambda message: convert_task_logs.append(str(message))),
    )
    convert_task_pdf = convert_task_out / "convert_task_imgs_图集合并.pdf"
    record(
        "convert_task_imgs2pdf_module_exports",
        callable(run_convert_imgs_to_pdf_task_core_module)
        and isinstance(ConvertImgsToPdfCallbacks(), ConvertImgsToPdfCallbacks)
        and convert_task_result.get("status") == "success"
        and convert_task_result.get("success_count") == 2
        and convert_task_pdf.exists()
        and any("多图合并PDF" in item for item in convert_task_logs),
        {
            "result": convert_task_result,
            "logs": convert_task_logs,
            "output": str(convert_task_pdf),
        },
    )

    convert_file_root = root / "convert_file_adapter"
    convert_file_root.mkdir()
    convert_file_out = root / "convert_file_adapter_out"
    convert_file_out.mkdir()
    (convert_file_root / "doc.docx").write_text("doc", encoding="utf-8")
    make_pdf(convert_file_root / "scan.pdf", ["convert file adapter"])
    (convert_file_root / "slides.pptx").write_text("ppt", encoding="utf-8")
    convert_file_calls = []
    convert_file_copies = []
    convert_file_logs = []

    def fake_doc_to_pdf(app_obj, src, dst):
        convert_file_calls.append(("word", Path(src).name, Path(dst).name, app_obj))
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        Path(dst).write_bytes(b"word-pdf")
        return "SUCCESS"

    def fake_pdf_to_word(src, dst):
        convert_file_calls.append(("pdf", Path(src).name, Path(dst).name))
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        Path(dst).write_bytes(b"pdf-word")
        return "SUCCESS"

    def fake_ppt_to_pdf(app_obj, src, dst):
        convert_file_calls.append(("ppt", Path(src).name, Path(dst).name, app_obj))
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        Path(dst).write_bytes(b"ppt-pdf")
        return "SUCCESS"

    def fake_pdf_to_ppt(app_obj, src, dst):
        convert_file_calls.append(("pdfppt", Path(src).name, Path(dst).name, app_obj))
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        Path(dst).write_bytes(b"pdf-ppt")
        return "SUCCESS"

    def fake_copy(src, dst):
        convert_file_copies.append((Path(src).name, Path(dst).name))
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        Path(dst).write_bytes(Path(src).read_bytes())

    convert_file_context = ConvertFileContext(
        word_app=object(),
        ppt_app=object(),
        skip_complex=False,
        convert_doc_to_pdf=fake_doc_to_pdf,
        convert_pdf_to_word=fake_pdf_to_word,
        convert_ppt_to_pdf=fake_ppt_to_pdf,
        convert_pdf_to_ppt=fake_pdf_to_ppt,
        check_pdf_complexity=lambda _src: False,
        copy_file_safe=fake_copy,
        log=lambda message: convert_file_logs.append(str(message)),
    )
    word_adapter_result = process_convert_file_module(
        convert_file_root / "doc.docx",
        convert_file_root,
        convert_file_out,
        "word2pdf",
        convert_file_context,
    )
    pdf_adapter_result = process_convert_file_module(
        convert_file_root / "scan.pdf",
        convert_file_root,
        convert_file_out,
        "pdf2word",
        convert_file_context,
    )
    ppt_adapter_result = process_convert_file_module(
        convert_file_root / "slides.pptx",
        convert_file_root,
        convert_file_out,
        "ppt2pdf",
        convert_file_context,
    )
    pdf_ppt_adapter_result = process_convert_file_module(
        convert_file_root / "scan.pdf",
        convert_file_root,
        convert_file_out,
        "pdf2ppt",
        convert_file_context,
    )
    txt_adapter_result = process_convert_file_module(
        convert_core_root / "notes.txt",
        convert_core_root,
        convert_file_out,
        "txt2word",
        convert_file_context,
    )
    md_pdf_adapter_result = process_convert_file_module(
        convert_core_root / "article.md",
        convert_core_root,
        convert_file_out,
        "md2pdf",
        convert_file_context,
    )
    pdf_md_adapter_result = process_convert_file_module(
        convert_file_root / "scan.pdf",
        convert_file_root,
        convert_file_out,
        "pdf2md",
        convert_file_context,
    )
    complex_context = ConvertFileContext(
        skip_complex=True,
        check_pdf_complexity=lambda _src: True,
        copy_file_safe=fake_copy,
        log=lambda message: convert_file_logs.append(str(message)),
    )
    complex_adapter_result = process_convert_file_module(
        convert_file_root / "scan.pdf",
        convert_file_root,
        convert_file_out / "complex",
        "pdf2word",
        complex_context,
    )
    missing_word_logs = []
    missing_word_result = process_convert_file_module(
        convert_file_root / "doc.docx",
        convert_file_root,
        convert_file_out / "missing_word",
        "word2pdf",
        ConvertFileContext(log=lambda message: missing_word_logs.append(str(message))),
    )
    missing_ppt_logs = []
    missing_ppt_result = process_convert_file_module(
        convert_file_root / "slides.pptx",
        convert_file_root,
        convert_file_out / "missing_ppt",
        "ppt2pdf",
        ConvertFileContext(log=lambda message: missing_ppt_logs.append(str(message))),
    )
    record(
        "convert_file_adapter_module_exports",
        callable(process_convert_file_module)
        and isinstance(ConvertFileContext(), ConvertFileContext)
        and word_adapter_result.get("ok")
        and pdf_adapter_result.get("ok")
        and ppt_adapter_result.get("ok")
        and pdf_ppt_adapter_result.get("ok")
        and txt_adapter_result.get("ok")
        and md_pdf_adapter_result.get("ok")
        and pdf_md_adapter_result.get("ok")
        and complex_adapter_result.get("status") == "skipped_complex"
        and (convert_file_out / "doc.pdf").exists()
        and (convert_file_out / "scan.docx").exists()
        and (convert_file_out / "slides.pdf").exists()
        and (convert_file_out / "scan.pptx").exists()
        and (convert_file_out / "notes.docx").exists()
        and (convert_file_out / "article.pdf").exists()
        and (convert_file_out / "scan.md").exists()
        and (convert_file_out / "complex" / "scan.pdf").exists()
        and ("word", "doc.docx", "doc.pdf", convert_file_context.word_app) in convert_file_calls
        and ("pdf", "scan.pdf", "scan.docx") in convert_file_calls
        and ("ppt", "slides.pptx", "slides.pdf", convert_file_context.ppt_app) in convert_file_calls
        and ("pdfppt", "scan.pdf", "scan.pptx", convert_file_context.ppt_app) in convert_file_calls,
        {
            "word": word_adapter_result,
            "pdf": pdf_adapter_result,
            "ppt": ppt_adapter_result,
            "pdf_ppt": pdf_ppt_adapter_result,
            "txt_word": txt_adapter_result,
            "md_pdf": md_pdf_adapter_result,
            "pdf_md": pdf_md_adapter_result,
            "complex": complex_adapter_result,
            "calls": convert_file_calls,
            "copies": convert_file_copies,
            "logs": convert_file_logs,
        },
    )
    record(
        "convert_file_missing_office_fails_instead_of_copying",
        not missing_word_result.get("ok")
        and not missing_ppt_result.get("ok")
        and missing_word_result.get("status") == "failed"
        and missing_ppt_result.get("status") == "failed"
        and not (convert_file_out / "missing_word" / "doc.docx").exists()
        and not (convert_file_out / "missing_ppt" / "slides.pptx").exists()
        and any("Word COM" in item for item in missing_word_logs)
        and any("PowerPoint COM" in item for item in missing_ppt_logs),
        {
            "word": missing_word_result,
            "ppt": missing_ppt_result,
            "word_logs": missing_word_logs,
            "ppt_logs": missing_ppt_logs,
        },
    )

    pdf_ppt_rich_root = root / "pdf_ppt_editable"
    pdf_ppt_rich_root.mkdir()
    pdf_ppt_src = pdf_ppt_rich_root / "editable.pdf"
    pdf_ppt_out = pdf_ppt_rich_root / "editable.pptx"
    make_pdf(pdf_ppt_src, ["Editable PPT text block"])
    pdf_ppt_status = mod._convert_pdf_to_ppt_safely(None, str(pdf_ppt_src), str(pdf_ppt_out))
    pptx_slide_xml = ""
    if pdf_ppt_out.exists():
        with zipfile.ZipFile(pdf_ppt_out) as archive:
            pptx_slide_xml = "\n".join(
                archive.read(name).decode("utf-8", errors="ignore")
                for name in archive.namelist()
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            )
    record(
        "pdf_to_ppt_editable_text",
        pdf_ppt_status == "SUCCESS"
        and pdf_ppt_out.exists()
        and pdf_ppt_out.stat().st_size > 0
        and "Editable PPT text block" in pptx_slide_xml,
        {"status": pdf_ppt_status, "output": str(pdf_ppt_out), "xml_has_text": "Editable PPT text block" in pptx_slide_xml},
    )

    pdf_md_rich_root = root / "pdf_md_rich"
    pdf_md_rich_root.mkdir()
    pdf_md_image = pdf_md_rich_root / "embedded.png"
    Image.new("RGB", (48, 32), "purple").save(pdf_md_image)
    pdf_md_src = pdf_md_rich_root / "rich.pdf"
    pdf_md_canvas = canvas.Canvas(str(pdf_md_src))
    pdf_md_canvas.drawString(72, 740, "Rich markdown text")
    pdf_md_canvas.drawImage(ImageReader(str(pdf_md_image)), 72, 660, width=96, height=64)
    pdf_md_canvas.line(72, 610, 260, 610)
    pdf_md_canvas.line(72, 580, 260, 580)
    pdf_md_canvas.line(72, 550, 260, 550)
    pdf_md_canvas.line(72, 610, 72, 550)
    pdf_md_canvas.line(160, 610, 160, 550)
    pdf_md_canvas.line(260, 610, 260, 550)
    pdf_md_canvas.drawString(84, 590, "Name")
    pdf_md_canvas.drawString(176, 590, "Value")
    pdf_md_canvas.drawString(84, 560, "Alpha")
    pdf_md_canvas.drawString(176, 560, "42")
    pdf_md_canvas.save()
    pdf_md_out = pdf_md_rich_root / "rich.md"
    pdf_md_status = convert_pdf_to_md_file_module(str(pdf_md_src), str(pdf_md_out))
    pdf_md_text = pdf_md_out.read_text(encoding="utf-8") if pdf_md_out.exists() else ""
    pdf_md_assets = pdf_md_rich_root / "rich_assets"
    pdf_md_asset_files = list(pdf_md_assets.glob("*")) if pdf_md_assets.exists() else []
    record(
        "pdf_to_md_rich_assets",
        pdf_md_status == "SUCCESS"
        and "Rich markdown text" in pdf_md_text
        and "![" in pdf_md_text
        and "rich_assets/" in pdf_md_text.replace("\\", "/")
        and any(path.is_file() and path.stat().st_size > 0 for path in pdf_md_asset_files),
        {
            "status": pdf_md_status,
            "output": str(pdf_md_out),
            "assets": [path.name for path in pdf_md_asset_files],
            "text_preview": pdf_md_text[:500],
        },
    )

    pdf_src = root / "pdf2word_src.pdf"
    make_pdf(pdf_src, ["pdf to word test"])
    word_out = root / "pdf2word_out.docx"
    status = mod.convert_pdf_to_word(str(pdf_src), str(word_out))
    record("pdf_to_word", status == "SUCCESS" and word_out.exists() and word_out.stat().st_size > 0, status)

    import imageio_ffmpeg

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    wav = root / "tone.wav"
    mp4 = root / "tone.mp4"
    subprocess.run([ffmpeg, "-y", "-f", "lavfi", "-i", "sine=frequency=880:duration=1", str(wav)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(
        [ffmpeg, "-y", "-f", "lavfi", "-i", "color=c=black:s=320x240:d=1", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-shortest", "-c:v", "libx264", "-c:a", "aac", str(mp4)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    mp3 = root / "from_video.mp3"
    m4a = root / "from_audio.m4a"
    s1 = mod.convert_audio_format(str(mp4), str(mp3), "mp3", "128k")
    s2 = mod.convert_audio_format(str(wav), str(m4a), "m4a", "128k")
    record("video_to_audio", s1 == "SUCCESS" and mp3.exists() and mp3.stat().st_size > 0, s1)
    record("audio_convert", s2 == "SUCCESS" and m4a.exists() and m4a.stat().st_size > 0, s2)

    audio_module_root = root / "audio_module"
    audio_module_root.mkdir()
    (audio_module_root / "one.wav").write_bytes(b"fake-audio-one")
    (audio_module_root / "two.mp4").write_bytes(b"fake-video-two")
    audio_module_files = collect_audio_files_module(str(audio_module_root), collect_input_files=lambda *_args, **_kwargs: [str(audio_module_root / "one.wav"), str(audio_module_root / "two.mp4")])
    audio_module_output = build_audio_output_path_module(str(audio_module_root / "one.wav"), str(audio_module_root), str(audio_module_root / "out"), "mp3")
    audio_module_statuses = []

    class MiniAudioTracker:
        def __init__(self):
            self.units = 0
            self.current = []

        def set_current_item(self, value, stage):
            self.current.append((value, stage))

        def complete_units(self, value=1, stage=None):
            self.units += int(value or 0)

    def fake_module_convert(src, dst, target_fmt, bitrate="192k"):
        audio_module_statuses.append((Path(src).name, Path(dst).name, target_fmt, bitrate))
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        Path(dst).write_bytes(b"converted")
        return "SUCCESS"

    def fake_module_copy(src, dst):
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        Path(dst).write_bytes(Path(src).read_bytes())
        return dst

    def set_audio_module_counts(result, *, processed=0, success=0, failed=0, skipped=0):
        result.update(
            {
                "processed_count": processed,
                "success_count": success,
                "failed_count": failed,
                "skipped_count": skipped,
            }
        )

    audio_module_result = run_audio_task_core_module(
        object(),
        str(audio_module_root),
        normalized_input=str(audio_module_root),
        input_root=str(audio_module_root),
        output_folder=str(audio_module_root / "out"),
        audio_files=list(audio_module_files),
        result={"outputs": [], "failed_items": []},
        tracker=MiniAudioTracker(),
        is_parallel_enabled=lambda *_args, **_kwargs: True,
        get_parallel_worker_count=lambda total: 2,
        convert_audio_format=fake_module_convert,
        copy_file_safe=fake_module_copy,
        set_task_result_counts=set_audio_module_counts,
        set_task_result_finished=lambda result, status, **kwargs: result.update({"status": status, **kwargs}) or result,
        set_task_result_output_root=lambda result, value: result.update({"output_root": value}),
        add_task_result_output=lambda result, value: result.setdefault("outputs", []).append(str(value)),
        write_failed_report=lambda *_args, **_kwargs: "",
        log=lambda *_args, **_kwargs: None,
        progress_bar=type("Bar", (), {"set": lambda self, value: None})(),
        stop_requested=lambda: False,
        executor_factory=mod.concurrent.futures.ThreadPoolExecutor,
        get_audio_task_args=lambda _app: ("convert", "mp3", "128k", False),
        callbacks=AudioTaskCallbacksModule(log=lambda *_args, **_kwargs: None, stop_requested=lambda: False),
    )
    record(
        "audio_task_module_exports",
        len(audio_module_files) == 2
        and audio_module_output[1].endswith("one.mp3")
        and audio_module_result.get("status") == "success"
        and audio_module_result.get("processed_count") == 2
        and audio_module_result.get("success_count") == 2
        and len(audio_module_statuses) >= 1,
        {
            "files": audio_module_files,
            "output": audio_module_output,
            "result": audio_module_result,
            "converted": audio_module_statuses,
        },
    )

    transcript_paths = build_transcript_output_paths_module(
        str(audio_module_root / "one.wav"),
        str(audio_module_root),
        str(audio_module_root / "transcripts"),
        "txt+srt",
    )

    class FakeSegment:
        def __init__(self, start, end, text):
            self.start = start
            self.end = end
            self.text = text

    class FakeInfo:
        language = "zh"

    class FakeWhisperModel:
        def transcribe(self, *_args, **_kwargs):
            return [FakeSegment(0.0, 1.25, "风兮语音转文字测试")], FakeInfo()

    transcript_progress = []
    transcript_result = transcribe_media_file_module(
        str(audio_module_root / "one.wav"),
        str(audio_module_root),
        str(audio_module_root / "transcripts"),
        model_name="base",
        language="中文",
        output_format="txt+srt",
        model_factory=lambda _model_name: FakeWhisperModel(),
        progress_callback=transcript_progress.append,
    )
    transcript_txt = Path(transcript_paths[0])
    transcript_srt = Path(transcript_paths[1])
    record(
        "speech_to_text_core_outputs",
        transcript_result.get("status") == "success"
        and transcript_txt.exists()
        and transcript_srt.exists()
        and "风兮语音转文字测试" in transcript_txt.read_text(encoding="utf-8")
        and "00:00:00,000 --> 00:00:01,250" in transcript_srt.read_text(encoding="utf-8"),
        {"result": transcript_result, "paths": transcript_paths},
    )
    record(
        "speech_to_text_realtime_progress_callback",
        any(item.get("type") == "segment" and item.get("segment", {}).get("text") == "风兮语音转文字测试" for item in transcript_progress)
        and transcript_progress[-1].get("type") == "done",
        transcript_progress,
    )

    transcribe_module_calls = []
    transcribe_module_progress = []

    def fake_module_transcribe(src, input_root, output_folder, **kwargs):
        transcribe_module_calls.append((Path(src).name, kwargs))
        outputs = build_transcript_output_paths_module(src, input_root, output_folder, kwargs.get("output_format", "txt"))
        progress_callback = kwargs.get("progress_callback")
        if callable(progress_callback):
            progress_callback(
                {
                    "type": "segment",
                    "src": src,
                    "index": 1,
                    "segment": {"start": 0.0, "end": 1.0, "text": "module live transcript"},
                }
            )
        for output in outputs:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            Path(output).write_text("module transcript\n", encoding="utf-8")
        return {"src": src, "outputs": outputs, "output": outputs[0], "status": "success", "ok": True, "message": "SUCCESS"}

    audio_transcribe_result = run_audio_task_core_module(
        object(),
        str(audio_module_root),
        normalized_input=str(audio_module_root),
        input_root=str(audio_module_root),
        output_folder=str(audio_module_root / "transcribe_task"),
        audio_files=[str(audio_module_root / "one.wav")],
        result={"outputs": [], "failed_items": []},
        tracker=MiniAudioTracker(),
        is_parallel_enabled=lambda *_args, **_kwargs: False,
        get_parallel_worker_count=lambda total: 1,
        convert_audio_format=fake_module_convert,
        copy_file_safe=fake_module_copy,
        set_task_result_counts=set_audio_module_counts,
        set_task_result_finished=lambda result, status, **kwargs: result.update({"status": status, **kwargs}) or result,
        set_task_result_output_root=lambda result, value: result.update({"output_root": value}),
        add_task_result_output=lambda result, value: result.setdefault("outputs", []).append(str(value)),
        write_failed_report=lambda *_args, **_kwargs: "",
        log=lambda *_args, **_kwargs: None,
        progress_bar=type("Bar", (), {"set": lambda self, value: None})(),
        stop_requested=lambda: False,
        executor_factory=mod.concurrent.futures.ThreadPoolExecutor,
        get_audio_task_args=lambda _app: ("transcribe", "txt", "192k", False),
        get_audio_transcribe_args=lambda _app: {"model_name": "base", "language": "中文", "output_format": "txt"},
        transcribe_media_file=fake_module_transcribe,
        callbacks=AudioTaskCallbacksModule(
            log=lambda *_args, **_kwargs: None,
            stop_requested=lambda: False,
            on_transcript_progress=lambda src, payload: transcribe_module_progress.append((Path(src).name, payload)),
        ),
    )
    record(
        "audio_transcribe_task_module",
        audio_transcribe_result.get("status") == "success"
        and audio_transcribe_result.get("success_count") == 1
        and transcribe_module_calls
        and Path(audio_transcribe_result["outputs"][0]).exists(),
        {"result": audio_transcribe_result, "calls": transcribe_module_calls},
    )
    record(
        "audio_transcribe_task_realtime_progress",
        transcribe_module_progress
        and transcribe_module_progress[0][0] == "one.wav"
        and transcribe_module_progress[0][1].get("segment", {}).get("text") == "module live transcript",
        transcribe_module_progress,
    )

    audio_resume_out = audio_module_root / "transcribe_resume"
    audio_resume_txt = audio_resume_out / "one.txt"
    audio_resume_txt.parent.mkdir(parents=True)
    audio_resume_txt.write_text("existing transcript\n", encoding="utf-8")
    audio_resume_result = run_audio_task_core_module(
        object(),
        str(audio_module_root),
        normalized_input=str(audio_module_root),
        input_root=str(audio_module_root),
        output_folder=str(audio_resume_out),
        audio_files=[str(audio_module_root / "one.wav")],
        result={"outputs": [], "failed_items": []},
        tracker=MiniAudioTracker(),
        is_parallel_enabled=lambda *_args, **_kwargs: False,
        get_parallel_worker_count=lambda total: 1,
        convert_audio_format=fake_module_convert,
        copy_file_safe=fake_module_copy,
        set_task_result_counts=set_audio_module_counts,
        set_task_result_finished=lambda result, status, **kwargs: result.update({"status": status, **kwargs}) or result,
        set_task_result_output_root=lambda result, value: result.update({"output_root": value}),
        add_task_result_output=lambda result, value: result.setdefault("outputs", []).append(str(value)),
        write_failed_report=lambda *_args, **_kwargs: "",
        log=lambda *_args, **_kwargs: None,
        progress_bar=type("Bar", (), {"set": lambda self, value: None})(),
        stop_requested=lambda: False,
        executor_factory=mod.concurrent.futures.ThreadPoolExecutor,
        get_audio_task_args=lambda _app: ("transcribe", "txt", "192k", False),
        get_audio_transcribe_args=lambda _app: {"model_name": "base", "language": "中文", "output_format": "txt"},
        transcribe_media_file=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("audio transcribe should resume")),
        callbacks=AudioTaskCallbacksModule(log=lambda *_args, **_kwargs: None, stop_requested=lambda: False),
    )
    record(
        "audio_transcribe_resume_skips_existing_output",
        audio_resume_result.get("status") == "success"
        and audio_resume_result.get("success_count") == 1
        and audio_resume_result.get("skipped_count") == 1
        and audio_resume_result.get("outputs") == [str(audio_resume_txt)],
        audio_resume_result,
    )

    audio_parallel_root = root / "audio_parallel"
    audio_parallel_root.mkdir()
    (audio_parallel_root / "a.wav").write_bytes(b"fake-audio-a")
    (audio_parallel_root / "b.wav").write_bytes(b"fake-audio-b")
    app.current_task = "audio"
    mod._ensure_lazy_tab_initialized(app, "audio")
    app.audio_mode_var.set("convert")
    app.audio_target_fmt.set("mp3")
    app.audio_bitrate.set("128k")
    app.audio_delete_var.set(False)
    app.enable_multithread.set(True)
    audio_executor_workers = []
    converted_audio = []
    original_executor = mod.concurrent.futures.ThreadPoolExecutor
    original_audio_convert = mod.convert_audio_format

    class RecordingAudioExecutor(original_executor):
        def __init__(self, *args, **kwargs):
            audio_executor_workers.append(kwargs.get("max_workers") if "max_workers" in kwargs else (args[0] if args else None))
            super().__init__(*args, **kwargs)

    def fake_audio_convert(src, dst, target_fmt, bitrate="192k"):
        converted_audio.append((Path(src).name, Path(dst).name, target_fmt, bitrate))
        Path(dst).write_bytes(b"converted")
        return "SUCCESS"

    mod.concurrent.futures.ThreadPoolExecutor = RecordingAudioExecutor
    mod.convert_audio_format = fake_audio_convert
    try:
        app.run_process(str(audio_parallel_root), "audio")
        audio_parallel_result = dict(getattr(app, "_fx_last_task_result", {}) or {})
    finally:
        mod.convert_audio_format = original_audio_convert
        mod.concurrent.futures.ThreadPoolExecutor = original_executor
        app.enable_multithread.set(False)
    audio_parallel_out = audio_parallel_root / mod.RESULT_FOLDER_NAME
    record(
        "audio_parallel_executor",
        bool(audio_executor_workers)
        and max(value or 0 for value in audio_executor_workers) > 1
        and (audio_parallel_out / "a.mp3").exists()
        and (audio_parallel_out / "b.mp3").exists()
        and audio_parallel_result.get("status") == "success"
        and audio_parallel_result.get("processed_count") == 2
        and audio_parallel_result.get("success_count") == 2,
        {
            "workers": audio_executor_workers,
            "converted": converted_audio,
            "result": audio_parallel_result,
        },
    )

    audio_transcribe_root = root / "audio_transcribe_workflow"
    audio_transcribe_root.mkdir()
    (audio_transcribe_root / "speech.wav").write_bytes(b"fake-speech")
    app.current_task = "audio"
    mod._ensure_lazy_tab_initialized(app, "audio")
    mod._tighten_layout(app, "audio")
    try:
        audio_tab_name = next(
            name
            for name, frame in (getattr(app.main_panel, "_tab_dict", {}) or {}).items()
            if frame is app.tab_audio
        )
        app.main_panel.set(audio_tab_name)
        app.update_idletasks()
        mod._tighten_layout(app, "audio")
    except Exception:
        pass
    audio_model_hint = ""
    try:
        audio_model_hint = app._fx_audio_transcribe_model_hint.cget("text")
    except Exception:
        audio_model_hint = ""
    record(
        "audio_transcribe_model_hint",
        "base 为默认推荐" in audio_model_hint
        and "tiny 最快" in audio_model_hint
        and "medium 准确率最高" in audio_model_hint,
        audio_model_hint,
    )
    audio_preview_height = 999
    audio_preview_before_hint = False
    audio_card_top_pady = 999
    audio_title_top_pady = 999
    audio_settings_top_pady = 999
    audio_tab_row = 999
    audio_tab_top_pady = 999
    main_tab_button_manager = "unknown"
    try:
        preview_frame = app._fx_audio_transcribe_preview_frame
        preview_box = app._fx_audio_transcribe_preview_box
        hint_widget = app._fx_audio_transcribe_model_hint
        audio_preview_height = int(preview_box.cget("height"))
        audio_siblings = list(preview_frame.master.pack_slaves())
        audio_preview_before_hint = audio_siblings.index(preview_frame) < audio_siblings.index(hint_widget)
        audio_settings_frame = preview_frame.master
        audio_card = audio_settings_frame.master
        audio_title = audio_card.winfo_children()[0]
        card_pady = audio_card.pack_info().get("pady", 999)
        title_pady = audio_title.pack_info().get("pady", 999)
        settings_pady = audio_settings_frame.pack_info().get("pady", 999)
        audio_card_top_pady = int(card_pady[0] if isinstance(card_pady, tuple) else card_pady)
        audio_title_top_pady = int(title_pady[0] if isinstance(title_pady, tuple) else title_pady)
        audio_settings_top_pady = int(settings_pady[0] if isinstance(settings_pady, tuple) else settings_pady)
        audio_tab_grid = app.tab_audio.grid_info()
        audio_tab_row = int(audio_tab_grid.get("row", 999))
        tab_pady = audio_tab_grid.get("pady", 999)
        audio_tab_top_pady = int(tab_pady[0] if isinstance(tab_pady, tuple) else tab_pady)
        segmented_button = getattr(app.main_panel, "_segmented_button", None)
        main_tab_button_manager = segmented_button.winfo_manager() if segmented_button is not None else ""
    except Exception:
        audio_preview_height = 999
        audio_preview_before_hint = False
        audio_card_top_pady = 999
        audio_title_top_pady = 999
        audio_settings_top_pady = 999
        audio_tab_row = 999
        audio_tab_top_pady = 999
        main_tab_button_manager = "error"
    record(
        "audio_transcribe_preview_roomy_layout",
        145 <= audio_preview_height <= 180
        and audio_preview_before_hint
        and audio_card_top_pady <= 2
        and audio_title_top_pady <= 2
        and audio_settings_top_pady <= 2
        and audio_tab_row == 0
        and audio_tab_top_pady <= 2
        and main_tab_button_manager != "grid",
        {
            "height": audio_preview_height,
            "preview_before_hint": audio_preview_before_hint,
            "card_top_pady": audio_card_top_pady,
            "title_top_pady": audio_title_top_pady,
            "settings_top_pady": audio_settings_top_pady,
            "tab_row": audio_tab_row,
            "tab_top_pady": audio_tab_top_pady,
            "tab_button_manager": main_tab_button_manager,
        },
    )
    app.audio_mode_var.set("transcribe")
    app.audio_transcribe_model.set("tiny")
    app.audio_transcribe_language.set("中文")
    app.audio_transcribe_format.set("txt+srt")
    app.audio_delete_var.set(False)
    transcribe_workflow_calls = []
    original_speech_transcribe = mod._speech_transcribe_media_file

    def fake_workflow_transcribe(src, input_root, output_folder, **kwargs):
        transcribe_workflow_calls.append((Path(src).name, kwargs))
        outputs = build_transcript_output_paths_module(src, input_root, output_folder, kwargs.get("output_format", "txt"))
        progress_callback = kwargs.get("progress_callback")
        if callable(progress_callback):
            progress_callback(
                {
                    "type": "stage",
                    "stage": "transcribe",
                    "src": src,
                }
            )
            progress_callback(
                {
                    "type": "segment",
                    "src": src,
                    "index": 1,
                    "segment": {"start": 2.0, "end": 3.5, "text": "workflow live preview"},
                }
            )
        for output in outputs:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            Path(output).write_text("workflow transcript\n", encoding="utf-8")
        return {"src": src, "outputs": outputs, "output": outputs[0], "status": "success", "ok": True, "message": "SUCCESS"}

    mod._speech_transcribe_media_file = fake_workflow_transcribe
    try:
        app.run_process(str(audio_transcribe_root), "audio")
        audio_transcribe_workflow_result = dict(getattr(app, "_fx_last_task_result", {}) or {})
    finally:
        mod._speech_transcribe_media_file = original_speech_transcribe
    try:
        app.update()
    except Exception:
        pass
    try:
        audio_preview_text = app._fx_audio_transcribe_preview_box.get("1.0", "end")
    except Exception:
        audio_preview_text = ""
    audio_transcribe_out = audio_transcribe_root / mod.RESULT_FOLDER_NAME
    record(
        "audio_transcribe_workflow",
        audio_transcribe_workflow_result.get("status") == "success"
        and (audio_transcribe_out / "speech.txt").exists()
        and (audio_transcribe_out / "speech.srt").exists()
        and transcribe_workflow_calls
        and transcribe_workflow_calls[0][1].get("model_name") == "tiny",
        {"result": audio_transcribe_workflow_result, "calls": transcribe_workflow_calls},
    )
    record(
        "audio_transcribe_realtime_preview_ui",
        "workflow live preview" in audio_preview_text
        and "00:00:02.000 -> 00:00:03.500" in audio_preview_text,
        audio_preview_text,
    )

    audio_last_settings = mod._save_last_settings_category(app, "audio")
    app.audio_mode_var.set("video2mp3")
    app.audio_transcribe_model.set("base")
    app.audio_transcribe_language.set("自动识别")
    app.audio_transcribe_format.set("txt")
    apply_audio_ok, _apply_audio_message = mod._restore_last_settings_category(app, "audio")
    record(
        "last_settings_audio_transcribe_save_restore",
        apply_audio_ok
        and isinstance(audio_last_settings, dict)
        and app.audio_mode_var.get() == "transcribe"
        and app.audio_transcribe_model.get() == "tiny"
        and app.audio_transcribe_language.get() == "中文"
        and app.audio_transcribe_format.get() == "txt+srt",
        {
            "saved": audio_last_settings,
            "mode": app.audio_mode_var.get(),
            "model": app.audio_transcribe_model.get(),
            "language": app.audio_transcribe_language.get(),
            "format": app.audio_transcribe_format.get(),
        },
    )

    mod._ensure_lazy_tab_initialized(app, "zip")
    mod._refresh_visible_tab_layout(app, "zip")
    record(
        "zip_depth_control_visible",
        getattr(app, "zip_min_depth_var", None) is not None
        and getattr(app, "zip_min_depth_entry", None) is not None
        and getattr(app, "zip_max_depth_var", None) is not None
        and getattr(app, "zip_max_depth_entry", None) is not None
        and app.zip_min_depth_entry is not app.zip_max_depth_entry,
        {
            "start": getattr(app, "zip_min_depth_entry", None),
            "end": getattr(app, "zip_max_depth_entry", None),
        },
    )
    try:
        zip_tab = getattr(app, mod.TAB_LAYOUT_ATTRS["zip"])
        zip_card = list(zip_tab.winfo_children())[0]
        zip_children = list(zip_card.winfo_children())
        zip_mode_frame = zip_children[1]
        zip_depth_frame = getattr(app, "_fx_zip_depth_frame", None)
        zip_depth_grid = zip_depth_frame.grid_info() if zip_depth_frame is not None else {}
        zip_mode_grid = zip_mode_frame.grid_info()
    except Exception as exc:
        zip_depth_grid = {"error": str(exc)}
        zip_mode_grid = {}
    record(
        "zip_depth_control_on_right_side",
        zip_depth_grid.get("column") == 1
        and zip_mode_grid.get("column") == 0
        and getattr(app, "_fx_zip_depth_frame", None) is not None
        and getattr(app, "_fx_zip_depth_frame").winfo_manager() == "grid",
        {"mode_grid": zip_mode_grid, "depth_grid": zip_depth_grid},
    )
    try:
        zip_min_grid = app.zip_min_depth_entry.grid_info()
        zip_max_grid = app.zip_max_depth_entry.grid_info()
        zip_dash_visible = any(
            isinstance(child, mod.customtkinter.CTkLabel)
            and str(child.cget("text") or "") == "-"
            and child.grid_info().get("column") == 2
            for child in getattr(app, "_fx_zip_depth_frame").winfo_children()
        )
    except Exception as exc:
        zip_min_grid = {"error": str(exc)}
        zip_max_grid = {}
        zip_dash_visible = False
    record(
        "zip_depth_range_uses_two_inputs",
        zip_min_grid.get("column") == 1
        and zip_max_grid.get("column") == 3
        and zip_dash_visible
        and mod._get_zip_max_depth(app) == "",
        {"start_grid": zip_min_grid, "end_grid": zip_max_grid, "dash": zip_dash_visible},
    )
    try:
        zip_policy_combo = getattr(app, "zip_archive_policy_combo", None)
        zip_policy_values = list(zip_policy_combo.cget("values") or []) if zip_policy_combo is not None else []
    except Exception:
        zip_policy_combo = None
        zip_policy_values = []
    record(
        "zip_archive_policy_control_visible",
        getattr(app, "zip_archive_policy_var", None) is not None
        and zip_policy_combo is not None
        and zip_policy_combo.winfo_manager() == "grid"
        and "复用已有压缩包（断点续跑）" in zip_policy_values
        and "删除旧包并重新压缩" in zip_policy_values
        and mod._get_zip_archive_policy(app) == "reuse_existing",
        {"values": zip_policy_values, "policy": mod._get_zip_archive_policy(app)},
    )

    zip_preview_root = root / "zip_preview_subfolders_only"
    (zip_preview_root / "child").mkdir(parents=True)
    app.current_task = "zip"
    app.zip_mode_var.set("smart_recursive")
    app.zip_min_depth_var.set("")
    app.zip_max_depth_var.set("")
    zip_preview = mod._build_start_preview(app, str(zip_preview_root), "zip")
    record(
        "zip_start_preview_uses_zip_plan",
        zip_preview.get("effective_count", 0) > 0,
        zip_preview,
    )

    for mode in ["total", "recursive", "smart_recursive"]:
        zroot = root / f"zip_{mode}"
        (zroot / "sub").mkdir(parents=True)
        (zroot / "a.txt").write_text("a", encoding="utf-8")
        (zroot / "sub" / "b.txt").write_text("b", encoding="utf-8")
        app.zip_mode_var.set(mode)
        app.current_task = "zip"
        app.run_process(str(zroot), "zip")
        expected = zroot / f"{zroot.name}_Backup.zip" if mode == "total" else zroot / f"{zroot.name}.zip"
        ok = wait_for(lambda: expected.exists())
        record(f"zip_{mode}", ok, expected)

    zip_core_root = root / "zip_core_semantics"
    (zip_core_root / "sub").mkdir(parents=True)
    (zip_core_root / "a.txt").write_text("a", encoding="utf-8")
    (zip_core_root / "sub" / "b.txt").write_text("b", encoding="utf-8")
    zip_core_plan_counts = {
        mode: len(plan_zip_archives_module(zip_core_root, mode))
        for mode in ("total", "recursive", "smart_recursive")
    }
    zip_core_run = run_zip_task_module(zip_core_root, "smart_recursive")
    zip_core_output = zip_core_root / f"{zip_core_root.name}.zip"
    record(
        "zip_core_module_semantics",
        normalize_zip_mode_module("bad") == "total"
        and zip_core_plan_counts == {"total": 1, "recursive": 2, "smart_recursive": 1}
        and estimate_zip_progress_units_module(zip_core_root, "smart_recursive") == 1
        and zip_core_run.get("status") == "success"
        and zip_core_output.exists(),
        {
            "counts": zip_core_plan_counts,
            "result": zip_core_run,
        },
    )
    zip_resume_result = run_zip_task_module(zip_core_root, "smart_recursive")
    record(
        "zip_resume_skips_existing_archive",
        zip_resume_result.get("status") == "success"
        and zip_resume_result.get("success_count") == 1
        and zip_resume_result.get("skipped_count") == 1
        and zip_resume_result.get("outputs") == [str(zip_core_output.resolve())],
        zip_resume_result,
    )
    with zipfile.ZipFile(zip_core_output, "w") as archive:
        archive.writestr("old.txt", "old archive")
    zip_rebuild_result = run_zip_task_module(zip_core_root, "smart_recursive", archive_policy="rebuild_existing")
    try:
        with zipfile.ZipFile(zip_core_output) as archive:
            rebuilt_names = set(archive.namelist())
    except Exception:
        rebuilt_names = set()
    record(
        "zip_rebuild_existing_archive_policy",
        normalize_zip_archive_policy_module("replace") == "rebuild_existing"
        and zip_rebuild_result.get("status") == "success"
        and zip_rebuild_result.get("archive_policy") == "rebuild_existing"
        and zip_rebuild_result.get("skipped_count") == 0
        and "old.txt" not in rebuilt_names
        and "a.txt" in rebuilt_names,
        {"result": zip_rebuild_result, "names": sorted(rebuilt_names)},
    )

    zip_smart_mix_root = root / "zip_smart_mix_semantics"
    (zip_smart_mix_root / "child_a").mkdir(parents=True)
    (zip_smart_mix_root / "child_b").mkdir()
    (zip_smart_mix_root / "child_a" / "a.txt").write_text("a", encoding="utf-8")
    (zip_smart_mix_root / "child_b" / "nested").mkdir()
    (zip_smart_mix_root / "child_b" / "nested" / "deep.txt").write_text("deep", encoding="utf-8")
    (zip_smart_mix_root / "child_b" / "nested.zip").write_text("old archive", encoding="utf-8")
    zip_smart_mix_jobs = plan_zip_archives_module(zip_smart_mix_root, "smart_recursive")
    zip_smart_mix_outputs = {Path(item["output"]).relative_to(zip_smart_mix_root).as_posix() for item in zip_smart_mix_jobs}
    record(
        "zip_smart_new_layer_semantics",
        zip_smart_mix_outputs
        == {
            "zip_smart_mix_semantics.zip",
            "child_a.zip",
            "child_b.zip",
            "child_b/nested.zip",
        },
        {"outputs": sorted(zip_smart_mix_outputs), "jobs": zip_smart_mix_jobs},
    )

    zip_depth_root = root / "zip_depth_limit"
    (zip_depth_root / "level2" / "level3").mkdir(parents=True)
    (zip_depth_root / "level2" / "level3" / "deep.txt").write_text("deep", encoding="utf-8")
    recursive_depth_outputs = {
        Path(item["output"]).relative_to(zip_depth_root).as_posix()
        for item in plan_zip_archives_module(zip_depth_root, "recursive", max_depth=2)
    }
    smart_depth_outputs = {
        Path(item["output"]).relative_to(zip_depth_root).as_posix()
        for item in plan_zip_archives_module(zip_depth_root, "smart_recursive", max_depth=2)
    }
    recursive_range_outputs = {
        Path(item["output"]).relative_to(zip_depth_root).as_posix()
        for item in plan_zip_archives_module(zip_depth_root, "recursive", max_depth="2-3")
    }
    smart_range_outputs = {
        Path(item["output"]).relative_to(zip_depth_root).as_posix()
        for item in plan_zip_archives_module(zip_depth_root, "smart_recursive", max_depth="2-3")
    }
    record(
        "zip_depth_range_recursive_and_smart",
        normalize_zip_max_depth_module("2") == 2
        and normalize_zip_depth_range_module("2-3") == (2, 3)
        and normalize_zip_depth_range_module("4") == (1, 4)
        and normalize_zip_max_depth_module("") is None
        and recursive_depth_outputs == {"zip_depth_limit.zip", "level2.zip"}
        and smart_depth_outputs == {"zip_depth_limit.zip", "level2.zip"}
        and recursive_range_outputs == {"level2.zip", "level2/level3.zip"}
        and smart_range_outputs == {"level2.zip", "level2/level3.zip"}
        and estimate_zip_progress_units_module(zip_depth_root, "smart_recursive", max_depth=2) == 2,
        {
            "recursive": sorted(recursive_depth_outputs),
            "smart": sorted(smart_depth_outputs),
            "recursive_range": sorted(recursive_range_outputs),
            "smart_range": sorted(smart_range_outputs),
        },
    )

    zip_smart_boundary_before_root = root / "zip_smart_boundary_before_range"
    (zip_smart_boundary_before_root / "Archive1" / "child_pdf").mkdir(parents=True)
    (zip_smart_boundary_before_root / "Archive1" / "doc.pdf").write_text("pdf", encoding="utf-8")
    (zip_smart_boundary_before_root / "Archive1" / "child_pdf" / "deep.pdf").write_text("deep", encoding="utf-8")
    smart_boundary_before_outputs = {
        Path(item["output"]).relative_to(zip_smart_boundary_before_root).as_posix()
        for item in plan_zip_archives_module(zip_smart_boundary_before_root, "smart_recursive", max_depth="3-4")
    }

    zip_smart_boundary_inside_root = root / "zip_smart_boundary_inside_range"
    (zip_smart_boundary_inside_root / "level2" / "Archive1" / "child_pdf").mkdir(parents=True)
    (zip_smart_boundary_inside_root / "level2" / "Archive1" / "doc.pdf").write_text("pdf", encoding="utf-8")
    (zip_smart_boundary_inside_root / "level2" / "Archive1" / "child_pdf" / "deep.pdf").write_text("deep", encoding="utf-8")
    smart_boundary_inside_outputs = {
        Path(item["output"]).relative_to(zip_smart_boundary_inside_root).as_posix()
        for item in plan_zip_archives_module(zip_smart_boundary_inside_root, "smart_recursive", max_depth="3-4")
    }
    record(
        "zip_smart_depth_range_stops_at_mixed_boundary",
        smart_boundary_before_outputs == set()
        and smart_boundary_inside_outputs == {"level2/Archive1.zip"},
        {
            "before_range": sorted(smart_boundary_before_outputs),
            "inside_range": sorted(smart_boundary_inside_outputs),
        },
    )

    zip_ds_store_root = root / "zip_smart_ignores_ds_store"
    (zip_ds_store_root / "child_a").mkdir(parents=True)
    (zip_ds_store_root / "child_b").mkdir()
    (zip_ds_store_root / ".DS_Store").write_bytes(b"macos metadata")
    (zip_ds_store_root / "child_a" / "a.pdf").write_text("a", encoding="utf-8")
    (zip_ds_store_root / "child_b" / "b.pdf").write_text("b", encoding="utf-8")
    zip_ds_store_jobs = plan_zip_archives_module(zip_ds_store_root, "smart_recursive")
    zip_ds_store_outputs = {
        Path(item["output"]).relative_to(zip_ds_store_root).as_posix()
        for item in zip_ds_store_jobs
    }
    zip_ds_store_result = run_zip_task_module(zip_ds_store_root, "smart_recursive")
    zip_ds_store_root_archive = zip_ds_store_root / f"{zip_ds_store_root.name}.zip"
    try:
        with zipfile.ZipFile(zip_ds_store_root_archive) as archive:
            zip_ds_store_entries = set(archive.namelist())
    except Exception:
        zip_ds_store_entries = set()
    record(
        "zip_smart_ignores_ds_store_artifacts",
        zip_ds_store_outputs
        == {
            f"{zip_ds_store_root.name}.zip",
            "child_a.zip",
            "child_b.zip",
        }
        and zip_ds_store_result.get("status") == "success"
        and (zip_ds_store_root / "child_a.zip").exists()
        and (zip_ds_store_root / "child_b.zip").exists()
        and ".DS_Store" not in zip_ds_store_entries
        and plan_zip_archives_module(zip_ds_store_root / ".DS_Store", "smart_recursive") == [],
        {
            "outputs": sorted(zip_ds_store_outputs),
            "result": zip_ds_store_result,
            "entries": sorted(zip_ds_store_entries),
        },
    )

    app.zip_mode_var.set("smart_recursive")
    app.zip_min_depth_var.set("2")
    app.zip_max_depth_var.set("4")
    app.zip_archive_policy_var.set("删除旧包并重新压缩")
    zip_last = mod._save_last_settings_category(app, "zip")
    app.zip_mode_var.set("total")
    app.zip_min_depth_var.set("")
    app.zip_max_depth_var.set("")
    app.zip_archive_policy_var.set("复用已有压缩包（断点续跑）")
    zip_apply_ok, _zip_apply_message = mod._restore_last_settings_category(app, "zip")
    record(
        "last_settings_zip_save_restore",
        zip_apply_ok
        and isinstance(zip_last, dict)
        and app.zip_mode_var.get() == "smart_recursive"
        and app.zip_min_depth_var.get() == "2"
        and app.zip_max_depth_var.get() == "4"
        and mod._get_zip_max_depth(app) == "2-4"
        and mod._get_zip_archive_policy(app) == "rebuild_existing",
        {
            "saved": zip_last,
            "mode": app.zip_mode_var.get(),
            "start": app.zip_min_depth_var.get(),
            "end": app.zip_max_depth_var.get(),
            "depth": mod._get_zip_max_depth(app),
            "archive_policy": mod._get_zip_archive_policy(app),
        },
    )

    zip_smart_notice_messages = mod._build_zip_plan_messages(zip_smart_mix_root, "smart_recursive", max_depth="2-4", archive_policy="rebuild_existing")
    record(
        "zip_smart_plan_notice",
        any("2-4" in item for item in zip_smart_notice_messages)
        and any("智能混合" in item for item in zip_smart_notice_messages)
        and any("本次预计生成" in item for item in zip_smart_notice_messages)
        and any("重新压缩" in item for item in zip_smart_notice_messages)
        and any("child_a.zip" in item for item in zip_smart_notice_messages),
        zip_smart_notice_messages,
    )

    single_zip_src = root / "single_zip_input.txt"
    single_zip_src.write_text("zip me", encoding="utf-8")
    app.zip_mode_var.set("total")
    app.current_task = "zip"
    app.run_process(str(single_zip_src), "zip")
    single_zip_out = root / "single_zip_input.txt_Backup.zip"
    record("single_file_input_zip_total", wait_for(lambda: single_zip_out.exists()), single_zip_out)

    fd = root / "file_dedup"
    fd.mkdir()
    (fd / "a.txt").write_text("same", encoding="utf-8")
    (fd / "b.txt").write_text("same", encoding="utf-8")
    app.file_mode_var.set("dedup")
    app.current_task = "file"
    task_dedup_calls = []
    original_task_dedup = mod._run_file_dedup_task_core

    def traced_task_dedup(*args, **kwargs):
        task_dedup_calls.append(True)
        return original_task_dedup(*args, **kwargs)

    mod._run_file_dedup_task_core = traced_task_dedup
    try:
        app.run_process(str(fd), "file")
    finally:
        mod._run_file_dedup_task_core = original_task_dedup
    wait_for(lambda: len(list(fd.glob("*.txt"))) == 1)
    dedup_task_result = mod._get_last_task_result(app)
    record(
        "file_dedup",
        len(list(fd.glob("*.txt"))) == 1
        and bool(task_dedup_calls)
        and isinstance(dedup_task_result, dict)
        and dedup_task_result.get("status") == "success"
        and dedup_task_result.get("processed_count") == 2,
        {
            "remaining": [p.name for p in fd.glob("*.txt")],
            "task_calls": len(task_dedup_calls),
            "task_result": dedup_task_result,
        },
    )

    dedup_core_root = root / "file_dedup_core"
    dedup_core_root.mkdir()
    (dedup_core_root / "x.txt").write_text("same", encoding="utf-8")
    (dedup_core_root / "y.txt").write_text("same", encoding="utf-8")
    (dedup_core_root / "z.txt").write_text("other", encoding="utf-8")
    deleted_by_core = []
    dedup_core_result = run_file_dedup_task_module(
        [dedup_core_root / "x.txt", dedup_core_root / "y.txt", dedup_core_root / "z.txt"],
        delete_file=lambda path: (deleted_by_core.append(Path(path).name), Path(path).unlink()),
        log=lambda *_args, **_kwargs: None,
        stop_requested=lambda: False,
        progress=lambda *_args, **_kwargs: None,
    )
    record(
        "file_dedup_core_module_exports",
        dedup_core_result.get("status") == "success"
        and dedup_core_result.get("kept_count") == 2
        and dedup_core_result.get("removed_count") == 1
        and sorted(p.name for p in dedup_core_root.glob("*.txt")) == ["x.txt", "z.txt"]
        and deleted_by_core == ["y.txt"],
        {
            "result": dedup_core_result,
            "deleted": deleted_by_core,
            "remaining": sorted(p.name for p in dedup_core_root.glob("*.txt")),
        },
    )

    img_root = root / "imgs2pdf"
    img_root.mkdir()
    Image.new("RGB", (60, 60), "red").save(img_root / "1.png")
    Image.new("RGB", (60, 60), "blue").save(img_root / "2.jpg")
    app.current_task = "convert"
    app.cv_mode.set("imgs2pdf")
    convert_preview = mod._build_start_preview(app, str(img_root), "convert")
    record(
        "convert_preview_uses_core_rules",
        convert_preview["effective_count"] == 2
        and convert_preview["mode_detail"] == "多图合并 ➔ PDF电子书",
        convert_preview,
    )
    convert_task_calls = []
    original_convert_imgs_task = mod.run_convert_imgs_to_pdf_task_core

    def traced_convert_imgs_task(*args, **kwargs):
        convert_task_calls.append(True)
        return original_convert_imgs_task(*args, **kwargs)

    mod.run_convert_imgs_to_pdf_task_core = traced_convert_imgs_task
    try:
        app.run_process(str(img_root), "convert")
    finally:
        mod.run_convert_imgs_to_pdf_task_core = original_convert_imgs_task
    imgs_pdf = img_root / "【处理完成】结果文件夹" / "imgs2pdf_图集合并.pdf"
    imgs2pdf_result = mod._get_last_task_result(app)
    record(
        "imgs2pdf_workflow",
        wait_for(lambda: imgs_pdf.exists())
        and bool(convert_task_calls)
        and isinstance(imgs2pdf_result, dict)
        and imgs2pdf_result.get("status") == "success"
        and imgs2pdf_result.get("task_type") == "convert",
        {
            "output": str(imgs_pdf),
            "task_calls": len(convert_task_calls),
            "task_result": imgs2pdf_result,
        },
    )

    convert_extended_root = root / "convert_extended_workflow"
    convert_extended_root.mkdir()
    (convert_extended_root / "workflow.txt").write_text("workflow txt\n第二行", encoding="utf-8")
    app.current_task = "convert"
    app.cv_mode.set("txt2word")
    app.run_process(str(convert_extended_root), "convert")
    convert_extended_out = convert_extended_root / "workflow.docx"
    convert_extended_result = mod._get_last_task_result(app)
    record(
        "convert_extended_txt2word_workflow",
        wait_for(lambda: convert_extended_out.exists())
        and isinstance(convert_extended_result, dict)
        and convert_extended_result.get("status") == "success"
        and convert_extended_result.get("success_count") == 1
        and str(convert_extended_out) in convert_extended_result.get("outputs", []),
        {
            "output": str(convert_extended_out),
            "task_result": convert_extended_result,
        },
    )

    rm_root = root / "pdf_remove"
    rm_root.mkdir()
    src = rm_root / "src.pdf"
    make_pdf(src, ["remove me"])
    pkt = mod.create_watermark_packet("XMU TEST", "SmileySans-Oblique", 28, 0.2, 45)
    wm_pdf = rm_root / "wm.pdf"
    mod.add_watermark_to_pdf(str(src), str(wm_pdf), pkt)
    before_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(wm_pdf)).pages)
    app.current_task = "remove_wm"
    app.rm_wm_preserve_mine.set(False)
    app.run_process(str(rm_root), "remove_wm")
    cleaned_pdf = rm_root / mod.RESULT_FOLDER_NAME / "wm.pdf"
    wait_for(lambda: cleaned_pdf.exists())
    after_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(cleaned_pdf)).pages)
    record("pdf_remove_wm_workflow", "XMU TEST" in before_text and "XMU TEST" not in after_text, cleaned_pdf)

    rm_single_root = root / "pdf_remove_single"
    rm_single_root.mkdir()
    single_src = rm_single_root / "single.pdf"
    make_pdf(single_src, ["single remove"])
    single_wm = rm_single_root / "single_wm.pdf"
    mod.add_watermark_to_pdf(str(single_src), str(single_wm), pkt)
    single_before_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(single_wm)).pages)
    app.current_task = "remove_wm"
    app.rm_wm_preserve_mine.set(False)
    app.rm_wm_overwrite_original.set(False)
    app.run_process(str(single_wm), "remove_wm")
    single_cleaned_pdf = rm_single_root / "single_wm_去水印.pdf"
    wait_for(lambda: single_cleaned_pdf.exists())
    single_after_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(single_cleaned_pdf)).pages)
    record(
        "pdf_remove_wm_single_file_output",
        "XMU TEST" in single_before_text
        and "XMU TEST" not in single_after_text
        and not (rm_single_root / mod.RESULT_FOLDER_NAME).exists(),
        single_cleaned_pdf,
    )
    single_cleaned_pdf.write_bytes(b"existing remove watermark result")
    app.current_task = "remove_wm"
    app.rm_wm_preserve_mine.set(False)
    app.rm_wm_overwrite_original.set(False)
    app.run_process(str(single_wm), "remove_wm")
    single_resume_result = dict(getattr(app, "_fx_last_task_result", {}) or {})
    record(
        "pdf_remove_wm_single_resume_existing_output",
        single_cleaned_pdf.read_bytes() == b"existing remove watermark result"
        and single_resume_result.get("status") == "success"
        and single_resume_result.get("skipped_count") == 1
        and str(single_cleaned_pdf) in list(single_resume_result.get("outputs") or []),
        single_resume_result,
    )

    rm_single_overwrite_root = root / "pdf_remove_single_overwrite"
    rm_single_overwrite_root.mkdir()
    overwrite_src = rm_single_overwrite_root / "overwrite.pdf"
    make_pdf(overwrite_src, ["overwrite remove"])
    mod.add_watermark_to_pdf(str(overwrite_src), str(overwrite_src), pkt)
    overwrite_before_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(overwrite_src)).pages)
    app.current_task = "remove_wm"
    app.rm_wm_preserve_mine.set(False)
    app.rm_wm_overwrite_original.set(True)
    app.run_process(str(overwrite_src), "remove_wm")
    wait_for(lambda: overwrite_src.exists())
    overwrite_after_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(overwrite_src)).pages)
    record(
        "pdf_remove_wm_single_file_overwrite",
        "XMU TEST" in overwrite_before_text
        and "XMU TEST" not in overwrite_after_text
        and not (rm_single_overwrite_root / mod.RESULT_FOLDER_NAME).exists(),
        overwrite_src,
    )
    app.rm_wm_overwrite_original.set(False)

    pm_root = root / "pdf_merge"
    pm_root.mkdir()
    make_pdf(pm_root / "a.pdf", ["A"])
    make_pdf(pm_root / "b.pdf", ["B"])
    app.current_task = "pdf"
    app.pdf_mode_var.set("merge")
    app.run_process(str(pm_root), "pdf")
    merged_pdf = pm_root / mod.RESULT_FOLDER_NAME / "Merged_All.pdf"
    record("pdf_merge_workflow", wait_for(lambda: merged_pdf.exists()), merged_pdf)
    merged_pdf.write_bytes(b"existing merged pdf result")
    app.current_task = "pdf"
    app.pdf_mode_var.set("merge")
    app.run_process(str(pm_root), "pdf")
    merge_resume_result = dict(getattr(app, "_fx_last_task_result", {}) or {})
    record(
        "pdf_merge_resume_existing_output",
        merged_pdf.read_bytes() == b"existing merged pdf result"
        and merge_resume_result.get("status") == "success"
        and merge_resume_result.get("skipped_count", 0) >= 1
        and str(merged_pdf) in list(merge_resume_result.get("outputs") or []),
        merge_resume_result,
    )

    ocr_root = root / "pdf_ocr"
    ocr_root.mkdir()
    scan_pdf = ocr_root / "scan.pdf"
    make_pdf(scan_pdf, ["Hello OCR PDF"])
    app.current_task = "pdf"
    app.pdf_mode_var.set("ocr")
    original_ocr_engine_cls = pdf_ocr_task_module.FengxiPdfOcrEngine
    original_compare_report = pdf_ocr_task_module._run_compare_report

    class FakePdfOcrEngine:
        backend_key = "fake_ocr"

        def __init__(self, *args, **kwargs):
            self.backend_key = "fake_ocr"
            self.backend_usage = {"fake_ocr": 1}

        def close(self):
            return None

        def ocr_pdf_to_searchable_pdf(
            self,
            src,
            dst,
            extraction_mode="mixed",
            password="",
            layered=True,
            progress_callback=None,
            stop_checker=None,
        ):
            shutil.copy2(src, dst)
            if callable(progress_callback):
                progress_callback(1, 1)
                progress_callback(
                    1,
                    1,
                    {
                        "page_number": 1,
                        "total_pages": 1,
                        "text_count": 1,
                        "ocr_count": 1,
                        "lines": ["OCR: Hello OCR PDF", "text: Hello source text"],
                    },
                )
            return {"backend_usage": {"fake_ocr": 1}}

    def fake_compare_report(src, report_path, options):
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        Path(report_path).write_text(f"# OCR Compare\n- Source: {Path(src).name}\n- Backend: fake_ocr\n", encoding="utf-8")
        return {"report_path": str(report_path), "backend_usage": {"fake_ocr": 1}}

    pdf_ocr_task_module.FengxiPdfOcrEngine = FakePdfOcrEngine
    pdf_ocr_task_module._run_compare_report = fake_compare_report
    try:
        if hasattr(app, "pdf_ocr_compare_report"):
            app.pdf_ocr_compare_report.set(True)
        app.pdf_ocr_mode.set("fullPage | 整页强制 OCR")
        if hasattr(app, "pdf_ocr_cls"):
            app.pdf_ocr_cls.set(False)
        if getattr(app, "_fx_pdf_ocr_lang_map", None):
            app.pdf_ocr_language.set(next(iter(app._fx_pdf_ocr_lang_map.keys())))
        app.run_process(str(ocr_root), "pdf")
        ocr_dir = next((p for p in ocr_root.iterdir() if p.is_dir()), None)
        ocr_pdf = ocr_dir / "scan.pdf" if ocr_dir else None
        compare_report = (ocr_root / mod.RESULT_FOLDER_NAME / "_ocr_compare_reports" / "scan.ocr_compare.md")
        ocr_text = ""
        if ocr_pdf and wait_for(lambda: ocr_pdf.exists()):
            ocr_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(ocr_pdf)).pages)
        record("pdf_ocr_searchable", bool(ocr_pdf and ocr_pdf.exists() and "Hello OCR PDF" in ocr_text), ocr_pdf or "missing")
        record("pdf_ocr_compare_report", wait_for(lambda: compare_report.exists()), compare_report)
        try:
            app.update()
        except Exception:
            pass
        preview_text = ""
        try:
            preview_text = app._fx_pdf_ocr_preview_box.get("1.0", "end")
        except Exception:
            preview_text = ""
        record(
            "pdf_ocr_realtime_preview_ui",
            "scan.pdf" in preview_text and "Hello OCR PDF" in preview_text,
            preview_text,
        )

        ocr_single_root = root / "pdf_ocr_single"
        ocr_single_root.mkdir()
        ocr_single_pdf = ocr_single_root / "single_scan.pdf"
        make_pdf(ocr_single_pdf, ["Hello OCR Single"])
        app.current_task = "pdf"
        app.pdf_mode_var.set("ocr")
        if hasattr(app, "pdf_ocr_compare_report"):
            app.pdf_ocr_compare_report.set(False)
        app.run_process(str(ocr_single_pdf), "pdf")
        ocr_single_out = ocr_single_root / mod.RESULT_FOLDER_NAME / "single_scan.pdf"
        ocr_single_text = ""
        if wait_for(lambda: ocr_single_out.exists()):
            ocr_single_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(ocr_single_out)).pages)
        record(
            "single_file_input_pdf_ocr",
            ocr_single_out.exists() and "Hello OCR Single" in ocr_single_text,
            ocr_single_out,
        )

        ocr_drag_root = root / "pdf_ocr_drag"
        ocr_drag_root.mkdir()
        ocr_drag_pdf = ocr_drag_root / "drag_scan.pdf"
        make_pdf(ocr_drag_pdf, ["Hello OCR Drag"])
        app.current_task = "pdf"
        app.pdf_mode_var.set("ocr")
        if hasattr(app, "pdf_ocr_compare_report"):
            app.pdf_ocr_compare_report.set(False)
        app.accept_drag_drop([str(ocr_drag_pdf).encode("utf-8")])
        drag_input_value = app.input_path.get()
        app.run_process(drag_input_value, "pdf")
        ocr_drag_out = ocr_drag_root / mod.RESULT_FOLDER_NAME / "drag_scan.pdf"
        ocr_drag_text = ""
        if wait_for(lambda: ocr_drag_out.exists()):
            ocr_drag_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(ocr_drag_out)).pages)
        record(
            "drag_drop_single_file_pdf_ocr",
            drag_input_value == str(ocr_drag_pdf)
            and getattr(app, "_fx_input_pick_mode", None) == "file"
            and ocr_drag_out.exists()
            and "Hello OCR Drag" in ocr_drag_text,
            ocr_drag_out,
        )
    finally:
        pdf_ocr_task_module.FengxiPdfOcrEngine = original_ocr_engine_cls
        pdf_ocr_task_module._run_compare_report = original_compare_report

    record(
        "pdf_ocr_brand_independent",
        hasattr(app, "pdf_ocr_model_root") and not hasattr(app, "pdf_ocr_umi_path"),
        getattr(app, "pdf_ocr_model_root", None),
    )
    backend_keys = set(getattr(app, "_fx_pdf_ocr_backend_map", {}).values())
    record(
        "pdf_ocr_multi_backend_ui",
        {"auto", "rapidocr", "paddleocr", "easyocr", "tesseract_cli"}.issubset(backend_keys),
        sorted(backend_keys),
    )
    backend_status_text = app.pdf_ocr_backend_status_var.get() if hasattr(app, "pdf_ocr_backend_status_var") else ""
    record(
        "pdf_ocr_backend_status_panel",
        "后端状态" in backend_status_text,
        backend_status_text[:160],
    )
    from tools.fx_pdf_ocr import discover_backend_status

    backend_status_map = {item["key"]: item for item in discover_backend_status(detailed=True)}
    rapidocr_status = backend_status_map.get("rapidocr", {})
    record(
        "pdf_ocr_backend_runtime_probe",
        bool(rapidocr_status.get("available")),
        rapidocr_status.get("reason", ""),
    )

    from tools.fx_pdf_ocr import (
        FengxiPdfOcrEngine,
        build_ocr_preprocess_candidates,
        score_ocr_rows,
    )

    low_contrast_image = Image.new("RGB", (240, 120), (235, 235, 235))
    low_contrast_path = root / "ocr_low_contrast_probe.png"
    low_contrast_image.save(low_contrast_path)
    low_contrast_bytes = low_contrast_path.read_bytes()
    light_candidates = build_ocr_preprocess_candidates(low_contrast_bytes, "light")
    scan_candidates = build_ocr_preprocess_candidates(low_contrast_bytes, "scan")
    record(
        "pdf_ocr_preprocess_candidates",
        [item["key"] for item in light_candidates] == ["original", "enhanced"]
        and "binary" in [item["key"] for item in scan_candidates],
        {
            "light": [item["key"] for item in light_candidates],
            "scan": [item["key"] for item in scan_candidates],
        },
    )

    class LowQualityBackend:
        backend_key = "low"

        def close(self):
            return None

        def ocr_image_bytes(self, _image_bytes):
            return [{"box": [[0, 0], [10, 0], [10, 10], [0, 10]], "text": "?", "score": 0.05}]

    class HighQualityBackend:
        backend_key = "high"

        def close(self):
            return None

        def ocr_image_bytes(self, _image_bytes):
            return [
                {
                    "box": [[0, 0], [120, 0], [120, 20], [0, 20]],
                    "text": "Hello OCR fallback works",
                    "score": 0.96,
                }
            ]

    fallback_engine = object.__new__(FengxiPdfOcrEngine)
    fallback_engine.requested_backend_key = "auto"
    fallback_engine.backend_key = "low"
    fallback_engine.preprocess_mode = "off"
    fallback_engine.backend_usage = {}
    fallback_engine.backend_errors = []
    fallback_engine._backend_cache = {"low": LowQualityBackend(), "high": HighQualityBackend()}
    fallback_engine._iter_backend_candidates = lambda: ["low", "high"]
    fallback_engine._get_backend = lambda backend_key: fallback_engine._backend_cache[backend_key]
    probe_backend_rows, probe_attempt = fallback_engine._ocr_one_image(low_contrast_bytes)
    record(
        "pdf_ocr_auto_quality_fallback",
        probe_attempt.get("backend") == "high"
        and probe_backend_rows[0]["text"] == "Hello OCR fallback works"
        and fallback_engine.backend_usage.get("high") == 1
        and score_ocr_rows(probe_backend_rows) >= 0.48,
        {
            "attempt": probe_attempt,
            "usage": fallback_engine.backend_usage,
            "score": score_ocr_rows(probe_backend_rows),
        },
    )

    import pythoncom
    import win32com.client

    for progid, name in [("Word.Application", "word"), ("PowerPoint.Application", "ppt")]:
        ok, detail = office_available(progid, mod=mod)
        record(f"{name}_com_available", ok, detail, skipped=not ok)

    word_available, _ = office_available("Word.Application", mod=mod)
    if word_available:
        pythoncom.CoInitialize()
        try:
            dispatch_probe = None
            try:
                dispatch_probe = mod.win32com.client.DispatchEx("Word.Application")
                record(
                    "word_dispatchex_gen_py_safe_patch",
                    bool(getattr(dispatch_probe, "Version", None)),
                    str(getattr(dispatch_probe, "Version", "")),
                )
            finally:
                try:
                    if dispatch_probe is not None:
                        dispatch_probe.Quit()
                except Exception:
                    pass

            word = mod._create_hidden_word_app()
            word.Visible = False
            with mod._DisableWin32ComGenCache():
                docx_src = root / "office_src.docx"
                doc = word.Documents.Add()
                doc.Content.Text = "hello word feature test"
                doc.SaveAs2(str(docx_src.resolve()), FileFormat=16)
                doc.Close(False)

                pdf_out = root / "office_word2pdf.pdf"
                status = mod.convert_doc_to_pdf(word, str(docx_src.resolve()), str(pdf_out.resolve()))
                record("word_to_pdf", status == "SUCCESS" and pdf_out.exists(), status)

                wm_docx = root / "office_word_wm.docx"
                status = mod.add_watermark_to_word(word, str(docx_src.resolve()), str(wm_docx.resolve()), "XMU TEST", "SmileySans-Oblique", 60, 0.08, 45)
                record("word_watermark", status == "SUCCESS" and wm_docx.exists(), status)

                word_guard_src = root / "office_word_copy_guard_src.docx"
                doc = word.Documents.Add()
                doc.Content.Text = (
                    "WORD GUARD VISIBLE PARAGRAPH 01\r"
                    "WORD GUARD VISIBLE PARAGRAPH 02\r"
                    "WORD GUARD VISIBLE PARAGRAPH 03\r"
                    "WORD GUARD VISIBLE PARAGRAPH 04"
                )
                doc.SaveAs2(str(word_guard_src.resolve()), FileFormat=16)
                doc.Close(False)
                word_guard_docx = root / "office_word_copy_guard.docx"
                word_guard_status = mod.add_watermark_to_word(
                    word,
                    str(word_guard_src.resolve()),
                    str(word_guard_docx.resolve()),
                    "WORD GUARD",
                    "SmileySans-Oblique",
                    60,
                    0.08,
                    45,
                    copy_guard=True,
                    copy_guard_strength="standard",
                )
                word_guard_opened = word.Documents.Open(str(word_guard_docx.resolve()))
                try:
                    word_guard_full_text = str(word_guard_opened.Content.Text or "")
                    word_guard_first_range = word_guard_opened.Paragraphs(1).Range.Duplicate
                    word_guard_first_range.End = max(
                        int(word_guard_first_range.Start),
                        int(word_guard_first_range.End) - 1,
                    )
                    word_guard_first_copy = str(word_guard_first_range.Text or "").strip()
                    word_guard_variable = str(
                        word_guard_opened.Variables(WORD_COPY_GUARD_VARIABLE_MODULE).Value or ""
                    )
                    word_guard_copy_paragraphs = []
                    for paragraph_index in range(1, int(word_guard_opened.Paragraphs.Count) + 1):
                        paragraph = word_guard_opened.Paragraphs(paragraph_index)
                        paragraph_text = str(paragraph.Range.Text or "").replace("\r", "").replace("\x07", "").strip()
                        if len(paragraph_text) < 80 or not paragraph_text.startswith(COPY_GUARD_TEXT_PREFIX_MODULE):
                            continue
                        try:
                            style_ok = (
                                int(paragraph.Range.Font.Hidden) == 0
                                and float(paragraph.Range.Font.Size) <= 1.1
                                and int(paragraph.Range.Font.Color) == 0xFFFFFF
                            )
                        except Exception:
                            style_ok = False
                        word_guard_copy_paragraphs.append((paragraph_index, paragraph_text, style_ok))
                    word_guard_pdf = root / "office_word_copy_guard.pdf"
                    word_guard_opened.ExportAsFixedFormat(str(word_guard_pdf.resolve()), 17)
                finally:
                    word_guard_opened.Close(False)
                word_guard_first_noise = min(
                    (word_guard_full_text.find(item[1]) for item in word_guard_copy_paragraphs),
                    default=-1,
                )
                word_guard_last_visible = word_guard_full_text.rfind("WORD GUARD VISIBLE PARAGRAPH 04")
                word_guard_upgrade_docx = root / "office_word_copy_guard_upgrade.docx"
                word_guard_upgrade_status = mod.add_watermark_to_word(
                    word,
                    str(word_guard_docx.resolve()),
                    str(word_guard_upgrade_docx.resolve()),
                    "WORD GUARD",
                    "SmileySans-Oblique",
                    60,
                    0.08,
                    45,
                    copy_guard=True,
                    copy_guard_strength="standard",
                )
                record(
                    "word_copy_guard_between_paragraphs_full_copy_noises_local_copy_clean",
                    word_guard_status == "SUCCESS"
                    and word_guard_docx.exists()
                    and word_guard_variable == WORD_COPY_GUARD_VALUE_MODULE
                    and len(word_guard_copy_paragraphs) >= 4
                    and all(item[2] for item in word_guard_copy_paragraphs)
                    and word_guard_first_copy == "WORD GUARD VISIBLE PARAGRAPH 01"
                    and 0 < word_guard_first_noise < word_guard_last_visible
                    and word_guard_upgrade_status == "SKIP:already watermarked and copy guard exists",
                    {
                        "status": word_guard_status,
                        "first_copy": word_guard_first_copy,
                        "guard_paragraph_count": len(word_guard_copy_paragraphs),
                        "first_noise": word_guard_first_noise,
                        "last_visible": word_guard_last_visible,
                        "variable": word_guard_variable,
                        "upgrade_status": word_guard_upgrade_status,
                    },
                )

                wm_color_docx = root / "office_word_wm_color.docx"
                status = mod.add_watermark_to_word(word, str(docx_src.resolve()), str(wm_color_docx.resolve()), "COLOR TEST", "SmileySans-Oblique", 60, 0.3, 45, color="#3366CC")
                color_opened = word.Documents.Open(str(wm_color_docx.resolve()))
                try:
                    color_shape = color_opened.Sections(1).Headers(1).Shapes(1)
                    word_color_value = int(color_shape.Fill.ForeColor.RGB)
                finally:
                    color_opened.Close(False)
                record(
                    "word_watermark_custom_color",
                    status == "SUCCESS" and wm_color_docx.exists() and word_color_value == 0xCC6633,
                    {"status": status, "rgb": word_color_value},
                )

                wm_visible_pdf = root / "office_word_wm_visible.pdf"
                wm_visible_doc = word.Documents.Open(str(wm_docx.resolve()))
                try:
                    wm_visible_doc.ExportAsFixedFormat(str(wm_visible_pdf.resolve()), 17)
                finally:
                    wm_visible_doc.Close(False)
                wm_visible_pixels = rendered_pdf_nonwhite_pixels(wm_visible_pdf)
                record(
                    "word_watermark_visible_when_exported",
                    wm_visible_pdf.exists() and wm_visible_pixels > 8000,
                    {"pixels": wm_visible_pixels, "pdf": str(wm_visible_pdf)},
                )

                wm_first_src = root / "office_word_first_page_src.docx"
                doc = word.Documents.Add()
                doc.Content.Text = "first page watermark body\r"
                doc.Content.InsertAfter("\fsecond page should stay clean")
                doc.SaveAs2(str(wm_first_src.resolve()), FileFormat=16)
                doc.Close(False)
                wm_first_docx = root / "office_word_first_page_wm.docx"
                status = mod.add_watermark_to_word(
                    word,
                    str(wm_first_src.resolve()),
                    str(wm_first_docx.resolve()),
                    "FIRST PAGE ONLY",
                    "SmileySans-Oblique",
                    60,
                    0.3,
                    45,
                    page_range="first",
                    force_mode=True,
                )
                wm_first_pdf = root / "office_word_first_page_wm.pdf"
                wm_first_doc = word.Documents.Open(str(wm_first_docx.resolve()))
                try:
                    wm_first_doc.ExportAsFixedFormat(str(wm_first_pdf.resolve()), 17)
                finally:
                    wm_first_doc.Close(False)
                first_page_pixels = rendered_pdf_page_nonwhite_pixels(wm_first_pdf, 0)
                second_page_pixels = rendered_pdf_page_nonwhite_pixels(wm_first_pdf, 1)
                record(
                    "word_watermark_first_page_only_scope",
                    status == "SUCCESS"
                    and wm_first_docx.exists()
                    and wm_first_pdf.exists()
                    and first_page_pixels > second_page_pixels + 5000,
                    {
                        "status": status,
                        "first_page_pixels": first_page_pixels,
                        "second_page_pixels": second_page_pixels,
                        "pdf": str(wm_first_pdf),
                    },
                )

                wm_first_random_src = root / "office_word_first_random_src.docx"
                doc = word.Documents.Add()
                doc.Content.Text = "first random page one\r"
                doc.Content.InsertAfter("\fsecond page should stay clean")
                doc.Content.InsertAfter("\fthird page should receive watermark")
                doc.SaveAs2(str(wm_first_random_src.resolve()), FileFormat=16)
                doc.Close(False)
                wm_first_random_docx = root / "office_word_first_random_wm.docx"
                import tools.fx_watermark_core as wm_core_word_random

                original_word_random_randint = wm_core_word_random.random.randint
                wm_core_word_random.random.randint = lambda start, end: 2
                try:
                    status = mod.add_watermark_to_word(
                        word,
                        str(wm_first_random_src.resolve()),
                        str(wm_first_random_docx.resolve()),
                        "FIRST RANDOM WORD",
                        "SmileySans-Oblique",
                        60,
                        0.3,
                        45,
                        page_range="first_random",
                        force_mode=True,
                    )
                finally:
                    wm_core_word_random.random.randint = original_word_random_randint
                wm_first_random_pdf = root / "office_word_first_random_wm.pdf"
                wm_first_random_doc = word.Documents.Open(str(wm_first_random_docx.resolve()))
                try:
                    wm_first_random_doc.ExportAsFixedFormat(str(wm_first_random_pdf.resolve()), 17)
                finally:
                    wm_first_random_doc.Close(False)
                word_random_pixels = [rendered_pdf_page_nonwhite_pixels(wm_first_random_pdf, index) for index in range(3)]
                record(
                    "word_watermark_first_random_two_pages",
                    status == "SUCCESS"
                    and wm_first_random_docx.exists()
                    and wm_first_random_pdf.exists()
                    and word_random_pixels[0] > word_random_pixels[1] + 5000
                    and word_random_pixels[2] > word_random_pixels[1] + 5000,
                    {
                        "status": status,
                        "pixels": word_random_pixels,
                        "pdf": str(wm_first_random_pdf),
                    },
                )

                cleaned_docx = root / "office_word_clean.docx"
                status = mod.remove_watermark_from_word(word, str(wm_docx.resolve()), str(cleaned_docx.resolve()), preserve_mine=False)
                record("word_remove_wm", status == "SUCCESS" and cleaned_docx.exists(), status)

                header_img = root / "office_header_inline.png"
                Image.new("RGBA", (1200, 520), (255, 0, 0, 120)).save(header_img)
                inline_docx = root / "office_header_inline.docx"
                doc = word.Documents.Add()
                doc.Content.Text = "header inline watermark probe"
                header = doc.Sections(1).Headers(1)
                header.Range.Text = "HEADER\r"
                header.Range.Collapse(0)
                header.Range.InlineShapes.AddPicture(str(header_img.resolve()))
                doc.SaveAs2(str(inline_docx.resolve()), FileFormat=16)
                doc.Close(False)

                inline_cleaned_docx = root / "office_header_inline_clean.docx"
                status = mod.remove_watermark_from_word(word, str(inline_docx.resolve()), str(inline_cleaned_docx.resolve()), preserve_mine=False)
                inline_opened = word.Documents.Open(str(inline_cleaned_docx.resolve()))
                inline_header = inline_opened.Sections(1).Headers(1)
                inline_left = inline_header.Range.InlineShapes.Count
                inline_opened.Close(False)
                record(
                    "word_remove_wm_header_inline_image",
                    status == "SUCCESS" and inline_cleaned_docx.exists() and inline_left == 0,
                    f"status={status}, inline_left={inline_left}",
                )

                header_logo = root / "office_header_logo.png"
                Image.new("RGBA", (180, 60), (0, 120, 255, 255)).save(header_logo)
                safe_header_docx = root / "office_header_safe.docx"
                doc = word.Documents.Add()
                doc.Content.Text = "normal header assets should stay"
                header = doc.Sections(1).Headers(1)
                header.Range.Text = "Fengxi Header\r"
                header.Range.Collapse(0)
                header.Range.InlineShapes.AddPicture(str(header_logo.resolve()))
                note_shape = header.Shapes.AddTextEffect(0, "HEADER NOTE", "Arial", 12, False, False, 20, 10)
                note_shape.Rotation = 0
                note_shape.Left = 20
                note_shape.Top = 10
                safe_header_docx_out = root / "office_header_safe_clean.docx"
                doc.SaveAs2(str(safe_header_docx.resolve()), FileFormat=16)
                doc.Close(False)

                status = mod.remove_watermark_from_word(word, str(safe_header_docx.resolve()), str(safe_header_docx_out.resolve()), preserve_mine=False)
                safe_opened = word.Documents.Open(str(safe_header_docx_out.resolve()))
                safe_header = safe_opened.Sections(1).Headers(1)
                safe_inline_left = safe_header.Range.InlineShapes.Count
                safe_shape_left = safe_header.Shapes.Count
                safe_header_text = safe_header.Range.Text or ""
                safe_opened.Close(False)
                record(
                    "word_remove_wm_preserve_header_assets",
                    status == "SUCCESS"
                    and safe_header_docx_out.exists()
                    and safe_inline_left >= 1
                    and safe_shape_left >= 1
                    and "Fengxi Header" in safe_header_text,
                    f"status={status}, inline={safe_inline_left}, shapes={safe_shape_left}, text={safe_header_text!r}",
                )

                meta_docx = root / "office_meta.docx"
                status = mod.modify_office_meta(word, str(docx_src.resolve()), str(meta_docx.resolve()), "AgentTester", app_type="word")
                record("word_meta_author", status == "SUCCESS" and meta_docx.exists(), status)

                batch_docx = root / "office_batch_watermark.docx"
                doc = word.Documents.Add()
                doc.Content.Text = "batch watermark workflow"
                doc.SaveAs2(str(batch_docx.resolve()), FileFormat=16)
                doc.Close(False)
                mod._safe_named_widget_set(app, "wm_text", "BATCH WATERMARK")
                mod._safe_var_set(app, "output_strategy_var", mod.OUTPUT_STRATEGY_VALUE_TO_LABEL["same_dir"])
                mod._safe_var_set(app, "wm_delete_var", False)
                mod._safe_var_set(app, "wm_convert_pdf", False)
                mod._safe_var_set(app, "wm_skip_hyphen_var", False)
                mod._safe_var_set(app, "wm_range_var", "all")
                mod._safe_var_set(app, "wm_overwrite_var", "force")
                app.run_process(str(batch_docx.resolve()), "watermark")
                batch_result = mod._get_last_task_result(app)
                batch_outputs = [Path(path) for path in batch_result.get("outputs", [])]
                batch_output_candidates = batch_outputs + [
                    path
                    for path in batch_docx.parent.rglob(f"{batch_docx.stem}*.docx")
                    if path.resolve() != batch_docx.resolve()
                ]
                batch_output_exists = any(path.exists() and path.suffix.lower() == ".docx" for path in batch_output_candidates)
                batch_logs = list(getattr(app, "_fx_last_task_logs", []) or [])
                record(
                    "watermark_docx_run_process_safe_word_dispatch",
                    batch_result.get("status") == "success"
                    and batch_result.get("failed_count") == 0
                    and batch_output_exists
                    and not any("Word COM 初始化失败" in str(item) for item in batch_logs),
                    {"result": batch_result, "outputs": [str(path) for path in batch_output_candidates], "logs": batch_logs[-8:]},
                )

                batch_docx_outputs = [path for path in batch_output_candidates if path.exists() and path.suffix.lower() == ".docx"]
                batch_docx_has_marker = False
                batch_docx_has_text = False
                if batch_docx_outputs:
                    with zipfile.ZipFile(batch_docx_outputs[0]) as archive:
                        for name in archive.namelist():
                            if not name.endswith(".xml"):
                                continue
                            xml_text = archive.read(name).decode("utf-8", errors="replace")
                            batch_docx_has_marker = batch_docx_has_marker or "XMU_DONE" in xml_text
                            batch_docx_has_text = batch_docx_has_text or "BATCH WATERMARK" in xml_text
                record(
                    "watermark_docx_single_same_dir_output_model",
                    batch_result.get("status") == "success"
                    and batch_result.get("success_count") == 1
                    and batch_result.get("failed_count") == 0
                    and bool(batch_result.get("outputs"))
                    and batch_docx_outputs
                    and batch_docx_outputs[0].parent == batch_docx.parent
                    and batch_docx_has_marker
                    and batch_docx_has_text,
                    {
                        "result": batch_result,
                        "outputs": [str(path) for path in batch_docx_outputs],
                        "marker": batch_docx_has_marker,
                        "text": batch_docx_has_text,
                    },
                )

                batch_visible_pdf = root / "office_batch_watermark_visible.pdf"
                batch_visible_pixels = 0
                if batch_docx_outputs:
                    batch_visible_doc = word.Documents.Open(str(batch_docx_outputs[0].resolve()))
                    try:
                        batch_visible_doc.ExportAsFixedFormat(str(batch_visible_pdf.resolve()), 17)
                    finally:
                        batch_visible_doc.Close(False)
                    batch_visible_pixels = rendered_pdf_nonwhite_pixels(batch_visible_pdf)
                record(
                    "watermark_docx_direct_visible_when_exported",
                    batch_result.get("status") == "success"
                    and batch_visible_pdf.exists()
                    and batch_visible_pixels > 8000,
                    {
                        "result": batch_result,
                        "pixels": batch_visible_pixels,
                        "pdf": str(batch_visible_pdf),
                    },
                )

                batch_pdf_docx = root / "office_batch_watermark_pdf.docx"
                doc = word.Documents.Add()
                doc.Content.Text = "batch watermark pdf workflow"
                doc.SaveAs2(str(batch_pdf_docx.resolve()), FileFormat=16)
                doc.Close(False)
                mod._safe_named_widget_set(app, "wm_text", "BATCH PDF WATERMARK")
                mod._safe_var_set(app, "output_strategy_var", mod.OUTPUT_STRATEGY_VALUE_TO_LABEL["same_dir"])
                mod._safe_var_set(app, "wm_delete_var", False)
                mod._safe_var_set(app, "wm_convert_pdf", True)
                mod._safe_var_set(app, "wm_skip_hyphen_var", False)
                mod._safe_var_set(app, "wm_range_var", "all")
                mod._safe_var_set(app, "wm_overwrite_var", "force")
                original_runtime_doc_to_pdf = mod._FX_RUNTIME_CONVERT_DOC_TO_PDF
                mod._FX_RUNTIME_CONVERT_DOC_TO_PDF = lambda *_args, **_kwargs: "ERROR:forced regression fallback"
                try:
                    app.run_process(str(batch_pdf_docx.resolve()), "watermark")
                finally:
                    mod._FX_RUNTIME_CONVERT_DOC_TO_PDF = original_runtime_doc_to_pdf
                batch_pdf_result = mod._get_last_task_result(app)
                batch_pdf_outputs = [Path(path) for path in batch_pdf_result.get("outputs", [])]
                batch_pdf_candidates = batch_pdf_outputs + [
                    path
                    for path in batch_pdf_docx.parent.rglob(f"{batch_pdf_docx.stem}*.pdf")
                    if path.exists()
                ]
                batch_pdf_output = next((path for path in batch_pdf_candidates if path.exists() and path.suffix.lower() == ".pdf"), None)
                batch_pdf_has_text = False
                if batch_pdf_output is not None:
                    reader = PdfReader(str(batch_pdf_output))
                    batch_pdf_has_text = any("BATCH PDF WATERMARK" in (page.extract_text() or "") for page in reader.pages)
                record(
                    "watermark_docx_convert_pdf_safe_fallback",
                    batch_pdf_result.get("status") == "success"
                    and batch_pdf_result.get("success_count") == 1
                    and batch_pdf_result.get("failed_count") == 0
                    and batch_pdf_output is not None
                    and batch_pdf_has_text,
                    {
                        "result": batch_pdf_result,
                        "outputs": [str(path) for path in batch_pdf_candidates],
                        "has_text": batch_pdf_has_text,
                    },
                )

            word.Quit()
        finally:
            pythoncom.CoUninitialize()
    else:
        for name in ["word_dispatchex_gen_py_safe_patch", "word_to_pdf", "word_watermark", "word_copy_guard_between_paragraphs_full_copy_noises_local_copy_clean", "word_watermark_visible_when_exported", "word_remove_wm", "word_remove_wm_header_inline_image", "word_remove_wm_preserve_header_assets", "word_meta_author", "watermark_docx_run_process_safe_word_dispatch", "watermark_docx_single_same_dir_output_model", "watermark_docx_direct_visible_when_exported", "watermark_docx_convert_pdf_safe_fallback"]:
            record(name, True, "skipped_no_word_com", skipped=True)

    ppt_available, _ = office_available("PowerPoint.Application", mod=mod)
    if ppt_available:
        pythoncom.CoInitialize()
        try:
            ppt = win32com.client.DispatchEx("PowerPoint.Application")
            pres = ppt.Presentations.Add()
            slide = pres.Slides.Add(1, 11)
            slide.Shapes.AddTextbox(1, 50, 50, 400, 50).TextFrame.TextRange.Text = "hello ppt"
            pptx_src = root / "office_src.pptx"
            pres.SaveAs(str(pptx_src.resolve()))
            try:
                pres.Close()
            except Exception:
                try:
                    ppt.Presentations.Close()
                except Exception:
                    pass

            ppt_pdf = root / "office_ppt2pdf.pdf"
            status = mod.convert_ppt_to_pdf(ppt, str(pptx_src.resolve()), str(ppt_pdf.resolve()))
            record("ppt_to_pdf", status == "SUCCESS" and ppt_pdf.exists(), status)
            ppt.Quit()
        finally:
            pythoncom.CoUninitialize()
    else:
        record("ppt_to_pdf", True, "skipped_no_ppt_com", skipped=True)

    failed_cases = [item["case"] for item in results if not item["ok"]]
    print(json.dumps({"total": len(results), "failed": failed_cases}, ensure_ascii=True), flush=True)
    mod._get_user_pref_root = original_pref_root
    try:
        app.destroy()
    except Exception:
        pass
    if not failed_cases:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
