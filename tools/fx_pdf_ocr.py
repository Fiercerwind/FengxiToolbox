import csv
import importlib
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from io import BytesIO, StringIO
from pathlib import Path

from PIL import Image


MIN_RENDER_SIZE = 1080
DEFAULT_PROFILE_KEY = "general"
DEFAULT_BACKEND_KEY = "auto"
AUTO_BACKEND_ORDER = ["rapidocr", "paddleocr", "easyocr", "tesseract_cli"]

PROFILE_OPTIONS = [
    {
        "key": "general",
        "label": "风兮通用 OCR（中英，推荐）",
        "rapidocr_det_lang": "ch",
        "rapidocr_rec_lang": "ch",
        "paddle_lang": "ch",
        "easyocr_langs": ["ch_sim", "en"],
        "tesseract_lang": "chi_sim+eng",
    },
    {
        "key": "english",
        "label": "英文优先 OCR",
        "rapidocr_det_lang": "en",
        "rapidocr_rec_lang": "en",
        "paddle_lang": "en",
        "easyocr_langs": ["en"],
        "tesseract_lang": "eng",
    },
]

BACKEND_OPTIONS = [
    {
        "key": "auto",
        "label": "自动选择（推荐）",
        "description": "按风兮优先级自动选择当前环境可用的 OCR 后端。",
    },
    {
        "key": "rapidocr",
        "label": "RapidOCR（轻量 ONNX）",
        "description": "启动轻、打包友好，适合作为默认方案。",
    },
    {
        "key": "paddleocr",
        "label": "PaddleOCR（官方 Python）",
        "description": "官方路线，模型与能力更完整，但依赖更重。",
    },
    {
        "key": "easyocr",
        "label": "EasyOCR（Torch）",
        "description": "语言覆盖广，适合做补充兜底。",
    },
    {
        "key": "tesseract_cli",
        "label": "Tesseract CLI",
        "description": "经典 OCR 命令行路线，外部依赖明确，适合作为备用通道。",
    },
]


_REGISTERED_DLL_DIRS = set()
_REGISTERED_DLL_HANDLES = []


def _fallback_model_root():
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "FengxiToolbox" / "ocr_models" / "rapidocr"
    return Path.home() / ".fengxi_toolbox" / "ocr_models" / "rapidocr"


def _project_root():
    return Path(__file__).resolve().parents[1]


def default_model_root():
    env_root = os.environ.get("FX_OCR_MODEL_ROOT")
    if env_root:
        return str(Path(env_root))
    bundled_root = _project_root() / "assets" / "ocr_models" / "rapidocr"
    if bundled_root.exists():
        return str(bundled_root)
    return str(_fallback_model_root())


def resolve_model_root(model_root=None):
    root = Path(model_root or default_model_root()).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_profile_options():
    return [{"key": item["key"], "label": item["label"]} for item in PROFILE_OPTIONS]


def get_default_profile_key():
    return DEFAULT_PROFILE_KEY


def build_profile_display_map():
    return {f'{item["label"]} | {item["key"]}': item["key"] for item in PROFILE_OPTIONS}


def get_default_profile_display():
    display_map = build_profile_display_map()
    for display, profile_key in display_map.items():
        if profile_key == DEFAULT_PROFILE_KEY:
            return display
    first = next(iter(display_map), None)
    return first or "风兮通用 OCR（中英，推荐） | general"


def get_backend_options():
    return [{"key": item["key"], "label": item["label"]} for item in BACKEND_OPTIONS]


def get_default_backend_key():
    return DEFAULT_BACKEND_KEY


def build_backend_display_map():
    return {f'{item["label"]} | {item["key"]}': item["key"] for item in BACKEND_OPTIONS}


def get_default_backend_display():
    display_map = build_backend_display_map()
    for display, backend_key in display_map.items():
        if backend_key == DEFAULT_BACKEND_KEY:
            return display
    first = next(iter(display_map), None)
    return first or "自动选择（推荐） | auto"


def get_backend_label(backend_key):
    for item in BACKEND_OPTIONS:
        if item["key"] == backend_key:
            return item["label"]
    return backend_key


def _get_profile(profile_key):
    for item in PROFILE_OPTIONS:
        if item["key"] == profile_key:
            return item
    return PROFILE_OPTIONS[0]


def _module_exists(module_name):
    return importlib.util.find_spec(module_name) is not None


def _prepend_env_path(path):
    current = os.environ.get("PATH", "")
    normalized = os.path.normcase(os.path.normpath(path))
    parts = [part for part in current.split(os.pathsep) if part]
    for part in parts:
        if os.path.normcase(os.path.normpath(part)) == normalized:
            return False
    os.environ["PATH"] = path + (os.pathsep + current if current else "")
    return True


def _iter_onnxruntime_capi_dirs():
    candidates = []
    if os.name == "nt":
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            candidates.append(Path(meipass) / "onnxruntime" / "capi")

        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / "_internal" / "onnxruntime" / "capi")
        candidates.append(exe_dir / "onnxruntime" / "capi")

    spec = importlib.util.find_spec("onnxruntime")
    locations = getattr(spec, "submodule_search_locations", None) or []
    for location in locations:
        candidates.append(Path(location) / "capi")

    seen = set()
    for candidate in candidates:
        try:
            resolved = Path(candidate).resolve()
        except Exception:
            continue
        if not resolved.is_dir():
            continue
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)
        yield resolved


def _iter_windows_ocr_runtime_dirs():
    seen = set()
    candidates = []

    if os.name == "nt" and _is_frozen_runtime():
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            meipass_path = Path(meipass)
            candidates.extend(
                [
                    meipass_path,
                    meipass_path / "numpy.libs",
                    meipass_path / "pywin32_system32",
                ]
            )

        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend(
            [
                exe_dir / "_internal",
                exe_dir / "_internal" / "numpy.libs",
                exe_dir / "_internal" / "pywin32_system32",
            ]
        )

    candidates.extend(_iter_onnxruntime_capi_dirs())

    for candidate in candidates:
        try:
            resolved = Path(candidate).resolve()
        except Exception:
            continue
        if not resolved.is_dir():
            continue
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)
        yield resolved


def _preload_windows_ocr_core_dlls():
    if os.name != "nt":
        return

    import ctypes

    for directory in _iter_onnxruntime_capi_dirs():
        for dll_name in ("onnxruntime.dll", "onnxruntime_providers_shared.dll"):
            dll_path = directory / dll_name
            if not dll_path.exists():
                continue
            try:
                ctypes.WinDLL(str(dll_path))
            except Exception:
                continue


def _prepare_windows_ocr_runtime_dirs():
    if os.name != "nt":
        return []

    prepared = []
    for candidate in _iter_windows_ocr_runtime_dirs():
        candidate_text = str(candidate)
        normalized = os.path.normcase(candidate_text)
        if normalized in _REGISTERED_DLL_DIRS:
            prepared.append(candidate_text)
            continue

        _prepend_env_path(candidate_text)
        if hasattr(os, "add_dll_directory"):
            handle = os.add_dll_directory(candidate_text)
            _REGISTERED_DLL_HANDLES.append(handle)
        _REGISTERED_DLL_DIRS.add(normalized)
        prepared.append(candidate_text)
    _preload_windows_ocr_core_dlls()
    return prepared


def _is_frozen_runtime():
    return bool(getattr(sys, "frozen", False))


def _rapidocr_runtime_hint():
    capi_dirs = list(_iter_onnxruntime_capi_dirs())
    if _module_exists("rapidocr") and (_module_exists("onnxruntime") or capi_dirs):
        return True, "已发现 RapidOCR 运行条件，处理时再验证"
    if _is_frozen_runtime() and capi_dirs:
        return True, f"已发现打包 OCR 运行时目录: {capi_dirs[0]}"
    return False, "需要 `rapidocr` 与 `onnxruntime`"


def _probe_python_modules(*module_names):
    for module_name in module_names:
        importlib.import_module(module_name)


def _probe_backend_import(key):
    if key == "rapidocr":
        _prepare_windows_ocr_runtime_dirs()
        _probe_python_modules("onnxruntime", "rapidocr")
        return True, "已通过真实导入探测"
    if key == "paddleocr":
        _probe_python_modules("paddle", "paddleocr")
        return True, "已通过真实导入探测"
    if key == "easyocr":
        _probe_python_modules("easyocr")
        return True, "已通过真实导入探测"
    if key == "tesseract_cli":
        tesseract_path = shutil.which("tesseract")
        if not tesseract_path:
            raise RuntimeError("未找到系统 tesseract 命令")
        return True, f"检测到 `{tesseract_path}`"
    return False, "未知后端"


def _describe_expected_runtime_files(directory):
    expected = [
        "onnxruntime.dll",
        "onnxruntime_providers_shared.dll",
        "onnxruntime_pybind11_state.pyd",
    ]
    result = {"directory": str(directory), "exists": directory.is_dir(), "files": {}}
    for name in expected:
        path = directory / name
        result["files"][name] = {
            "exists": path.exists(),
            "size": path.stat().st_size if path.exists() else None,
        }
    return result


def run_packaged_ocr_diagnostics(diag_path=None):
    diagnostics = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "frozen": bool(getattr(sys, "frozen", False)),
        "sys_executable": sys.executable,
        "sys_meipass": getattr(sys, "_MEIPASS", ""),
        "cwd": os.getcwd(),
        "default_model_root": default_model_root(),
        "resolved_model_root": str(resolve_model_root()),
        "path_entries": [
            entry
            for entry in os.environ.get("PATH", "").split(os.pathsep)
            if entry and any(flag in entry.lower() for flag in ("onnx", "rapidocr", "numpy", "shapely"))
        ],
        "sys_path_entries": [
            entry
            for entry in sys.path
            if entry and any(flag in str(entry).lower() for flag in ("onnx", "rapidocr", "_internal"))
        ],
    }

    diagnostics["capi_dirs_before_prepare"] = [str(path) for path in _iter_onnxruntime_capi_dirs()]
    try:
        diagnostics["prepared_dirs"] = _prepare_windows_ocr_runtime_dirs()
    except Exception:
        diagnostics["prepared_dirs"] = []
        diagnostics["prepare_error"] = traceback.format_exc()

    capi_dirs = []
    seen = set()
    for raw_path in diagnostics.get("capi_dirs_before_prepare", []) + diagnostics.get("prepared_dirs", []):
        key = os.path.normcase(str(raw_path))
        if key in seen:
            continue
        seen.add(key)
        capi_dirs.append(Path(raw_path))
    diagnostics["runtime_files"] = [_describe_expected_runtime_files(path) for path in capi_dirs]

    module_checks = {}
    for module_name in ("onnxruntime", "rapidocr"):
        entry = {"find_spec": False, "origin": None, "import_ok": False, "error": None, "traceback": None}
        try:
            spec = importlib.util.find_spec(module_name)
            entry["find_spec"] = spec is not None
            entry["origin"] = getattr(spec, "origin", None) if spec is not None else None
        except Exception:
            entry["traceback"] = traceback.format_exc()
        try:
            module = importlib.import_module(module_name)
            entry["import_ok"] = True
            entry["module_file"] = getattr(module, "__file__", None)
            if module_name == "onnxruntime":
                try:
                    entry["available_providers"] = list(module.get_available_providers())
                except Exception:
                    entry["available_providers_error"] = traceback.format_exc()
        except Exception as exc:
            entry["error"] = str(exc)
            entry["traceback"] = traceback.format_exc()
        module_checks[module_name] = entry
    diagnostics["module_checks"] = module_checks

    try:
        diagnostics["backend_status_detailed"] = discover_backend_status(detailed=True)
    except Exception:
        diagnostics["backend_status_detailed_error"] = traceback.format_exc()

    backend_resolution = {}
    for backend_key in ("rapidocr", "auto"):
        try:
            resolved = _resolve_backend_key(backend_key)
            backend_resolution[backend_key] = {"ok": True, "resolved": resolved}
        except Exception as exc:
            backend_resolution[backend_key] = {
                "ok": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
    diagnostics["backend_resolution"] = backend_resolution

    try:
        backend = RapidOcrBackend(DEFAULT_PROFILE_KEY, cls=False, model_root=resolve_model_root(), limit_side_len=2880, cpu_threads=1)
        diagnostics["rapidocr_backend_init"] = {"ok": True}
        backend.close()
    except Exception as exc:
        diagnostics["rapidocr_backend_init"] = {
            "ok": False,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }

    if diag_path:
        diag_file = Path(diag_path).resolve()
        diag_file.parent.mkdir(parents=True, exist_ok=True)
        diag_file.write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")
    return diagnostics


def discover_backend_status(detailed=False):
    statuses = []
    tesseract_path = shutil.which("tesseract")
    for item in BACKEND_OPTIONS:
        key = item["key"]
        available = False
        reason = ""
        if key == "auto":
            available = True
            reason = "会自动挑选可用后端"
        elif key == "rapidocr":
            if detailed:
                try:
                    prepared = _prepare_windows_ocr_runtime_dirs()
                    available, reason = _probe_backend_import("rapidocr")
                    if available and prepared:
                        reason = f"{reason} | DLL目录: {prepared[0]}"
                except Exception as exc:
                    available = False
                    reason = f"导入失败: {exc}"
            else:
                available, reason = _rapidocr_runtime_hint()
        elif key == "paddleocr":
            if detailed and _module_exists("paddleocr") and _module_exists("paddle"):
                try:
                    available, reason = _probe_backend_import("paddleocr")
                except Exception as exc:
                    available = False
                    reason = f"导入失败: {exc}"
            elif _module_exists("paddleocr") and _module_exists("paddle"):
                available = True
                reason = "已发现 PaddleOCR 依赖，处理时再验证"
            else:
                reason = "需要 `paddleocr` 与 `paddle`"
        elif key == "easyocr":
            if detailed and _module_exists("easyocr"):
                try:
                    available, reason = _probe_backend_import("easyocr")
                except Exception as exc:
                    available = False
                    reason = f"导入失败: {exc}"
            elif _module_exists("easyocr"):
                available = True
                reason = "已发现 EasyOCR 依赖，处理时再验证"
            else:
                reason = "需要 `easyocr`"
        elif key == "tesseract_cli":
            available = bool(tesseract_path)
            reason = f"检测到 `{tesseract_path}`" if tesseract_path else "需要系统安装 `tesseract` 命令"
        statuses.append(
            {
                "key": key,
                "label": item["label"],
                "available": bool(available),
                "reason": reason,
            }
        )
    return statuses


def build_backend_status_text(detailed=False):
    lines = ["后端状态："]
    for item in discover_backend_status(detailed=detailed):
        key = item["key"]
        if key == "auto":
            lines.append(f"- {key}: 自动选择")
            continue
        flag = "可用" if item["available"] else "未就绪"
        detail = item["reason"]
        lines.append(f"- {key}: {flag} | {detail}")
    lines.append("- auto 顺序: rapidocr -> paddleocr -> easyocr -> tesseract_cli")
    return "\n".join(lines)


def _render_page_as_png_bytes(page, fitz):
    rect = page.rect
    width = abs(rect[2] - rect[0])
    height = abs(rect[3] - rect[1])
    short_edge = min(width, height)
    if short_edge < MIN_RENDER_SIZE:
        zoom = MIN_RENDER_SIZE / max(short_edge, 1)
        matrix = fitz.Matrix(zoom, zoom)
    else:
        matrix = fitz.Identity
    pixmap = page.get_pixmap(matrix=matrix)
    return pixmap.tobytes("png")


def compare_pdf_ocr_backends(
    src,
    profile_key=None,
    model_root=None,
    cls=False,
    password="",
    page_index=0,
    cpu_threads=4,
    limit_side_len=2880,
):
    import fitz

    src = str(Path(src).resolve())
    profile_key = profile_key or DEFAULT_PROFILE_KEY
    model_root = resolve_model_root(model_root)
    statuses = discover_backend_status()
    status_map = {item["key"]: item for item in statuses}

    doc = fitz.open(src)
    try:
        if doc.is_encrypted and not doc.authenticate(password or ""):
            raise ValueError("PDF 已加密，密码不正确或未提供密码。")
        if doc.page_count <= 0:
            raise ValueError("PDF 没有可用于 OCR 的页面。")
        page_index = max(0, min(int(page_index), doc.page_count - 1))
        page = doc[page_index]
        image_bytes = _render_page_as_png_bytes(page, fitz)
    finally:
        doc.close()

    results = []
    for backend_key in AUTO_BACKEND_ORDER:
        info = status_map.get(backend_key, {})
        if not info.get("available"):
            results.append(
                {
                    "backend": backend_key,
                    "status": "unavailable",
                    "seconds": None,
                    "text_length": 0,
                    "text_preview": "",
                    "line_count": 0,
                    "reason": info.get("reason", "后端未就绪"),
                }
            )
            continue

        started = time.perf_counter()
        backend = None
        try:
            backend_cls = BACKEND_CLASS_MAP[backend_key]
            backend = backend_cls(
                profile_key,
                cls=cls,
                model_root=model_root,
                limit_side_len=limit_side_len,
                cpu_threads=cpu_threads,
            )
            rows = backend.ocr_image_bytes(image_bytes)
            text = "\n".join((row.get("text") or "").strip() for row in rows if (row.get("text") or "").strip())
            elapsed = time.perf_counter() - started
            preview = text[:240].replace("\r", " ").replace("\n", " | ")
            results.append(
                {
                    "backend": backend_key,
                    "status": "ok",
                    "seconds": round(elapsed, 3),
                    "text_length": len(text),
                    "text_preview": preview,
                    "line_count": len(rows),
                    "reason": info.get("reason", ""),
                }
            )
        except Exception as exc:
            elapsed = time.perf_counter() - started
            results.append(
                {
                    "backend": backend_key,
                    "status": "error",
                    "seconds": round(elapsed, 3),
                    "text_length": 0,
                    "text_preview": "",
                    "line_count": 0,
                    "reason": str(exc),
                }
            )
        finally:
            if backend is not None:
                backend.close()

    return {
        "src": src,
        "page_index": page_index,
        "profile": profile_key,
        "model_root": str(model_root),
        "compare_mode": "fullPage_first_page",
        "results": results,
    }


def write_pdf_ocr_comparison_report(
    src,
    report_path,
    profile_key=None,
    model_root=None,
    cls=False,
    password="",
    page_index=0,
    cpu_threads=4,
    limit_side_len=2880,
):
    summary = compare_pdf_ocr_backends(
        src=src,
        profile_key=profile_key,
        model_root=model_root,
        cls=cls,
        password=password,
        page_index=page_index,
        cpu_threads=cpu_threads,
        limit_side_len=limit_side_len,
    )

    report_path = Path(report_path).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# 风兮 OCR 后端对比报告",
        "",
        f"- 文件：`{summary['src']}`",
        f"- 采样页：第 {summary['page_index'] + 1} 页",
        "- 采样方式：整页渲染（用于统一比较各 OCR 后端）",
        f"- OCR 配置：`{summary['profile']}`",
        f"- 模型目录：`{summary['model_root']}`",
        "",
        "## 结果概览",
        "",
        "| 后端 | 状态 | 耗时(秒) | 文本长度 | 识别块数 | 说明 |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]

    for item in summary["results"]:
        seconds = "-" if item["seconds"] is None else str(item["seconds"])
        lines.append(
            f"| `{item['backend']}` | {item['status']} | {seconds} | {item['text_length']} | {item['line_count']} | {item['reason']} |"
        )

    lines.extend(["", "## 文本预览", ""])
    for item in summary["results"]:
        lines.append(f"### {item['backend']}")
        lines.append(f"- 状态：`{item['status']}`")
        if item["seconds"] is not None:
            lines.append(f"- 耗时：`{item['seconds']}` 秒")
        if item["reason"]:
            lines.append(f"- 说明：{item['reason']}")
        preview = item["text_preview"] or "(无文本预览)"
        lines.append("")
        lines.append("```text")
        lines.append(preview)
        lines.append("```")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "report_path": str(report_path),
        "summary": summary,
    }


def _resolve_backend_key(requested_key):
    requested_key = requested_key or DEFAULT_BACKEND_KEY
    if requested_key != "auto":
        if requested_key not in BACKEND_CLASS_MAP and requested_key != "tesseract_cli":
            raise ValueError(f"未知 OCR 后端: {requested_key}")
        try:
            _probe_backend_import(requested_key)
        except Exception as exc:
            raise RuntimeError(f"OCR 后端不可用: {get_backend_label(requested_key)}。{exc}") from exc
        return requested_key

    errors = []
    for candidate in AUTO_BACKEND_ORDER:
        try:
            _probe_backend_import(candidate)
            return candidate
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")
    error_text = "；".join(errors) if errors else "未发现可尝试的后端。"
    raise RuntimeError(f"当前环境没有可用的 OCR 后端。已尝试: {error_text}")


def transform_to_rotation(matrix):
    a, b, c, d, _, _ = matrix
    scale = math.sqrt(a**2 + b**2)
    if scale < 1e-6:
        return 0
    cos_theta = a / scale
    sin_theta = b / scale
    determinant = a * d - b * c
    if determinant < 0:
        cos_theta = -cos_theta
    theta_rad = math.atan2(sin_theta, cos_theta)
    theta_deg = math.degrees(theta_rad)
    return round(theta_deg) % 360


class SearchablePdfBuilder:
    def __init__(self, fitz, origin_path, output_path, password="", layered=True):
        self.fitz = fitz
        self.origin_path = str(origin_path)
        self.output_path = str(output_path)
        self.password = password or ""
        self.opacity = 0 if layered else 1
        self.is_insert_font = False
        self.font = fitz.Font("cjk")
        self.pdf = self._load_pdf()

    def _load_pdf(self):
        doc = self.fitz.open(self.origin_path)
        if doc.is_encrypted and not doc.authenticate(self.password):
            raise ValueError("PDF 已加密，密码不正确或未提供密码。")
        if doc.is_pdf:
            return doc

        data = doc.convert_to_pdf()
        pdf = self.fitz.open("pdf", data)
        try:
            pdf.set_toc(doc.get_toc())
        except Exception:
            pass
        meta = doc.metadata
        if not meta.get("producer"):
            meta["producer"] = "Fengxi Toolbox OCR"
        if not meta.get("creator"):
            meta["creator"] = "Fengxi Toolbox searchable PDF"
        pdf.set_metadata(meta)
        for src_page in doc:
            links = src_page.get_links()
            dst_page = pdf[src_page.number]
            for link in links:
                if link.get("kind") == self.fitz.LINK_NAMED:
                    continue
                dst_page.insert_link(link)
        doc.close()
        return pdf

    def _calculate_font_size(self, text, width, height):
        if height > width:
            width, height = height, width
        fontsize = round(height)
        min_size = 5
        text_length = lambda size: self.font.text_length(text, fontsize=size)
        while text_length(fontsize) > width and fontsize >= min_size:
            fontsize -= 1
        while text_length(fontsize) < width:
            fontsize += 1
        while text_length(fontsize) > width and fontsize >= min_size:
            fontsize -= 0.1
        return fontsize

    def add_page(self, page_index, text_blocks):
        page = self.pdf[page_index]
        page.clean_contents()
        rotation = page.rotation
        inserted = False
        for block in text_blocks:
            if self.opacity == 0 and block.get("from") == "text":
                continue
            text = block.get("text", "").strip()
            if not text:
                continue
            if not inserted:
                self.is_insert_font = inserted = True
                page.insert_font(fontname="cjk", fontbuffer=self.font.buffer)
            box = block["box"]
            x0, y0 = box[0]
            x2, y2 = box[2]
            width = max(1, x2 - x0)
            height = max(1, y2 - y0)
            fontsize = self._calculate_font_size(text, width, height)
            point = self.fitz.Point(x0, y2) * page.derotation_matrix
            page.insert_text(
                point,
                text,
                fontsize=fontsize,
                fontname="cjk",
                rotate=rotation,
                stroke_opacity=self.opacity,
                fill_opacity=self.opacity,
            )

    def finish(self):
        if self.is_insert_font:
            try:
                self.pdf.subset_fonts()
            except Exception:
                pass
            self._save(deflate=True, garbage=3)
        else:
            self._save()

    def _save(self, **options):
        temp_path = self.output_path + ".temp"
        try:
            self.pdf.save(self.output_path, **options)
            self.pdf.close()
        except Exception:
            self.pdf.save(temp_path, **options)
            self.pdf.close()
            if os.path.exists(self.output_path):
                os.remove(self.output_path)
            os.replace(temp_path, self.output_path)


class BaseOcrBackend:
    backend_key = ""

    def __init__(self, profile_key, cls=False, model_root=None, limit_side_len=2880, cpu_threads=4):
        self.profile_key = profile_key or DEFAULT_PROFILE_KEY
        self.profile = _get_profile(self.profile_key)
        self.use_cls = bool(cls)
        self.model_root = resolve_model_root(model_root)
        self.limit_side_len = int(limit_side_len)
        self.cpu_threads = max(1, int(cpu_threads))

    def ocr_image_bytes(self, image_bytes):
        raise NotImplementedError

    def close(self):
        return None


class RapidOcrBackend(BaseOcrBackend):
    backend_key = "rapidocr"

    def __init__(self, profile_key, cls=False, model_root=None, limit_side_len=2880, cpu_threads=4):
        super().__init__(profile_key, cls=cls, model_root=model_root, limit_side_len=limit_side_len, cpu_threads=cpu_threads)
        _prepare_windows_ocr_runtime_dirs()
        from rapidocr import RapidOCR

        self.api = RapidOCR(params=self._build_params())

    def _build_params(self):
        from rapidocr.utils.typings import LangDet, LangRec, ModelType, OCRVersion

        det_lang_map = {
            "ch": LangDet.CH,
            "en": LangDet.EN,
            "multi": LangDet.MULTI,
        }
        rec_lang_map = {
            "ch": LangRec.CH,
            "en": LangRec.EN,
        }
        return {
            "Global.text_score": 0.5,
            "Global.use_det": True,
            "Global.use_cls": self.use_cls,
            "Global.use_rec": True,
            "Global.max_side_len": self.limit_side_len,
            "Global.model_root_dir": str(self.model_root),
            "Global.log_level": "error",
            "EngineConfig.onnxruntime.intra_op_num_threads": self.cpu_threads,
            "EngineConfig.onnxruntime.inter_op_num_threads": 1,
            "EngineConfig.onnxruntime.enable_cpu_mem_arena": False,
            "Det.limit_side_len": min(self.limit_side_len, 1536),
            "Det.limit_type": "min",
            "Det.lang_type": det_lang_map.get(self.profile.get("rapidocr_det_lang", "ch"), LangDet.CH),
            "Det.model_type": ModelType.MOBILE,
            "Det.ocr_version": OCRVersion.PPOCRV4,
            "Rec.lang_type": rec_lang_map.get(self.profile.get("rapidocr_rec_lang", "ch"), LangRec.CH),
            "Rec.model_type": ModelType.MOBILE,
            "Rec.ocr_version": OCRVersion.PPOCRV4,
        }

    def ocr_image_bytes(self, image_bytes):
        results = []
        result = self.api(image_bytes, use_cls=self.use_cls)
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            return results
        txts = list(getattr(result, "txts", None) or [])
        scores = list(getattr(result, "scores", None) or [])
        for box, text, score in zip(boxes, txts, scores):
            results.append(
                {
                    "box": [[float(point[0]), float(point[1])] for point in box],
                    "text": text,
                    "score": float(score),
                    "from": "ocr",
                }
            )
        return results

    def close(self):
        self.api = None


class PaddleOcrBackend(BaseOcrBackend):
    backend_key = "paddleocr"

    def __init__(self, profile_key, cls=False, model_root=None, limit_side_len=2880, cpu_threads=4):
        super().__init__(profile_key, cls=cls, model_root=model_root, limit_side_len=limit_side_len, cpu_threads=cpu_threads)
        from paddleocr import PaddleOCR

        self.api = PaddleOCR(
            use_angle_cls=self.use_cls,
            lang=self.profile.get("paddle_lang", "ch"),
            show_log=False,
        )

    def ocr_image_bytes(self, image_bytes):
        with Image.open(BytesIO(image_bytes)) as image:
            rgb = image.convert("RGB")
            import numpy as np

            result = self.api.ocr(np.array(rgb), cls=self.use_cls)

        lines = result[0] if result and isinstance(result[0], list) else result
        results = []
        for row in lines or []:
            if not row or len(row) < 2:
                continue
            box, payload = row[0], row[1]
            if not payload or len(payload) < 2:
                continue
            text, score = payload[0], payload[1]
            if not str(text).strip():
                continue
            results.append(
                {
                    "box": [[float(point[0]), float(point[1])] for point in box],
                    "text": str(text),
                    "score": float(score),
                    "from": "ocr",
                }
            )
        return results


class EasyOcrBackend(BaseOcrBackend):
    backend_key = "easyocr"

    def __init__(self, profile_key, cls=False, model_root=None, limit_side_len=2880, cpu_threads=4):
        super().__init__(profile_key, cls=cls, model_root=model_root, limit_side_len=limit_side_len, cpu_threads=cpu_threads)
        import easyocr

        self.reader = easyocr.Reader(
            self.profile.get("easyocr_langs", ["ch_sim", "en"]),
            gpu=False,
            model_storage_directory=str(self.model_root),
        )

    def ocr_image_bytes(self, image_bytes):
        with Image.open(BytesIO(image_bytes)) as image:
            rgb = image.convert("RGB")
            import numpy as np

            result = self.reader.readtext(np.array(rgb), detail=1, paragraph=False)

        results = []
        for row in result:
            if not row or len(row) < 3:
                continue
            box, text, score = row[0], row[1], row[2]
            if not str(text).strip():
                continue
            results.append(
                {
                    "box": [[float(point[0]), float(point[1])] for point in box],
                    "text": str(text),
                    "score": float(score),
                    "from": "ocr",
                }
            )
        return results


class TesseractCliBackend(BaseOcrBackend):
    backend_key = "tesseract_cli"

    def __init__(self, profile_key, cls=False, model_root=None, limit_side_len=2880, cpu_threads=4):
        super().__init__(profile_key, cls=cls, model_root=model_root, limit_side_len=limit_side_len, cpu_threads=cpu_threads)
        self.exe = shutil.which("tesseract")
        if not self.exe:
            raise RuntimeError("未找到 tesseract 命令。")

    def ocr_image_bytes(self, image_bytes):
        with tempfile.TemporaryDirectory(prefix="fx_tesseract_") as tmp_dir:
            tmp_dir = Path(tmp_dir)
            image_path = tmp_dir / "page.png"
            image_path.write_bytes(image_bytes)
            cmd = [
                self.exe,
                str(image_path),
                "stdout",
                "-l",
                self.profile.get("tesseract_lang", "chi_sim+eng"),
                "--psm",
                "11",
                "tsv",
            ]
            completed = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr.strip() or "Tesseract OCR 执行失败。")

        results = []
        reader = csv.DictReader(StringIO(completed.stdout), delimiter="\t")
        for row in reader:
            text = (row.get("text") or "").strip()
            if not text:
                continue
            try:
                left = float(row.get("left") or 0)
                top = float(row.get("top") or 0)
                width = float(row.get("width") or 0)
                height = float(row.get("height") or 0)
                conf = float(row.get("conf") or 0)
            except ValueError:
                continue
            if width <= 0 or height <= 0:
                continue
            results.append(
                {
                    "box": [
                        [left, top],
                        [left + width, top],
                        [left + width, top + height],
                        [left, top + height],
                    ],
                    "text": text,
                    "score": max(0.0, min(conf / 100.0, 1.0)),
                    "from": "ocr",
                }
            )
        return results


BACKEND_CLASS_MAP = {
    "rapidocr": RapidOcrBackend,
    "paddleocr": PaddleOcrBackend,
    "easyocr": EasyOcrBackend,
    "tesseract_cli": TesseractCliBackend,
}


class FengxiPdfOcrEngine:
    def __init__(
        self,
        model_root=None,
        profile_key=None,
        backend_key=None,
        cls=False,
        limit_side_len=2880,
        cpu_threads=4,
    ):
        import fitz

        self.fitz = fitz
        self.model_root = resolve_model_root(model_root)
        self.profile_key = profile_key or DEFAULT_PROFILE_KEY
        self.requested_backend_key = backend_key or DEFAULT_BACKEND_KEY
        self.use_cls = bool(cls)
        self.cpu_threads = max(1, int(cpu_threads))
        self.limit_side_len = int(limit_side_len)
        self.backend_key = _resolve_backend_key(self.requested_backend_key)
        backend_cls = BACKEND_CLASS_MAP[self.backend_key]
        self.backend = backend_cls(
            self.profile_key,
            cls=self.use_cls,
            model_root=self.model_root,
            limit_side_len=self.limit_side_len,
            cpu_threads=self.cpu_threads,
        )

    def close(self):
        if getattr(self, "backend", None):
            self.backend.close()
        self.backend = None

    def _render_full_page(self, page):
        rect = page.rect
        width = abs(rect[2] - rect[0])
        height = abs(rect[3] - rect[1])
        short_edge = min(width, height)
        if short_edge < MIN_RENDER_SIZE:
            zoom = MIN_RENDER_SIZE / max(short_edge, 1)
            matrix = self.fitz.Matrix(zoom, zoom)
        else:
            zoom = 1
            matrix = self.fitz.Identity
        pixmap = page.get_pixmap(matrix=matrix)
        return {
            "bytes": pixmap.tobytes("png"),
            "xy": (0, 0),
            "scale_w": 1 / zoom,
            "scale_h": 1 / zoom,
        }

    def _extract_page_blocks(self, page, extraction_mode):
        page_rotation = page.rotation
        images = []
        text_blocks = []

        if extraction_mode == "fullPage":
            images.append(self._render_full_page(page))
            return images, text_blocks

        page_dict = page.get_text("dict", clip=self.fitz.INFINITE_RECT())
        for block in page_dict["blocks"]:
            if block["type"] == 1 and extraction_mode in ("imageOnly", "mixed"):
                transform = block["transform"]
                image_rotation = transform_to_rotation(transform)
                abs_rotation = round(page_rotation + image_rotation) % 360
                image_bytes = block["image"]
                bbox = block["bbox"]
                width_visual = bbox[2] - bbox[0]
                height_visual = bbox[3] - bbox[1]
                width_raw = block["width"]
                height_raw = block["height"]
                if width_raw <= 0 or height_raw <= 0:
                    continue
                scale_w = width_visual / width_raw
                scale_h = height_visual / height_raw
                if abs_rotation != 0:
                    with Image.open(BytesIO(image_bytes)) as image:
                        image_format = image.format or "PNG"
                        rotated = image.rotate(-abs_rotation, expand=True)
                        buffer = BytesIO()
                        rotated.save(buffer, format=image_format)
                        image_bytes = buffer.getvalue()
                images.append(
                    {
                        "bytes": image_bytes,
                        "xy": (bbox[0], bbox[1]),
                        "scale_w": scale_w,
                        "scale_h": scale_h,
                    }
                )
            elif block["type"] == 0 and extraction_mode == "mixed":
                last_line = len(block["lines"]) - 1
                for index, line in enumerate(block["lines"]):
                    text = "".join(span["text"] for span in line["spans"])
                    if not text:
                        continue
                    bbox = line["bbox"]
                    if page_rotation == 0:
                        box = [
                            [bbox[0], bbox[1]],
                            [bbox[2], bbox[1]],
                            [bbox[2], bbox[3]],
                            [bbox[0], bbox[3]],
                        ]
                    else:
                        rotation_matrix = page.rotation_matrix
                        point1 = self.fitz.Point(bbox[0], bbox[1]) * rotation_matrix
                        point2 = self.fitz.Point(bbox[2], bbox[3]) * rotation_matrix
                        x0 = min(point1.x, point2.x)
                        x1 = max(point1.x, point2.x)
                        y0 = min(point1.y, point2.y)
                        y1 = max(point1.y, point2.y)
                        box = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
                    text_blocks.append(
                        {
                            "box": box,
                            "text": text,
                            "score": 1,
                            "from": "text",
                            "end": "\n" if index == last_line else "",
                        }
                    )
        return images, text_blocks

    def _ocr_images(self, images):
        results = []
        for image in images:
            backend_rows = self.backend.ocr_image_bytes(image["bytes"])
            x, y = image["xy"]
            scale_w = image["scale_w"]
            scale_h = image["scale_h"]
            for row in backend_rows:
                normalized_box = []
                for point in row["box"]:
                    normalized_box.append(
                        [
                            float(point[0]) * scale_w + x,
                            float(point[1]) * scale_h + y,
                        ]
                    )
                results.append(
                    {
                        "box": normalized_box,
                        "text": row["text"],
                        "score": float(row.get("score", 0)),
                        "from": row.get("from", "ocr"),
                    }
                )
        return results

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
        extraction_mode = extraction_mode or "mixed"
        if extraction_mode not in {"mixed", "fullPage", "imageOnly"}:
            raise ValueError(f"不支持的 OCR 模式: {extraction_mode}")

        src = str(Path(src).resolve())
        dst = str(Path(dst).resolve())
        Path(dst).parent.mkdir(parents=True, exist_ok=True)

        builder = SearchablePdfBuilder(self.fitz, src, dst, password=password, layered=layered)
        source_doc = self.fitz.open(src)
        try:
            if source_doc.is_encrypted and not source_doc.authenticate(password or ""):
                raise ValueError("PDF 已加密，密码不正确或未提供密码。")
            total_pages = source_doc.page_count
            for page_index in range(total_pages):
                if callable(stop_checker) and stop_checker():
                    raise KeyboardInterrupt("用户停止了 OCR 任务。")
                if callable(progress_callback):
                    progress_callback(page_index + 1, total_pages)
                page = source_doc[page_index]
                images, text_blocks = self._extract_page_blocks(page, extraction_mode)
                ocr_blocks = self._ocr_images(images) if images else []
                builder.add_page(page_index, text_blocks + ocr_blocks)
            builder.finish()
        finally:
            source_doc.close()

        return {
            "src": src,
            "dst": dst,
            "pages": total_pages,
            "mode": extraction_mode,
            "layered": layered,
            "profile": self.profile_key,
            "requested_backend": self.requested_backend_key,
            "backend": self.backend_key,
            "backend_label": get_backend_label(self.backend_key),
            "model_root": str(self.model_root),
        }
