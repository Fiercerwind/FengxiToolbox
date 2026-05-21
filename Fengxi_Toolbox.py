import ast
import dis
import inspect
import io
import json
import marshal
import importlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import types
import time
import customtkinter
import pypdf
import pywinstyles
import pythoncom
import tkinter
import tkinter.filedialog
import tkinter.font
import tkinter.messagebox
import tkinter.ttk
import windnd
import win32com.client
import win32gui
from win32com.shell import shell, shellcon
from PIL import Image as PILImage, ImageDraw, ImageFont
from pathlib import Path
from reportlab.lib import pagesizes
from reportlab.pdfbase import ttfonts
from reportlab.pdfgen import canvas


RUNTIME_BIN = Path(__file__).with_name("fengxi_runtime.bin")
DEBUG_LOG = Path(tempfile.gettempdir()) / "fx_toolbox_loader.log"
DEFAULT_STARTUP_TAB = "watermark"
LAZY_TAB_SPECS = {
    "watermark": {"init": "init_watermark_ui"},
    "remove_wm": {"init": "init_remove_wm_ui"},
    "convert": {"init": "init_convert_ui"},
    "audio": {"init": "init_audio_ui"},
    "zip": {"init": "init_zip_ui"},
    "pdf": {"init": "init_pdf_ui"},
    "image": {"init": "init_img_ui"},
    "meta": {"init": "init_meta_ui"},
    "file": {"init": "init_file_ui"},
}
TAB_LAYOUT_ATTRS = {
    "watermark": "tab_wm",
    "remove_wm": "tab_rm_wm",
    "convert": "tab_cv",
    "audio": "tab_audio",
    "zip": "tab_zip",
    "pdf": "tab_pdf",
    "image": "tab_img",
    "meta": "tab_meta",
    "file": "tab_file",
}
LAZY_ATTR_PREFIXES = (
    ("pdf_", "pdf"),
    ("file_", "file"),
    ("zip_", "zip"),
    ("cv_", "convert"),
    ("rm_wm_", "remove_wm"),
    ("audio_", "audio"),
    ("img_", "image"),
    ("meta_", "meta"),
    ("wm_", "watermark"),
)
SIDEBAR_BUTTON_SPECS = {
    "btn_nav_wm": {"label": "批量水印", "icon": "shield"},
    "btn_nav_rm_wm": {"label": "去除水印", "icon": "eraser"},
    "btn_nav_cv": {"label": "格式转换", "icon": "swap"},
    "btn_nav_audio": {"label": "音频工具", "icon": "music"},
    "btn_nav_zip": {"label": "批量压缩", "icon": "box"},
    "btn_nav_pdf": {"label": "PDF 工具", "icon": "document"},
    "btn_nav_img": {"label": "图片工厂", "icon": "image"},
    "btn_nav_meta": {"label": "属性隐私", "icon": "lock"},
    "btn_nav_file": {"label": "文件管家", "icon": "folder"},
}
SIDEBAR_AUX_BUTTON_SPECS = {
    "btn_help_proxy": {"label": "使用教程", "icon": "book"},
    "btn_donate": {"label": "赞助作者", "icon": "coffee"},
}
SIDEBAR_ICON_NAV = (213, 228, 245, 255)
SIDEBAR_ICON_HELP = (232, 222, 208, 255)
SIDEBAR_ICON_DONATE = (239, 206, 123, 255)
CONTENT_ICON_PRIMARY = (173, 200, 228, 255)
CONTENT_ICON_SECONDARY = (194, 214, 236, 255)
SIDEBAR_AUX_STYLES = {
    "help": {
        "fg_color": "#161B21",
        "hover_color": "#222A34",
        "border_color": "#566274",
        "text_color": "#E8EDF5",
    },
    "donate": {
        "fg_color": "#241A10",
        "hover_color": "#322517",
        "border_color": "#B89352",
        "text_color": "#F6E2B2",
    },
}
FAST_SIDEBAR_BUILD_FONT = ("Microsoft YaHei UI", 12)
APP_ICON_PNG = "fengxi_app_icon.png"
APP_ICON_ICO = "fengxi_app_icon.ico"
APP_RELEASE_VERSION = "4.0.0"
APP_DISPLAY_VERSION = "4.0"
ZIP_MODE_LABEL_TEXTS = {
    "仅压缩总文件 (Total Zip)": "仅压缩总文件 (Total Zip)",
    "全层级递归压缩 (Total + Recursive)": "全层级递归压缩 (Total + Recursive)",
    "智能混合模式 (Smart Recursive) [推荐]": "智能混合模式 (Smart Recursive) [推荐]",
}
ZIP_MODE_DESCRIPTION_TEXT = (
    "功能说明：\n"
    "1. 仅压缩总文件：只在根目录生成一个包含所有内容的总压缩包。\n"
    "2. 全层级递归：会扫描每一层文件夹，并在各自【父级目录】生成对应压缩包。\n"
    "3. 智能混合模式：\n"
    "   • 若某一层同时包含文件和子文件夹，则该层会整体打包为一个压缩包。\n"
    "   • 整体打包后，会停止继续为该层内部子文件夹单独生成压缩包。\n"
    "   • 若某一层只有子文件夹、没有文件，则继续向下递归扫描。\n"
    "   • 根目录若同时包含文件和子文件夹，则会直接跳过对子文件夹的单独压缩，最终只保留根目录总包。\n"
    "4. 自动清理：生成前会自动删除同名的旧压缩包。"
)
HELP_TAB_TITLE = "使用教程"
INLINE_HELP_SECTIONS = (
    (
        "使用流程",
        (
            "1. 先在顶部输入框拖入或选择文件/文件夹。当前入口支持单个文件和文件夹，拖拽时也会保留真实路径。",
            "2. 在左侧选择功能模块，再在当前页面配置参数。",
            "3. 点击底部开始执行，进度条与运行信息框会显示当前处理状态。",
            "4. 默认输出到原文件同目录或【处理完成】结果文件夹；少数功能会按页面说明生成同名派生文件。",
            "5. 处理前请确认是否开启“删除源文件”或“覆盖原文件”类开关，这类选项会改变原始资料。",
        ),
    ),
    (
        "批量水印",
        (
            "支持 PDF、Word、PPT 等文档批量添加文字或图片水印。",
            "智能加水印支持文件名跳过规则：可设置按开头或结尾匹配指定字符，默认兼容跳过文件名去扩展名后以“-”结尾的文件。",
            "这是稳定区功能，除非明确要求，不应改动核心加水印处理逻辑。",
        ),
    ),
    (
        "去除水印",
        (
            "支持 Word、PDF、PPT 等资料的批量去水印尝试。",
            "可选择单个文件或文件夹；单文件默认在同目录生成去水印结果，文件夹默认生成【处理完成】结果文件夹。",
            "如开启覆盖原文件，会在处理成功后替换原文件；不建议在没有备份的唯一资料上直接开启。",
            "去水印属于识别和清理任务，不同文件结构差异很大，遇到异常文件建议先用副本测试。",
        ),
    ),
    (
        "格式转换",
        (
            "支持常用文档格式互转，包括 Word/PPT/PDF 等转换入口。",
            "选择单个文件时只处理该文件；选择文件夹时会按当前功能收集可处理文件。",
            "转换失败通常与 Office/WPS 环境、文件损坏、加密文档或路径权限有关。",
        ),
    ),
    (
        "音频工具",
        (
            "支持从视频中提取音频，以及常见音频格式转换。",
            "底层优先使用随 Python 环境可用的 ffmpeg 路线，打包版会随包带入必要依赖。",
            "大体积视频处理耗时较长，处理期间不要频繁切换或强制关闭。",
        ),
    ),
    (
        "批量压缩",
        (
            "仅压缩总文件：只在根目录生成一个包含所有内容的总压缩包。",
            "全层级递归：扫描每一层文件夹，并在各自父级目录生成对应压缩包。",
            "智能混合模式：某一层同时包含文件和子文件夹时，会整体打包该层并停止继续为内部子文件夹单独打包；若只有子文件夹则继续向下递归。",
            "生成前会自动删除同名旧压缩包，避免结果混乱。",
        ),
    ),
    (
        "PDF 工具",
        (
            "页面采用左侧功能入口、右侧参数面板，当前包括合并、拆分、加密、压缩、OCR 搜索版 PDF。",
            "PDF 压缩可选择 PDF 压缩程度和图片压缩程度，输出为原文件名_压缩.pdf。",
            "OCR 搜索版 PDF 会保留原页面画面并叠加透明文字层，支持 auto、rapidocr、paddleocr、easyocr、tesseract_cli 等后端路线。",
            "OCR 可选生成后端对比报告，便于比较不同识别路径效果。",
        ),
    ),
    (
        "图片工厂",
        (
            "支持图片批量处理、图片转 PDF、以及多图合并成一个 PDF。",
            "图片转 PDF 会为每张图片生成独立 PDF；多图合并 PDF 会按文件名排序合成为一份 PDF。",
            "支持 jpg、jpeg、png、bmp、webp、tif、tiff 等常见图片格式。",
        ),
    ),
    (
        "属性隐私",
        (
            "支持修改 PDF/Office 作者信息，以及批量修改文件时间属性。",
            "Office 元数据依赖本机 Office COM 环境；PDF 作者信息通过 PDF 元数据写入。",
            "处理前建议确认是否需要保留原始创建时间、修改时间或作者信息。",
        ),
    ),
    (
        "文件管家",
        (
            "支持批量重命名和重复文件清理。",
            "重命名包含添加、替换、截取等子模式；去重基于文件内容哈希判断。",
            "删除或去重类操作建议先用测试文件夹确认规则，避免误删。",
        ),
    ),
    (
        "重要约束",
        (
            "批量压缩和批量水印是稳定区，非必要不改业务代码。",
            "任何重要修改前需要先做可恢复备份。",
            "不得删除项目目录外的任何文件。",
            "每次工作应先读取记忆文件，再按项目和类别渐进加载上下文。",
        ),
    ),
)
RESULT_FOLDER_NAME = "【处理完成】结果文件夹"
QUEUE_HISTORY_LIMIT = 80
QUEUE_ERROR_MARKERS = (
    "❌",
    "🔥",
    "失败",
    "错误",
    "异常",
    "严重错误",
    "error",
    "failed",
    "traceback",
)
QUEUE_TASK_LABELS = {
    "watermark": "批量水印",
    "remove_wm": "去除水印",
    "convert": "格式转换",
    "audio": "音频工具",
    "zip": "批量压缩",
    "pdf": "PDF 工具",
    "image": "图片工厂",
    "meta": "属性隐私",
    "file": "文件管家",
}
QUEUE_STATUS_LABELS = {
    "queued": "等待",
    "running": "执行中",
    "success": "完成",
    "failed": "失败",
    "skipped": "跳过",
    "stopped": "已停止",
}
QUEUE_HISTORY_STATUS_DEFAULT = "全部状态"
QUEUE_HISTORY_TASK_DEFAULT = "全部功能"
QUEUE_HISTORY_FAILURE_DEFAULT = "全部失败"
QUEUE_HISTORY_STATUS_OPTIONS = (
    (QUEUE_HISTORY_STATUS_DEFAULT, ""),
    ("仅完成", "success"),
    ("仅失败", "failed"),
    ("仅跳过", "skipped"),
    ("仅停止", "stopped"),
)
QUEUE_HISTORY_FAILURE_OPTIONS = (
    (QUEUE_HISTORY_FAILURE_DEFAULT, ""),
    ("路径缺失", "path_missing"),
    ("权限问题", "permission"),
    ("超时", "timeout"),
    ("依赖问题", "dependency"),
    ("部分失败", "partial_failure"),
    ("日志失败", "log_failure"),
    ("普通失败", "generic_failure"),
    ("未知失败", "unknown"),
)
QUEUE_HISTORY_TASK_OPTIONS = ((QUEUE_HISTORY_TASK_DEFAULT, ""),) + tuple(
    (label, task_type) for task_type, label in QUEUE_TASK_LABELS.items()
)
QUEUE_HISTORY_STATUS_LABEL_TO_VALUE = {label: value for label, value in QUEUE_HISTORY_STATUS_OPTIONS}
QUEUE_HISTORY_FAILURE_LABEL_TO_VALUE = {label: value for label, value in QUEUE_HISTORY_FAILURE_OPTIONS}
QUEUE_HISTORY_TASK_LABEL_TO_VALUE = {label: value for label, value in QUEUE_HISTORY_TASK_OPTIONS}
INLINE_TITLE_ICON_SPECS = {
    "批量去水印": {"icon": "eraser", "size": 20, "color": CONTENT_ICON_PRIMARY},
    "文档格式互转": {"icon": "swap", "size": 20, "color": CONTENT_ICON_PRIMARY},
    "音频/视频处理": {"icon": "music", "size": 20, "color": CONTENT_ICON_PRIMARY},
    "批量压缩": {"icon": "box", "size": 20, "color": CONTENT_ICON_PRIMARY},
    "PDF 进阶工具箱": {"icon": "document", "size": 20, "color": CONTENT_ICON_PRIMARY},
    "图片批量工厂": {"icon": "image", "size": 20, "color": CONTENT_ICON_PRIMARY},
    "属性隐私设置": {"icon": "lock", "size": 20, "color": CONTENT_ICON_PRIMARY},
    "文件管家": {"icon": "folder", "size": 20, "color": CONTENT_ICON_PRIMARY},
    "水印内容": {"icon": "document", "size": 18, "color": CONTENT_ICON_SECONDARY},
    "参数配置": {"icon": "settings", "size": 18, "color": CONTENT_ICON_SECONDARY},
    "图片处理工具": {"icon": "image", "size": 18, "color": CONTENT_ICON_SECONDARY},
    "⚡": {"icon": "box", "size": 16, "color": CONTENT_ICON_SECONDARY, "display_text": ""},
}
BIF_NEWDIALOGSTYLE = 0x00000040
BIF_USENEWUI = shellcon.BIF_EDITBOX | BIF_NEWDIALOGSTYLE
BFFM_INITIALIZED = 1
BFFM_SETSELECTIONW = 1127
LAZY_RUNTIME_IMPORT_SPECS = {
    "pdf2docx": {
        "probe": "pdf2docx",
        "symbols": {
            "Converter": ("pdf2docx", "Converter"),
        },
    },
    "moviepy": {
        "probe": "moviepy",
        "symbols": {},
    },
    "moviepy.editor": {
        "probe": "moviepy",
        "fallback_modules": ["moviepy"],
        "symbols": {
            "AudioFileClip": ("moviepy", "AudioFileClip"),
            "VideoFileClip": ("moviepy", "VideoFileClip"),
        },
    },
}


def _debug(message):
    try:
        with DEBUG_LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"{message}\n")
    except Exception:
        pass


def _wrap_callable(owner, name, label=None):
    try:
        original = getattr(owner, name)
    except Exception:
        return
    if not callable(original):
        return
    if getattr(original, "__fx_wrapped__", False):
        return

    def wrapped(*args, **kwargs):
        tag = label or name
        _debug(f"{tag}:start")
        try:
            result = original(*args, **kwargs)
            _debug(f"{tag}:done")
            return result
        except Exception as exc:
            _debug(f"{tag}:error:{exc}")
            raise

    wrapped.__fx_wrapped__ = True
    setattr(owner, name, wrapped)


def _draw_sidebar_icon(draw, kind, color, size=22, stroke=2):
    c = color
    viewport = 24.0
    scale = max(0.5, float(size) / viewport)
    stroke_px = max(1, int(round(stroke * scale * 0.88)))
    thin_stroke_px = max(1, int(round(stroke_px * 0.72)))

    def pt(x, y):
        return (x * scale, y * scale)

    def path(points):
        return [pt(x, y) for x, y in points]

    def line(points, width=None):
        draw.line(path(points), fill=c, width=width or stroke_px, joint="curve")

    def polygon(points, closed=True, fill=None, outline=True, width=None):
        pts = path(points)
        if fill is not None:
            draw.polygon(pts, fill=fill)
        if outline:
            outline_path = pts + ([pts[0]] if closed else [])
            draw.line(outline_path, fill=c, width=width or stroke_px, joint="curve")

    def ellipse(x1, y1, x2, y2, width=None, fill=None):
        draw.ellipse(
            (x1 * scale, y1 * scale, x2 * scale, y2 * scale),
            outline=c if width else None,
            width=width or stroke_px,
            fill=fill,
        )

    def rounded_rect(x1, y1, x2, y2, radius, width=None):
        draw.rounded_rectangle(
            (x1 * scale, y1 * scale, x2 * scale, y2 * scale),
            radius=radius * scale,
            outline=c,
            width=width or stroke_px,
        )

    if kind == "shield":
        outer = [(12.0, 3.0), (17.1, 5.2), (16.6, 11.0), (12.0, 18.5), (7.4, 11.0), (6.9, 5.2)]
        inner = [(12.0, 5.0), (15.3, 6.4), (15.0, 10.0), (12.0, 15.0), (9.0, 10.0), (8.7, 6.4)]
        polygon(outer, fill=(243, 247, 252, 255), outline=False)
        polygon(inner, fill=(86, 136, 210, 255), outline=False)
    elif kind == "eraser":
        polygon([(7.1, 14.2), (11.7, 9.6), (16.9, 14.8), (12.3, 19.4)], width=stroke_px)
        polygon([(11.7, 9.6), (13.9, 7.4), (19.1, 12.6), (16.9, 14.8)], width=stroke_px)
        line([(9.3, 16.4), (14.5, 11.2)], width=thin_stroke_px)
        line([(12.0, 19.0), (17.2, 13.8)], width=thin_stroke_px)
        line([(14.1, 8.3), (18.2, 12.4)], width=thin_stroke_px)
    elif kind == "swap":
        line([(5.8, 8.1), (17.0, 8.1)])
        polygon([(18.2, 8.1), (14.9, 5.6), (14.9, 10.6)], fill=c, outline=False)
        line([(18.2, 15.9), (7.0, 15.9)])
        polygon([(5.8, 15.9), (9.1, 13.4), (9.1, 18.4)], fill=c, outline=False)
    elif kind == "music":
        draw.ellipse((4.8 * scale, 11.0 * scale, 11.9 * scale, 18.1 * scale), fill=c)
        draw.ellipse((12.1 * scale, 11.0 * scale, 19.2 * scale, 18.1 * scale), fill=c)
        draw.rounded_rectangle(
            (9.6 * scale, 4.0 * scale, 12.4 * scale, 14.4 * scale),
            radius=1.1 * scale,
            fill=c,
        )
        draw.rounded_rectangle(
            (15.9 * scale, 4.0 * scale, 18.7 * scale, 14.4 * scale),
            radius=1.1 * scale,
            fill=c,
        )
        draw.rounded_rectangle(
            (9.6 * scale, 4.0 * scale, 18.7 * scale, 6.8 * scale),
            radius=1.1 * scale,
            fill=c,
        )
        draw.rounded_rectangle(
            (10.4 * scale, 8.4 * scale, 17.9 * scale, 10.4 * scale),
            radius=0.8 * scale,
            fill=c,
        )
    elif kind == "box":
        polygon([(12.0, 4.2), (17.6, 7.2), (12.0, 10.3), (6.4, 7.2)])
        line([(6.4, 7.2), (6.4, 15.5), (12.0, 18.7), (12.0, 10.3)])
        line([(17.6, 7.2), (17.6, 15.5), (12.0, 18.7)])
        line([(12.0, 10.3), (12.0, 18.7)], width=thin_stroke_px)
    elif kind == "document":
        rounded_rect(5.9, 3.7, 17.7, 19.1, radius=1.8)
        line([(12.8, 3.8), (12.8, 8.1), (17.4, 8.1)])
        line([(12.8, 3.8), (17.4, 8.1)])
        line([(8.4, 11.1), (14.7, 11.1)], width=thin_stroke_px)
        line([(8.4, 14.2), (14.7, 14.2)], width=thin_stroke_px)
    elif kind == "image":
        rounded_rect(5.0, 5.5, 19.0, 17.4, radius=1.2)
        ellipse(7.0, 7.6, 9.9, 10.5, width=thin_stroke_px)
        line([(6.8, 14.9), (10.0, 11.8), (12.7, 14.0), (14.2, 12.3), (17.0, 15.0)])
    elif kind == "lock":
        rounded_rect(5.8, 10.7, 18.2, 19.0, radius=1.8)
        draw.arc(
            (7.6 * scale, 4.0 * scale, 16.4 * scale, 13.5 * scale),
            start=200,
            end=340,
            fill=c,
            width=stroke_px,
        )
        ellipse(11.0, 13.1, 12.8, 14.9, width=thin_stroke_px)
        line([(11.9, 14.8), (11.9, 16.6)], width=thin_stroke_px)
    elif kind == "folder":
        line([(4.9, 8.5), (9.0, 8.5), (10.9, 6.7), (18.7, 6.7)])
        rounded_rect(4.9, 8.5, 18.9, 17.8, radius=1.5)
    elif kind == "settings":
        ellipse(8.0, 8.0, 16.0, 16.0, width=stroke_px)
        ellipse(10.5, 10.5, 13.5, 13.5, width=thin_stroke_px)
        for x1, y1, x2, y2 in (
            (12.0, 3.6, 12.0, 5.5),
            (12.0, 18.5, 12.0, 20.4),
            (3.6, 12.0, 5.5, 12.0),
            (18.5, 12.0, 20.4, 12.0),
            (6.1, 6.1, 7.5, 7.5),
            (16.5, 16.5, 17.9, 17.9),
            (16.5, 7.5, 17.9, 6.1),
            (6.1, 17.9, 7.5, 16.5),
        ):
            line([(x1, y1), (x2, y2)], width=thin_stroke_px)
    elif kind == "book":
        line([(12.0, 5.2), (12.0, 18.6)], width=thin_stroke_px)
        line([(6.4, 6.2), (10.9, 5.5), (10.9, 17.9), (6.4, 17.1), (6.4, 6.2)])
        line([(17.6, 6.2), (13.1, 5.5), (13.1, 17.9), (17.6, 17.1), (17.6, 6.2)])
    elif kind == "coffee":
        rounded_rect(5.9, 10.3, 15.8, 16.2, radius=1.6)
        draw.arc(
            (13.4 * scale, 10.8 * scale, 18.3 * scale, 15.5 * scale),
            start=270,
            end=90,
            fill=c,
            width=stroke_px,
        )
        line([(6.3, 18.2), (16.2, 18.2)], width=thin_stroke_px)
        draw.arc(
            (7.5 * scale, 4.6 * scale, 9.5 * scale, 8.4 * scale),
            start=195,
            end=355,
            fill=c,
            width=thin_stroke_px,
        )
        draw.arc(
            (10.8 * scale, 3.8 * scale, 12.8 * scale, 7.6 * scale),
            start=195,
            end=355,
            fill=c,
            width=thin_stroke_px,
        )
    else:
        ellipse(5.5, 5.5, 18.5, 18.5, width=stroke_px)


def _build_sidebar_icon_image(kind, color, size=22):
    render_scale = 4
    render_size = max(size * render_scale, 64)
    canvas = PILImage.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    _draw_sidebar_icon(draw, kind, color, size=render_size, stroke=2)
    final_canvas = canvas.resize((size, size), PILImage.Resampling.LANCZOS)
    return customtkinter.CTkImage(light_image=final_canvas, dark_image=final_canvas, size=(size, size))


def _get_sidebar_icon_images(app):
    cache = getattr(app, "_fx_sidebar_icon_images", None)
    if cache is not None:
        return cache

    cache = {}
    for spec in SIDEBAR_BUTTON_SPECS.values():
        key = ("nav", spec["icon"])
        if key not in cache:
            cache[key] = _build_sidebar_icon_image(spec["icon"], SIDEBAR_ICON_NAV)
    help_spec = SIDEBAR_AUX_BUTTON_SPECS["btn_help_proxy"]
    donate_spec = SIDEBAR_AUX_BUTTON_SPECS["btn_donate"]
    cache[("help", help_spec["icon"])] = _build_sidebar_icon_image(help_spec["icon"], SIDEBAR_ICON_HELP)
    cache[("donate", donate_spec["icon"])] = _build_sidebar_icon_image(donate_spec["icon"], SIDEBAR_ICON_DONATE)
    app._fx_sidebar_icon_images = cache
    return cache


def _get_sidebar_brand_image(app):
    image = getattr(app, "_fx_sidebar_brand_image", None)
    if image is not None:
        return image

    png_path = _resolve_app_asset(APP_ICON_PNG)
    if not png_path.exists():
        return None

    try:
        brand_image = PILImage.open(png_path).convert("RGBA")
        image = customtkinter.CTkImage(
            light_image=brand_image,
            dark_image=brand_image,
            size=(44, 44),
        )
        app._fx_sidebar_brand_image = image
        return image
    except Exception as exc:
        _debug(f"sidebar_brand_image:error:{exc}")
        return None


def _get_inline_title_icon_image(app, kind, color, size):
    cache = getattr(app, "_fx_inline_title_icon_images", None)
    if cache is None:
        cache = {}
        app._fx_inline_title_icon_images = cache

    cache_key = (kind, color, size)
    image = cache.get(cache_key)
    if image is None:
        image = _build_sidebar_icon_image(kind, color, size=size)
        cache[cache_key] = image
    return image


def _ensure_inline_help_tab(app):
    help_tab = getattr(app, "tab_help", None)
    if help_tab is not None:
        return help_tab
    try:
        help_tab = app.main_panel.add(HELP_TAB_TITLE)
    except Exception:
        help_tab = app.main_panel.tab(HELP_TAB_TITLE)
    app.tab_help = help_tab
    _build_inline_help_page(app, help_tab)
    return help_tab


def _build_inline_help_page(app, help_tab):
    if getattr(help_tab, "_fx_help_page_built", False):
        return
    try:
        help_tab.grid_rowconfigure(0, weight=1)
        help_tab.grid_columnconfigure(0, weight=1)
    except Exception:
        pass

    card = customtkinter.CTkFrame(
        help_tab,
        fg_color=globals().get("COLOR_CARD", "#2B2B2B"),
        corner_radius=18,
        border_width=1,
        border_color=globals().get("COLOR_BORDER", "#3A3A3A"),
    )
    card.grid(row=0, column=0, sticky="nsew", padx=20, pady=18)
    card.grid_rowconfigure(1, weight=1)
    card.grid_columnconfigure(0, weight=1)

    header = customtkinter.CTkFrame(card, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=28, pady=(22, 10))
    header.grid_columnconfigure(1, weight=1)

    icon = _get_inline_title_icon_image(app, "book", CONTENT_ICON_PRIMARY, 24)
    customtkinter.CTkLabel(
        header,
        text="使用教程",
        image=icon,
        compound="left",
        anchor="w",
        font=customtkinter.CTkFont(family="Microsoft YaHei UI", size=22, weight="bold"),
        text_color=globals().get("COLOR_TEXT", "#E6EEF2"),
    ).grid(row=0, column=0, sticky="w")
    customtkinter.CTkLabel(
        header,
        text="内置说明随功能同步更新，内容较多时可向下滚动查看。",
        anchor="e",
        font=customtkinter.CTkFont(family="Microsoft YaHei UI", size=12),
        text_color=globals().get("COLOR_TEXT_SOFT", "#B2C0C8"),
    ).grid(row=0, column=1, sticky="e", padx=(18, 0))

    scroll = customtkinter.CTkScrollableFrame(
        card,
        fg_color=globals().get("COLOR_CARD_ALT", "#303030"),
        corner_radius=14,
        border_width=1,
        border_color=globals().get("COLOR_BORDER", "#3A3A3A"),
    )
    scroll.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))
    scroll.grid_columnconfigure(0, weight=1)

    for section_index, (title, lines) in enumerate(INLINE_HELP_SECTIONS):
        section = customtkinter.CTkFrame(scroll, fg_color="transparent")
        section.grid(row=section_index, column=0, sticky="ew", padx=18, pady=(16 if section_index else 18, 2))
        section.grid_columnconfigure(0, weight=1)
        customtkinter.CTkLabel(
            section,
            text=title,
            anchor="w",
            font=customtkinter.CTkFont(family="Microsoft YaHei UI", size=16, weight="bold"),
            text_color=globals().get("COLOR_TEXT", "#E6EEF2"),
        ).grid(row=0, column=0, sticky="ew")
        body_text = "\n".join(f"• {line}" for line in lines)
        customtkinter.CTkLabel(
            section,
            text=body_text,
            anchor="w",
            justify="left",
            wraplength=920,
            font=customtkinter.CTkFont(family="Microsoft YaHei UI", size=13),
            text_color=globals().get("COLOR_TEXT_SOFT", "#B2C0C8"),
        ).grid(row=1, column=0, sticky="ew", pady=(6, 0))

    help_tab._fx_help_page_built = True


def _set_help_button_selected(app, selected):
    btn = getattr(app, "btn_help_proxy", None)
    if btn is None:
        return
    try:
        if selected:
            btn.configure(
                text_color=globals().get("COLOR_TEXT", "#E6EEF2"),
                fg_color=SIDEBAR_AUX_STYLES["help"]["hover_color"],
                border_color=globals().get("COLOR_BORDER", "#566274"),
            )
        else:
            _style_sidebar_aux_button(
                btn,
                SIDEBAR_AUX_BUTTON_SPECS["btn_help_proxy"]["label"],
                _get_sidebar_icon_images(app).get(("help", SIDEBAR_AUX_BUTTON_SPECS["btn_help_proxy"]["icon"])),
                _get_sidebar_button_font(app),
                "help",
            )
    except Exception:
        pass


def _set_help_action_state(app, visible):
    if getattr(app, "is_running", False):
        return
    btn_run = getattr(app, "btn_run", None)
    btn_stop = getattr(app, "btn_stop", None)
    if btn_run is not None:
        try:
            if visible:
                btn_run.configure(state="disabled", text="查看使用说明中", fg_color="#455A64")
            else:
                btn_run.configure(
                    state="normal",
                    text="🚀 立即开始处理",
                    fg_color=globals().get("COLOR_ACCENT", "#8FA9B8"),
                )
        except Exception:
            pass
    if btn_stop is not None and visible:
        try:
            btn_stop.configure(state="disabled")
        except Exception:
            pass


def _show_inline_help(app):
    try:
        _ensure_inline_help_tab(app)
        app.main_panel.set(HELP_TAB_TITLE)
        app.current_task = "help"
        _set_help_button_selected(app, True)
        _set_help_action_state(app, True)
        for nav_name in (
            "btn_nav_wm",
            "btn_nav_rm_wm",
            "btn_nav_cv",
            "btn_nav_audio",
            "btn_nav_zip",
            "btn_nav_pdf",
            "btn_nav_img",
            "btn_nav_meta",
            "btn_nav_file",
        ):
            nav = getattr(app, nav_name, None)
            if nav is not None:
                nav.configure(
                    text_color=globals().get("COLOR_TEXT_SOFT", "#B2C0C8"),
                    fg_color="transparent",
                    border_color=globals().get("COLOR_SIDEBAR", "#202020"),
                )
        app.update_idletasks()
    except Exception as exc:
        _debug(f"inline_help:show_error:{exc}")


def _normalize_icon_title_text(text):
    text = str(text or "").strip()
    if not text:
        return ""
    while text:
        first = text[0]
        if first == "[" or first.isalnum() or ("\u4e00" <= first <= "\u9fff"):
            break
        text = text[1:].lstrip()
    return text


def _resolve_inline_title_spec(raw_text):
    raw_text = str(raw_text or "")
    for canonical_text in sorted(INLINE_TITLE_ICON_SPECS, key=len, reverse=True):
        if canonical_text in raw_text:
            return canonical_text, INLINE_TITLE_ICON_SPECS[canonical_text]

    canonical_text = _normalize_icon_title_text(raw_text)
    spec = INLINE_TITLE_ICON_SPECS.get(canonical_text)
    if spec is None:
        return "", None
    return canonical_text, spec


def _apply_inline_title_icons(app, root_widget):
    if root_widget is None:
        return

    pending = [root_widget]
    while pending:
        widget = pending.pop(0)
        try:
            pending.extend(widget.winfo_children())
        except Exception:
            pass

        if not isinstance(widget, customtkinter.CTkLabel):
            continue
        try:
            raw_text = widget.cget("text")
        except Exception:
            continue

        canonical_text, spec = _resolve_inline_title_spec(raw_text)
        if spec is None:
            continue

        signature = (
            canonical_text,
            spec["icon"],
            spec["size"],
            spec["color"],
            spec.get("display_text", canonical_text),
        )
        if getattr(widget, "_fx_inline_title_icon_signature", None) == signature:
            continue

        display_text = spec.get("display_text", canonical_text)
        try:
            widget.configure(
                text=display_text,
                image=_get_inline_title_icon_image(app, spec["icon"], spec["color"], spec["size"]),
                compound="left",
                anchor="w",
            )
            widget._fx_inline_title_icon_signature = signature
        except Exception:
            pass


def _normalize_input_path_value(value):
    text = _coerce_input_path_text(value).strip().strip('"')
    if not text:
        return ""
    return os.path.abspath(os.path.normpath(text))


def _sanitize_filename_component(value, fallback="task_result"):
    text = str(value or "").strip()
    if not text:
        return fallback
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r'[<>:"/\\\\|?*\x00-\x1f]+', "_", text)
    text = re.sub(r"\s+", "_", text).strip(" ._")
    return text or fallback


def _decode_input_path_bytes(raw):
    candidates = []
    for encoding in ("utf-8", "mbcs", "gbk", sys.getfilesystemencoding()):
        if encoding and encoding not in candidates:
            candidates.append(encoding)
    for encoding in candidates:
        try:
            return raw.decode(encoding)
        except Exception:
            continue
    return raw.decode("utf-8", errors="replace")


def _coerce_input_path_text(value):
    if value is None:
        return ""
    if isinstance(value, (bytes, bytearray)):
        return _decode_input_path_bytes(bytes(value))

    text = str(value).strip()
    if not text:
        return ""

    for marker in ("b'", 'b"', "B'", 'B"'):
        marker_index = text.find(marker)
        if marker_index < 0:
            continue
        literal_text = text[marker_index:]
        try:
            literal_value = ast.literal_eval(literal_text)
        except Exception:
            continue
        if isinstance(literal_value, (bytes, bytearray)):
            return _decode_input_path_bytes(bytes(literal_value))

    return text


class _LazyImportSymbol:
    def __init__(self, module_name, attr_name):
        self._module_name = module_name
        self._attr_name = attr_name
        self._resolved = None

    def _resolve(self):
        if self._resolved is None:
            module = _resolve_lazy_runtime_module(self._module_name)
            self._resolved = getattr(module, self._attr_name)
        return self._resolved

    def __call__(self, *args, **kwargs):
        return self._resolve()(*args, **kwargs)

    def __getattr__(self, item):
        return getattr(self._resolve(), item)

    def __repr__(self):
        return f"<lazy import {self._module_name}.{self._attr_name}>"


class _LazyImportModule(types.ModuleType):
    def __init__(self, module_name):
        super().__init__(module_name)
        self.__dict__["_fx_lazy_module_name"] = module_name
        self.__dict__["__package__"] = module_name.rpartition(".")[0]
        if "." not in module_name:
            self.__dict__["__path__"] = []

    def _resolve(self):
        return _resolve_lazy_runtime_module(self._fx_lazy_module_name)

    def __getattr__(self, item):
        return getattr(self._resolve(), item)


def _has_lazy_runtime_module(module_name):
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False


def _is_lazy_runtime_proxy(module_obj, module_name):
    return getattr(module_obj, "_fx_lazy_module_name", None) == module_name


def _resolve_lazy_runtime_module(module_name):
    cache = globals().setdefault("_fx_lazy_runtime_cache", {})
    if module_name in cache:
        return cache[module_name]

    removed = {}
    for name in LAZY_RUNTIME_IMPORT_SPECS:
        if name == module_name or name.startswith(module_name + ".") or module_name.startswith(name + "."):
            module_obj = sys.modules.get(name)
            if _is_lazy_runtime_proxy(module_obj, name):
                removed[name] = sys.modules.pop(name)

    spec = LAZY_RUNTIME_IMPORT_SPECS.get(module_name, {})
    candidate_names = [module_name]
    for fallback_name in spec.get("fallback_modules", ()):
        if fallback_name and fallback_name not in candidate_names:
            candidate_names.append(fallback_name)

    last_exc = None
    resolved_name = module_name
    module = None
    for candidate_name in candidate_names:
        try:
            module = importlib.import_module(candidate_name)
            resolved_name = candidate_name
            break
        except Exception as exc:
            last_exc = exc
    if module is None:
        for name, module_obj in removed.items():
            if name not in sys.modules:
                sys.modules[name] = module_obj
        raise last_exc

    if resolved_name != module_name:
        _debug(f"lazy_runtime_imports:fallback:{module_name}->{resolved_name}")

    cache[module_name] = module
    cache[resolved_name] = module
    return module


def _install_runtime_lazy_imports():
    previous = {}
    installed = {}

    for module_name, spec in LAZY_RUNTIME_IMPORT_SPECS.items():
        probe_name = spec.get("probe", module_name)
        if not _has_lazy_runtime_module(probe_name):
            continue
        proxy = _LazyImportModule(module_name)
        for attr_name, target in spec.get("symbols", {}).items():
            target_module, target_attr = target
            setattr(proxy, attr_name, _LazyImportSymbol(target_module, target_attr))
        installed[module_name] = proxy

    moviepy_proxy = installed.get("moviepy")
    moviepy_editor_proxy = installed.get("moviepy.editor")
    if moviepy_proxy is not None and moviepy_editor_proxy is not None:
        moviepy_proxy.editor = moviepy_editor_proxy

    for module_name, proxy in installed.items():
        if module_name in sys.modules:
            continue
        previous[module_name] = None
        sys.modules[module_name] = proxy

    if previous:
        _debug(f"lazy_runtime_imports:installed:{','.join(sorted(previous))}")
    return previous


def _restore_runtime_lazy_imports(previous):
    if not previous:
        return
    for module_name, prior in previous.items():
        current = sys.modules.get(module_name)
        if prior is None:
            if _is_lazy_runtime_proxy(current, module_name):
                sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = prior
    _debug("lazy_runtime_imports:restored")


class _UnifiedInputPathPicker:
    def __init__(self, parent, initial_path=""):
        self.parent = parent
        self.result = ""
        self.current_dir = self._resolve_initial_dir(initial_path)
        self.path_var = tkinter.StringVar(value=self.current_dir)
        self.status_var = tkinter.StringVar(value="可直接双击文件确认，或选择文件夹后点确定。")
        self._item_paths = {}

        self.window = customtkinter.CTkToplevel(parent)
        _apply_window_icon(self.window)
        self.window.title("选择文件或文件夹")
        self.window.geometry("860x560")
        self.window.minsize(760, 480)
        self.window.transient(parent)
        self.window.protocol("WM_DELETE_WINDOW", self._cancel)
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)

        card = customtkinter.CTkFrame(self.window, corner_radius=16)
        card.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        toolbar = customtkinter.CTkFrame(card, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        toolbar.grid_columnconfigure(0, weight=1)

        self.path_entry = customtkinter.CTkEntry(toolbar, textvariable=self.path_var, height=38)
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        customtkinter.CTkButton(toolbar, text="打开", width=72, height=38, command=self._open_typed_path).grid(
            row=0, column=1, padx=(0, 8)
        )
        customtkinter.CTkButton(toolbar, text="上一级", width=84, height=38, command=self._go_up).grid(
            row=0, column=2, padx=(0, 8)
        )
        customtkinter.CTkButton(toolbar, text="刷新", width=72, height=38, command=self._refresh_entries).grid(
            row=0, column=3
        )

        body = tkinter.Frame(card)
        body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 10))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.tree = tkinter.ttk.Treeview(body, columns=("kind", "size"), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="名称")
        self.tree.heading("kind", text="类型")
        self.tree.heading("size", text="大小")
        self.tree.column("#0", width=460, anchor="w")
        self.tree.column("kind", width=100, anchor="center")
        self.tree.column("size", width=120, anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = tkinter.ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        customtkinter.CTkLabel(card, textvariable=self.status_var, anchor="w", justify="left").grid(
            row=2, column=0, sticky="ew", padx=18, pady=(0, 10)
        )

        actions = customtkinter.CTkFrame(card, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 18))
        actions.grid_columnconfigure(0, weight=1)

        customtkinter.CTkButton(
            actions,
            text="选择当前文件夹",
            width=130,
            height=38,
            command=self._choose_current_directory,
        ).grid(row=0, column=0, sticky="w")
        customtkinter.CTkButton(actions, text="确定", width=88, height=38, command=self._confirm_selection).grid(
            row=0, column=1, padx=(8, 8)
        )
        customtkinter.CTkButton(actions, text="取消", width=88, height=38, command=self._cancel).grid(
            row=0, column=2
        )

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Return>", self._on_tree_double_click)
        self.path_entry.bind("<Return>", lambda _event: self._open_typed_path())

        self._center_on_parent()
        self._refresh_entries()

    def _resolve_initial_dir(self, initial_path):
        normalized = _normalize_input_path_value(initial_path)
        if normalized and os.path.isfile(normalized):
            return os.path.dirname(normalized)
        if normalized and os.path.isdir(normalized):
            return normalized
        home_dir = _normalize_input_path_value(os.path.expanduser("~"))
        return home_dir if os.path.isdir(home_dir) else os.getcwd()

    def _center_on_parent(self):
        try:
            self.parent.update_idletasks()
            self.window.update_idletasks()
            width = 860
            height = 560
            x = max(self.parent.winfo_rootx() + (self.parent.winfo_width() - width) // 2, 80)
            y = max(self.parent.winfo_rooty() + (self.parent.winfo_height() - height) // 2, 60)
            self.window.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass

    def _format_size(self, size):
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        if size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        return f"{size / (1024 * 1024 * 1024):.1f} GB"

    def _refresh_entries(self):
        target_dir = _normalize_input_path_value(self.path_var.get()) or self.current_dir
        if not os.path.isdir(target_dir):
            self.status_var.set("当前路径不是文件夹，请输入有效路径后再打开。")
            return

        try:
            entries = sorted(os.scandir(target_dir), key=lambda entry: (not entry.is_dir(), entry.name.lower()))
        except Exception as exc:
            self.status_var.set(f"无法读取目录: {exc}")
            return

        self.current_dir = target_dir
        self.path_var.set(target_dir)
        self.tree.delete(*self.tree.get_children())
        self._item_paths = {}

        for index, entry in enumerate(entries):
            item_id = f"item_{index}"
            item_path = os.path.abspath(entry.path)
            item_kind = "文件夹" if entry.is_dir() else "文件"
            item_size = ""
            if entry.is_file():
                try:
                    item_size = self._format_size(entry.stat().st_size)
                except Exception:
                    item_size = "-"
            self.tree.insert("", "end", iid=item_id, text=entry.name, values=(item_kind, item_size))
            self._item_paths[item_id] = item_path

        self.status_var.set(f"当前目录: {target_dir} | 共 {len(entries)} 项，可直接选择文件或文件夹。")

    def _get_selected_path(self):
        selection = self.tree.selection()
        if not selection:
            return ""
        return self._item_paths.get(selection[0], "")

    def _on_tree_select(self, _event=None):
        selected_path = self._get_selected_path()
        if not selected_path:
            self.status_var.set(f"当前目录: {self.current_dir} | 可双击文件确认，双击文件夹进入。")
            return
        selected_type = "文件夹" if os.path.isdir(selected_path) else "文件"
        self.status_var.set(f"已选中{selected_type}: {selected_path}")

    def _on_tree_double_click(self, _event=None):
        selected_path = self._get_selected_path()
        if not selected_path:
            return
        if os.path.isdir(selected_path):
            self.path_var.set(selected_path)
            self._refresh_entries()
            return
        self._finish(selected_path)

    def _open_typed_path(self):
        typed_path = _normalize_input_path_value(self.path_var.get())
        if not typed_path:
            tkinter.messagebox.showwarning("提示", "请输入文件或文件夹路径。", parent=self.window)
            return
        if os.path.isdir(typed_path):
            self.path_var.set(typed_path)
            self._refresh_entries()
            return
        if os.path.isfile(typed_path):
            self._finish(typed_path)
            return
        tkinter.messagebox.showwarning("提示", "路径不存在，请重新输入。", parent=self.window)

    def _go_up(self):
        current = _normalize_input_path_value(self.current_dir)
        if not current:
            return
        parent_dir = os.path.dirname(current.rstrip("\\/")) or current
        if not os.path.isdir(parent_dir):
            parent_dir = current
        self.path_var.set(parent_dir)
        self._refresh_entries()

    def _choose_current_directory(self):
        self._finish(self.current_dir)

    def _confirm_selection(self):
        selected_path = self._get_selected_path()
        if not selected_path:
            tkinter.messagebox.showwarning(
                "提示",
                "请先选择一个文件或文件夹，或使用“选择当前文件夹”。",
                parent=self.window,
            )
            return
        self._finish(selected_path)

    def _finish(self, path):
        self.result = _normalize_input_path_value(path)
        try:
            self.window.grab_release()
        except Exception:
            pass
        self.window.destroy()

    def _cancel(self):
        self.result = ""
        try:
            self.window.grab_release()
        except Exception:
            pass
        self.window.destroy()

    def show(self):
        try:
            self.window.lift()
            self.window.attributes("-topmost", True)
            self.window.after(150, lambda: self.window.attributes("-topmost", False))
        except Exception:
            pass
        try:
            self.window.grab_set()
        except Exception:
            pass
        self.path_entry.focus_set()
        self.parent.wait_window(self.window)
        return self.result


def _choose_input_path_via_shell_dialog(app, initial_dir=""):
    normalized_initial = _normalize_input_path_value(initial_dir)
    if normalized_initial and os.path.isfile(normalized_initial):
        normalized_initial = os.path.dirname(normalized_initial)
    if normalized_initial and not os.path.isdir(normalized_initial):
        normalized_initial = ""

    def _browse_callback(hwnd, msg, lparam, lpdata):
        if msg == BFFM_INITIALIZED and lpdata:
            try:
                win32gui.SendMessage(hwnd, BFFM_SETSELECTIONW, 1, lpdata)
            except Exception as exc:
                _debug(f"shell_picker:set_selection_error:{exc}")
        return 0

    try:
        app.update_idletasks()
    except Exception:
        pass

    try:
        owner_hwnd = int(app.winfo_id())
    except Exception:
        owner_hwnd = 0

    flags = BIF_USENEWUI | shellcon.BIF_BROWSEINCLUDEFILES | shellcon.BIF_VALIDATE
    try:
        result = shell.SHBrowseForFolder(
            owner_hwnd,
            None,
            "选择文件或文件夹",
            flags,
            _browse_callback,
            normalized_initial or None,
        )
    except Exception as exc:
        _debug(f"shell_picker:dialog_error:{exc}")
        return ""

    if not result:
        return ""

    pidl = result[0] if isinstance(result, (tuple, list)) else result
    if not pidl:
        return ""

    try:
        selected_path = shell.SHGetPathFromIDList(pidl)
    except Exception as exc:
        _debug(f"shell_picker:get_path_error:{exc}")
        return ""

    return _normalize_input_path_value(selected_path)


def _resolve_app_asset(name):
    try:
        base_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    except Exception:
        base_dir = Path(__file__).resolve().parent
    return base_dir / "assets" / name


def _apply_app_icon(app):
    ico_path = _resolve_app_asset(APP_ICON_ICO)
    png_path = _resolve_app_asset(APP_ICON_PNG)
    try:
        if ico_path.exists():
            app.iconbitmap(default=str(ico_path))
    except Exception as exc:
        _debug(f"app_icon:iconbitmap_error:{exc}")
    try:
        if png_path.exists():
            app._fx_window_icon = tkinter.PhotoImage(file=str(png_path))
            app.iconphoto(True, app._fx_window_icon)
    except Exception as exc:
        _debug(f"app_icon:iconphoto_error:{exc}")


def _apply_window_icon(window):
    try:
        if hasattr(window, "_fx_window_icon") and getattr(window, "_fx_window_icon", None) is not None:
            window.iconphoto(True, window._fx_window_icon)
            return
    except Exception:
        pass
    ico_path = _resolve_app_asset(APP_ICON_ICO)
    png_path = _resolve_app_asset(APP_ICON_PNG)
    try:
        if ico_path.exists():
            window.iconbitmap(default=str(ico_path))
    except Exception as exc:
        _debug(f"window_icon:iconbitmap_error:{exc}")
    try:
        if png_path.exists():
            window._fx_window_icon = tkinter.PhotoImage(file=str(png_path))
            window.iconphoto(True, window._fx_window_icon)
    except Exception as exc:
        _debug(f"window_icon:iconphoto_error:{exc}")


def _apply_release_identity(app):
    try:
        app.title(f"风兮文件批量处理工具箱 {APP_DISPLAY_VERSION}")
    except Exception as exc:
        _debug(f"release_identity:title_error:{exc}")


def _style_sidebar_aux_button(button, text, image, font, variant):
    palette = SIDEBAR_AUX_STYLES.get(variant, SIDEBAR_AUX_STYLES["help"])
    button.configure(
        text=text,
        image=image,
        compound="left",
        border_spacing=12,
        width=208,
        height=40,
        anchor="w",
        corner_radius=14,
        border_width=1,
        font=font,
        fg_color=palette["fg_color"],
        hover_color=palette["hover_color"],
        border_color=palette["border_color"],
        text_color=palette["text_color"],
    )


def _run_with_fast_sidebar_button_construction(app, build_callable):
    try:
        original_init = customtkinter.CTkButton.__init__
    except Exception:
        return build_callable()

    if getattr(app, "_fx_sidebar_fast_build_active", False):
        return build_callable()

    def patched_init(button_self, *args, **kwargs):
        master = args[0] if args else kwargs.get("master")
        sidebar_frame = getattr(app, "sidebar_frame", None)
        if master is sidebar_frame and isinstance(kwargs.get("text"), str):
            # Sidebar buttons are restyled before the window becomes visible,
            # so we can use cheaper placeholder text/font during construction.
            kwargs["text"] = ""
            kwargs["font"] = FAST_SIDEBAR_BUILD_FONT
        return original_init(button_self, *args, **kwargs)

    app._fx_sidebar_fast_build_active = True
    customtkinter.CTkButton.__init__ = patched_init
    try:
        return build_callable()
    finally:
        customtkinter.CTkButton.__init__ = original_init
        app._fx_sidebar_fast_build_active = False


def _get_sidebar_button_font(app):
    font = getattr(app, "_fx_sidebar_button_font", None)
    if font is None:
        font = customtkinter.CTkFont(family="Microsoft YaHei UI", size=14, weight="bold")
        app._fx_sidebar_button_font = font
    return font


def _apply_shell_layout_tightening(app):
    if getattr(app, "_fx_shell_layout_tightened", False):
        return

    shell_fill_color = globals().get("COLOR_CARD_ALT", "#303030")
    try:
        app.configure(fg_color=shell_fill_color)
    except Exception:
        pass

    app.sidebar_frame.configure(width=300)
    app.grid_columnconfigure(0, minsize=300, weight=0)

    app.top_bar.grid_configure(pady=(8, 0))
    app.main_panel.grid_configure(pady=(0, 0))
    app.bottom_bar.grid_configure(pady=(0, 8))
    try:
        app.main_panel.configure(fg_color=shell_fill_color)
    except Exception:
        pass

    app.top_bar.configure(height=92)
    app.btn_browse.configure(height=40, text="浏览文件/文件夹")
    app.entry_path.configure(height=40)
    for child in app.top_bar.winfo_children():
        if child is app.btn_browse:
            child.grid_configure(pady=(2, 8), padx=(0, 20))
        elif child is app.entry_path:
            child.grid_configure(pady=(2, 8), padx=(24, 16))
        else:
            child.grid_configure(pady=(6, 0), padx=24)

    app.bottom_bar.configure(height=228)
    try:
        app.bottom_bar.grid_propagate(False)
        app.bottom_bar.grid_rowconfigure(2, weight=0, minsize=128)
    except Exception:
        pass
    for child in app.bottom_bar.winfo_children():
        if child is app.progress_bar:
            child.grid_configure(pady=(10, 8), padx=24)
        elif child is app.log_box:
            try:
                child.configure(height=128)
            except Exception:
                pass
            child.grid_configure(pady=(6, 8), padx=30, sticky="ew")
        else:
            try:
                child.configure(height=42)
            except Exception:
                pass
            for action_child in child.winfo_children():
                try:
                    if isinstance(action_child, customtkinter.CTkButton):
                        action_child.configure(height=40)
                    elif isinstance(action_child, customtkinter.CTkSwitch):
                        action_child.configure(height=28)
                except Exception:
                    pass
            child.grid_configure(padx=30, pady=0, sticky="ew")

    sidebar_children = app.sidebar_frame.winfo_children()
    if sidebar_children:
        try:
            sidebar_children[0].grid_configure(padx=14, pady=(14, 8), sticky="ew")
        except Exception:
            pass
        try:
            header_children = sidebar_children[0].winfo_children()
            if len(header_children) >= 3:
                brand_image = _get_sidebar_brand_image(app)
                if brand_image is not None:
                    try:
                        header_children[0].configure(text="", image=brand_image, compound="center")
                    except Exception:
                        pass
                header_children[0].grid_configure(padx=(12, 10), pady=14, sticky="w")
                try:
                    header_children[1].configure(font=customtkinter.CTkFont(family="Microsoft YaHei UI", size=17, weight="bold"))
                except Exception:
                    pass
                header_children[1].grid_configure(padx=(0, 14), pady=(12, 2), sticky="sw")
                header_children[2].grid_configure(padx=(0, 14), pady=(0, 8), sticky="nw")
        except Exception:
            pass

    sidebar_icon_images = _get_sidebar_icon_images(app)
    sidebar_button_font = _get_sidebar_button_font(app)
    for nav_name in (
        "btn_nav_wm",
        "btn_nav_rm_wm",
        "btn_nav_cv",
        "btn_nav_audio",
        "btn_nav_zip",
        "btn_nav_pdf",
        "btn_nav_img",
        "btn_nav_meta",
        "btn_nav_file",
    ):
        nav = getattr(app, nav_name, None)
        if nav is not None:
            try:
                nav_spec = SIDEBAR_BUTTON_SPECS.get(nav_name, {})
                nav.configure(
                    text=nav_spec.get("label", nav.cget("text")),
                    image=sidebar_icon_images.get(("nav", nav_spec.get("icon"))),
                    compound="left",
                    border_spacing=12,
                    font=sidebar_button_font,
                    height=40,
                    anchor="w",
                )
                nav.grid_configure(padx=12, pady=3, sticky="ew")
            except Exception:
                pass

    if getattr(app, "btn_help", None) is not None:
        try:
            app.btn_help.grid_remove()
        except Exception:
            pass
        if getattr(app, "btn_help_proxy", None) is None:
            app.btn_help_proxy = customtkinter.CTkButton(
                app.sidebar_frame,
                command=lambda target=app: _show_inline_help(target),
            )
        else:
            app.btn_help_proxy.configure(command=lambda target=app: _show_inline_help(target))
        _style_sidebar_aux_button(
            app.btn_help_proxy,
            SIDEBAR_AUX_BUTTON_SPECS["btn_help_proxy"]["label"],
            sidebar_icon_images.get(("help", SIDEBAR_AUX_BUTTON_SPECS["btn_help_proxy"]["icon"])),
            sidebar_button_font,
            "help",
        )
        app.sidebar_frame.grid_rowconfigure(10, minsize=0, weight=0)
        app.btn_help_proxy.grid(row=10, column=0, padx=12, pady=(7, 3), sticky="ew")
        app.sidebar_frame.grid_rowconfigure(11, minsize=0, weight=0)
    if getattr(app, "btn_donate", None) is not None:
        _style_sidebar_aux_button(
            app.btn_donate,
            SIDEBAR_AUX_BUTTON_SPECS["btn_donate"]["label"],
            sidebar_icon_images.get(("donate", SIDEBAR_AUX_BUTTON_SPECS["btn_donate"]["icon"])),
            sidebar_button_font,
            "donate",
        )
        app.btn_donate.grid_configure(row=11, padx=12, pady=(3, 7), sticky="ew")

    footer_candidates = app.sidebar_frame.winfo_children()
    if footer_candidates:
        app.sidebar_frame.grid_rowconfigure(12, minsize=0, weight=0)
        for footer in footer_candidates:
            if isinstance(footer, customtkinter.CTkLabel):
                try:
                    footer.grid_configure(row=12, padx=12, pady=(10, 8), sticky="ew")
                except Exception:
                    pass
                break

    app._fx_shell_layout_tightened = True


def _tighten_single_tab_layout(app, task_name):
    tab_attr = TAB_LAYOUT_ATTRS.get(task_name)
    if not tab_attr:
        return

    tab = getattr(app, tab_attr, None)
    if tab is None or getattr(tab, "_fx_layout_tightened", False):
        return

    children = tab.winfo_children()
    if children:
        try:
            children[0].pack_configure(padx=20, pady=18)
        except Exception:
            pass

    if task_name == "watermark" and children:
        _tighten_watermark_tab_layout(app, tab)

    if task_name == "pdf" and children:
        pdf_card = children[0]
        _tighten_pdf_tab_layout(pdf_card)

    if task_name == "meta" and children:
        meta_card = children[0]
        _tighten_meta_tab_layout(meta_card)

    if task_name == "zip":
        _patch_zip_tab_texts(tab)

    _apply_inline_title_icons(app, tab)

    tab._fx_layout_tightened = True


def _tighten_pdf_tab_layout(pdf_card):
    try:
        pdf_card.pack_configure(padx=18, pady=10)
    except Exception:
        pass

    pdf_sections = pdf_card.winfo_children()
    if len(pdf_sections) < 2:
        return

    try:
        pdf_sections[0].pack_configure(anchor="w", padx=24, pady=(16, 8))
    except Exception:
        pass
    try:
        pdf_sections[1].pack_configure(fill="both", expand=True, padx=24, pady=(0, 12))
    except Exception:
        pass

    content_sections = list(pdf_sections[1].winfo_children())
    if len(content_sections) == 1:
        try:
            nested_sections = list(content_sections[0].winfo_children())
        except Exception:
            nested_sections = []
        if len(nested_sections) >= 2:
            try:
                content_sections[0].pack_configure(fill="both", expand=True, padx=0, pady=0)
            except Exception:
                pass
            content_sections = nested_sections
    if len(content_sections) < 2:
        return

    base_panel, detail_shell = content_sections[0], content_sections[1]
    try:
        base_panel.configure(width=230)
        base_panel.pack_configure(side="left", fill="y", padx=(0, 10))
    except Exception:
        pass
    try:
        detail_shell.pack_configure(side="left", fill="both", expand=True, padx=0, pady=0)
    except Exception:
        pass

    base_children = list(base_panel.winfo_children())
    if base_children:
        try:
            base_children[0].pack_configure(anchor="w", pady=(0, 8))
        except Exception:
            pass

    shared_panel = None
    compact_button_font = customtkinter.CTkFont(size=11)
    for child in base_children[1:]:
        if isinstance(child, customtkinter.CTkButton):
            try:
                child.configure(height=40, font=compact_button_font)
                child.pack_configure(fill="x", pady=(0, 5))
            except Exception:
                pass
        else:
            shared_panel = child

    if shared_panel is not None:
        try:
            shared_panel.pack_configure(fill="x", pady=(4, 0))
        except Exception:
            pass
        shared_children = list(shared_panel.winfo_children())
        for index, child in enumerate(shared_children):
            try:
                if isinstance(child, customtkinter.CTkSwitch):
                    child.configure(height=24)
                    child.pack_configure(anchor="w", pady=(0, 6))
                elif isinstance(child, customtkinter.CTkLabel):
                    child.configure(font=customtkinter.CTkFont(size=10))
                    child.pack_configure(anchor="w", pady=(0, 2))
                elif isinstance(child, customtkinter.CTkEntry):
                    child.configure(height=30)
                    child.pack_configure(fill="x", pady=0)
                elif index == 0:
                    child.pack_configure(pady=(0, 6))
            except Exception:
                pass

    try:
        detail_children = list(detail_shell.winfo_children())
    except Exception:
        detail_children = []
    for panel in detail_children:
        try:
            for child in panel.winfo_children():
                if isinstance(child, customtkinter.CTkLabel):
                    try:
                        child.pack_configure(padx=6)
                    except Exception:
                        pass
        except Exception:
            pass


def _tighten_meta_tab_layout(meta_card):
    try:
        meta_card.pack_configure(padx=18, pady=10)
    except Exception:
        pass

    sections = meta_card.winfo_children()
    if len(sections) < 5:
        return

    try:
        sections[0].pack_configure(anchor="w", padx=24, pady=(8, 2))
    except Exception:
        pass

    spacer = sections[1]
    try:
        if not spacer.winfo_children():
            spacer.pack_forget()
        else:
            spacer.configure(height=8)
            spacer.pack_configure(fill="x", padx=24, pady=0)
    except Exception:
        pass

    try:
        sections[2].pack_configure(fill="x", padx=24, pady=(4, 4))
        for radio in sections[2].winfo_children():
            try:
                radio.configure(height=26)
            except Exception:
                pass
    except Exception:
        pass

    for section in sections[3:5]:
        try:
            section.configure(height=82)
            section.pack_propagate(False)
            section.pack_configure(fill="x", padx=24, pady=(0, 4))
            section_children = list(section.winfo_children())
            if len(section_children) >= 2:
                try:
                    section_children[0].pack_configure(anchor="w", pady=(0, 2))
                except Exception:
                    pass
                try:
                    section_children[1].configure(height=30)
                    section_children[1].pack_configure(fill="x", pady=0)
                except Exception:
                    pass
        except Exception:
            pass


def _patch_zip_tab_texts(tab):
    try:
        stack = list(tab.winfo_children())
    except Exception:
        stack = []
    while stack:
        widget = stack.pop()
        try:
            text_value = widget.cget("text")
        except Exception:
            text_value = None
        if isinstance(text_value, str):
            new_label = ZIP_MODE_LABEL_TEXTS.get(text_value)
            if new_label is not None and text_value != new_label:
                try:
                    widget.configure(text=new_label)
                except Exception:
                    pass
            elif text_value.startswith("功能说明：") and text_value != ZIP_MODE_DESCRIPTION_TEXT:
                try:
                    widget.configure(text=ZIP_MODE_DESCRIPTION_TEXT, justify="left")
                except Exception:
                    pass
        try:
            stack.extend(widget.winfo_children())
        except Exception:
            pass


def _refresh_visible_tab_layout(app, task_name):
    tab_attr = TAB_LAYOUT_ATTRS.get(task_name)
    if not tab_attr:
        return

    tab = getattr(app, tab_attr, None)
    if tab is None:
        return
    children = list(tab.winfo_children())
    if not children:
        return

    card = children[0]
    if task_name == "pdf":
        _tighten_pdf_tab_layout(card)
    elif task_name == "meta":
        _tighten_meta_tab_layout(card)
    elif task_name == "zip":
        _patch_zip_tab_texts(tab)
    _apply_inline_title_icons(app, tab)


def _tighten_watermark_tab_layout(app, tab):
    try:
        tab.grid_rowconfigure(0, weight=1, minsize=0)
        tab.grid_columnconfigure(0, weight=3, minsize=0)
        tab.grid_columnconfigure(1, weight=2, minsize=0)
    except Exception:
        pass

    panels = list(tab.winfo_children())
    if len(panels) < 2:
        return

    left_panel, right_panel = panels[0], panels[1]
    try:
        left_panel.grid_configure(row=0, column=0, padx=(0, 14), pady=0, sticky="nsew")
        right_panel.grid_configure(row=0, column=1, padx=0, pady=0, sticky="nsew")
        right_panel.grid_configure(padx=0, pady=0, sticky="nsew")
        left_panel.configure(height=520)
        right_panel.configure(height=520)
        left_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_rowconfigure(10, weight=1)
    except Exception:
        pass

    left_children = list(left_panel.winfo_children())
    if len(left_children) >= 2:
        try:
            left_children[0].pack_configure(anchor="w", padx=24, pady=(18, 8))
        except Exception:
            pass
        try:
            left_children[1].configure(height=390)
            left_children[1].pack_configure(fill="both", expand=True, padx=24, pady=(0, 18))
        except Exception:
            pass

    right_children = list(right_panel.winfo_children())
    for child in right_children:
        try:
            current = child.pack_info()
        except Exception:
            continue
        side = current.get("side", None)
        fill = current.get("fill", None)
        expand = bool(int(current.get("expand", 0))) if str(current.get("expand", "0")).isdigit() else current.get("expand", False)
        padx = current.get("padx", 0)
        try:
            child.pack_configure(side=side, fill=fill, expand=expand, padx=padx, pady=(0, 3))
        except Exception:
            pass

    if right_children:
        try:
            right_children[0].configure(height=28)
            right_children[0].pack_configure(anchor="w", padx=24, pady=(6, 1))
        except Exception:
            pass
    for index in (1, 2):
        if index < len(right_children):
            try:
                right_children[index].configure(height=28)
                right_children[index].pack_propagate(False)
                right_children[index].pack_configure(fill="x", padx=24, pady=(0, 1))
                for radio in right_children[index].winfo_children():
                    try:
                        radio.configure(height=28)
                    except Exception:
                        pass
            except Exception:
                pass
    for index in (3, 5, 6, 7):
        if index < len(right_children):
            try:
                right_children[index].configure(height=30)
                right_children[index].pack_configure(anchor="w", padx=24, pady=(0, 1))
            except Exception:
                pass
    if len(right_children) > 4:
        try:
            right_children[4].configure(height=38)
            right_children[4].pack_configure(fill="x", padx=24, pady=(0, 2))
        except Exception:
            pass
    for index in (8, 9, 10):
        if index < len(right_children):
            try:
                right_children[index].configure(height=36)
                right_children[index].pack_propagate(False)
                right_children[index].pack_configure(fill="x", padx=24, pady=(0, 1))
                slider_parts = list(right_children[index].winfo_children())
                if slider_parts:
                    try:
                        slider_parts[0].configure(height=18)
                        slider_parts[0].pack_propagate(False)
                        slider_parts[0].pack_configure(fill="x", pady=(0, 0))
                        for item in slider_parts[0].winfo_children():
                            try:
                                item.configure(height=18, font=customtkinter.CTkFont(size=11))
                            except Exception:
                                pass
                    except Exception:
                        pass
                if len(slider_parts) > 1:
                    try:
                        slider_parts[1].configure(height=16)
                        slider_parts[1].pack_configure(fill="x", pady=(0, 0))
                    except Exception:
                        pass
            except Exception:
                pass
    if len(right_children) > 11:
        try:
            controls_height = 56 if getattr(right_children[11], "_fx_wm_filename_rule_controls", False) else 30
            right_children[11].configure(height=controls_height)
            right_children[11].pack_propagate(False)
            right_children[11].pack_configure(fill="x", padx=24, pady=(0, 2))
            for child in right_children[11].winfo_children():
                try:
                    if getattr(right_children[11], "_fx_wm_filename_rule_controls", False):
                        continue
                    child.configure(height=30)
                except Exception:
                    pass
        except Exception:
            pass


def _tighten_layout(app, task_name=None):
    try:
        _apply_shell_layout_tightening(app)
        if task_name is None:
            for name in TAB_LAYOUT_ATTRS:
                _tighten_single_tab_layout(app, name)
        else:
            _tighten_single_tab_layout(app, task_name)
    except Exception as exc:
        _debug(f"layout:tighten_error:{exc}")


def _load_runtime_namespace():
    _debug("load_runtime:start")
    if not RUNTIME_BIN.exists():
        _debug(f"load_runtime:missing:{RUNTIME_BIN}")
        raise FileNotFoundError(f"Missing runtime payload: {RUNTIME_BIN}")
    code = marshal.loads(RUNTIME_BIN.read_bytes())
    namespace = {
        "__name__": "fengxi_embedded_runtime",
        "__file__": __file__,
        "__package__": None,
    }
    lazy_import_state = _install_runtime_lazy_imports()
    try:
        exec(code, namespace)
    finally:
        _restore_runtime_lazy_imports(lazy_import_state)
    _debug("load_runtime:done")
    return namespace


def _locate_ffmpeg():
    env_bin = os.environ.get("FFMPEG_BINARY")
    if env_bin and os.path.exists(env_bin):
        return env_bin
    try:
        import imageio_ffmpeg
        ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_bin and os.path.exists(ffmpeg_bin):
            os.environ["FFMPEG_BINARY"] = ffmpeg_bin
            return ffmpeg_bin
    except Exception:
        pass
    return None


def _ffmpeg_convert(src, dst, target_fmt, bitrate="192k"):
    ffmpeg_bin = _locate_ffmpeg()
    if not ffmpeg_bin:
        return "MISSING_LIB:ffmpeg backend not available"

    codec_map = {
        "mp3": ["-acodec", "libmp3lame"],
        "wav": ["-acodec", "pcm_s16le"],
        "flac": ["-acodec", "flac"],
        "m4a": ["-acodec", "aac"],
        "aac": ["-acodec", "aac"],
        "ogg": ["-acodec", "libvorbis"],
    }

    target_fmt = target_fmt.lower()
    cmd = [ffmpeg_bin, "-y", "-i", src, "-vn"]
    if bitrate and target_fmt not in ("wav", "flac"):
        cmd.extend(["-b:a", bitrate])
    cmd.extend(codec_map.get(target_fmt, []))
    cmd.append(dst)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    except Exception as exc:
        return f"ERROR:{exc}"

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return f"ERROR:{detail or 'ffmpeg convert failed'}"
    if not os.path.exists(dst) or os.path.getsize(dst) <= 0:
        return "ERROR:output file not created"
    return "SUCCESS"


_debug("bootstrap:start")
_ns = _load_runtime_namespace()
_ns["convert_audio_format"] = _ffmpeg_convert
_ns["HAS_MOVIEPY"] = bool(_locate_ffmpeg()) or bool(_ns.get("HAS_MOVIEPY"))
_debug(f"bootstrap:patched:has_moviepy={_ns['HAS_MOVIEPY']}")

for _key, _value in _ns.items():
    if _key in {"__name__", "__file__", "__package__", "__builtins__"}:
        continue
    globals()[_key] = _value
_debug("bootstrap:globals_loaded")


def _patch_task_routing():
    try:
        original = FengxiToolboxApp.resolve_task_config
    except Exception as exc:
        _debug(f"patch_task_routing:missing:{exc}")
        return
    if getattr(original, "__fx_task_routing_patch__", False):
        return

    def patched(self, task_type, all_files):
        args, force_single_thread, extra = original(self, task_type, all_files)
        try:
            if task_type == "remove_wm":
                force_single_thread = True
                _debug("patch_task_routing:force_single_thread:remove_wm")
            elif task_type == "pdf" and self.pdf_mode_var.get() == "merge":
                force_single_thread = True
                _debug("patch_task_routing:force_single_thread:pdf_merge")
            elif task_type == "file" and self.file_mode_var.get() == "dedup":
                force_single_thread = True
                _debug("patch_task_routing:force_single_thread:file_dedup")
        except Exception as exc:
            _debug(f"patch_task_routing:error:{exc}")
        return args, force_single_thread, extra

    patched.__fx_task_routing_patch__ = True
    FengxiToolboxApp.resolve_task_config = patched
    _debug("patch_task_routing:installed")


_patch_task_routing()


def _choose_input_path_interactive(app):
    current_value = ""
    try:
        current_value = app.input_path.get()
    except Exception:
        current_value = ""

    current_path = _normalize_input_path_value(current_value)
    last_input_dir = getattr(app, "_fx_last_input_dir", "")

    initial_dir = current_path
    if initial_dir and os.path.isfile(initial_dir):
        initial_dir = os.path.dirname(initial_dir)
    if not initial_dir:
        initial_dir = _normalize_input_path_value(last_input_dir)
    if initial_dir and not os.path.isdir(initial_dir):
        initial_dir = os.path.dirname(initial_dir)
    if not initial_dir:
        home_dir = _normalize_input_path_value(os.path.expanduser("~"))
        initial_dir = home_dir if os.path.isdir(home_dir) else os.getcwd()

    selected_path = _choose_input_path_via_shell_dialog(app, initial_dir)
    if not selected_path:
        _debug("shell_picker:cancelled_or_failed")
        return ""

    normalized_path = _normalize_input_path_value(selected_path)
    if not normalized_path:
        return ""

    app._fx_input_pick_mode = "file" if os.path.isfile(normalized_path) else "folder"
    app._fx_last_input_dir = normalized_path if os.path.isdir(normalized_path) else os.path.dirname(normalized_path)
    try:
        app.input_path.set(normalized_path)
    except Exception:
        pass
    try:
        app.log(
            f"🎯 [目标锁定] 已载入{'文件' if os.path.isfile(normalized_path) else '文件夹'}: {normalized_path}"
        )
    except Exception:
        pass
    return normalized_path


def _patch_drag_drop_input_support():
    try:
        original = FengxiToolboxApp.accept_drag_drop
    except Exception as exc:
        _debug(f"patch_drag_drop:missing:{exc}")
        return

    if getattr(original, "__fx_drag_drop_patch__", False):
        return

    def patched(self, filenames):
        if not filenames:
            return

        raw_items = list(filenames)
        normalized_items = []
        for item in raw_items:
            normalized = _normalize_input_path_value(item)
            if normalized:
                normalized_items.append(normalized)

        if not normalized_items:
            try:
                self.log("❌ [错误] 拖拽目标路径无效")
            except Exception:
                pass
            return

        selected_path = normalized_items[0]
        is_file = os.path.isfile(selected_path)
        is_dir = os.path.isdir(selected_path)
        if not (is_file or is_dir):
            try:
                self.log(f"❌ [错误] 拖拽目标不存在: {selected_path}")
            except Exception:
                pass
            return

        self._fx_input_pick_mode = "file" if is_file else "folder"
        self._fx_last_input_dir = os.path.dirname(selected_path) if is_file else selected_path

        try:
            self.input_path.set(selected_path)
        except Exception:
            pass

        if len(normalized_items) > 1:
            try:
                self.log(f"⚠️ [拖拽] 检测到 {len(normalized_items)} 个项目，当前仅使用第 1 个: {selected_path}")
            except Exception:
                pass

        try:
            self.log(f"🎯 [目标锁定] 已拖入{'文件' if is_file else '文件夹'}: {selected_path}")
        except Exception:
            pass

    patched.__fx_drag_drop_patch__ = True
    FengxiToolboxApp.accept_drag_drop = patched
    _debug("patch_drag_drop:installed")


_patch_drag_drop_input_support()


def _run_single_file_zip_via_staging(app, input_file, original_run_process):
    source_file = Path(input_file)
    staging_root = Path(tempfile.mkdtemp(prefix="fx_single_zip_"))
    staging_dir = staging_root / source_file.name
    staging_dir.mkdir(parents=True, exist_ok=True)
    staged_file = staging_dir / source_file.name
    shutil.copy2(source_file, staged_file)
    moved_outputs = []
    try:
        try:
            app.log(f"📦 [单文件模式] 正在准备压缩: {source_file.name}")
        except Exception:
            pass
        original_run_process(app, str(staging_dir), "zip")
        for produced_zip in staging_dir.glob("*.zip"):
            target_zip = source_file.parent / produced_zip.name
            if target_zip.exists():
                try:
                    target_zip.unlink()
                except Exception:
                    pass
            shutil.move(str(produced_zip), str(target_zip))
            moved_outputs.append(target_zip)
            result = _get_last_task_result(app)
            _add_task_result_output(result, target_zip)
        for target_zip in moved_outputs:
            try:
                app.log(f"✅ [单文件压缩] 已输出: {target_zip.name}")
            except Exception:
                pass
        result = _get_last_task_result(app)
        if result is not None:
            _set_task_result_output_root(result, source_file.parent)
            _set_task_result_counts(result, processed=1, success=1 if moved_outputs else 0, failed=0 if moved_outputs else 1)
            if moved_outputs:
                _set_task_result_finished(
                    result,
                    "success",
                    message="单文件压缩完成",
                    detail=f"已生成 {len(moved_outputs)} 个压缩包",
                )
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)
    return moved_outputs


def _patch_single_input_support():
    try:
        original_select_folder = FengxiToolboxApp.select_folder
        original_collect_input_files = FengxiToolboxApp.collect_input_files
        original_run_process = FengxiToolboxApp.run_process
    except Exception as exc:
        _debug(f"patch_single_input:missing:{exc}")
        return

    if getattr(original_run_process, "__fx_single_input_patch__", False):
        return

    def patched_select_folder(self):
        _choose_input_path_interactive(self)

    def patched_collect_input_files(self, input_folder, task_type):
        normalized_input = _normalize_input_path_value(input_folder)
        single_target = _normalize_input_path_value(getattr(self, "_fx_single_input_target", ""))
        target = ""
        if normalized_input and os.path.isfile(normalized_input):
            target = normalized_input
        elif single_target and os.path.isfile(single_target):
            parent_dir = os.path.dirname(single_target)
            if normalized_input and normalized_input == parent_dir:
                target = single_target
        if target:
            log_key = (task_type, target)
            if getattr(self, "_fx_single_input_logged", None) != log_key:
                try:
                    self.log(f"📄 [单文件模式] 仅处理: {os.path.basename(target)}")
                except Exception:
                    pass
                self._fx_single_input_logged = log_key
            return [target]
        return original_collect_input_files(self, input_folder, task_type)

    def patched_run_process(self, input_folder, task_type):
        normalized_input = _normalize_input_path_value(input_folder)
        prev_single_target = getattr(self, "_fx_single_input_target", None)
        prev_single_log = getattr(self, "_fx_single_input_logged", None)
        enable_multithread_var = getattr(self, "enable_multithread", None)
        prev_multithread = None
        try:
            if normalized_input and os.path.isfile(normalized_input):
                self._fx_last_input_dir = os.path.dirname(normalized_input)
                self._fx_input_pick_mode = "file"
                self._fx_single_input_logged = None
                if enable_multithread_var is not None:
                    try:
                        prev_multithread = bool(enable_multithread_var.get())
                        enable_multithread_var.set(False)
                        _debug(f"patch_single_input:force_single_thread:{task_type}")
                    except Exception as exc:
                        _debug(f"patch_single_input:toggle_multithread_error:{exc}")
                if task_type == "zip":
                    return _run_single_file_zip_via_staging(self, normalized_input, original_run_process)
                self._fx_single_input_target = normalized_input
                return original_run_process(self, os.path.dirname(normalized_input), task_type)
            if normalized_input and os.path.isdir(normalized_input):
                self._fx_last_input_dir = normalized_input
                self._fx_input_pick_mode = "folder"
            self._fx_single_input_target = None
            self._fx_single_input_logged = None
            return original_run_process(self, input_folder, task_type)
        finally:
            if prev_multithread is not None and enable_multithread_var is not None:
                try:
                    enable_multithread_var.set(prev_multithread)
                except Exception:
                    pass
            self._fx_single_input_target = prev_single_target
            self._fx_single_input_logged = prev_single_log

    def patched_on_start_click(self):
        if getattr(self, "is_running", False):
            return
        if getattr(self, "current_task", None) == "help":
            self.log("ℹ️ [使用教程] 当前页面仅用于查看说明，请先切换到具体功能页。")
            return
        selected_input = _normalize_input_path_value(self.input_path.get())
        if not selected_input:
            self.log("❌ [错误] 目标路径未定义")
            tkinter.messagebox.showwarning("提示", "请先选择文件或文件夹！")
            return
        if self.current_task == "watermark" and not self.font_list:
            tkinter.messagebox.showerror("资源错误", "fonts 文件夹为空！\n无法添加水印。")
            return
        if self.current_task == "audio" and not HAS_MOVIEPY:
            tkinter.messagebox.showerror("依赖缺失", "未安装 moviepy 库，无法进行音频处理。\n请运行: pip install moviepy")
            return

        self.is_running = True
        self.stop_event = False
        self.progress_bar.set(0)
        self.btn_run.configure(state="disabled", text="⚡ 执行中...", fg_color="#455A64")
        self.btn_stop.configure(state="normal")
        threading.Thread(target=self.run_process, args=(selected_input, self.current_task), daemon=True).start()

    patched_select_folder.__fx_single_input_patch__ = True
    patched_collect_input_files.__fx_single_input_patch__ = True
    patched_run_process.__fx_single_input_patch__ = True
    patched_on_start_click.__fx_single_input_patch__ = True
    FengxiToolboxApp.select_folder = patched_select_folder
    FengxiToolboxApp.collect_input_files = patched_collect_input_files
    FengxiToolboxApp.run_process = patched_run_process
    FengxiToolboxApp.on_start_click = patched_on_start_click
    _debug("patch_single_input:installed")


_patch_single_input_support()


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _safe_getattr(obj, attr_name, default=None):
    try:
        return getattr(obj, attr_name)
    except Exception:
        return default


def _shape_rotation_distance(rotation):
    angle = _safe_float(rotation) % 360.0
    candidates = (0.0, 90.0, 180.0, 270.0, 360.0)
    return min(abs(angle - candidate) for candidate in candidates)


def _contains_watermark_keyword(text):
    normalized = (text or "").strip().lower()
    if not normalized:
        return False
    keywords = (
        "xmu_done",
        "watermark",
        "confidential",
        "draft",
        "sample",
        "do not copy",
        "internal use",
        "for review",
        "water mark",
        "water-mark",
        "水印",
        "机密",
        "保密",
        "绝密",
        "内部",
        "样稿",
        "草稿",
        "作废",
        "仅供",
        "测试章",
    )
    return any(keyword in normalized for keyword in keywords)


def _collect_shape_marker_text(shape):
    parts = []
    for attr_name in ("Name", "AlternativeText", "Title"):
        try:
            value = getattr(shape, attr_name, "")
        except Exception:
            value = ""
        if value:
            parts.append(str(value))
    try:
        text_effect = getattr(shape, "TextEffect", None)
        text_value = getattr(text_effect, "Text", "")
        if text_value:
            parts.append(str(text_value))
    except Exception:
        pass
    try:
        text_frame = getattr(shape, "TextFrame", None)
        if text_frame and getattr(text_frame, "HasText", False):
            text_value = text_frame.TextRange.Text
            if text_value:
                parts.append(str(text_value))
    except Exception:
        pass
    return " ".join(part for part in parts if part).strip()


def _collect_inline_shape_marker_text(ishape):
    parts = []
    for attr_name in ("AlternativeText", "Title"):
        try:
            value = getattr(ishape, attr_name, "")
        except Exception:
            value = ""
        if value:
            parts.append(str(value))
    try:
        range_obj = getattr(ishape, "Range", None)
        text_value = getattr(range_obj, "Text", "")
        if text_value:
            parts.append(str(text_value))
    except Exception:
        pass
    return " ".join(part for part in parts if part).strip()


def _shape_looks_like_watermark(shape, page_width, page_height, preserve_mine=False):
    marker_text = _collect_shape_marker_text(shape)
    normalized_marker = marker_text.lower()
    if "xmu_done" in normalized_marker:
        return not preserve_mine
    if _contains_watermark_keyword(marker_text):
        return True

    width = _safe_float(_safe_getattr(shape, "Width", 0.0))
    height = _safe_float(_safe_getattr(shape, "Height", 0.0))
    left = _safe_float(_safe_getattr(shape, "Left", 0.0))
    top = _safe_float(_safe_getattr(shape, "Top", 0.0))
    transparency = _safe_float(_safe_getattr(_safe_getattr(shape, "Fill", None), "Transparency", 0.0))
    rotation_distance = _shape_rotation_distance(_safe_getattr(shape, "Rotation", 0.0))

    large_enough = width >= page_width * 0.35 or height >= page_height * 0.20
    if page_width <= 0 or page_height <= 0:
        return False

    center_x = left + width / 2.0
    center_y = top + height / 2.0
    near_center = abs(center_x - page_width / 2.0) <= page_width * 0.30 and abs(center_y - page_height / 2.0) <= page_height * 0.30
    off_canvas = left < 0 or top < 0
    diagonal = rotation_distance > 12.0
    translucent = transparency >= 0.15

    return large_enough and ((diagonal and (near_center or off_canvas)) or (translucent and (near_center or off_canvas)))


def _inline_shape_looks_like_watermark(ishape, page_width, page_height, preserve_mine=False):
    marker_text = _collect_inline_shape_marker_text(ishape)
    normalized_marker = marker_text.lower()
    if "xmu_done" in normalized_marker:
        return not preserve_mine
    if _contains_watermark_keyword(marker_text):
        return True

    width = _safe_float(_safe_getattr(ishape, "Width", 0.0))
    height = _safe_float(_safe_getattr(ishape, "Height", 0.0))
    if page_width <= 0 or page_height <= 0:
        return False

    return width >= page_width * 0.45 and height >= page_height * 0.16


def _remove_watermark_from_word_safely(word_app, src, dst, preserve_mine=False, is_pdf_source=False):
    doc = None
    removed_header_shapes = 0
    removed_doc_shapes = 0
    removed_header_inline = 0
    try:
        src_abs = os.path.abspath(src)
        dst_abs = os.path.abspath(dst)
        doc = word_app.Documents.Open(src_abs)
        page_width = _safe_float(_safe_getattr(_safe_getattr(doc, "PageSetup", None), "PageWidth", 0.0))
        page_height = _safe_float(_safe_getattr(_safe_getattr(doc, "PageSetup", None), "PageHeight", 0.0))

        for section in doc.Sections:
            for header in section.Headers:
                try:
                    header_shapes = header.Shapes
                    for index in range(header_shapes.Count, 0, -1):
                        shape = header.Shapes(index)
                        if not _shape_looks_like_watermark(shape, page_width, page_height, preserve_mine=preserve_mine):
                            continue
                        shape.Delete()
                        removed_header_shapes += 1
                except Exception as exc:
                    _debug(f"patch_remove_wm:header_shape_iter_error:{exc}")

                try:
                    inline_shapes = header.Range.InlineShapes
                    for index in range(inline_shapes.Count, 0, -1):
                        ishape = inline_shapes(index)
                        if not _inline_shape_looks_like_watermark(ishape, page_width, page_height, preserve_mine=preserve_mine):
                            continue
                        ishape.Delete()
                        removed_header_inline += 1
                except Exception as exc:
                    _debug(f"patch_remove_wm:header_inline_iter_error:{exc}")

        if is_pdf_source and not preserve_mine:
            try:
                for index in range(doc.Shapes.Count, 0, -1):
                    shape = doc.Shapes(index)
                    try:
                        if not _shape_looks_like_watermark(shape, page_width, page_height, preserve_mine=False):
                            continue
                    except Exception:
                        continue
                    shape.Delete()
                    removed_doc_shapes += 1
            except Exception as exc:
                _debug(f"patch_remove_wm:doc_shape_iter_error:{exc}")

        doc.SaveAs(dst_abs)
        doc.Close()
        doc = None
        _debug(
            "patch_remove_wm:safe_cleanup:"
            f"header_shapes={removed_header_shapes}:header_inline={removed_header_inline}:"
            f"doc_shapes={removed_doc_shapes}:pdf_source={is_pdf_source}:dst={dst_abs}"
        )
        return "SUCCESS"
    except Exception as exc:
        _debug(f"patch_remove_wm:safe_cleanup_error:{exc}")
        try:
            if doc is not None:
                doc.Close(False)
        except Exception:
            pass
        return "ERROR"


def _patch_remove_watermark_robustness():
    try:
        original = remove_watermark_from_word
    except Exception as exc:
        _debug(f"patch_remove_wm:missing:{exc}")
        return

    if getattr(original, "__fx_remove_wm_patch__", False):
        return

    def patched(word_app, src, dst, preserve_mine=False, is_pdf_source=False):
        return _remove_watermark_from_word_safely(
            word_app,
            src,
            dst,
            preserve_mine=preserve_mine,
            is_pdf_source=is_pdf_source,
        )

    patched.__fx_remove_wm_patch__ = True
    patched.__fx_remove_wm_original__ = original
    globals()["remove_watermark_from_word"] = patched
    _debug("patch_remove_wm:installed")


_patch_remove_watermark_robustness()


def _write_failed_report(output_folder, failed_list):
    if not failed_list:
        return None
    report_path = os.path.join(output_folder, "!失败文件清单.txt")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("以下文件处理失败（已原样保留）：\n")
        for item in failed_list:
            fh.write(f"{item}\n")
    return report_path


def _copy_tree_contents(src_dir, dst_dir, skip_names=None):
    skip_names = set(skip_names or [])
    src_root = Path(src_dir)
    dst_root = Path(dst_dir)
    if not src_root.exists():
        return
    for item in src_root.rglob("*"):
        rel = item.relative_to(src_root)
        if rel.name in skip_names:
            continue
        target = dst_root / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _read_failed_report_items(report_path):
    if not report_path or not os.path.exists(report_path):
        return []
    lines = Path(report_path).read_text(encoding="utf-8", errors="ignore").splitlines()
    return [line.strip() for line in lines[1:] if line.strip()]


def _create_hidden_word_app():
    word_app = win32com.client.DispatchEx("Word.Application")
    try:
        word_app.Visible = False
    except Exception:
        pass
    try:
        word_app.DisplayAlerts = 0
    except Exception:
        pass
    return word_app


def _get_remove_wm_overwrite_original(app):
    if getattr(app, "rm_wm_overwrite_original", None) is None:
        return False
    try:
        return bool(app.rm_wm_overwrite_original.get())
    except Exception:
        return False


def _build_single_remove_wm_output_path(source_path):
    source = Path(source_path)
    candidate = source.with_name(f"{source.stem}_去水印{source.suffix}")
    counter = 2
    while candidate.exists() and os.path.normcase(str(candidate)) != os.path.normcase(str(source)):
        candidate = source.with_name(f"{source.stem}_去水印_{counter}{source.suffix}")
        counter += 1
    return str(candidate)


def _replace_file_safely(src, dst):
    dst_path = Path(dst)
    temp_path = dst_path.with_name(f".{dst_path.name}.fx_replace_tmp")
    try:
        if temp_path.exists():
            temp_path.unlink()
    except Exception:
        pass
    try:
        shutil.copy2(src, temp_path)
        os.replace(str(temp_path), str(dst_path))
    finally:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass


def _finalize_single_remove_wm_output(app, source_file, staged_output_file, overwrite_original=False):
    source_file = _normalize_input_path_value(source_file)
    staged_output_file = _normalize_input_path_value(staged_output_file)
    if not source_file or not staged_output_file or not os.path.exists(staged_output_file):
        return None

    final_path = source_file if overwrite_original else _build_single_remove_wm_output_path(source_file)
    if overwrite_original:
        _replace_file_safely(staged_output_file, final_path)
        try:
            app.log(f"✅ [单文件去水印] 已直接覆盖原文件：{os.path.basename(final_path)}")
        except Exception:
            pass
    else:
        shutil.copy2(staged_output_file, final_path)
        try:
            app.log(f"✅ [单文件去水印] 已输出新文件：{final_path}")
        except Exception:
            pass
    return final_path


def _resolve_result_output_folder(input_value):
    normalized_input = _normalize_input_path_value(input_value)
    if normalized_input and os.path.isfile(normalized_input):
        input_root = os.path.dirname(normalized_input)
    else:
        input_root = normalized_input
    return normalized_input, input_root, os.path.join(input_root, RESULT_FOLDER_NAME)


def _task_result_now():
    return time.time()


def _new_task_result(input_value="", task_type=""):
    normalized_input = _normalize_input_path_value(input_value)
    started_at = _task_result_now()
    return {
        "task_type": task_type or "",
        "input": normalized_input,
        "status": "unknown",
        "success": False,
        "stopped": False,
        "skipped": False,
        "message": "",
        "detail": "",
        "error": "",
        "outputs": [],
        "output_root": "",
        "failed_items": [],
        "processed_count": 0,
        "success_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "started_at": started_at,
        "finished_at": None,
        "duration_seconds": 0.0,
    }


def _normalize_task_output_path(path_value):
    normalized = _normalize_input_path_value(path_value)
    return normalized if normalized else ""


def _add_task_result_output(result, path_value):
    if not isinstance(result, dict):
        return
    normalized = _normalize_task_output_path(path_value)
    if not normalized:
        return
    outputs = result.setdefault("outputs", [])
    if normalized not in outputs:
        outputs.append(normalized)


def _set_task_result_output_root(result, path_value):
    if not isinstance(result, dict):
        return
    normalized = _normalize_task_output_path(path_value)
    if normalized:
        result["output_root"] = normalized


def _set_task_result_counts(result, *, processed=None, success=None, failed=None, skipped=None):
    if not isinstance(result, dict):
        return
    if processed is not None:
        result["processed_count"] = max(0, int(processed))
    if success is not None:
        result["success_count"] = max(0, int(success))
    if failed is not None:
        result["failed_count"] = max(0, int(failed))
    if skipped is not None:
        result["skipped_count"] = max(0, int(skipped))


def _set_task_result_finished(result, status, message="", detail="", error="", stopped=False, skipped=False):
    if not isinstance(result, dict):
        return result
    finished_at = _task_result_now()
    result["finished_at"] = finished_at
    result["duration_seconds"] = max(0.0, finished_at - float(result.get("started_at") or finished_at))
    normalized_status = str(status or "unknown").strip().lower() or "unknown"
    result["status"] = normalized_status
    result["success"] = normalized_status == "success"
    result["stopped"] = bool(stopped or normalized_status == "stopped")
    result["skipped"] = bool(skipped or normalized_status == "skipped")
    result["message"] = str(message or result.get("message") or "")
    result["detail"] = str(detail or result.get("detail") or "")
    result["error"] = str(error or result.get("error") or "")
    result["failed_count"] = max(0, int(result.get("failed_count") or 0))
    result["success_count"] = max(0, int(result.get("success_count") or 0))
    result["processed_count"] = max(0, int(result.get("processed_count") or 0))
    result["skipped_count"] = max(0, int(result.get("skipped_count") or 0))
    result["failed_items"] = list(result.get("failed_items") or [])
    result["outputs"] = [item for item in result.get("outputs", []) if item]
    return result


def _attach_task_result(app, result):
    if app is None or not isinstance(result, dict):
        return result
    try:
        app._fx_last_task_result = result
    except Exception:
        pass
    return result


def _start_task_result(app, input_value, task_type):
    result = _new_task_result(input_value=input_value, task_type=task_type)
    return _attach_task_result(app, result)


def _get_last_task_result(app):
    try:
        result = getattr(app, "_fx_last_task_result", None)
    except Exception:
        result = None
    return result if isinstance(result, dict) else None


def _clear_last_task_result(app):
    try:
        app._fx_last_task_result = None
    except Exception:
        pass


def _export_task_result(result, output_path):
    if not isinstance(result, dict) or not output_path:
        return False
    try:
        path = Path(_normalize_input_path_value(output_path))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception as exc:
        _debug(f"task_result:export_error:{exc}")
        return False


def _finalize_current_task_result(app, status, message="", detail="", error="", stopped=False, skipped=False):
    result = _get_last_task_result(app)
    if result is None:
        result = _start_task_result(app, "", "")
    return _set_task_result_finished(
        result,
        status=status,
        message=message,
        detail=detail,
        error=error,
        stopped=stopped,
        skipped=skipped,
    )


def _summarize_logs_for_task_result(logs):
    entries = [str(item).strip() for item in (logs or []) if str(item).strip()]
    if not entries:
        return "", "", False, False

    error_lines = [item for item in entries if "❌" in item or "🔥" in item or "错误" in item or "失败" in item]
    stop_lines = [item for item in entries if "⏹️" in item or "中止" in item or "停止" in item]
    success_lines = [item for item in entries if "🎉 [完成]" in item or "✅ [完成]" in item or "已全部完成" in item]
    if error_lines:
        return "failed", error_lines[-1], False, False
    if stop_lines:
        return "stopped", stop_lines[-1], True, False
    if success_lines:
        return "success", success_lines[-1], False, False
    return "", entries[-1], False, False


def _infer_task_result_from_context(app, input_value, task_type, return_value=None, logs=None, exception=None):
    result = _get_last_task_result(app)
    if result is None:
        result = _start_task_result(app, input_value, task_type)
    if task_type and not result.get("task_type"):
        result["task_type"] = task_type
    if input_value and not result.get("input"):
        result["input"] = _normalize_input_path_value(input_value)

    if exception is not None:
        return _set_task_result_finished(
            result,
            status="failed",
            message=str(exception),
            detail=str(exception),
            error=str(exception),
        )

    if result.get("finished_at"):
        return result

    inferred_status = ""
    inferred_message = ""
    stopped = False
    skipped = False

    if getattr(app, "stop_event", False):
        inferred_status = "stopped"
        inferred_message = "用户停止"
        stopped = True

    if not inferred_status:
        log_status, log_message, log_stopped, log_skipped = _summarize_logs_for_task_result(logs)
        if log_status:
            inferred_status = log_status
            inferred_message = log_message
            stopped = log_stopped
            skipped = log_skipped

    if not inferred_status and isinstance(return_value, str):
        normalized_return = return_value.strip()
        if normalized_return == "SUCCESS":
            inferred_status = "success"
            inferred_message = normalized_return
        elif normalized_return.startswith("ERROR"):
            inferred_status = "failed"
            inferred_message = normalized_return
        elif normalized_return.startswith("SKIP"):
            inferred_status = "skipped"
            inferred_message = normalized_return
            skipped = True

    if not inferred_status:
        failed_items = list(result.get("failed_items") or [])
        if failed_items or int(result.get("failed_count") or 0) > 0:
            inferred_status = "failed"
            inferred_message = result.get("detail") or "存在失败项目"
        elif result.get("outputs") or result.get("output_root"):
            inferred_status = "success"
            inferred_message = result.get("detail") or "执行完成"
        else:
            inferred_status = "success"
            inferred_message = result.get("detail") or "执行完成"

    return _set_task_result_finished(
        result,
        status=inferred_status,
        message=inferred_message,
        detail=result.get("detail") or inferred_message,
        error=result.get("error") or (inferred_message if inferred_status == "failed" else ""),
        stopped=stopped,
        skipped=skipped,
    )


def _collect_result_file_paths(output_root):
    normalized_root = _normalize_input_path_value(output_root)
    if not normalized_root or not os.path.exists(normalized_root):
        return []
    root_path = Path(normalized_root)
    results = []
    if root_path.is_file():
        return [str(root_path)]
    skip_names = {"!失败文件清单.txt"}
    for item in root_path.rglob("*"):
        if not item.is_file():
            continue
        if item.name in skip_names:
            continue
        results.append(str(item))
    return results


def _coerce_progress_value(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _clamp_progress_value(value):
    return max(0.0, min(1.0, _coerce_progress_value(value)))


def _get_active_progress_tracker(app):
    return getattr(app, "_fx_progress_tracker", None)


def _unwrap_runtime_run_process(callable_obj):
    current = callable_obj
    seen = set()
    while isinstance(current, types.FunctionType) and id(current) not in seen:
        seen.add(id(current))
        if getattr(current, "__module__", "") == "fengxi_embedded_runtime" and current.__name__ == "run_process":
            return current
        next_func = None
        for cell in current.__closure__ or ():
            try:
                value = cell.cell_contents
            except ValueError:
                continue
            if isinstance(value, types.FunctionType):
                next_func = value
                break
        if next_func is None:
            break
        current = next_func
    return None


def _build_runtime_progress_site_map(runtime_run_process):
    if runtime_run_process is None:
        return {
            "before_process_single": set(),
            "pass_through": set(),
            "direct_pre": set(),
        }

    cached = getattr(runtime_run_process, "__fx_progress_site_map__", None)
    if cached is not None:
        return cached

    instructions = list(dis.get_instructions(runtime_run_process))
    site_map = {
        "before_process_single": set(),
        "pass_through": set(),
        "direct_pre": set(),
    }

    for index, instr in enumerate(instructions):
        if instr.opname != "LOAD_ATTR" or instr.argval != "progress_bar":
            continue

        method_index = None
        last_call_index = None
        for follow_index in range(index + 1, min(index + 40, len(instructions))):
            follow = instructions[follow_index]
            if follow.opname == "LOAD_METHOD" and follow.argval == "set":
                method_index = follow_index
            elif method_index is not None and follow.opname == "CALL":
                last_call_index = follow_index
            elif method_index is not None and follow.opname == "POP_TOP":
                break
        call_index = last_call_index
        if method_index is None or call_index is None:
            continue
        if call_index + 1 >= len(instructions) or instructions[call_index + 1].opname != "POP_TOP":
            continue

        call_offset = instructions[call_index].offset
        look_back = instructions[max(0, index - 12):index]
        look_ahead = instructions[call_index + 1:min(len(instructions), call_index + 18)]

        if any(item.opname == "LOAD_METHOD" and item.argval == "process_single_file" for item in look_ahead):
            site_map["before_process_single"].add(call_offset)
            continue

        if any(item.opname == "STORE_FAST" and item.argval == "processed" for item in look_back):
            site_map["pass_through"].add(call_offset)
            continue

        meaningful_next = None
        for item in look_ahead:
            if item.opname in {"POP_TOP", "EXTENDED_ARG", "NOP"}:
                continue
            meaningful_next = item
            break
        if meaningful_next is not None and meaningful_next.opname.startswith("JUMP"):
            site_map["pass_through"].add(call_offset)
            continue

        site_map["direct_pre"].add(call_offset)

    runtime_run_process.__fx_progress_site_map__ = site_map
    return site_map


def _count_zip_progress_units(input_value, mode):
    normalized = _normalize_input_path_value(input_value)
    if not normalized:
        return 0
    if os.path.isfile(normalized):
        return 1

    if mode != "smart_recursive":
        total_files = 0
        for _, _, files in os.walk(normalized):
            total_files += len(files)
        return total_files

    total_items = 0
    for _, dirs, files in os.walk(normalized):
        total_items += len(files)
        total_items += len(dirs)
    return total_items


def _estimate_progress_total_units(app, input_value, task_type):
    normalized = _normalize_input_path_value(input_value)
    try:
        all_files = list(app.collect_input_files(normalized, task_type))
    except Exception:
        all_files = []

    if task_type == "pdf":
        mode = ""
        if getattr(app, "pdf_mode_var", None) is not None:
            try:
                mode = app.pdf_mode_var.get()
            except Exception:
                mode = ""
        pdf_count = sum(1 for item in all_files if str(item).lower().endswith(".pdf"))
        if mode in {"merge", "split", "encrypt", "ocr", "compress"}:
            return pdf_count

    if task_type == "zip":
        mode = ""
        if getattr(app, "zip_mode_var", None) is not None:
            try:
                mode = app.zip_mode_var.get()
            except Exception:
                mode = ""
        return _count_zip_progress_units(normalized, mode)

    if task_type == "image":
        mode = _get_image_pdf_mode(app)
        if mode in {"to_pdf", "merge_pdf"}:
            return max(1, len(_collect_image_to_pdf_files(app, normalized)))

    return len(all_files)


class _FxRunProgressTracker:
    def __init__(self, app, total_units, original_progress_set, runtime_run_process, site_map):
        self.app = app
        self.total_units = max(1, int(total_units or 0))
        self.original_progress_set = original_progress_set
        self.runtime_code = getattr(runtime_run_process, "__code__", None)
        self.site_map = site_map or {}
        self.lock = threading.Lock()
        self.completed_units = 0
        self.pending_direct_offset = None
        self.seen_activity = False
        self.keep_final_on_reset = False

    def _apply_progress_locked(self, value):
        self.original_progress_set(_clamp_progress_value(value))

    def current_fraction(self):
        with self.lock:
            return self.completed_units / self.total_units

    def set_current_item_fraction(self, item_fraction):
        with self.lock:
            self.seen_activity = True
            overall = (self.completed_units + max(0.0, min(1.0, _coerce_progress_value(item_fraction)))) / self.total_units
            self._apply_progress_locked(overall)

    def complete_units(self, count=1):
        with self.lock:
            self.seen_activity = True
            self.completed_units = min(self.total_units, self.completed_units + max(0, int(count or 0)))
            self.pending_direct_offset = None
            self._apply_progress_locked(self.completed_units / self.total_units)

    def finalize_pending(self):
        with self.lock:
            if self.pending_direct_offset is not None:
                self.completed_units = min(self.total_units, self.completed_units + 1)
                self.pending_direct_offset = None
                self.seen_activity = True
                self._apply_progress_locked(self.completed_units / self.total_units)

    def note_process_single_complete(self):
        self.complete_units(1)

    def handle_runtime_progress_call(self, call_offset, raw_value):
        raw_fraction = _clamp_progress_value(raw_value)
        with self.lock:
            if call_offset in self.site_map.get("before_process_single", set()):
                self.seen_activity = True
                self._apply_progress_locked(self.completed_units / self.total_units)
                return True

            if call_offset in self.site_map.get("direct_pre", set()):
                if self.pending_direct_offset is not None:
                    self.completed_units = min(self.total_units, self.completed_units + 1)
                self.pending_direct_offset = call_offset
                self.seen_activity = True
                self._apply_progress_locked(self.completed_units / self.total_units)
                return True

            if call_offset in self.site_map.get("pass_through", set()):
                self.seen_activity = True
                estimated_completed = int(round(raw_fraction * self.total_units))
                self.completed_units = min(self.total_units, max(self.completed_units, estimated_completed))
                self._apply_progress_locked(raw_fraction)
                return True

        return False

    def handle_reset(self):
        self.finalize_pending()
        if getattr(self.app, "stop_event", False) or not self.seen_activity:
            return False
        self.keep_final_on_reset = True
        self.original_progress_set(1.0)
        return True

    def should_ignore_reset_zero(self, frame_code, value):
        if not self.keep_final_on_reset:
            return False
        if frame_code is not getattr(type(self.app), "reset_ui").__code__:
            return False
        return _coerce_progress_value(value, default=1.0) <= 0.0


def _install_run_progress_tracker(app, input_value, task_type, runtime_run_process, site_map):
    progress_bar = getattr(app, "progress_bar", None)
    original_progress_set = getattr(progress_bar, "set", None)
    if progress_bar is None or not callable(original_progress_set):
        return None

    tracker = _FxRunProgressTracker(
        app=app,
        total_units=_estimate_progress_total_units(app, input_value, task_type),
        original_progress_set=original_progress_set,
        runtime_run_process=runtime_run_process,
        site_map=site_map,
    )

    original_process_single = getattr(app, "process_single_file", None)
    original_reset_ui = getattr(app, "reset_ui", None)

    def patched_progress_set(value, *args, **kwargs):
        frame = inspect.currentframe().f_back
        try:
            if frame is not None and tracker.runtime_code is not None and frame.f_code is tracker.runtime_code:
                if tracker.handle_runtime_progress_call(frame.f_lasti, value):
                    return None
            if frame is not None and tracker.should_ignore_reset_zero(frame.f_code, value):
                return None
            return original_progress_set(value, *args, **kwargs)
        finally:
            del frame

    def patched_process_single_file(*args, **kwargs):
        try:
            return original_process_single(*args, **kwargs)
        finally:
            tracker.note_process_single_complete()

    def patched_reset_ui(*args, **kwargs):
        tracker.handle_reset()
        return original_reset_ui(*args, **kwargs)

    progress_bar.set = patched_progress_set
    if callable(original_process_single):
        app.process_single_file = patched_process_single_file
    if callable(original_reset_ui):
        app.reset_ui = patched_reset_ui
    app._fx_progress_tracker = tracker

    def restore():
        try:
            progress_bar.set = original_progress_set
        except Exception:
            pass
        try:
            if callable(original_process_single):
                app.process_single_file = original_process_single
        except Exception:
            pass
        try:
            if callable(original_reset_ui):
                app.reset_ui = original_reset_ui
        except Exception:
            pass
        try:
            if getattr(app, "_fx_progress_tracker", None) is tracker:
                app._fx_progress_tracker = None
        except Exception:
            pass

    tracker.restore = restore
    return tracker


def _run_remove_wm_pdf_roundtrip(app, pdf_files, input_folder, output_folder):
    failed_list = []
    preserve_mine = False
    tracker = _get_active_progress_tracker(app)
    result = _get_last_task_result(app)
    if result is None:
        result = _start_task_result(app, input_folder, "remove_wm")
    _set_task_result_output_root(result, output_folder)
    if getattr(app, "rm_wm_preserve_mine", None) is not None:
        try:
            preserve_mine = bool(app.rm_wm_preserve_mine.get())
        except Exception:
            preserve_mine = False

    temp_root = Path(tempfile.mkdtemp(prefix="fx_rm_pdf_"))
    pythoncom.CoInitialize()
    try:
        total = max(1, len(pdf_files))
        for index, src in enumerate(pdf_files):
            if getattr(app, "stop_event", False):
                try:
                    app.log("⏹️ [停止] 去水印任务已被用户中止")
                except Exception:
                    pass
                break

            rel = os.path.relpath(src, input_folder)
            dst_pdf = os.path.join(output_folder, rel)
            os.makedirs(os.path.dirname(dst_pdf), exist_ok=True)
            stage_dir = temp_root / f"job_{index:03d}"
            stage_dir.mkdir(parents=True, exist_ok=True)
            stage_docx = stage_dir / "from_pdf.docx"
            cleaned_docx = stage_dir / "cleaned.docx"

            try:
                app.log(f"🧼 [PDF去水印] 正在处理：{os.path.basename(src)}")
            except Exception:
                pass

            try:
                convert_status = convert_pdf_to_word(src, str(stage_docx))
                if convert_status != "SUCCESS" or not stage_docx.exists():
                    raise RuntimeError(f"convert_pdf_to_word:{convert_status}")

                chosen_docx = stage_docx
                word_for_remove = _create_hidden_word_app()
                try:
                    remove_status = remove_watermark_from_word(
                        word_for_remove,
                        str(stage_docx),
                        str(cleaned_docx),
                        preserve_mine=preserve_mine,
                        is_pdf_source=True,
                    )
                finally:
                    try:
                        word_for_remove.Quit()
                    except Exception:
                        pass

                if remove_status != "SUCCESS":
                    raise RuntimeError(f"remove_watermark_from_word:{remove_status}")
                if not cleaned_docx.exists():
                    raise RuntimeError("remove_watermark_from_word:no_output")
                chosen_docx = cleaned_docx

                word_for_pdf = _create_hidden_word_app()
                try:
                    pdf_status = convert_doc_to_pdf(word_for_pdf, str(chosen_docx), dst_pdf)
                finally:
                    try:
                        word_for_pdf.Quit()
                    except Exception:
                        pass
                if pdf_status != "SUCCESS" or not os.path.exists(dst_pdf):
                    raise RuntimeError(f"convert_doc_to_pdf:{pdf_status}")
            except Exception as exc:
                failed_list.append(rel)
                try:
                    app.log(f"❌ [失败] PDF 去水印错误: {os.path.basename(src)}: {exc}")
                except Exception:
                    pass
            else:
                try:
                    app.log(f"✅ [PDF去水印] 已输出：{os.path.basename(dst_pdf)}")
                except Exception:
                    pass
                _add_task_result_output(result, dst_pdf)
            finally:
                if tracker is not None:
                    tracker.complete_units(1)
                else:
                    try:
                        app.progress_bar.set((index + 1) / total)
                    except Exception:
                        pass
    finally:
        pythoncom.CoUninitialize()
        shutil.rmtree(temp_root, ignore_errors=True)
    _set_task_result_counts(result, processed=len(pdf_files), success=len(pdf_files) - len(failed_list), failed=len(failed_list), skipped=0)
    if failed_list:
        result["failed_items"] = list(failed_list)
    return failed_list


def _run_remove_wm_task(app, input_folder, original_run_process):
    normalized_input = _normalize_input_path_value(input_folder)
    input_root = os.path.dirname(normalized_input) if normalized_input and os.path.isfile(normalized_input) else normalized_input
    output_folder = os.path.join(input_root, RESULT_FOLDER_NAME)
    os.makedirs(output_folder, exist_ok=True)
    result = _get_last_task_result(app)
    if result is None:
        result = _start_task_result(app, normalized_input, "remove_wm")
    _set_task_result_output_root(result, output_folder)

    all_files = app.collect_input_files(normalized_input, "remove_wm")
    pdf_files = [path for path in all_files if path.lower().endswith(".pdf")]
    other_files = [path for path in all_files if not path.lower().endswith(".pdf")]

    if not pdf_files:
        original_run_process(app, input_folder, "remove_wm")
        return _infer_task_result_from_context(app, normalized_input, "remove_wm")

    failed_list = []

    if other_files:
        staging_root = Path(tempfile.mkdtemp(prefix="fx_rm_mix_"))
        staging_output = staging_root / RESULT_FOLDER_NAME
        original_reset_ui = getattr(app, "reset_ui", None)
        try:
            for src in other_files:
                rel = os.path.relpath(src, input_root)
                staged = staging_root / rel
                staged.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, staged)

            if callable(original_reset_ui):
                app.reset_ui = lambda: None
            original_run_process(app, str(staging_root), "remove_wm")
            _copy_tree_contents(staging_output, output_folder, skip_names={"!澶辫触鏂囦欢娓呭崟.txt"})
            failed_list.extend(_read_failed_report_items(staging_output / "!澶辫触鏂囦欢娓呭崟.txt"))
        finally:
            if callable(original_reset_ui):
                app.reset_ui = original_reset_ui
            shutil.rmtree(staging_root, ignore_errors=True)

    failed_list.extend(_run_remove_wm_pdf_roundtrip(app, pdf_files, input_root, output_folder))

    if failed_list:
        deduped_failed = []
        seen = set()
        for item in failed_list:
            if item in seen:
                continue
            seen.add(item)
            deduped_failed.append(item)
        app.log("\n========= ❌ 失败清单 =========")
        for item in deduped_failed:
            app.log(f"• {item}")
        report_path = _write_failed_report(output_folder, deduped_failed)
        if report_path:
            app.log(f"\n📄 [报告] 已生成报告: {report_path}")
        app.log("完成 (含错误)")
        app.log(f"去水印任务结束，但有 {len(deduped_failed)} 个文件处理失败。")
    elif not getattr(app, "stop_event", False):
        app.log("\n🎉 [完成] 去水印已全部处理完成！")


def _run_remove_wm_task(app, input_folder, original_run_process):
    normalized_input = _normalize_input_path_value(input_folder)
    is_single_input = bool(normalized_input and os.path.isfile(normalized_input))
    input_root = os.path.dirname(normalized_input) if is_single_input else normalized_input
    overwrite_original = is_single_input and _get_remove_wm_overwrite_original(app)
    tracker = _get_active_progress_tracker(app)

    single_output_root = None
    if is_single_input:
        single_output_root = Path(tempfile.mkdtemp(prefix="fx_rm_single_out_"))
        output_folder = str(single_output_root / RESULT_FOLDER_NAME)
    else:
        output_folder = os.path.join(input_root, RESULT_FOLDER_NAME)
    os.makedirs(output_folder, exist_ok=True)

    try:
        all_files = app.collect_input_files(normalized_input, "remove_wm")
        pdf_files = [path for path in all_files if path.lower().endswith(".pdf")]
        other_files = [path for path in all_files if not path.lower().endswith(".pdf")]

        if not pdf_files and not is_single_input:
            return original_run_process(app, input_folder, "remove_wm")

        failed_list = []

        if other_files:
            staging_root = Path(tempfile.mkdtemp(prefix="fx_rm_mix_"))
            staging_output = staging_root / RESULT_FOLDER_NAME
            failed_report_path = staging_output / "!失败文件清单.txt"
            original_reset_ui = getattr(app, "reset_ui", None)
            try:
                for src in other_files:
                    rel = os.path.relpath(src, input_root)
                    staged = staging_root / rel
                    staged.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, staged)

                if callable(original_reset_ui):
                    app.reset_ui = lambda: None
                original_run_process(app, str(staging_root), "remove_wm")
                if tracker is not None:
                    tracker.finalize_pending()
                _copy_tree_contents(staging_output, output_folder, skip_names={failed_report_path.name})
                failed_list.extend(_read_failed_report_items(failed_report_path))
            finally:
                if callable(original_reset_ui):
                    app.reset_ui = original_reset_ui
                shutil.rmtree(staging_root, ignore_errors=True)

        if pdf_files:
            failed_list.extend(_run_remove_wm_pdf_roundtrip(app, pdf_files, input_root, output_folder))

        if is_single_input:
            rel = os.path.relpath(normalized_input, input_root)
            staged_output_file = os.path.join(output_folder, rel)
            deduped_failed = list(dict.fromkeys(item for item in failed_list if item))
            if not deduped_failed and not os.path.exists(staged_output_file):
                deduped_failed.append(rel)

            if deduped_failed:
                app.log("\n========= ❌ 失败清单 =========")
                for item in deduped_failed:
                    app.log(f"• {item}")
                app.log("去水印未生成有效结果，原文件保持不变。")
                return

            final_path = _finalize_single_remove_wm_output(
                app,
                normalized_input,
                staged_output_file,
                overwrite_original=overwrite_original,
            )
            if final_path and not getattr(app, "stop_event", False):
                app.log("\n🎉 [完成] 单文件去水印已处理完成！")
            return

        if failed_list:
            deduped_failed = []
            seen = set()
            for item in failed_list:
                if item in seen:
                    continue
                seen.add(item)
                deduped_failed.append(item)
            app.log("\n========= ❌ 失败清单 =========")
            for item in deduped_failed:
                app.log(f"• {item}")
            report_path = _write_failed_report(output_folder, deduped_failed)
            if report_path:
                app.log(f"\n📄 [报告] 已生成报告: {report_path}")
                _add_task_result_output(result, report_path)
            app.log("完成 (含错误)")
            app.log(f"去水印任务结束，但有 {len(deduped_failed)} 个文件处理失败。")
            result["failed_items"] = list(deduped_failed)
            _set_task_result_counts(result, processed=len(pdf_files) + len(other_files), success=max(0, len(pdf_files) - len(deduped_failed)), failed=len(deduped_failed), skipped=0)
            _set_task_result_finished(
                result,
                "failed",
                message=f"去水印任务结束，但有 {len(deduped_failed)} 个文件处理失败。",
                detail=f"失败 {len(deduped_failed)} 个文件",
                error=f"失败 {len(deduped_failed)} 个文件",
            )
        elif not getattr(app, "stop_event", False):
            app.log("\n🎉 [完成] 去水印已全部处理完成！")
            _set_task_result_counts(result, processed=len(pdf_files) + len(other_files), success=len(pdf_files) + len(other_files), failed=0, skipped=0)
            _set_task_result_finished(
                result,
                "success",
                message="去水印已全部处理完成",
                detail=f"成功处理 {len(pdf_files) + len(other_files)} 个文件",
            )
        else:
            _set_task_result_counts(result, processed=len(pdf_files) + len(other_files), success=max(0, len(pdf_files) - len(failed_list)), failed=len(failed_list), skipped=0)
            _set_task_result_finished(result, "stopped", message="用户停止去水印任务", detail="用户停止去水印任务", stopped=True)
    finally:
        if single_output_root is not None:
            shutil.rmtree(single_output_root, ignore_errors=True)


def _run_pdf_ocr_task(app, input_folder):
    from tools.fx_pdf_ocr import (
        FengxiPdfOcrEngine,
        default_model_root,
        get_default_backend_key,
        get_default_profile_key,
        resolve_model_root,
        write_pdf_ocr_comparison_report,
    )

    normalized_input, input_root, output_folder = _resolve_result_output_folder(input_folder)
    result = _get_last_task_result(app)
    if result is None:
        result = _start_task_result(app, normalized_input, "pdf")
    _set_task_result_output_root(result, output_folder)
    os.makedirs(output_folder, exist_ok=True)
    all_files = app.collect_input_files(normalized_input, "pdf")
    pdf_files = [f for f in all_files if f.lower().endswith(".pdf")]

    if not pdf_files:
        app.log("⚠️ [提示] 未找到可处理的 PDF 文件")
        _set_task_result_counts(result, processed=0, success=0, failed=0, skipped=1)
        _set_task_result_finished(result, "skipped", message="未找到可处理的 PDF 文件", detail="未找到可处理的 PDF 文件", skipped=True)
        return

    model_root = default_model_root()
    if getattr(app, "pdf_ocr_model_root", None) is not None:
        model_root = app.pdf_ocr_model_root.get().strip() or model_root
    resolved_model_root = resolve_model_root(model_root)

    language_display = ""
    if getattr(app, "pdf_ocr_language", None) is not None:
        language_display = app.pdf_ocr_language.get().strip()
    config_map = getattr(app, "_fx_pdf_ocr_lang_map", {})
    language_config = config_map.get(language_display, get_default_profile_key())

    backend_display = ""
    if getattr(app, "pdf_ocr_backend", None) is not None:
        backend_display = app.pdf_ocr_backend.get().strip()
    backend_map = getattr(app, "_fx_pdf_ocr_backend_map", {})
    backend_key = backend_map.get(backend_display, get_default_backend_key())

    mode_display = "mixed"
    if getattr(app, "pdf_ocr_mode", None) is not None:
        mode_display = app.pdf_ocr_mode.get().strip()
    mode_map = getattr(app, "_fx_pdf_ocr_mode_map", {})
    extraction_mode = mode_map.get(mode_display, mode_display or "mixed")
    if "|" in extraction_mode:
        extraction_mode = extraction_mode.split("|", 1)[0].strip()

    use_cls = False
    if getattr(app, "pdf_ocr_cls", None) is not None:
        use_cls = bool(app.pdf_ocr_cls.get())

    compare_report = False
    if getattr(app, "pdf_ocr_compare_report", None) is not None:
        compare_report = bool(app.pdf_ocr_compare_report.get())

    password = ""
    if getattr(app, "pdf_pwd_entry", None) is not None:
        password = app.pdf_pwd_entry.get().strip()

    failed_list = []
    engine = FengxiPdfOcrEngine(
        model_root=resolved_model_root,
        profile_key=language_config,
        backend_key=backend_key,
        cls=use_cls,
        limit_side_len=2880,
        cpu_threads=max(1, min(os.cpu_count() or 4, 8)),
    )
    app.log(f"🛡️ [安全模式] OCR 搜索版 PDF 使用单线程稳定处理，共 {len(pdf_files)} 个文件...")
    app.log(f"🤖 [OCR] 风兮模型目录：{resolved_model_root}")
    app.log(f"🧩 [OCR] 后端：{engine.backend_key}{' (自动选择)' if backend_key == 'auto' else ''}")
    app.log(
        f"🧠 [OCR] 模型：{language_config} | 模式：{extraction_mode} | 方向纠正：{'开' if use_cls else '关'}"
        f" | 对比报告：{'开' if compare_report else '关'}"
    )
    tracker = _get_active_progress_tracker(app)
    success_count = 0
    try:
        total = len(pdf_files)
        for index, src in enumerate(pdf_files):
            if app.stop_event:
                app.log("⏹️ [停止] OCR 任务已被用户中止")
                break
            rel = os.path.relpath(src, input_root)
            dst = os.path.join(output_folder, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            app.log(f"🔎 [OCR] 正在处理：{os.path.basename(src)}")
            if tracker is not None:
                tracker.set_current_item_fraction(0.02)
            should_count_completion = True
            try:
                if compare_report:
                    report_dir = os.path.join(output_folder, "_ocr_compare_reports")
                    report_name = f"{Path(src).stem}.ocr_compare.md"
                    report_result = write_pdf_ocr_comparison_report(
                        src=src,
                        report_path=os.path.join(report_dir, report_name),
                        profile_key=language_config,
                        model_root=resolved_model_root,
                        cls=use_cls,
                        password=password,
                        page_index=0,
                        cpu_threads=max(1, min(os.cpu_count() or 4, 8)),
                        limit_side_len=2880,
                    )
                    app.log(f"🧪 [OCR] 已生成后端对比报告：{report_result['report_path']}")
                    if tracker is not None:
                        tracker.set_current_item_fraction(0.08)

                def _page_progress(page_done, total_pages):
                    if total_pages <= 0:
                        return
                    overall_fraction = page_done / total_pages
                    if tracker is not None:
                        tracker.set_current_item_fraction(overall_fraction)
                    else:
                        app.progress_bar.set((index + overall_fraction) / total)

                engine.ocr_pdf_to_searchable_pdf(
                    src,
                    dst,
                    extraction_mode=extraction_mode,
                    password=password,
                    layered=True,
                    progress_callback=_page_progress,
                    stop_checker=lambda: app.stop_event,
                )
            except KeyboardInterrupt:
                should_count_completion = False
                app.log("⏹️ [停止] OCR 任务已被用户中止")
                break
            except Exception as exc:
                failed_list.append(rel)
                try:
                    shutil.copy2(src, dst)
                except Exception:
                    pass
                app.log(f"❌ [失败] OCR 错误: {os.path.basename(src)}: {exc}")
            else:
                success_count += 1
                _add_task_result_output(result, dst)
                app.log(f"✅ [OCR] 已生成可搜索 PDF：{os.path.basename(src)}")
            finally:
                if should_count_completion:
                    if tracker is not None:
                        tracker.complete_units(1)
                    else:
                        app.progress_bar.set((index + 1) / total)
    finally:
        engine.close()

    if failed_list:
        result["failed_items"] = list(failed_list)
        _set_task_result_counts(result, processed=len(pdf_files), success=success_count, failed=len(failed_list), skipped=0)
        app.log("\n========= ❌ 失败清单 =========")
        for item in failed_list:
            app.log(f"• {item}")
        report_path = _write_failed_report(output_folder, failed_list)
        if report_path:
            app.log(f"\n📄 [报告] 已生成报告: {report_path}")
            _add_task_result_output(result, report_path)
        app.log(f"完成 (含错误)")
        app.log(f"OCR 搜索版 PDF 任务结束，但有 {len(failed_list)} 个文件处理失败。")
        _set_task_result_finished(
            result,
            "failed",
            message=f"OCR 搜索版 PDF 任务结束，但有 {len(failed_list)} 个文件处理失败。",
            detail=f"失败 {len(failed_list)} 个文件",
            error=f"失败 {len(failed_list)} 个文件",
        )
    elif not app.stop_event:
        _set_task_result_counts(result, processed=len(pdf_files), success=success_count, failed=0, skipped=0)
        app.log("\n🎉 [完成] OCR 搜索版 PDF 已全部生成！")
        _set_task_result_finished(
            result,
            "success",
            message="OCR 搜索版 PDF 已全部生成",
            detail=f"成功处理 {success_count} 个文件",
        )
    else:
        _set_task_result_counts(result, processed=success_count + len(failed_list), success=success_count, failed=len(failed_list), skipped=0)
        _set_task_result_finished(result, "stopped", message="用户停止 OCR 任务", detail="用户停止 OCR 任务", stopped=True)


PDF_COMPRESS_LEVELS = {
    "轻度": {"garbage": 2, "clean": False, "deflate": True, "use_objstms": False, "compression_effort": 1},
    "标准": {"garbage": 3, "clean": True, "deflate": True, "use_objstms": True, "compression_effort": 6},
    "强力": {"garbage": 4, "clean": True, "deflate": True, "use_objstms": True, "compression_effort": 9},
}

PDF_IMAGE_COMPRESS_LEVELS = {
    "保留原图": {"enabled": False, "quality": 95, "max_side": None},
    "轻度": {"enabled": True, "quality": 85, "max_side": 2400},
    "标准": {"enabled": True, "quality": 70, "max_side": 1800},
    "强力": {"enabled": True, "quality": 55, "max_side": 1200},
}


def _get_pdf_compress_profile(app):
    level_var = getattr(app, "pdf_compress_level_var", None)
    image_var = getattr(app, "pdf_image_compress_level_var", None)
    try:
        level = str(level_var.get() or "标准").strip() if level_var is not None else "标准"
    except Exception:
        level = "标准"
    try:
        image_level = str(image_var.get() or "标准").strip() if image_var is not None else "标准"
    except Exception:
        image_level = "标准"
    return (
        level if level in PDF_COMPRESS_LEVELS else "标准",
        image_level if image_level in PDF_IMAGE_COMPRESS_LEVELS else "标准",
    )


def _build_pdf_compress_output_path(src, output_folder):
    source = Path(src)
    target_dir = Path(output_folder)
    target = target_dir / f"{source.stem}_压缩{source.suffix}"
    counter = 2
    while target.exists():
        target = target_dir / f"{source.stem}_压缩_{counter}{source.suffix}"
        counter += 1
    return str(target)


def _jpeg_bytes_from_pixmap(pixmap, quality, max_side):
    from PIL import Image

    if pixmap.alpha:
        pixmap = Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")
    else:
        mode = "RGB" if pixmap.n < 4 else "CMYK"
        pixmap = Image.frombytes(mode, (pixmap.width, pixmap.height), pixmap.samples)
        if pixmap.mode != "RGB":
            pixmap = pixmap.convert("RGB")

    if max_side and max(pixmap.size) > max_side:
        pixmap.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    buffer = io.BytesIO()
    pixmap.save(buffer, format="JPEG", quality=int(quality), optimize=True)
    return buffer.getvalue()


def _compress_pdf_images(doc, image_profile):
    import fitz

    if not image_profile.get("enabled"):
        return 0

    seen_xrefs = set()
    changed = 0
    quality = image_profile.get("quality", 70)
    max_side = image_profile.get("max_side")
    for page in doc:
        for image_info in page.get_images(full=True):
            xref = image_info[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            try:
                original = doc.extract_image(xref)
                original_bytes = original.get("image", b"")
                if not original_bytes:
                    continue
                pixmap = fitz.Pixmap(doc, xref)
                if pixmap.width < 96 or pixmap.height < 96:
                    continue
                jpeg_bytes = _jpeg_bytes_from_pixmap(pixmap, quality, max_side)
                if len(jpeg_bytes) >= len(original_bytes) * 0.98:
                    continue
                page.replace_image(xref, stream=jpeg_bytes)
                changed += 1
            except Exception as exc:
                _debug(f"pdf_compress:image_skip:{xref}:{exc}")
    return changed


def compress_pdf_file(src, dst, compress_level="标准", image_level="标准", password=""):
    import fitz

    pdf_profile = PDF_COMPRESS_LEVELS.get(compress_level, PDF_COMPRESS_LEVELS["标准"])
    image_profile = PDF_IMAGE_COMPRESS_LEVELS.get(image_level, PDF_IMAGE_COMPRESS_LEVELS["标准"])
    doc = fitz.open(src)
    try:
        if doc.is_encrypted:
            if not password or not doc.authenticate(password):
                return "ERROR:PDF 已加密，密码不正确或未提供密码。"

        image_changes = _compress_pdf_images(doc, image_profile)
        save_kwargs = {
            "garbage": pdf_profile["garbage"],
            "clean": pdf_profile["clean"],
            "deflate": pdf_profile["deflate"],
            "deflate_images": True,
            "deflate_fonts": True,
            "use_objstms": pdf_profile["use_objstms"],
            "compression_effort": pdf_profile["compression_effort"],
        }
        doc.save(dst, **save_kwargs)
    finally:
        doc.close()

    if not os.path.exists(dst) or os.path.getsize(dst) <= 0:
        return "ERROR:压缩输出文件未生成。"
    return f"SUCCESS:{image_changes}"


def _run_pdf_compress_task(app, input_folder):
    normalized_input, input_root, output_folder = _resolve_result_output_folder(input_folder)
    result = _get_last_task_result(app)
    if result is None:
        result = _start_task_result(app, normalized_input, "pdf")
    _set_task_result_output_root(result, output_folder)
    all_files = app.collect_input_files(normalized_input, "pdf")
    pdf_files = [f for f in all_files if f.lower().endswith(".pdf")]
    if not pdf_files:
        app.log("⚠️ 未找到可压缩的 PDF 文件。")
        _set_task_result_counts(result, processed=0, success=0, failed=0, skipped=1)
        _set_task_result_finished(result, "skipped", message="未找到可压缩的 PDF 文件", detail="未找到可压缩的 PDF 文件", skipped=True)
        return

    os.makedirs(output_folder, exist_ok=True)
    compress_level, image_level = _get_pdf_compress_profile(app)
    password = ""
    if getattr(app, "pdf_pwd_entry", None) is not None:
        try:
            password = app.pdf_pwd_entry.get().strip()
        except Exception:
            password = ""

    tracker = _get_active_progress_tracker(app)
    failed_list = []
    success_count = 0
    total = len(pdf_files)
    app.log(f"📉 [PDF 压缩] 共 {total} 个 PDF，压缩程度：{compress_level}，图片压缩：{image_level}")
    for index, src in enumerate(pdf_files):
        if getattr(app, "stop_event", False):
            app.log("⏹️ [停止] PDF 压缩任务已被用户中止")
            break
        dst = _build_pdf_compress_output_path(src, output_folder)
        should_count_completion = True
        try:
            before_size = os.path.getsize(src)
            app.log(f"📄 [PDF 压缩] 正在处理：{os.path.basename(src)}")
            status = compress_pdf_file(src, dst, compress_level, image_level, password=password)
            if not status.startswith("SUCCESS"):
                failed_list.append(f"{src}: {status}")
                app.log(f"❌ [失败] {os.path.basename(src)}: {status}")
                continue
            after_size = os.path.getsize(dst)
            ratio = 0 if before_size <= 0 else max(0, round((1 - after_size / before_size) * 100, 1))
            image_changes = status.split(":", 1)[1] if ":" in status else "0"
            app.log(f"✅ [PDF 压缩] {os.path.basename(dst)} | 减少 {ratio}% | 图片 {image_changes} 项")
            success_count += 1
            _add_task_result_output(result, dst)
            if getattr(app, "pdf_delete_var", None) is not None:
                try:
                    if bool(app.pdf_delete_var.get()):
                        os.remove(src)
                        app.log(f"🗑️ 已删除源文件：{os.path.basename(src)}")
                except Exception as exc:
                    failed_list.append(f"{src}: 删除源文件失败: {exc}")
        except Exception as exc:
            failed_list.append(f"{src}: {exc}")
            app.log(f"❌ [失败] {os.path.basename(src)}: {exc}")
        finally:
            if should_count_completion:
                if tracker is not None:
                    tracker.complete_units(1)
                else:
                    app.progress_bar.set((index + 1) / total)

    if failed_list:
        result["failed_items"] = list(failed_list)
        _set_task_result_counts(result, processed=total, success=success_count, failed=len(failed_list), skipped=0)
        app.log("\n========= ❌ 失败清单 =========")
        for item in failed_list:
            app.log(f"• {item}")
        report_path = _write_failed_report(output_folder, failed_list)
        if report_path:
            app.log(f"\n📄 [报告] 已生成报告: {report_path}")
            _add_task_result_output(result, report_path)
        app.log(f"PDF 压缩任务结束，但有 {len(failed_list)} 个文件处理失败。")
        _set_task_result_finished(
            result,
            "failed",
            message=f"PDF 压缩任务结束，但有 {len(failed_list)} 个文件处理失败。",
            detail=f"失败 {len(failed_list)} 个文件",
            error=f"失败 {len(failed_list)} 个文件",
        )
    elif not getattr(app, "stop_event", False):
        _set_task_result_counts(result, processed=total, success=success_count, failed=0, skipped=0)
        app.log("\n🎉 [完成] PDF 压缩已全部完成！")
        _set_task_result_finished(
            result,
            "success",
            message="PDF 压缩已全部完成",
            detail=f"成功处理 {success_count} 个文件",
        )
    else:
        _set_task_result_counts(result, processed=success_count + len(failed_list), success=success_count, failed=len(failed_list), skipped=0)
        _set_task_result_finished(result, "stopped", message="用户停止 PDF 压缩任务", detail="用户停止 PDF 压缩任务", stopped=True)


IMAGE_TO_PDF_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def _collect_image_to_pdf_files(app, input_value):
    normalized_input = _normalize_input_path_value(input_value)
    if not normalized_input:
        return []
    if os.path.isfile(normalized_input):
        suffix = Path(normalized_input).suffix.lower()
        return [normalized_input] if suffix in IMAGE_TO_PDF_EXTS else []

    try:
        files = app.collect_input_files(normalized_input, "image")
    except Exception:
        files = []
    image_files = [path for path in files if Path(str(path)).suffix.lower() in IMAGE_TO_PDF_EXTS]
    return sorted(image_files, key=lambda item: os.path.basename(str(item)).lower())


def _build_image_pdf_output_path(src, output_folder):
    source = Path(src)
    candidate = Path(output_folder) / f"{source.stem}.pdf"
    counter = 2
    while candidate.exists():
        candidate = Path(output_folder) / f"{source.stem}_{counter}.pdf"
        counter += 1
    return str(candidate)


def _image_file_to_pdf(src, dst):
    image = PILImage.open(src)
    try:
        if image.mode in {"RGBA", "LA"}:
            background = PILImage.new("RGB", image.size, (255, 255, 255))
            alpha = image.getchannel("A") if "A" in image.getbands() else None
            background.paste(image.convert("RGBA"), mask=alpha)
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")
        image.save(dst, "PDF", resolution=100.0)
    finally:
        try:
            image.close()
        except Exception:
            pass
    if not os.path.exists(dst) or os.path.getsize(dst) <= 0:
        return "ERROR:PDF 输出文件未生成"
    return "SUCCESS"


def _get_image_pdf_mode(app):
    mode_var = getattr(app, "img_mode_var", None)
    try:
        return str(mode_var.get() or "").strip() if mode_var is not None else ""
    except Exception:
        return ""


def _run_image_to_pdf_task(app, input_folder, merge=False):
    normalized_input, input_root, output_folder = _resolve_result_output_folder(input_folder)
    result = _get_last_task_result(app)
    if result is None:
        result = _start_task_result(app, normalized_input, "image")
    _set_task_result_output_root(result, output_folder)
    image_files = _collect_image_to_pdf_files(app, normalized_input)
    if not image_files:
        app.log("⚠️ 未找到可转 PDF 的图片文件。")
        _set_task_result_counts(result, processed=0, success=0, failed=0, skipped=1)
        _set_task_result_finished(result, "skipped", message="未找到可转 PDF 的图片文件", detail="未找到可转 PDF 的图片文件", skipped=True)
        return
    os.makedirs(output_folder, exist_ok=True)

    tracker = _get_active_progress_tracker(app)
    failed_list = []
    success_count = 0
    should_delete = False
    if getattr(app, "img_delete_var", None) is not None:
        try:
            should_delete = bool(app.img_delete_var.get())
        except Exception:
            should_delete = False

    if merge:
        output_name = f"{Path(input_root or normalized_input).name or 'images'}_图集合并.pdf"
        dst = os.path.join(output_folder, output_name)
        app.log(f"🧩 [多图合并PDF] 共 {len(image_files)} 张图片，正在合并...")
        status = merge_images_to_pdf(image_files, dst)
        if status != "SUCCESS" or not os.path.exists(dst):
            failed_list.append(f"{normalized_input}: {status}")
            app.log(f"❌ [失败] 多图合并 PDF: {status}")
        else:
            success_count = len(image_files)
            _add_task_result_output(result, dst)
            app.log(f"✅ [多图合并PDF] 已输出：{os.path.basename(dst)}")
            if should_delete:
                for src in image_files:
                    try:
                        os.remove(src)
                    except Exception as exc:
                        failed_list.append(f"{src}: 删除源文件失败: {exc}")
        if tracker is not None:
            tracker.complete_units(len(image_files))
        else:
            app.progress_bar.set(1)
    else:
        total = len(image_files)
        app.log(f"📄 [图片转PDF] 共 {total} 张图片，逐张生成 PDF...")
        for index, src in enumerate(image_files):
            if getattr(app, "stop_event", False):
                app.log("⏹️ [停止] 图片转 PDF 任务已被用户中止")
                break
            dst = _build_image_pdf_output_path(src, output_folder)
            try:
                status = _image_file_to_pdf(src, dst)
                if status != "SUCCESS":
                    failed_list.append(f"{src}: {status}")
                    app.log(f"❌ [失败] {os.path.basename(src)}: {status}")
                else:
                    success_count += 1
                    _add_task_result_output(result, dst)
                    app.log(f"✅ [图片转PDF] {os.path.basename(src)} -> {os.path.basename(dst)}")
                    if should_delete:
                        os.remove(src)
            except Exception as exc:
                failed_list.append(f"{src}: {exc}")
                app.log(f"❌ [失败] {os.path.basename(src)}: {exc}")
            finally:
                if tracker is not None:
                    tracker.complete_units(1)
                else:
                    app.progress_bar.set((index + 1) / total)

    if failed_list:
        result["failed_items"] = list(failed_list)
        _set_task_result_counts(result, processed=len(image_files), success=success_count, failed=len(failed_list), skipped=0)
        app.log("\n========= ❌ 失败清单 =========")
        for item in failed_list:
            app.log(f"• {item}")
        report_path = _write_failed_report(output_folder, failed_list)
        if report_path:
            app.log(f"\n📄 [报告] 已生成报告: {report_path}")
            _add_task_result_output(result, report_path)
        app.log(f"图片转 PDF 任务结束，但有 {len(failed_list)} 个文件处理失败。")
        _set_task_result_finished(
            result,
            "failed",
            message=f"图片转 PDF 任务结束，但有 {len(failed_list)} 个文件处理失败。",
            detail=f"失败 {len(failed_list)} 个文件",
            error=f"失败 {len(failed_list)} 个文件",
        )
    elif not getattr(app, "stop_event", False):
        _set_task_result_counts(result, processed=len(image_files), success=success_count, failed=0, skipped=0)
        app.log("\n🎉 [完成] 图片 PDF 任务已全部完成！")
        _set_task_result_finished(
            result,
            "success",
            message="图片 PDF 任务已全部完成",
            detail=f"成功处理 {success_count} 个文件",
        )
    else:
        _set_task_result_counts(result, processed=success_count + len(failed_list), success=success_count, failed=len(failed_list), skipped=0)
        _set_task_result_finished(result, "stopped", message="用户停止图片 PDF 任务", detail="用户停止图片 PDF 任务", stopped=True)


def _patch_pdf_ocr_mode():
    try:
        original_init_pdf_ui = FengxiToolboxApp.init_pdf_ui
        original_run_process = FengxiToolboxApp.run_process
    except Exception as exc:
        _debug(f"patch_pdf_ocr_mode:missing:{exc}")
        return

    if getattr(original_init_pdf_ui, "__fx_pdf_ocr_patch__", False):
        return

    def patched_init_pdf_ui(self):
        original_init_pdf_ui(self)
        if getattr(self, "_fx_pdf_ocr_ui_ready", False):
            return
        try:
            from tools.fx_pdf_ocr import (
                build_backend_display_map,
                build_backend_status_text,
                build_profile_display_map,
                default_model_root,
                get_default_backend_display,
                get_default_profile_display,
            )

            card = self.tab_pdf.winfo_children()[0]
            card_children = card.winfo_children()
            header = card_children[0]
            body = card_children[1]

            try:
                header.pack_configure(anchor="w", padx=28, pady=(24, 14))
            except Exception:
                pass
            try:
                body.pack_configure(fill="both", expand=True, padx=28, pady=(0, 20))
            except Exception:
                pass

            if len(body.winfo_children()) >= 5:
                try:
                    body.winfo_children()[4].configure(text="设置密码 (加密模式 / OCR 解密文档可用):")
                except Exception:
                    pass

            self.pdf_ocr_model_root = tkinter.StringVar(value=default_model_root())
            backend_map = build_backend_display_map()
            if not backend_map:
                fallback_backend = get_default_backend_display()
                backend_map = {fallback_backend: "auto"}
            self._fx_pdf_ocr_backend_map = backend_map
            self.pdf_ocr_backend = tkinter.StringVar(
                value=get_default_backend_display()
            )
            lang_map = build_profile_display_map()
            if not lang_map:
                fallback = get_default_profile_display()
                lang_map = {fallback: "general"}
            self._fx_pdf_ocr_lang_map = lang_map
            self.pdf_ocr_language = tkinter.StringVar(
                value=get_default_profile_display()
            )
            self._fx_pdf_ocr_mode_map = {
                "mixed | 混合 OCR / 原文本 (推荐)": "mixed",
                "fullPage | 整页强制 OCR": "fullPage",
                "imageOnly | 仅 OCR 图片": "imageOnly",
            }
            self.pdf_ocr_mode = tkinter.StringVar(value="mixed | 混合 OCR / 原文本 (推荐)")
            self.pdf_ocr_cls = tkinter.BooleanVar(value=False)
            self.pdf_ocr_compare_report = tkinter.BooleanVar(value=False)

            base_controls = list(body.winfo_children())
            merge_text = base_controls[0].cget("text")
            split_text = base_controls[1].cget("text")
            encrypt_text = base_controls[2].cget("text")
            delete_text = base_controls[3].cget("text")
            pwd_label_text = base_controls[4].cget("text")
            pwd_placeholder = base_controls[5].cget("placeholder_text")
            pwd_value = ""
            try:
                pwd_value = base_controls[5].get()
            except Exception:
                pass
            for widget in base_controls:
                try:
                    widget.destroy()
                except Exception:
                    pass

            content_row = customtkinter.CTkFrame(body, fg_color="transparent")
            content_row.pack(fill="both", expand=True, padx=0, pady=(4, 0))

            base_panel = customtkinter.CTkFrame(content_row, fg_color="transparent", width=250)
            base_panel.pack(side="left", fill="y", padx=(0, 14))
            base_panel.pack_propagate(False)

            detail_shell = customtkinter.CTkFrame(content_row, **self._get_panel_style())
            detail_shell.pack(side="left", fill="both", expand=True)
            detail_shell.grid_columnconfigure(0, weight=1)
            detail_shell.grid_rowconfigure(0, weight=1)

            nav_label = customtkinter.CTkLabel(
                base_panel,
                text="PDF 功能",
                text_color="#E6EEF2",
                font=customtkinter.CTkFont(size=14, weight="bold"),
            )
            nav_label.pack(anchor="w", pady=(4, 10))

            mode_buttons = {}

            def select_pdf_mode(mode):
                try:
                    self.pdf_mode_var.set(mode)
                except Exception:
                    pass
                for key, button in mode_buttons.items():
                    try:
                        if key == mode:
                            button.configure(fg_color="#7A695B", border_color="#D0B38A", text_color="#FFFFFF")
                        else:
                            button.configure(fg_color="transparent", border_color="#44515A", text_color="#DDE6EA")
                    except Exception:
                        pass
                for key, panel in self._fx_pdf_detail_panels.items():
                    try:
                        if key == mode:
                            panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
                            panel.tkraise()
                        else:
                            panel.grid_remove()
                    except Exception:
                        pass

            def make_mode_button(mode, title, hint):
                frame = customtkinter.CTkButton(
                    base_panel,
                    text=f"{title}\n{hint}",
                    command=lambda selected=mode: select_pdf_mode(selected),
                    height=54,
                    anchor="w",
                    corner_radius=8,
                    border_width=1,
                    fg_color="transparent",
                    hover_color="#303030",
                    border_color="#44515A",
                    text_color="#DDE6EA",
                    font=customtkinter.CTkFont(size=12),
                )
                frame.pack(fill="x", pady=(0, 7))
                mode_buttons[mode] = frame

            make_mode_button("merge", merge_text, "多份合成一份")
            make_mode_button("split", split_text, "逐页拆分输出")
            make_mode_button("encrypt", encrypt_text, "设置打开密码")
            make_mode_button("compress", "PDF 压缩", "压缩体积和图片")
            make_mode_button("ocr", "OCR 搜索版 PDF", "生成可搜索文字层")

            shared_panel = customtkinter.CTkFrame(base_panel, fg_color="transparent")
            shared_panel.pack(fill="x", pady=(6, 0))

            self.chk_delete = customtkinter.CTkSwitch(
                shared_panel,
                text=delete_text,
                variable=self.pdf_delete_var,
                **self._get_switch_style(),
            )
            self.chk_delete.pack(anchor="w", pady=(0, 10))

            customtkinter.CTkLabel(
                shared_panel,
                text=pwd_label_text,
                text_color=COLOR_TEXT_SOFT,
                font=customtkinter.CTkFont(size=11),
            ).pack(anchor="w", pady=(0, 4))

            self.pdf_pwd_entry = customtkinter.CTkEntry(
                shared_panel,
                placeholder_text=pwd_placeholder,
                **self._get_entry_style(),
            )
            self.pdf_pwd_entry.pack(fill="x")
            if pwd_value:
                try:
                    self.pdf_pwd_entry.insert(0, pwd_value)
                except Exception:
                    pass

            self.pdf_compress_level_var = tkinter.StringVar(value="标准")
            self.pdf_image_compress_level_var = tkinter.StringVar(value="标准")
            self._fx_pdf_detail_panels = {}

            def create_detail_panel(key, title):
                panel = customtkinter.CTkFrame(detail_shell, fg_color="transparent")
                panel.grid_columnconfigure(0, weight=1)
                customtkinter.CTkLabel(
                    panel,
                    text=title,
                    text_color="#E6EEF2",
                    font=customtkinter.CTkFont(size=15, weight="bold"),
                    height=22,
                ).pack(anchor="w", padx=8, pady=(0, 8))
                self._fx_pdf_detail_panels[key] = panel
                return panel

            def add_panel_note(parent, text):
                customtkinter.CTkLabel(
                    parent,
                    text=text,
                    text_color=COLOR_TEXT_SOFT,
                    font=customtkinter.CTkFont(size=12),
                    justify="left",
                    wraplength=620,
                ).pack(anchor="w", fill="x", padx=8, pady=(0, 8))

            merge_panel = create_detail_panel("merge", "PDF 合并")
            add_panel_note(merge_panel, "把输入中的 PDF 按文件名顺序合并为一个 PDF。适合先把文件放进同一个文件夹后统一处理。")

            split_panel = create_detail_panel("split", "PDF 拆分")
            add_panel_note(split_panel, "把每份 PDF 按页面拆成单页文件，并在结果目录中按原文件名建立子文件夹。")

            encrypt_panel = create_detail_panel("encrypt", "PDF 加密")
            add_panel_note(encrypt_panel, "在左侧密码框填写打开密码后开始处理。密码框也兼容加密 PDF 的 OCR 和压缩读取。")

            compress_panel = create_detail_panel("compress", "PDF 压缩")
            add_panel_note(compress_panel, "PDF 压缩程度控制对象清理、字体和数据流压缩；图片压缩程度控制内嵌图片的重压缩和降采样。")
            compress_grid = customtkinter.CTkFrame(compress_panel, fg_color="transparent")
            compress_grid.pack(fill="x", padx=8, pady=(2, 10))
            compress_grid.grid_columnconfigure(0, weight=1)
            compress_grid.grid_columnconfigure(1, weight=1)

            pdf_level_field = customtkinter.CTkFrame(compress_grid, fg_color="transparent")
            pdf_level_field.grid(row=0, column=0, sticky="ew", padx=(0, 8))
            customtkinter.CTkLabel(
                pdf_level_field,
                text="PDF 压缩程度：",
                text_color=COLOR_TEXT_SOFT,
                font=customtkinter.CTkFont(size=11),
            ).pack(anchor="w", pady=(0, 4))
            customtkinter.CTkComboBox(
                pdf_level_field,
                values=list(PDF_COMPRESS_LEVELS.keys()),
                variable=self.pdf_compress_level_var,
                height=32,
                **self._get_combo_style(),
            ).pack(fill="x")

            image_level_field = customtkinter.CTkFrame(compress_grid, fg_color="transparent")
            image_level_field.grid(row=0, column=1, sticky="ew")
            customtkinter.CTkLabel(
                image_level_field,
                text="图片压缩程度：",
                text_color=COLOR_TEXT_SOFT,
                font=customtkinter.CTkFont(size=11),
            ).pack(anchor="w", pady=(0, 4))
            customtkinter.CTkComboBox(
                image_level_field,
                values=list(PDF_IMAGE_COMPRESS_LEVELS.keys()),
                variable=self.pdf_image_compress_level_var,
                height=32,
                **self._get_combo_style(),
            ).pack(fill="x")

            add_panel_note(
                compress_panel,
                "提示：如果 PDF 主要由扫描图片组成，调高图片压缩更有效；如果 PDF 主要是文字，PDF 压缩程度通常更关键。",
            )

            ocr_panel = create_detail_panel("ocr", "OCR 配置")

            customtkinter.CTkLabel(
                ocr_panel,
                text="OCR 模型目录：",
                text_color=COLOR_TEXT_SOFT,
                font=customtkinter.CTkFont(size=11),
                height=18,
            ).pack(anchor="w", padx=8, pady=(0, 2))

            customtkinter.CTkEntry(
                ocr_panel,
                textvariable=self.pdf_ocr_model_root,
                **self._get_entry_style(),
            ).pack(fill="x", padx=8, pady=(0, 6))

            ocr_top_fields = customtkinter.CTkFrame(ocr_panel, fg_color="transparent")
            ocr_top_fields.pack(fill="x", padx=8, pady=(0, 6))

            backend_field = customtkinter.CTkFrame(ocr_top_fields, fg_color="transparent")
            backend_field.pack(side="left", fill="x", expand=True, padx=(0, 8))

            customtkinter.CTkLabel(
                backend_field,
                text="OCR 后端：",
                text_color=COLOR_TEXT_SOFT,
                font=customtkinter.CTkFont(size=11),
                height=18,
            ).pack(anchor="w", pady=(0, 2))

            customtkinter.CTkComboBox(
                backend_field,
                values=list(backend_map.keys()),
                variable=self.pdf_ocr_backend,
                height=32,
                **self._get_combo_style(),
            ).pack(fill="x")

            self.pdf_ocr_backend_status_var = tkinter.StringVar(value="")

            def refresh_pdf_ocr_backend_status(detailed=True):
                try:
                    raw_status = build_backend_status_text(detailed=detailed)
                    summary_parts = []
                    for line in raw_status.splitlines():
                        line = line.strip()
                        if not line.startswith("- "):
                            continue
                        name, _, desc = line[2:].partition(":")
                        short_desc = desc.split("|", 1)[0].strip() if desc else ""
                        summary_parts.append(f"{name.strip()}: {short_desc}")
                    if summary_parts:
                        self.pdf_ocr_backend_status_var.set("后端状态： " + " | ".join(summary_parts))
                    else:
                        self.pdf_ocr_backend_status_var.set(raw_status)
                except Exception as inner_exc:
                    self.pdf_ocr_backend_status_var.set(f"后端状态读取失败：{inner_exc}")

            lang_field = customtkinter.CTkFrame(ocr_top_fields, fg_color="transparent")
            lang_field.pack(side="left", fill="x", expand=True)

            customtkinter.CTkLabel(
                lang_field,
                text="OCR 识别配置：",
                text_color=COLOR_TEXT_SOFT,
                font=customtkinter.CTkFont(size=11),
                height=18,
            ).pack(anchor="w", pady=(0, 2))

            self.pdf_ocr_lang_combo = customtkinter.CTkComboBox(
                lang_field,
                values=list(lang_map.keys()),
                variable=self.pdf_ocr_language,
                height=32,
                **self._get_combo_style(),
            )
            self.pdf_ocr_lang_combo.pack(fill="x")

            ocr_mid_fields = customtkinter.CTkFrame(ocr_panel, fg_color="transparent")
            ocr_mid_fields.pack(fill="x", padx=8, pady=(0, 6))

            mode_field = customtkinter.CTkFrame(ocr_mid_fields, fg_color="transparent")
            mode_field.pack(side="left", fill="x", expand=True, padx=(0, 8))

            customtkinter.CTkLabel(
                mode_field,
                text="提取模式：",
                text_color=COLOR_TEXT_SOFT,
                font=customtkinter.CTkFont(size=11),
                height=18,
            ).pack(anchor="w", pady=(0, 2))

            customtkinter.CTkComboBox(
                mode_field,
                values=list(self._fx_pdf_ocr_mode_map.keys()),
                variable=self.pdf_ocr_mode,
                height=32,
                **self._get_combo_style(),
            ).pack(fill="x")

            refresh_field = customtkinter.CTkFrame(ocr_mid_fields, fg_color="transparent")
            refresh_field.pack(side="left", fill="y")

            customtkinter.CTkLabel(
                refresh_field,
                text="状态检测：",
                text_color=COLOR_TEXT_SOFT,
                font=customtkinter.CTkFont(size=11),
                height=18,
            ).pack(anchor="w", pady=(0, 2))

            customtkinter.CTkButton(
                refresh_field,
                text="刷新状态",
                command=lambda: refresh_pdf_ocr_backend_status(True),
                height=32,
                width=120,
                corner_radius=8,
                border_width=1,
                fg_color="transparent",
                hover_color="#303030",
                border_color="#7A695B",
                text_color="#E7E9EE",
            ).pack(anchor="w")

            customtkinter.CTkLabel(
                ocr_panel,
                textvariable=self.pdf_ocr_backend_status_var,
                text_color=COLOR_TEXT_SOFT,
                font=customtkinter.CTkFont(size=10),
                justify="left",
                wraplength=560,
            ).pack(anchor="w", fill="x", padx=8, pady=(0, 6))

            customtkinter.CTkSwitch(
                ocr_panel,
                text="纠正文本方向",
                variable=self.pdf_ocr_cls,
                **self._get_switch_style(),
            ).pack(anchor="w", padx=8, pady=(0, 4))

            customtkinter.CTkSwitch(
                ocr_panel,
                text="生成后端对比报告（首页）",
                variable=self.pdf_ocr_compare_report,
                **self._get_switch_style(),
            ).pack(anchor="w", padx=8, pady=(0, 4))

            customtkinter.CTkLabel(
                ocr_panel,
                text="说明：生成双层可搜索 PDF，保留原页面画面并叠加透明文字层。",
                text_color=COLOR_TEXT_SOFT,
                font=customtkinter.CTkFont(size=10),
                justify="left",
                wraplength=560,
            ).pack(anchor="w", fill="x", padx=8, pady=(0, 2))

            self.pdf_ocr_backend_status_var.set("后端状态：按需检测，可直接运行 OCR；如需查看详细可用性再点刷新。")
            try:
                select_pdf_mode(self.pdf_mode_var.get())
            except Exception:
                select_pdf_mode("merge")

            self._fx_pdf_ocr_ui_ready = True
        except Exception as exc:
            _debug(f"patch_pdf_ocr_mode:init_ui_error:{exc}")

    def patched_run_process(self, input_folder, task_type):
        if task_type == "pdf":
            try:
                pdf_mode = self.pdf_mode_var.get() if getattr(self, "pdf_mode_var", None) is not None else ""
                if pdf_mode == "compress":
                    try:
                        _run_pdf_compress_task(self, input_folder)
                    except Exception as exc:
                        self.log(f"🔥 [严重错误] {exc}")
                    finally:
                        self.reset_ui()
                    return
                if pdf_mode == "ocr":
                    try:
                        _run_pdf_ocr_task(self, input_folder)
                    except Exception as exc:
                        self.log(f"🔥 [严重错误] {exc}")
                    finally:
                        self.reset_ui()
                    return
            except Exception as exc:
                _debug(f"patch_pdf_ocr_mode:run_process_error:{exc}")
        return original_run_process(self, input_folder, task_type)

    patched_init_pdf_ui.__fx_pdf_ocr_patch__ = True
    patched_run_process.__fx_pdf_ocr_patch__ = True
    FengxiToolboxApp.init_pdf_ui = patched_init_pdf_ui
    FengxiToolboxApp.run_process = patched_run_process
    _debug("patch_pdf_ocr_mode:installed")


_patch_pdf_ocr_mode()


def _patch_image_pdf_modes():
    try:
        original_init_img_ui = FengxiToolboxApp.init_img_ui
        original_run_process = FengxiToolboxApp.run_process
    except Exception as exc:
        _debug(f"patch_image_pdf_modes:missing:{exc}")
        return

    if getattr(original_init_img_ui, "__fx_image_pdf_patch__", False):
        return

    def patched_init_img_ui(self):
        original_init_img_ui(self)
        if getattr(self, "_fx_image_pdf_ui_ready", False):
            return
        try:
            card = self.tab_img.winfo_children()[0]
            body = card.winfo_children()[1]
            children = list(body.winfo_children())
            insert_after = children[2] if len(children) > 2 else None
            pdf_modes_frame = customtkinter.CTkFrame(body, fg_color="transparent")
            if insert_after is not None:
                pdf_modes_frame.pack(after=insert_after, fill="x", pady=(0, 8))
            else:
                pdf_modes_frame.pack(fill="x", pady=(0, 8))

            customtkinter.CTkRadioButton(
                pdf_modes_frame,
                text="图片转 PDF (Single Image PDF)",
                variable=self.img_mode_var,
                value="to_pdf",
                **self._get_radio_style(),
            ).pack(anchor="w", pady=(0, 6))

            customtkinter.CTkRadioButton(
                pdf_modes_frame,
                text="多图合并 PDF (Merge Images PDF)",
                variable=self.img_mode_var,
                value="merge_pdf",
                **self._get_radio_style(),
            ).pack(anchor="w", pady=(0, 2))

            customtkinter.CTkLabel(
                pdf_modes_frame,
                text="图片转 PDF 会为每张图片生成一个 PDF；多图合并 PDF 会按文件名顺序合成一份 PDF。",
                text_color=COLOR_TEXT_SOFT,
                font=customtkinter.CTkFont(size=11),
                justify="left",
                wraplength=560,
            ).pack(anchor="w", fill="x", pady=(4, 0))
            self._fx_image_pdf_ui_ready = True
        except Exception as exc:
            _debug(f"patch_image_pdf_modes:init_ui_error:{exc}")

    def patched_run_process(self, input_folder, task_type):
        if task_type == "image":
            try:
                image_mode = _get_image_pdf_mode(self)
                if image_mode == "to_pdf":
                    try:
                        _run_image_to_pdf_task(self, input_folder, merge=False)
                    except Exception as exc:
                        self.log(f"🔥 [严重错误] {exc}")
                    finally:
                        self.reset_ui()
                    return
                if image_mode == "merge_pdf":
                    try:
                        _run_image_to_pdf_task(self, input_folder, merge=True)
                    except Exception as exc:
                        self.log(f"🔥 [严重错误] {exc}")
                    finally:
                        self.reset_ui()
                    return
            except Exception as exc:
                _debug(f"patch_image_pdf_modes:run_process_error:{exc}")
        return original_run_process(self, input_folder, task_type)

    patched_init_img_ui.__fx_image_pdf_patch__ = True
    patched_run_process.__fx_image_pdf_patch__ = True
    FengxiToolboxApp.init_img_ui = patched_init_img_ui
    FengxiToolboxApp.run_process = patched_run_process
    _debug("patch_image_pdf_modes:installed")


_patch_image_pdf_modes()


def _iter_widget_tree(widget):
    if widget is None:
        return
    yield widget
    try:
        children = widget.winfo_children()
    except Exception:
        children = []
    for child in children:
        yield from _iter_widget_tree(child)


def _find_watermark_skip_switch(root_widget):
    for widget in _iter_widget_tree(root_widget):
        if not isinstance(widget, customtkinter.CTkSwitch):
            continue
        try:
            label = str(widget.cget("text") or "")
        except Exception:
            continue
        if "-" not in label:
            continue
        if "文件名" in label or "结尾" in label:
            return widget
    return None


def _get_option_menu_style(combo_style):
    allowed_keys = {
        "corner_radius",
        "fg_color",
        "button_color",
        "button_hover_color",
        "text_color",
        "text_color_disabled",
        "dropdown_fg_color",
        "dropdown_hover_color",
        "dropdown_text_color",
        "font",
        "dropdown_font",
        "state",
        "hover",
        "dynamic_resizing",
        "anchor",
    }
    return {key: value for key, value in dict(combo_style or {}).items() if key in allowed_keys}


def _get_watermark_filename_rule(app):
    skip_var = getattr(app, "wm_skip_hyphen_var", None)
    if skip_var is None:
        return None
    try:
        enabled = bool(skip_var.get())
    except Exception:
        enabled = False
    if not enabled:
        return None

    mode_var = getattr(app, "wm_skip_name_position_var", None)
    marker_var = getattr(app, "wm_skip_name_text_var", None)

    try:
        mode_label = str(mode_var.get() or "结尾").strip() if mode_var is not None else "结尾"
    except Exception:
        mode_label = "结尾"
    try:
        marker_text = str(marker_var.get() or "").strip() if marker_var is not None else ""
    except Exception:
        marker_text = ""

    if not marker_text:
        marker_text = "-"
    mode = "prefix" if mode_label == "开头" else "suffix"
    return mode, marker_text


def _watermark_filename_matches_rule(name_no_ext, mode, marker):
    normalized_name = str(name_no_ext or "")
    normalized_marker = str(marker or "")
    if not normalized_name or not normalized_marker:
        return False
    if mode == "prefix":
        return normalized_name.startswith(normalized_marker)
    return normalized_name.endswith(normalized_marker)


def _get_user_pref_root():
    local_app_data = (os.environ.get("LOCALAPPDATA") or "").strip()
    if local_app_data:
        return Path(local_app_data) / "FengxiToolbox"
    try:
        return Path.home() / ".fengxi_toolbox"
    except Exception:
        return Path(__file__).resolve().parent


def _get_user_pref_file():
    return _get_user_pref_root() / "user_prefs.json"


def _get_queue_history_file():
    return _get_user_pref_root() / "queue_history.json"


def _load_user_prefs():
    path = _get_user_pref_file()
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _debug(f"user_prefs:load_error:{exc}")
    return {}


def _save_user_prefs(data):
    path = _get_user_pref_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        _debug(f"user_prefs:save_error:{exc}")


def _get_saved_watermark_text():
    prefs = _load_user_prefs()
    watermark_prefs = prefs.get("watermark")
    if isinstance(watermark_prefs, dict):
        value = watermark_prefs.get("text")
        if isinstance(value, str):
            return value
    return ""


def _save_watermark_text(value):
    normalized = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    prefs = _load_user_prefs()
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

    _save_user_prefs(prefs)


def _get_saved_watermark_filename_rule_settings():
    prefs = _load_user_prefs()
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
    if isinstance(position, str) and position in ("开头", "结尾"):
        saved["position"] = position

    marker = settings.get("marker")
    if isinstance(marker, str):
        saved["marker"] = marker
    return saved


def _save_watermark_filename_rule_settings(app):
    skip_var = getattr(app, "wm_skip_hyphen_var", None)
    mode_var = getattr(app, "wm_skip_name_position_var", None)
    marker_var = getattr(app, "wm_skip_name_text_var", None)
    if skip_var is None and mode_var is None and marker_var is None:
        return

    prefs = _load_user_prefs()
    watermark_prefs = prefs.get("watermark")
    if not isinstance(watermark_prefs, dict):
        watermark_prefs = {}

    enabled = False
    position = "结尾"
    marker = "-"

    try:
        if skip_var is not None:
            enabled = bool(skip_var.get())
    except Exception:
        enabled = False

    try:
        if mode_var is not None:
            raw_position = str(mode_var.get() or "").strip()
            if raw_position in ("开头", "结尾"):
                position = raw_position
    except Exception:
        position = "结尾"

    try:
        if marker_var is not None:
            marker = str(marker_var.get() or "")
    except Exception:
        marker = "-"

    watermark_prefs["filename_skip_rule"] = {
        "enabled": enabled,
        "position": position,
        "marker": marker,
    }
    prefs["watermark"] = watermark_prefs
    _save_user_prefs(prefs)


def _flush_watermark_filename_rule_persistence(app):
    if getattr(app, "_fx_wm_filename_rule_loading", False):
        return
    after_id = getattr(app, "_fx_wm_filename_rule_save_after_id", None)
    if after_id is not None:
        try:
            app.after_cancel(after_id)
        except Exception:
            pass
        app._fx_wm_filename_rule_save_after_id = None
    _save_watermark_filename_rule_settings(app)


def _schedule_watermark_filename_rule_persistence(app, delay_ms=300):
    if getattr(app, "_fx_wm_filename_rule_loading", False):
        return
    after_id = getattr(app, "_fx_wm_filename_rule_save_after_id", None)
    if after_id is not None:
        try:
            app.after_cancel(after_id)
        except Exception:
            pass

    def persist_later(target=app):
        target._fx_wm_filename_rule_save_after_id = None
        _save_watermark_filename_rule_settings(target)

    try:
        app._fx_wm_filename_rule_save_after_id = app.after(delay_ms, persist_later)
    except Exception:
        _flush_watermark_filename_rule_persistence(app)


def _install_watermark_filename_rule_memory(app):
    if getattr(app, "_fx_wm_filename_rule_memory_ready", False):
        return

    skip_var = getattr(app, "wm_skip_hyphen_var", None)
    mode_var = getattr(app, "wm_skip_name_position_var", None)
    marker_var = getattr(app, "wm_skip_name_text_var", None)

    saved = _get_saved_watermark_filename_rule_settings()
    try:
        app._fx_wm_filename_rule_loading = True
        if "enabled" in saved and skip_var is not None:
            skip_var.set(bool(saved["enabled"]))
        if "position" in saved and mode_var is not None:
            mode_var.set(saved["position"])
        if "marker" in saved and marker_var is not None:
            marker_var.set(saved["marker"])
    except Exception as exc:
        _debug(f"wm_filename_rule_memory:load_error:{exc}")
    finally:
        app._fx_wm_filename_rule_loading = False

    def on_var_change(*_args, target=app):
        _schedule_watermark_filename_rule_persistence(target)

    def on_focus_out(_event=None, target=app):
        _flush_watermark_filename_rule_persistence(target)

    for var in (skip_var, mode_var, marker_var):
        try:
            if var is not None:
                var.trace_add("write", on_var_change)
        except Exception:
            pass

    entry = getattr(app, "wm_skip_name_entry", None)
    if entry is not None:
        try:
            entry.bind("<FocusOut>", on_focus_out, add="+")
            entry.bind("<Return>", on_focus_out, add="+")
        except Exception:
            pass

    app._fx_wm_filename_rule_memory_ready = True


def _read_watermark_text_widget(app):
    widget = getattr(app, "wm_text", None)
    if widget is None:
        return ""
    try:
        return widget.get("1.0", "end-1c")
    except Exception:
        return ""


def _flush_watermark_text_persistence(app):
    if getattr(app, "_fx_wm_text_loading", False):
        return
    after_id = getattr(app, "_fx_wm_text_save_after_id", None)
    if after_id is not None:
        try:
            app.after_cancel(after_id)
        except Exception:
            pass
        app._fx_wm_text_save_after_id = None
    _save_watermark_text(_read_watermark_text_widget(app))


def _schedule_watermark_text_persistence(app, delay_ms=400):
    if getattr(app, "_fx_wm_text_loading", False):
        return
    after_id = getattr(app, "_fx_wm_text_save_after_id", None)
    if after_id is not None:
        try:
            app.after_cancel(after_id)
        except Exception:
            pass

    def persist_later(target=app):
        target._fx_wm_text_save_after_id = None
        _save_watermark_text(_read_watermark_text_widget(target))

    try:
        app._fx_wm_text_save_after_id = app.after(delay_ms, persist_later)
    except Exception:
        _flush_watermark_text_persistence(app)


def _install_watermark_text_memory(app):
    widget = getattr(app, "wm_text", None)
    if widget is None or getattr(app, "_fx_wm_text_memory_ready", False):
        return

    saved_text = _get_saved_watermark_text()
    if saved_text:
        current_text = _read_watermark_text_widget(app)
        if current_text != saved_text:
            try:
                app._fx_wm_text_loading = True
                widget.delete("1.0", "end")
                widget.insert("1.0", saved_text)
            except Exception as exc:
                _debug(f"wm_text_memory:load_error:{exc}")
            finally:
                app._fx_wm_text_loading = False

    def on_change(_event=None, target=app):
        _schedule_watermark_text_persistence(target)

    def on_focus_out(_event=None, target=app):
        _flush_watermark_text_persistence(target)

    try:
        widget.bind("<KeyRelease>", on_change, add="+")
        widget.bind("<FocusOut>", on_focus_out, add="+")
    except Exception:
        pass

    inner_text = getattr(widget, "_textbox", None)
    if inner_text is not None:
        try:
            inner_text.bind("<KeyRelease>", on_change, add="+")
            inner_text.bind("<FocusOut>", on_focus_out, add="+")
            inner_text.bind("<<Paste>>", on_change, add="+")
        except Exception:
            pass

    app._fx_wm_text_memory_ready = True


def _patch_watermark_filename_rule_ui():
    try:
        original_init_watermark_ui = FengxiToolboxApp.init_watermark_ui
        original_collect_input_files = FengxiToolboxApp.collect_input_files
        original_run_process = FengxiToolboxApp.run_process
    except Exception as exc:
        _debug(f"patch_watermark_filename_rule:missing:{exc}")
        return

    if getattr(original_init_watermark_ui, "__fx_watermark_filename_rule_patch__", False):
        return

    def patched_init_watermark_ui(self):
        original_init_watermark_ui(self)
        if getattr(self, "_fx_wm_filename_rule_ui_ready", False):
            return
        try:
            self.wm_skip_name_position_var = tkinter.StringVar(value="结尾")
            self.wm_skip_name_text_var = tkinter.StringVar(value="-")

            skip_switch = _find_watermark_skip_switch(getattr(self, "tab_wm", None))
            controls_parent = getattr(skip_switch, "master", None) if skip_switch is not None else None
            controls_row = customtkinter.CTkFrame(
                controls_parent if controls_parent is not None else self.tab_wm,
                height=56,
                fg_color="transparent",
            )
            controls_row._fx_wm_filename_rule_controls = True
            try:
                controls_row.pack_propagate(False)
            except Exception:
                pass

            if skip_switch is not None:
                try:
                    skip_switch.configure(text="按文件名规则跳过")
                except Exception:
                    pass
                controls_row.pack(after=skip_switch, fill="x", padx=0, pady=(0, 4))
            else:
                controls_row.grid(row=99, column=0, columnspan=2, sticky="ew", padx=18, pady=(4, 8))

            combo_style = {}
            try:
                combo_style = self._get_combo_style()
            except Exception:
                combo_style = {}
            option_menu_style = _get_option_menu_style(combo_style)

            fields_row = customtkinter.CTkFrame(controls_row, fg_color="transparent", height=30)
            fields_row.pack(fill="x", pady=(0, 2))

            customtkinter.CTkLabel(
                fields_row,
                text="匹配位置",
                text_color=globals().get("COLOR_TEXT_SOFT"),
                font=customtkinter.CTkFont(size=11),
                height=30,
            ).pack(side="left", padx=(0, 8))

            customtkinter.CTkOptionMenu(
                fields_row,
                variable=self.wm_skip_name_position_var,
                values=["结尾", "开头"],
                width=82,
                height=30,
                **option_menu_style,
            ).pack(side="left", padx=(0, 8))

            self.wm_skip_name_entry = customtkinter.CTkEntry(
                fields_row,
                width=126,
                height=30,
                textvariable=self.wm_skip_name_text_var,
                placeholder_text="-",
            )
            self.wm_skip_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 0))

            customtkinter.CTkLabel(
                controls_row,
                text="留空默认 “-”，可填写任意开头或结尾字符",
                text_color=globals().get("COLOR_TEXT_SOFT"),
                font=customtkinter.CTkFont(size=11),
                height=18,
                anchor="w",
            ).pack(anchor="w", fill="x")
            _install_watermark_filename_rule_memory(self)
        except Exception as exc:
            _debug(f"patch_watermark_filename_rule:init_ui_error:{exc}")
        self._fx_wm_filename_rule_ui_ready = True

    def patched_collect_input_files(self, input_folder, task_type):
        files = original_collect_input_files(self, input_folder, task_type)
        if task_type != "watermark":
            return files

        rule = getattr(self, "_fx_wm_filename_rule_runtime", None)
        if not rule:
            return files

        mode, marker = rule
        filtered_files = []
        skipped_files = []
        for path in files:
            try:
                name_no_ext = os.path.splitext(os.path.basename(str(path)))[0]
            except Exception:
                filtered_files.append(path)
                continue
            if _watermark_filename_matches_rule(name_no_ext, mode, marker):
                skipped_files.append(path)
            else:
                filtered_files.append(path)

        if skipped_files:
            try:
                direction = "开头" if mode == "prefix" else "结尾"
                preview = ", ".join(os.path.basename(item) for item in skipped_files[:5])
                if len(skipped_files) > 5:
                    preview = f"{preview} 等 {len(skipped_files)} 个文件"
                self.log(f"⏭️ [智能水印] 已跳过文件名{direction}为“{marker}”的文件：{preview}")
            except Exception:
                pass
        return filtered_files

    def patched_run_process(self, input_folder, task_type):
        if task_type != "watermark":
            return original_run_process(self, input_folder, task_type)

        try:
            _flush_watermark_filename_rule_persistence(self)
        except Exception as exc:
            _debug(f"patch_watermark_filename_rule:flush_before_run_error:{exc}")

        rule = _get_watermark_filename_rule(self)
        if not rule:
            return original_run_process(self, input_folder, task_type)

        skip_var = getattr(self, "wm_skip_hyphen_var", None)
        previous_runtime_rule = getattr(self, "_fx_wm_filename_rule_runtime", None)
        previous_skip_value = None
        restore_skip_value = False
        previous_rule_loading = getattr(self, "_fx_wm_filename_rule_loading", False)
        try:
            self._fx_wm_filename_rule_runtime = rule
            if skip_var is not None:
                try:
                    self._fx_wm_filename_rule_loading = True
                    previous_skip_value = skip_var.get()
                    skip_var.set(False)
                    restore_skip_value = True
                except Exception as exc:
                    _debug(f"patch_watermark_filename_rule:disable_builtin_skip_error:{exc}")
            return original_run_process(self, input_folder, task_type)
        finally:
            self._fx_wm_filename_rule_runtime = previous_runtime_rule
            if restore_skip_value and skip_var is not None:
                try:
                    skip_var.set(previous_skip_value)
                except Exception:
                    pass
            self._fx_wm_filename_rule_loading = previous_rule_loading

    patched_init_watermark_ui.__fx_watermark_filename_rule_patch__ = True
    patched_collect_input_files.__fx_watermark_filename_rule_patch__ = True
    patched_run_process.__fx_watermark_filename_rule_patch__ = True
    FengxiToolboxApp.init_watermark_ui = patched_init_watermark_ui
    FengxiToolboxApp.collect_input_files = patched_collect_input_files
    FengxiToolboxApp.run_process = patched_run_process
    _debug("patch_watermark_filename_rule:installed")


_patch_watermark_filename_rule_ui()


def _patch_watermark_text_memory_ui():
    try:
        original_init_watermark_ui = FengxiToolboxApp.init_watermark_ui
        original_on_start_click = FengxiToolboxApp.on_start_click
    except Exception as exc:
        _debug(f"patch_watermark_text_memory:missing:{exc}")
        return

    if getattr(original_init_watermark_ui, "__fx_wm_text_memory_patch__", False):
        return

    def patched_init_watermark_ui(self):
        original_init_watermark_ui(self)
        try:
            _install_watermark_text_memory(self)
        except Exception as exc:
            _debug(f"patch_watermark_text_memory:init_error:{exc}")

    def patched_on_start_click(self):
        if getattr(self, "current_task", None) == "watermark":
            try:
                _flush_watermark_text_persistence(self)
            except Exception as exc:
                _debug(f"patch_watermark_text_memory:flush_before_run_error:{exc}")
        return original_on_start_click(self)

    patched_init_watermark_ui.__fx_wm_text_memory_patch__ = True
    patched_on_start_click.__fx_wm_text_memory_patch__ = True
    FengxiToolboxApp.init_watermark_ui = patched_init_watermark_ui
    FengxiToolboxApp.on_start_click = patched_on_start_click
    _debug("patch_watermark_text_memory:installed")


_patch_watermark_text_memory_ui()


def _patch_remove_wm_output_ui():
    try:
        original_init_remove_wm_ui = FengxiToolboxApp.init_remove_wm_ui
    except Exception as exc:
        _debug(f"patch_remove_wm_output_ui:missing:{exc}")
        return

    if getattr(original_init_remove_wm_ui, "__fx_remove_wm_output_ui_patch__", False):
        return

    def patched_init_remove_wm_ui(self):
        original_init_remove_wm_ui(self)
        if getattr(self, "_fx_remove_wm_output_ui_ready", False):
            return
        try:
            self.rm_wm_overwrite_original = tkinter.BooleanVar(value=False)
            card = self.tab_rm_wm.winfo_children()[0]
            body = card.winfo_children()[1]
            widgets = body.winfo_children()
            separator = widgets[4] if len(widgets) > 4 else None

            switch = customtkinter.CTkSwitch(
                body,
                text="单文件时直接覆盖原文件（谨慎）",
                variable=self.rm_wm_overwrite_original,
                **self._get_switch_style(),
            )
            switch.pack(anchor="w", padx=0, pady=(4, 10))
            if separator is not None:
                switch.pack_configure(before=separator)

            note = customtkinter.CTkLabel(
                body,
                text="说明：单文件默认在同目录生成新的“_去水印”文件；开启后仅在处理成功时替换原文件。文件夹模式仍输出到【处理完成】结果文件夹。",
                text_color=COLOR_TEXT_SOFT,
                font=customtkinter.CTkFont(size=11),
                justify="left",
                wraplength=620,
            )
            note.pack(anchor="w", padx=0, pady=(0, 8))
            if separator is not None:
                note.pack_configure(before=separator)
        except Exception as exc:
            _debug(f"patch_remove_wm_output_ui:error:{exc}")
        self._fx_remove_wm_output_ui_ready = True

    patched_init_remove_wm_ui.__fx_remove_wm_output_ui_patch__ = True
    FengxiToolboxApp.init_remove_wm_ui = patched_init_remove_wm_ui
    _debug("patch_remove_wm_output_ui:installed")


_patch_remove_wm_output_ui()


def _patch_remove_wm_pdf_fallback():
    try:
        original_run_process = FengxiToolboxApp.run_process
    except Exception as exc:
        _debug(f"patch_remove_wm_pdf_fallback:missing:{exc}")
        return

    if getattr(original_run_process, "__fx_remove_wm_pdf_patch__", False):
        return

    def patched_run_process(self, input_folder, task_type):
        if task_type == "remove_wm":
            try:
                all_files = self.collect_input_files(input_folder, task_type)
                if any(path.lower().endswith(".pdf") for path in all_files):
                    try:
                        _run_remove_wm_task(self, input_folder, original_run_process)
                    except Exception as exc:
                        self.log(f"🔥 [严重错误] {exc}")
                    finally:
                        self.reset_ui()
                    return
            except Exception as exc:
                _debug(f"patch_remove_wm_pdf_fallback:run_process_error:{exc}")
        return original_run_process(self, input_folder, task_type)

    patched_run_process.__fx_remove_wm_pdf_patch__ = True
    FengxiToolboxApp.run_process = patched_run_process
    _debug("patch_remove_wm_pdf_fallback:installed")


_patch_remove_wm_pdf_fallback()


def _make_queue_task_id():
    return f"task_{int(time.time() * 1000)}_{os.getpid()}"


def _format_queue_time(timestamp=None):
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(timestamp or time.time())))
    except Exception:
        return time.strftime("%Y-%m-%d %H:%M:%S")


def _safe_widget_get(widget):
    try:
        if isinstance(widget, customtkinter.CTkTextbox):
            return widget.get("1.0", "end-1c")
        if hasattr(widget, "get"):
            return widget.get()
    except Exception:
        return None
    return None


def _safe_widget_set(widget, value):
    try:
        if isinstance(widget, customtkinter.CTkTextbox):
            widget.delete("1.0", "end")
            widget.insert("1.0", str(value or ""))
            return True
        if isinstance(widget, customtkinter.CTkEntry):
            widget.delete(0, "end")
            widget.insert(0, str(value or ""))
            return True
        if hasattr(widget, "set"):
            widget.set(value)
            return True
    except Exception:
        return False
    return False


def _queue_snapshot_app_state(app, task_type):
    variables = {}
    widgets = {}
    try:
        _ensure_lazy_tab_initialized(app, task_type)
    except Exception as exc:
        _debug(f"queue:snapshot_lazy_error:{task_type}:{exc}")

    for name, value in list(vars(app).items()):
        try:
            if isinstance(value, tkinter.Variable):
                variables[name] = value.get()
        except Exception:
            pass
        try:
            if isinstance(
                value,
                (
                    customtkinter.CTkEntry,
                    customtkinter.CTkTextbox,
                    customtkinter.CTkComboBox,
                    customtkinter.CTkOptionMenu,
                ),
            ):
                widget_value = _safe_widget_get(value)
                if widget_value is not None:
                    widgets[name] = widget_value
        except Exception:
            pass
    return {"variables": variables, "widgets": widgets}


def _queue_restore_app_state(app, task):
    task_type = task.get("task_type")
    if task_type:
        try:
            _ensure_lazy_tab_initialized(app, task_type)
        except Exception as exc:
            _debug(f"queue:restore_lazy_error:{task_type}:{exc}")
    snapshot = task.get("snapshot") if isinstance(task, dict) else {}
    if not isinstance(snapshot, dict):
        return
    variables = snapshot.get("variables") if isinstance(snapshot.get("variables"), dict) else {}
    widgets = snapshot.get("widgets") if isinstance(snapshot.get("widgets"), dict) else {}
    for name, value in variables.items():
        try:
            var = getattr(app, name, None)
            if isinstance(var, tkinter.Variable):
                var.set(value)
        except Exception:
            pass
    for name, value in widgets.items():
        try:
            widget = getattr(app, name, None)
            _safe_widget_set(widget, value)
        except Exception:
            pass
    try:
        if task.get("input"):
            app.input_path.set(task.get("input"))
    except Exception:
        pass
    if task_type:
        try:
            app.current_task = task_type
        except Exception:
            pass


def _queue_describe_task(app, task_type, input_path):
    label = QUEUE_TASK_LABELS.get(task_type, task_type or "未知任务")
    name = os.path.basename(str(input_path or "").rstrip("\\/")) or str(input_path or "未选择路径")
    detail = ""
    try:
        if task_type == "pdf" and getattr(app, "pdf_mode_var", None) is not None:
            detail = app.pdf_mode_var.get()
        elif task_type == "image" and getattr(app, "img_mode_var", None) is not None:
            detail = app.img_mode_var.get()
        elif task_type == "zip" and getattr(app, "zip_mode_var", None) is not None:
            detail = app.zip_mode_var.get()
        elif task_type == "convert" and getattr(app, "cv_mode", None) is not None:
            detail = app.cv_mode.get()
        elif task_type == "file" and getattr(app, "file_mode_var", None) is not None:
            detail = app.file_mode_var.get()
        elif task_type == "watermark":
            detail = "add"
        elif task_type == "remove_wm":
            detail = "remove"
    except Exception:
        detail = ""
    suffix = f" · {detail}" if detail else ""
    return f"{label}{suffix} · {name}"


def _load_queue_history():
    path = _get_queue_history_file()
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
    except Exception as exc:
        _debug(f"queue:history_load_error:{exc}")
    return []


def _save_queue_history(entries):
    path = _get_queue_history_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        safe_entries = list(entries or [])[-QUEUE_HISTORY_LIMIT:]
        path.write_text(json.dumps(safe_entries, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        _debug(f"queue:history_save_error:{exc}")


def _normalize_queue_history_entry(task):
    entry = dict(task or {})
    entry.pop("status_var", None)
    entry.pop("row", None)
    entry.pop("action_button", None)
    entry.pop("index_label", None)
    entry.pop("retry_source_id", None)
    entry.pop("retry_staging_root", None)
    entry.pop("retry_mode", None)
    entry.pop("retry_failed_items", None)
    task_result = entry.get("task_result")
    if isinstance(task_result, dict):
        entry["task_result"] = {
            "task_type": task_result.get("task_type", ""),
            "input": task_result.get("input", ""),
            "status": task_result.get("status", ""),
            "success": bool(task_result.get("success", False)),
            "stopped": bool(task_result.get("stopped", False)),
            "skipped": bool(task_result.get("skipped", False)),
            "message": task_result.get("message", ""),
            "detail": task_result.get("detail", ""),
            "error": task_result.get("error", ""),
            "outputs": list(task_result.get("outputs") or []),
            "output_root": task_result.get("output_root", ""),
            "failed_items": list(task_result.get("failed_items") or []),
            "processed_count": int(task_result.get("processed_count") or 0),
            "success_count": int(task_result.get("success_count") or 0),
            "failed_count": int(task_result.get("failed_count") or 0),
            "skipped_count": int(task_result.get("skipped_count") or 0),
            "started_at": task_result.get("started_at"),
            "finished_at": task_result.get("finished_at"),
            "duration_seconds": float(task_result.get("duration_seconds") or 0.0),
        }
    return entry


def _append_queue_history(app, task):
    history = getattr(app, "_fx_task_history", None)
    if history is None:
        history = _load_queue_history()
        app._fx_task_history = history
    history.append(_normalize_queue_history_entry(task))
    if len(history) > QUEUE_HISTORY_LIMIT:
        del history[:-QUEUE_HISTORY_LIMIT]
    _save_queue_history(history)


def _queue_status_text(status):
    return QUEUE_STATUS_LABELS.get(status, status or "")


def _queue_status_color(status):
    if status == "success":
        return "#A7D39B"
    if status == "failed":
        return "#F0A6A6"
    if status == "skipped":
        return "#B5C0CC"
    if status == "running":
        return "#F6D28B"
    if status == "stopped":
        return "#B5C0CC"
    return globals().get("COLOR_TEXT_SOFT", "#B2C0C8")


def _build_queue_history_search_blob(entry):
    parts = [
        entry.get("title", ""),
        entry.get("input", ""),
        entry.get("detail", ""),
        entry.get("error", ""),
        entry.get("output_root", ""),
        _queue_status_text(entry.get("status")),
    ]
    task_result = entry.get("task_result")
    if isinstance(task_result, dict):
        failure_kind, failure_reason = _classify_failure_reason(entry)
        parts.extend(
            [
                task_result.get("message", ""),
                task_result.get("detail", ""),
                task_result.get("error", ""),
                task_result.get("output_root", ""),
                failure_kind,
                failure_reason,
            ]
        )
        parts.extend(list(task_result.get("outputs") or []))
        parts.extend(list(task_result.get("failed_items") or []))
    return " ".join(str(item or "") for item in parts).lower()


def _classify_failure_reason(entry):
    item = dict(entry or {})
    task_result = item.get("task_result") if isinstance(item.get("task_result"), dict) else {}
    error_text = str(task_result.get("error") or item.get("error") or "").strip()
    detail_text = str(task_result.get("detail") or item.get("detail") or "").strip()
    logs = [str(text).strip() for text in (item.get("logs") or []) if str(text).strip()]
    failed_items = list(task_result.get("failed_items") or item.get("failed_items") or [])
    reason_text = error_text or detail_text
    if not reason_text and logs:
        reason_text = logs[-1]
    reason_lower = reason_text.lower()
    if any(marker in reason_lower for marker in ("路径不存在", "not found", "no such file", "找不到", "不存在")):
        return "path_missing", reason_text
    if any(marker in reason_lower for marker in ("权限", "access denied", "permission", "拒绝访问")):
        return "permission", reason_text
    if any(marker in reason_lower for marker in ("超时", "timeout", "timed out")):
        return "timeout", reason_text
    if any(marker in reason_lower for marker in ("依赖", "dll", "库", "module", "import", "onnxruntime", "com")):
        return "dependency", reason_text
    if failed_items:
        return "partial_failure", reason_text or f"{len(failed_items)} 个失败项"
    if any(marker in " ".join(logs).lower() for marker in ("❌", "🔥", "错误", "失败", "error", "failed", "traceback")):
        return "log_failure", reason_text or "日志包含失败标记"
    if reason_text:
        return "generic_failure", reason_text
    return "unknown", ""


def _filter_queue_history_entries(
    entries,
    status_filter=QUEUE_HISTORY_STATUS_DEFAULT,
    task_filter=QUEUE_HISTORY_TASK_DEFAULT,
    failure_filter=QUEUE_HISTORY_FAILURE_DEFAULT,
    keyword="",
):
    status_value = QUEUE_HISTORY_STATUS_LABEL_TO_VALUE.get(str(status_filter or "").strip(), "")
    task_value = QUEUE_HISTORY_TASK_LABEL_TO_VALUE.get(str(task_filter or "").strip(), "")
    failure_value = QUEUE_HISTORY_FAILURE_LABEL_TO_VALUE.get(str(failure_filter or "").strip(), "")
    normalized_keyword = str(keyword or "").strip().lower()
    filtered = []
    for entry in list(entries or []):
        if status_value and str(entry.get("status") or "") != status_value:
            continue
        if task_value and str(entry.get("task_type") or "") != task_value:
            continue
        if failure_value:
            failure_kind, _failure_reason = _classify_failure_reason(entry)
            if failure_kind != failure_value:
                continue
        if normalized_keyword and normalized_keyword not in _build_queue_history_search_blob(entry):
            continue
        filtered.append(entry)
    return filtered


def _get_queue_history_filters(app):
    try:
        status_filter = getattr(app, "_fx_history_filter_status_var", None)
        status_filter = status_filter.get() if status_filter is not None else QUEUE_HISTORY_STATUS_DEFAULT
    except Exception:
        status_filter = QUEUE_HISTORY_STATUS_DEFAULT
    try:
        task_filter = getattr(app, "_fx_history_filter_task_var", None)
        task_filter = task_filter.get() if task_filter is not None else QUEUE_HISTORY_TASK_DEFAULT
    except Exception:
        task_filter = QUEUE_HISTORY_TASK_DEFAULT
    try:
        failure_filter = getattr(app, "_fx_history_filter_failure_var", None)
        failure_filter = failure_filter.get() if failure_filter is not None else QUEUE_HISTORY_FAILURE_DEFAULT
    except Exception:
        failure_filter = QUEUE_HISTORY_FAILURE_DEFAULT
    try:
        keyword = getattr(app, "_fx_history_search_var", None)
        keyword = keyword.get() if keyword is not None else ""
    except Exception:
        keyword = ""
    return (
        str(status_filter or QUEUE_HISTORY_STATUS_DEFAULT),
        str(task_filter or QUEUE_HISTORY_TASK_DEFAULT),
        str(failure_filter or QUEUE_HISTORY_FAILURE_DEFAULT),
        str(keyword or ""),
    )


def _get_filtered_queue_history(app):
    status_filter, task_filter, failure_filter, keyword = _get_queue_history_filters(app)
    history = list(getattr(app, "_fx_task_history", []) or [])
    return _filter_queue_history_entries(
        history,
        status_filter=status_filter,
        task_filter=task_filter,
        failure_filter=failure_filter,
        keyword=keyword,
    )


def _refresh_history_summary(app, filtered_history=None, full_history=None):
    summary_var = getattr(app, "_fx_history_summary_var", None)
    if summary_var is None:
        return
    if full_history is None:
        full_history = list(getattr(app, "_fx_task_history", []) or [])
    if filtered_history is None:
        filtered_history = _get_filtered_queue_history(app)
    shown = len(filtered_history)
    total = len(full_history)
    failed = sum(1 for item in filtered_history if item.get("status") == "failed")
    try:
        summary_var.set(f"显示 {shown}/{total} 条 · 当前失败 {failed}")
    except Exception:
        pass


def _build_task_history_detail_text(entry):
    item = dict(entry or {})
    task_result = item.get("task_result") if isinstance(item.get("task_result"), dict) else {}
    lines = [
        f"标题：{item.get('title', '')}",
        f"功能：{QUEUE_TASK_LABELS.get(item.get('task_type'), item.get('task_type') or '未知任务')}",
        f"状态：{_queue_status_text(item.get('status'))}",
        f"输入：{item.get('input', '')}",
        f"创建时间：{_format_queue_time(item.get('created_at'))}",
        f"结束时间：{_format_queue_time(item.get('finished_at') or item.get('created_at'))}",
    ]
    duration_seconds = task_result.get("duration_seconds", item.get("duration_seconds", 0.0))
    try:
        duration_seconds = float(duration_seconds or 0.0)
    except Exception:
        duration_seconds = 0.0
    if duration_seconds > 0:
        lines.append(f"耗时：{duration_seconds:.3f}s")
    detail = task_result.get("detail") or item.get("detail", "")
    if detail:
        lines.append(f"详情：{detail}")
    error = task_result.get("error") or item.get("error", "")
    if error:
        lines.append(f"错误：{error}")
    output_root = task_result.get("output_root") or item.get("output_root", "")
    if output_root:
        lines.append(f"输出目录：{output_root}")
    outputs = list(task_result.get("outputs") or item.get("outputs") or [])
    if outputs:
        lines.append("")
        lines.append("输出文件：")
        lines.extend(f"- {path}" for path in outputs)
    failed_items = list(task_result.get("failed_items") or item.get("failed_items") or [])
    logs = [str(text).strip() for text in (item.get("logs") or []) if str(text).strip()]
    if item.get("status") == "failed" or error or failed_items:
        lines.append("")
        lines.append("失败概览：")
        lines.append(f"- 状态：{_queue_status_text(item.get('status'))}")
        if error:
            lines.append(f"- 失败原因：{error}")
        elif detail:
            lines.append(f"- 失败原因：{detail}")
        if failed_items:
            lines.append(f"- 失败项数量：{len(failed_items)}")
        failed_log_lines = [
            text for text in logs if any(marker in text.lower() for marker in ("❌", "🔥", "错误", "失败", "error", "failed", "traceback"))
        ]
        if failed_log_lines:
            lines.append(f"- 关键失败日志：{len(failed_log_lines)} 条")
    if error:
        lines.append("")
        lines.append("失败原因：")
        lines.append(f"- {error}")
    elif item.get("status") == "failed" and detail:
        lines.append("")
        lines.append("失败原因：")
        lines.append(f"- {detail}")
    if failed_items:
        lines.append("")
        lines.append("失败项：")
        lines.extend(f"- {path}" for path in failed_items)
    failed_log_lines = [
        text for text in logs if any(marker in text.lower() for marker in ("❌", "🔥", "错误", "失败", "error", "failed", "traceback"))
    ]
    if failed_log_lines:
        lines.append("")
        lines.append("关键日志：")
        lines.extend(f"- {text}" for text in failed_log_lines[-8:])
    if logs:
        lines.append("")
        lines.append("日志片段：")
        lines.extend(f"- {text}" for text in logs[-12:])
    lines.append("")
    lines.append("结构化结果 JSON：")
    lines.append(json.dumps(task_result, ensure_ascii=False, indent=2) if task_result else "{}")
    return "\n".join(lines)


def _apply_task_history_detail_highlights(detail_box, detail_text, entry):
    if detail_box is None:
        return
    try:
        detail_box.tag_remove("fx_history_fail_header", "1.0", "end")
        detail_box.tag_remove("fx_history_fail_text", "1.0", "end")
        detail_box.tag_remove("fx_history_fail_item", "1.0", "end")
        detail_box.tag_remove("fx_history_log_error", "1.0", "end")
        detail_box.tag_config("fx_history_fail_header", foreground="#F6C66A")
        detail_box.tag_config("fx_history_fail_text", foreground="#FF8A80")
        detail_box.tag_config("fx_history_fail_item", foreground="#FFD6A5")
        detail_box.tag_config("fx_history_log_error", foreground="#FFB4AB")
    except Exception:
        return

    item = dict(entry or {})
    task_result = item.get("task_result") if isinstance(item.get("task_result"), dict) else {}
    failed_items = list(task_result.get("failed_items") or item.get("failed_items") or [])
    status = str(item.get("status") or "")
    error = str(task_result.get("error") or item.get("error") or "").strip()
    detail = str(task_result.get("detail") or item.get("detail") or "").strip()
    logs = [str(text).strip() for text in (item.get("logs") or []) if str(text).strip()]
    highlight_lines = []
    if status == "failed":
        highlight_lines.append(("状态：失败", "fx_history_fail_text"))
    if error:
        highlight_lines.append((f"错误：{error}", "fx_history_fail_text"))
        highlight_lines.append((f"- {error}", "fx_history_fail_text"))
    elif status == "failed" and detail:
        highlight_lines.append((f"- {detail}", "fx_history_fail_text"))
    for header in ("失败概览：", "失败原因：", "失败项：", "关键日志："):
        highlight_lines.append((header, "fx_history_fail_header"))
    for item_path in failed_items:
        highlight_lines.append((f"- {item_path}", "fx_history_fail_item"))
    for log_line in logs:
        lowered = log_line.lower()
        if any(marker in lowered for marker in ("❌", "🔥", "错误", "失败", "error", "failed", "traceback")):
            highlight_lines.append((f"- {log_line}", "fx_history_log_error"))

    for text, tag in highlight_lines:
        if not text:
            continue
        start_index = "1.0"
        while True:
            try:
                match_index = detail_box.search(text, start_index, stopindex="end")
            except Exception:
                match_index = ""
            if not match_index:
                break
            end_index = f"{match_index}+{len(text)}c"
            try:
                detail_box.tag_add(tag, match_index, end_index)
            except Exception:
                break
            start_index = end_index


def _build_task_history_export_filename(entry):
    item = dict(entry or {})
    task_type = QUEUE_TASK_LABELS.get(item.get("task_type"), item.get("task_type") or "task")
    task_slug = _sanitize_filename_component(task_type, fallback="task")
    title_slug = _sanitize_filename_component(item.get("title") or item.get("input") or "history", fallback="history")
    timestamp = _sanitize_filename_component(_format_queue_time(item.get("finished_at") or item.get("created_at")), fallback="time")
    return f"fengxi_task_result_{task_slug}_{title_slug}_{timestamp}.json"


def _export_task_history_entry(entry, output_path):
    item = dict(entry or {})
    task_result = item.get("task_result") if isinstance(item.get("task_result"), dict) else {}
    if not task_result:
        return False, "当前历史记录没有可导出的结构化结果。"
    normalized_output = _normalize_input_path_value(output_path)
    if not normalized_output:
        return False, "未选择导出位置。"
    ok = _export_task_result(task_result, normalized_output)
    if not ok:
        return False, f"导出失败：{normalized_output}"
    return True, normalized_output


def _prompt_export_task_history_entry(app, entry, output_path=None):
    item = dict(entry or {})
    task_result = item.get("task_result") if isinstance(item.get("task_result"), dict) else {}
    if not task_result:
        try:
            tkinter.messagebox.showwarning("导出结果", "当前历史记录没有可导出的结构化结果。", parent=app)
        except Exception:
            pass
        return False
    selected_path = output_path
    if not selected_path:
        initial_dir = task_result.get("output_root") or os.path.dirname(_normalize_input_path_value(item.get("input"))) or str(Path.cwd())
        try:
            selected_path = tkinter.filedialog.asksaveasfilename(
                title="导出任务结果",
                parent=app,
                defaultextension=".json",
                initialdir=_normalize_input_path_value(initial_dir) or str(Path.cwd()),
                initialfile=_build_task_history_export_filename(item),
                filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
            )
        except Exception as exc:
            _debug(f"queue:history_export_dialog_error:{exc}")
            selected_path = ""
    ok, payload = _export_task_history_entry(item, selected_path)
    try:
        if ok:
            tkinter.messagebox.showinfo("导出结果", f"任务结果已导出到：\n{payload}", parent=app)
        elif selected_path:
            tkinter.messagebox.showerror("导出结果", payload, parent=app)
    except Exception:
        pass
    if ok:
        try:
            app.log(f"[任务历史] 已导出结果：{payload}")
        except Exception:
            pass
    return ok


def _build_task_history_log_export_text(entry):
    item = dict(entry or {})
    task_result = item.get("task_result") if isinstance(item.get("task_result"), dict) else {}
    logs = list(item.get("logs") or task_result.get("logs") or task_result.get("log_lines") or [])
    lines = [
        f"标题：{item.get('title', '')}",
        f"功能：{QUEUE_TASK_LABELS.get(item.get('task_type'), item.get('task_type') or '未知任务')}",
        f"状态：{_queue_status_text(item.get('status'))}",
        f"输入：{item.get('input', '')}",
        f"创建时间：{_format_queue_time(item.get('created_at'))}",
        f"结束时间：{_format_queue_time(item.get('finished_at') or item.get('created_at'))}",
        "",
        "日志：",
    ]
    if logs:
        lines.extend(f"- {text}" for text in logs)
    else:
        lines.append("- (empty)")
    return "\n".join(lines)


def _build_task_history_log_export_filename(entry):
    item = dict(entry or {})
    task_type = QUEUE_TASK_LABELS.get(item.get("task_type"), item.get("task_type") or "task")
    task_slug = _sanitize_filename_component(task_type, fallback="task")
    title_slug = _sanitize_filename_component(item.get("title") or item.get("input") or "history", fallback="history")
    timestamp = _sanitize_filename_component(_format_queue_time(item.get("finished_at") or item.get("created_at")), fallback="time")
    return f"fengxi_task_log_{task_slug}_{title_slug}_{timestamp}.txt"


def _export_task_history_log(entry, output_path):
    item = dict(entry or {})
    text = _build_task_history_log_export_text(item)
    normalized_output = _normalize_input_path_value(output_path)
    if not normalized_output:
        return False, "未选择导出位置。"
    try:
        path = Path(normalized_output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return True, normalized_output
    except Exception as exc:
        _debug(f"queue:history_log_export_error:{exc}")
        return False, f"导出失败：{normalized_output}"


def _prompt_export_task_history_log(app, entry, output_path=None):
    item = dict(entry or {})
    selected_path = output_path
    if not selected_path:
        initial_dir = _normalize_input_path_value(item.get("input")) or str(Path.cwd())
        try:
            selected_path = tkinter.filedialog.asksaveasfilename(
                title="导出任务日志",
                parent=app,
                defaultextension=".txt",
                initialdir=initial_dir,
                initialfile=_build_task_history_log_export_filename(item),
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            )
        except Exception as exc:
            _debug(f"queue:history_log_export_dialog_error:{exc}")
            selected_path = ""
    ok, payload = _export_task_history_log(item, selected_path)
    try:
        if ok:
            tkinter.messagebox.showinfo("导出日志", f"任务日志已导出到：\n{payload}", parent=app)
        elif selected_path:
            tkinter.messagebox.showerror("导出日志", payload, parent=app)
    except Exception:
        pass
    if ok:
        try:
            app.log(f"[任务历史] 已导出日志：{payload}")
        except Exception:
            pass
    return ok


def _resolve_task_history_open_target(entry):
    item = dict(entry or {})
    task_result = item.get("task_result") if isinstance(item.get("task_result"), dict) else {}
    candidates = [
        task_result.get("output_root"),
        item.get("output_root"),
    ]
    outputs = list(task_result.get("outputs") or item.get("outputs") or [])
    if outputs:
        candidates.extend(outputs)
    candidates.append(item.get("input"))
    for value in candidates:
        normalized = _normalize_input_path_value(value)
        if not normalized:
            continue
        if os.path.isdir(normalized):
            return normalized
        if os.path.isfile(normalized):
            return os.path.dirname(normalized)
    return ""


def _open_task_history_output(entry):
    target = _resolve_task_history_open_target(entry)
    if not target:
        return False, "当前历史记录没有可打开的输出位置。"
    try:
        os.startfile(target)
        return True, target
    except Exception as exc:
        _debug(f"queue:history_open_output_error:{exc}")
        return False, f"打开失败：{target}"


def _prompt_open_task_history_output(app, entry):
    ok, payload = _open_task_history_output(entry)
    try:
        if (not ok) and payload:
            tkinter.messagebox.showwarning("打开输出位置", payload, parent=app)
    except Exception:
        pass
    if ok:
        try:
            app.log(f"[任务历史] 已打开输出位置：{payload}")
        except Exception:
            pass
    return ok


def _show_task_history_detail(app, entry):
    _ensure_queue_state(app)
    detail_text = _build_task_history_detail_text(entry)
    detail_window = getattr(app, "_fx_history_detail_window", None)
    try:
        if detail_window is not None and detail_window.winfo_exists():
            detail_window.deiconify()
            detail_window.lift()
        else:
            detail_window = customtkinter.CTkToplevel(app)
            _apply_window_icon(detail_window)
            app._fx_history_detail_window = detail_window
            detail_window.title("任务历史详情")
            detail_window.geometry("820x620")
            detail_window.minsize(680, 480)
            try:
                detail_window.configure(fg_color=globals().get("COLOR_CARD_ALT", "#303030"))
            except Exception:
                pass
            detail_window.grid_columnconfigure(0, weight=1)
            detail_window.grid_rowconfigure(1, weight=1)
            customtkinter.CTkLabel(
                detail_window,
                text="任务历史详情",
                text_color=globals().get("COLOR_TEXT", "#E6EEF2"),
                font=customtkinter.CTkFont(size=20, weight="bold"),
                anchor="w",
            ).grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))
            detail_box = customtkinter.CTkTextbox(
                detail_window,
                wrap="word",
                fg_color=globals().get("COLOR_CARD", "#2B2B2B"),
                text_color=globals().get("COLOR_TEXT", "#E6EEF2"),
                border_width=1,
                border_color=globals().get("COLOR_BORDER", "#3A3A3A"),
                corner_radius=12,
            )
            detail_box.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 12))
            detail_window._fx_detail_box = detail_box
            actions = customtkinter.CTkFrame(detail_window, fg_color="transparent")
            actions.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 16))
            actions.grid_columnconfigure(0, weight=1)

            def copy_detail():
                try:
                    app.clipboard_clear()
                    app.clipboard_append(detail_window._fx_detail_box.get("1.0", "end-1c"))
                    app.update()
                except Exception as exc:
                    _debug(f"queue:history_detail_copy_error:{exc}")

            def export_detail_result():
                current_entry = getattr(detail_window, "_fx_entry", None)
                _prompt_export_task_history_entry(app, current_entry)

            def export_detail_log():
                current_entry = getattr(detail_window, "_fx_entry", None)
                _prompt_export_task_history_log(app, current_entry)

            def open_output_location():
                current_entry = getattr(detail_window, "_fx_entry", None)
                _prompt_open_task_history_output(app, current_entry)

            customtkinter.CTkButton(
                actions,
                text="导出结果",
                command=export_detail_result,
                height=34,
                width=92,
                corner_radius=10,
                fg_color="#56603D",
                hover_color="#68714A",
                text_color="#F5F8EA",
            ).grid(row=0, column=1, sticky="e", padx=(0, 8))
            customtkinter.CTkButton(
                actions,
                text="打开位置",
                command=open_output_location,
                height=34,
                width=92,
                corner_radius=10,
                fg_color="#3F5B57",
                hover_color="#4D6C67",
                text_color="#EAF6F3",
            ).grid(row=0, column=2, sticky="e", padx=(0, 8))
            customtkinter.CTkButton(
                actions,
                text="导出日志",
                command=export_detail_log,
                height=34,
                width=92,
                corner_radius=10,
                fg_color="#5A4E3D",
                hover_color="#6A5B49",
                text_color="#F8F1E6",
            ).grid(row=0, column=3, sticky="e", padx=(0, 8))

            customtkinter.CTkButton(
                actions,
                text="复制详情",
                command=copy_detail,
                height=34,
                width=92,
                corner_radius=10,
                fg_color="#44566C",
                hover_color="#51657D",
                text_color="#EEF5FF",
            ).grid(row=0, column=4, sticky="e")
        detail_box = getattr(detail_window, "_fx_detail_box", None)
        detail_window._fx_entry = dict(entry or {})
        if detail_box is not None:
            detail_box.delete("1.0", "end")
            detail_box.insert("1.0", detail_text)
            _apply_task_history_detail_highlights(detail_box, detail_text, detail_window._fx_entry)
            detail_box.see("1.0")
    except Exception as exc:
        _debug(f"queue:history_detail_error:{exc}")


def _reset_queue_history_filters(app):
    try:
        getattr(app, "_fx_history_filter_status_var", None).set(QUEUE_HISTORY_STATUS_DEFAULT)
    except Exception:
        pass
    try:
        getattr(app, "_fx_history_filter_task_var", None).set(QUEUE_HISTORY_TASK_DEFAULT)
    except Exception:
        pass
    try:
        getattr(app, "_fx_history_filter_failure_var", None).set(QUEUE_HISTORY_FAILURE_DEFAULT)
    except Exception:
        pass
    try:
        getattr(app, "_fx_history_search_var", None).set("")
    except Exception:
        pass
    _refresh_history_panel(app)


def _install_queue_history_filter_hooks(app):
    if getattr(app, "_fx_history_filter_hooks_ready", False):
        return

    def on_change(*_args):
        _refresh_history_panel(app)

    app._fx_history_filter_trace_callback = on_change
    for attr in ("_fx_history_filter_status_var", "_fx_history_filter_task_var", "_fx_history_filter_failure_var", "_fx_history_search_var"):
        var = getattr(app, attr, None)
        if isinstance(var, tkinter.Variable):
            try:
                var.trace_add("write", on_change)
            except Exception:
                pass
    app._fx_history_filter_hooks_ready = True


def _task_result_matches_task(task_result, task):
    if not isinstance(task_result, dict) or not isinstance(task, dict):
        return False
    task_input = _normalize_input_path_value(task.get("input"))
    result_input = _normalize_input_path_value(task_result.get("input"))
    task_type = str(task.get("task_type") or "")
    result_type = str(task_result.get("task_type") or "")
    if task_input and result_input and os.path.normcase(task_input) != os.path.normcase(result_input):
        return False
    if task_type and result_type and task_type != result_type:
        return False
    return True


def _queue_set_task_status(app, task, status, detail=""):
    task_result = task.get("task_result")
    if not _task_result_matches_task(task_result, task):
        task_result = _get_last_task_result(app)
    if not _task_result_matches_task(task_result, task):
        task_result = None
    if task_result is None and str(status or "") in {"success", "failed", "stopped", "skipped"}:
        task_result = _new_task_result(task.get("input"), task.get("task_type"))
        _set_task_result_finished(
            task_result,
            status=status,
            message=str(detail or status),
            detail=str(detail or status),
            error=str(detail or "") if str(status or "") == "failed" else "",
            stopped=str(status or "") == "stopped",
            skipped=str(status or "") == "skipped",
        )
    if isinstance(task_result, dict):
        task["task_result"] = dict(task_result)
        detail = task_result.get("detail") or detail
        task["output_root"] = task_result.get("output_root", "")
        task["outputs"] = list(task_result.get("outputs") or [])
        task["error"] = task_result.get("error", "")
        task["duration_seconds"] = task_result.get("duration_seconds", 0.0)
        task["skipped"] = bool(task_result.get("skipped", False))
        status = task_result.get("status") or status
    task["status"] = status
    task["finished_at"] = time.time() if status in {"success", "failed", "stopped", "skipped"} else task.get("finished_at")
    if detail:
        task["detail"] = str(detail)
    status_var = task.get("status_var")
    if status_var is not None:
        try:
            status_var.set(_queue_status_text(status))
        except Exception:
            pass
    row = task.get("row")
    if row is not None:
        try:
            for child in row.winfo_children():
                if isinstance(child, customtkinter.CTkLabel) and getattr(child, "_fx_queue_status_label", False):
                    child.configure(text_color=_queue_status_color(status))
        except Exception:
            pass
    _refresh_queue_panel(app)


def _queue_task_had_errors(task):
    task_result = task.get("task_result")
    if isinstance(task_result, dict):
        if task_result.get("status") in {"failed"} or task_result.get("error"):
            return True
        if task_result.get("failed_items"):
            return True
    if task.get("exception"):
        return True
    logs = task.get("logs") or []
    if getattr(task.get("app", None), "stop_event", False):
        return True
    joined = "\n".join(str(item) for item in logs).lower()
    return any(marker.lower() in joined for marker in QUEUE_ERROR_MARKERS)


def _queue_capture_task_logs(app, task):
    original_log = getattr(app, "log", None)
    if not callable(original_log):
        return None

    def patched_log(message, *args, **kwargs):
        text = str(message)
        try:
            task.setdefault("logs", []).append(text)
        except Exception:
            pass
        task_result = _get_last_task_result(app)
        if _task_result_matches_task(task_result, task):
            try:
                task_result.setdefault("logs", []).append(text)
            except Exception:
                pass
            try:
                task_result.setdefault("log_lines", []).append(text)
            except Exception:
                pass
        return original_log(message, *args, **kwargs)

    app.log = patched_log
    return original_log


def _queue_restore_task_logs(app, original_log):
    if original_log is not None:
        try:
            app.log = original_log
        except Exception:
            pass


def _split_failed_item_path(item):
    text = str(item or "").strip()
    if not text:
        return ""
    if ": " in text:
        head, _tail = text.split(": ", 1)
        if head and os.path.exists(head):
            return head
    return text


def _resolve_retry_failed_item_paths(source):
    if not isinstance(source, dict):
        return []
    source_input = _normalize_input_path_value(source.get("input"))
    if not source_input:
        return []
    input_root = os.path.dirname(source_input) if os.path.isfile(source_input) else source_input
    task_result = source.get("task_result") if isinstance(source.get("task_result"), dict) else {}
    failed_items = list(task_result.get("failed_items") or source.get("failed_items") or [])
    resolved = []
    seen = set()
    for item in failed_items:
        path_value = _split_failed_item_path(item)
        if not path_value:
            continue
        normalized = _normalize_input_path_value(path_value)
        if normalized and os.path.exists(normalized):
            candidate = normalized
        else:
            candidate = _normalize_input_path_value(os.path.join(input_root, path_value)) if input_root else ""
        if not candidate or not os.path.exists(candidate):
            continue
        key = os.path.normcase(candidate)
        if key in seen:
            continue
        seen.add(key)
        resolved.append(candidate)
    return resolved


def _build_retry_subset_input(app, source):
    if not isinstance(source, dict):
        return None
    failed_paths = _resolve_retry_failed_item_paths(source)
    if not failed_paths:
        return None
    source_input = _normalize_input_path_value(source.get("input"))
    if len(failed_paths) == 1 and os.path.isfile(failed_paths[0]):
        return {
            "mode": "single_file",
            "input": failed_paths[0],
            "failed_items": failed_paths,
            "cleanup": None,
        }
    task_type = str(source.get("task_type") or "")
    if task_type not in {"pdf", "image", "remove_wm"}:
        return None
    try:
        staging_root = Path(tempfile.mkdtemp(prefix="fx_retry_subset_"))
        for src in failed_paths:
            if os.path.isfile(source_input):
                relative = os.path.basename(src)
            else:
                try:
                    relative = os.path.relpath(src, source_input)
                except Exception:
                    relative = os.path.basename(src)
            dst = staging_root / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        return {
            "mode": "staging_dir",
            "input": str(staging_root),
            "failed_items": failed_paths,
            "cleanup": str(staging_root),
        }
    except Exception as exc:
        _debug(f"queue:retry_subset_build_error:{exc}")
        try:
            shutil.rmtree(staging_root, ignore_errors=True)
        except Exception:
            pass
        return None


def _queue_build_task(app, input_path=None, task_type=None, retry_source=None):
    normalized_input = _normalize_input_path_value(input_path if input_path is not None else app.input_path.get())
    task_type = task_type or getattr(app, "current_task", "")
    if not normalized_input:
        raise ValueError("请先选择文件或文件夹")
    if not os.path.exists(normalized_input):
        raise ValueError(f"路径不存在: {normalized_input}")
    if task_type == "help":
        raise ValueError("使用教程不能加入任务队列")
    snapshot = retry_source.get("snapshot") if isinstance(retry_source, dict) else None
    if not isinstance(snapshot, dict):
        snapshot = _queue_snapshot_app_state(app, task_type)
    task = {
        "id": _make_queue_task_id(),
        "input": normalized_input,
        "task_type": task_type,
        "title": retry_source.get("title") if isinstance(retry_source, dict) else _queue_describe_task(app, task_type, normalized_input),
        "snapshot": snapshot,
        "status": "queued",
        "created_at": time.time(),
        "started_at": None,
        "finished_at": None,
        "detail": "",
        "logs": [],
    }
    if isinstance(retry_source, dict):
        task["retry_source_id"] = retry_source.get("id")
    return task


def _ensure_queue_state(app):
    if not hasattr(app, "_fx_task_queue"):
        app._fx_task_queue = []
    if not hasattr(app, "_fx_task_history"):
        app._fx_task_history = _load_queue_history()
    if not hasattr(app, "_fx_task_queue_running"):
        app._fx_task_queue_running = False
    if not hasattr(app, "_fx_queue_window"):
        app._fx_queue_window = None
    if not hasattr(app, "_fx_history_filter_status_var"):
        app._fx_history_filter_status_var = tkinter.StringVar(master=app, value=QUEUE_HISTORY_STATUS_DEFAULT)
    if not hasattr(app, "_fx_history_filter_task_var"):
        app._fx_history_filter_task_var = tkinter.StringVar(master=app, value=QUEUE_HISTORY_TASK_DEFAULT)
    if not hasattr(app, "_fx_history_filter_failure_var"):
        app._fx_history_filter_failure_var = tkinter.StringVar(master=app, value=QUEUE_HISTORY_FAILURE_DEFAULT)
    if not hasattr(app, "_fx_history_search_var"):
        app._fx_history_search_var = tkinter.StringVar(master=app, value="")
    if not hasattr(app, "_fx_history_summary_var"):
        app._fx_history_summary_var = tkinter.StringVar(master=app, value="")


def _refresh_queue_status_summary(app):
    summary_var = getattr(app, "_fx_queue_summary_var", None)
    if summary_var is None:
        return
    try:
        queue = getattr(app, "_fx_task_queue", [])
        running = sum(1 for item in queue if item.get("status") == "running")
        queued = sum(1 for item in queue if item.get("status") == "queued")
        failed = sum(1 for item in getattr(app, "_fx_task_history", []) if item.get("status") == "failed")
        if running:
            summary = f"队列执行中 · 等待 {queued} · 可重试失败 {failed}"
        elif queued:
            summary = f"队列待执行 {queued} 项 · 可重试失败 {failed}"
        else:
            summary = f"队列空闲 · 可重试失败 {failed}"
        summary_var.set(summary)
    except Exception:
        pass


def _refresh_queue_panel(app):
    _refresh_queue_status_summary(app)
    panel = getattr(app, "_fx_queue_list_frame", None)
    if panel is None:
        return
    try:
        for child in panel.winfo_children():
            child.destroy()
        queue = getattr(app, "_fx_task_queue", [])
        if not queue:
            customtkinter.CTkLabel(
                panel,
                text="当前队列为空。配置好功能后点“加入队列”，就可以批量排队执行。",
                text_color=globals().get("COLOR_TEXT_SOFT", "#B2C0C8"),
                font=customtkinter.CTkFont(size=12),
                justify="left",
            ).pack(anchor="w", padx=16, pady=14)
            return
        for index, task in enumerate(queue, 1):
            row = customtkinter.CTkFrame(panel, fg_color=globals().get("COLOR_CARD_ALT", "#303030"), corner_radius=10)
            row.pack(fill="x", padx=10, pady=(8 if index == 1 else 4, 4))
            task["row"] = row
            row.grid_columnconfigure(1, weight=1)
            customtkinter.CTkLabel(
                row,
                text=f"{index:02d}",
                text_color="#F0D39A",
                font=customtkinter.CTkFont(size=12, weight="bold"),
                width=34,
            ).grid(row=0, column=0, rowspan=2, padx=(10, 6), pady=8, sticky="n")
            customtkinter.CTkLabel(
                row,
                text=task.get("title", ""),
                text_color=globals().get("COLOR_TEXT", "#E6EEF2"),
                font=customtkinter.CTkFont(size=12, weight="bold"),
                anchor="w",
            ).grid(row=0, column=1, padx=4, pady=(8, 1), sticky="ew")
            customtkinter.CTkLabel(
                row,
                text=task.get("input", ""),
                text_color=globals().get("COLOR_TEXT_SOFT", "#B2C0C8"),
                font=customtkinter.CTkFont(size=10),
                anchor="w",
            ).grid(row=1, column=1, padx=4, pady=(0, 8), sticky="ew")
            status_label = customtkinter.CTkLabel(
                row,
                text=_queue_status_text(task.get("status")),
                text_color=_queue_status_color(task.get("status")),
                font=customtkinter.CTkFont(size=12, weight="bold"),
                width=64,
            )
            status_label._fx_queue_status_label = True
            status_label.grid(row=0, column=2, rowspan=2, padx=(6, 10), pady=8, sticky="e")
    except Exception as exc:
        _debug(f"queue:refresh_panel_error:{exc}")


def _refresh_history_panel(app):
    panel = getattr(app, "_fx_history_list_frame", None)
    history = list(getattr(app, "_fx_task_history", []) or [])
    filtered_history = _get_filtered_queue_history(app)
    _refresh_history_summary(app, filtered_history=filtered_history, full_history=history)
    if panel is None:
        return
    try:
        for child in panel.winfo_children():
            child.destroy()
        if not history:
            customtkinter.CTkLabel(
                panel,
                text="暂无历史记录。完成队列任务后会自动记录到这里。",
                text_color=globals().get("COLOR_TEXT_SOFT", "#B2C0C8"),
                font=customtkinter.CTkFont(size=12),
                justify="left",
            ).pack(anchor="w", padx=16, pady=14)
            return
        if not filtered_history:
            customtkinter.CTkLabel(
                panel,
                text="没有符合筛选条件的历史记录。可以调整状态、功能类型或搜索关键词。",
                text_color=globals().get("COLOR_TEXT_SOFT", "#B2C0C8"),
                font=customtkinter.CTkFont(size=12),
                justify="left",
            ).pack(anchor="w", padx=16, pady=14)
            return
        for item in reversed(filtered_history[-QUEUE_HISTORY_LIMIT:]):
            row = customtkinter.CTkFrame(panel, fg_color=globals().get("COLOR_CARD_ALT", "#303030"), corner_radius=10)
            row.pack(fill="x", padx=10, pady=(6, 4))
            row.grid_columnconfigure(0, weight=1)
            top = customtkinter.CTkFrame(row, fg_color="transparent")
            top.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
            top.grid_columnconfigure(0, weight=1)
            customtkinter.CTkLabel(
                top,
                text=item.get("title", ""),
                text_color=globals().get("COLOR_TEXT", "#E6EEF2"),
                font=customtkinter.CTkFont(size=12, weight="bold"),
                anchor="w",
            ).grid(row=0, column=0, sticky="ew")
            customtkinter.CTkLabel(
                top,
                text=_queue_status_text(item.get("status")),
                text_color=_queue_status_color(item.get("status")),
                font=customtkinter.CTkFont(size=12, weight="bold"),
                width=58,
            ).grid(row=0, column=1, padx=(8, 0), sticky="e")
            task_result = item.get("task_result") if isinstance(item.get("task_result"), dict) else {}
            stats_parts = []
            processed_count = int(task_result.get("processed_count") or 0)
            success_count = int(task_result.get("success_count") or 0)
            failed_count = int(task_result.get("failed_count") or 0)
            skipped_count = int(task_result.get("skipped_count") or 0)
            duration_seconds = float(task_result.get("duration_seconds") or item.get("duration_seconds") or 0.0)
            if processed_count:
                stats_parts.append(f"结果 {success_count}/{processed_count}")
            if failed_count:
                stats_parts.append(f"失败 {failed_count}")
            if skipped_count:
                stats_parts.append(f"跳过 {skipped_count}")
            if duration_seconds > 0:
                stats_parts.append(f"耗时 {duration_seconds:.2f}s")
            detail_lines = [
                item.get("input", ""),
                f"功能：{QUEUE_TASK_LABELS.get(item.get('task_type'), item.get('task_type') or '未知任务')} · 时间：{_format_queue_time(item.get('finished_at') or item.get('created_at'))}",
            ]
            if stats_parts:
                detail_lines.append(" · ".join(stats_parts))
            output_root = task_result.get("output_root") or item.get("output_root", "")
            if output_root:
                detail_lines.append(f"输出：{output_root}")
            error_text = task_result.get("error") or item.get("error", "")
            if error_text:
                detail_lines.append(str(error_text)[:160])
            failure_kind, failure_reason = _classify_failure_reason(item)
            if item.get("status") == "failed" and failure_kind and failure_kind != "unknown":
                failure_labels = {
                    "path_missing": "路径缺失",
                    "permission": "权限问题",
                    "timeout": "超时",
                    "dependency": "依赖问题",
                    "partial_failure": "部分失败",
                    "log_failure": "日志失败",
                    "generic_failure": "普通失败",
                }
                detail_lines.append(f"失败分类：{failure_labels.get(failure_kind, failure_kind)}")
                if failure_reason:
                    detail_lines.append(failure_reason[:120])
            if item.get("detail"):
                detail_lines.append(str(item.get("detail"))[:160])
            customtkinter.CTkLabel(
                row,
                text="\n".join(line for line in detail_lines if line),
                text_color=globals().get("COLOR_TEXT_SOFT", "#B2C0C8"),
                font=customtkinter.CTkFont(size=10),
                justify="left",
                anchor="w",
            ).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
            is_failed = item.get("status") == "failed"
            action_col = customtkinter.CTkFrame(row, fg_color="transparent")
            action_col.grid(row=0, column=1, rowspan=2, padx=(0, 10), pady=8, sticky="ne")
            customtkinter.CTkButton(
                action_col,
                text="详情",
                command=lambda source=item: _show_task_history_detail(app, source),
                height=30,
                width=72,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#303030",
                border_width=1,
                border_color="#566274",
                text_color="#E8EDF5",
            ).pack(anchor="e", pady=(0, 6))
            customtkinter.CTkButton(
                action_col,
                text="重试" if is_failed else "回放",
                command=(lambda source=item: _queue_retry_history_task(app, source))
                if is_failed
                else (lambda source=item: _queue_replay_history_task(app, source)),
                height=30,
                width=72,
                corner_radius=8,
                fg_color="#6D4F3B" if is_failed else "#44566C",
                hover_color="#7C5B43" if is_failed else "#51657D",
                text_color="#FFF6E6" if is_failed else "#EEF5FF",
            ).pack(anchor="e")
    except Exception as exc:
        _debug(f"queue:refresh_history_error:{exc}")


def _show_task_queue_window(app):
    _ensure_queue_state(app)
    window = getattr(app, "_fx_queue_window", None)
    try:
        if window is not None and window.winfo_exists():
            window.deiconify()
            window.lift()
            _refresh_queue_panel(app)
            _refresh_history_panel(app)
            return window
    except Exception:
        pass

    window = customtkinter.CTkToplevel(app)
    _apply_window_icon(window)
    app._fx_queue_window = window
    window.title("任务队列与历史记录")
    window.geometry("860x620")
    window.minsize(760, 520)
    try:
        window.configure(fg_color=globals().get("COLOR_CARD_ALT", "#303030"))
    except Exception:
        pass
    window.grid_columnconfigure(0, weight=1)
    window.grid_columnconfigure(1, weight=1)
    window.grid_rowconfigure(1, weight=1)

    header = customtkinter.CTkFrame(window, fg_color="transparent")
    header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(16, 8))
    header.grid_columnconfigure(0, weight=1)
    customtkinter.CTkLabel(
        header,
        text="任务队列",
        text_color=globals().get("COLOR_TEXT", "#E6EEF2"),
        font=customtkinter.CTkFont(size=20, weight="bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="w")
    customtkinter.CTkLabel(
        header,
        textvariable=app._fx_queue_summary_var,
        text_color=globals().get("COLOR_TEXT_SOFT", "#B2C0C8"),
        font=customtkinter.CTkFont(size=12),
        anchor="e",
    ).grid(row=0, column=1, sticky="e", padx=(16, 0))

    queue_card = customtkinter.CTkFrame(window, fg_color=globals().get("COLOR_CARD", "#2B2B2B"), corner_radius=14, border_width=1, border_color=globals().get("COLOR_BORDER", "#3A3A3A"))
    queue_card.grid(row=1, column=0, sticky="nsew", padx=(18, 8), pady=(0, 16))
    queue_card.grid_rowconfigure(1, weight=1)
    queue_card.grid_columnconfigure(0, weight=1)
    customtkinter.CTkLabel(
        queue_card,
        text="等待执行",
        text_color=globals().get("COLOR_TEXT", "#E6EEF2"),
        font=customtkinter.CTkFont(size=14, weight="bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
    app._fx_queue_list_frame = customtkinter.CTkScrollableFrame(queue_card, fg_color="transparent")
    app._fx_queue_list_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
    queue_actions = customtkinter.CTkFrame(queue_card, fg_color="transparent")
    queue_actions.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
    queue_actions.grid_columnconfigure(0, weight=1)
    customtkinter.CTkButton(
        queue_actions,
        text="开始队列",
        command=lambda target=app: _start_task_queue(target),
        height=34,
        corner_radius=10,
        fg_color="#7A695B",
        hover_color="#8B7867",
        text_color="#FFFFFF",
    ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
    customtkinter.CTkButton(
        queue_actions,
        text="清空等待",
        command=lambda target=app: _clear_queued_tasks(target),
        height=34,
        width=92,
        corner_radius=10,
        fg_color="transparent",
        hover_color="#303030",
        border_width=1,
        border_color="#566274",
        text_color="#E8EDF5",
    ).grid(row=0, column=1, sticky="e")

    history_card = customtkinter.CTkFrame(window, fg_color=globals().get("COLOR_CARD", "#2B2B2B"), corner_radius=14, border_width=1, border_color=globals().get("COLOR_BORDER", "#3A3A3A"))
    history_card.grid(row=1, column=1, sticky="nsew", padx=(8, 18), pady=(0, 16))
    history_card.grid_rowconfigure(2, weight=1)
    history_card.grid_columnconfigure(0, weight=1)
    history_header = customtkinter.CTkFrame(history_card, fg_color="transparent")
    history_header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
    history_header.grid_columnconfigure(0, weight=1)
    customtkinter.CTkLabel(
        history_header,
        text="历史与失败重试",
        text_color=globals().get("COLOR_TEXT", "#E6EEF2"),
        font=customtkinter.CTkFont(size=14, weight="bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="w")
    customtkinter.CTkLabel(
        history_header,
        textvariable=app._fx_history_summary_var,
        text_color=globals().get("COLOR_TEXT_SOFT", "#B2C0C8"),
        font=customtkinter.CTkFont(size=11),
        anchor="e",
    ).grid(row=0, column=1, sticky="e", padx=(12, 0))
    history_filters = customtkinter.CTkFrame(history_card, fg_color="transparent")
    history_filters.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
    history_filters.grid_columnconfigure(3, weight=1)
    customtkinter.CTkOptionMenu(
        history_filters,
        variable=app._fx_history_filter_status_var,
        values=[label for label, _value in QUEUE_HISTORY_STATUS_OPTIONS],
        command=lambda _value, target=app: _refresh_history_panel(target),
        height=32,
        width=110,
    ).grid(row=0, column=0, padx=(0, 8), sticky="w")
    customtkinter.CTkOptionMenu(
        history_filters,
        variable=app._fx_history_filter_task_var,
        values=[label for label, _value in QUEUE_HISTORY_TASK_OPTIONS],
        command=lambda _value, target=app: _refresh_history_panel(target),
        height=32,
        width=124,
    ).grid(row=0, column=1, padx=(0, 8), sticky="w")
    customtkinter.CTkOptionMenu(
        history_filters,
        variable=app._fx_history_filter_failure_var,
        values=[label for label, _value in QUEUE_HISTORY_FAILURE_OPTIONS],
        command=lambda _value, target=app: _refresh_history_panel(target),
        height=32,
        width=118,
    ).grid(row=0, column=2, padx=(0, 8), sticky="w")
    app._fx_history_search_entry = customtkinter.CTkEntry(
        history_filters,
        textvariable=app._fx_history_search_var,
        height=32,
        placeholder_text="搜索路径、错误、失败原因、输出位置...",
    )
    app._fx_history_search_entry.grid(row=0, column=3, sticky="ew")
    app._fx_history_list_frame = customtkinter.CTkScrollableFrame(history_card, fg_color="transparent")
    app._fx_history_list_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
    history_actions = customtkinter.CTkFrame(history_card, fg_color="transparent")
    history_actions.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
    history_actions.grid_columnconfigure(0, weight=1)
    customtkinter.CTkButton(
        history_actions,
        text="只重试失败",
        command=lambda target=app: _queue_retry_failed_history(target),
        height=34,
        corner_radius=10,
        fg_color="#6D4F3B",
        hover_color="#7C5B43",
        text_color="#FFF6E6",
    ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
    customtkinter.CTkButton(
        history_actions,
        text="重置筛选",
        command=lambda target=app: _reset_queue_history_filters(target),
        height=34,
        width=92,
        corner_radius=10,
        fg_color="transparent",
        hover_color="#303030",
        border_width=1,
        border_color="#566274",
        text_color="#E8EDF5",
    ).grid(row=0, column=1, sticky="e", padx=(0, 8))
    customtkinter.CTkButton(
        history_actions,
        text="刷新",
        command=lambda target=app: (_refresh_queue_panel(target), _refresh_history_panel(target)),
        height=34,
        width=82,
        corner_radius=10,
        fg_color="transparent",
        hover_color="#303030",
        border_width=1,
        border_color="#566274",
        text_color="#E8EDF5",
    ).grid(row=0, column=2, sticky="e")

    def on_close():
        try:
            window.withdraw()
        except Exception:
            pass

    window.protocol("WM_DELETE_WINDOW", on_close)
    _install_queue_history_filter_hooks(app)
    _refresh_queue_panel(app)
    _refresh_history_panel(app)
    return window


def _queue_add_current_task(app, start_after_add=False):
    _ensure_queue_state(app)
    try:
        task = _queue_build_task(app)
    except Exception as exc:
        try:
            app.log(f"❌ [队列] 无法加入队列：{exc}")
            tkinter.messagebox.showwarning("任务队列", str(exc))
        except Exception:
            pass
        return None
    app._fx_task_queue.append(task)
    try:
        app.log(f"📌 [队列] 已加入：{task['title']}")
    except Exception:
        pass
    _refresh_queue_panel(app)
    if start_after_add:
        _start_task_queue(app)
    return task


def _clear_queued_tasks(app):
    _ensure_queue_state(app)
    if getattr(app, "_fx_task_queue_running", False):
        try:
            app.log("ℹ️ [队列] 正在执行时不能清空等待项。")
        except Exception:
            pass
        return
    app._fx_task_queue = [item for item in app._fx_task_queue if item.get("status") == "running"]
    _refresh_queue_panel(app)


def _queue_retry_history_task(app, source):
    return _queue_replay_history_task(app, source, action_name="重试", prefer_failed_subset=True)


def _queue_replay_history_task(app, source, action_name="回放", prefer_failed_subset=False):
    _ensure_queue_state(app)
    try:
        retry_input = source.get("input")
        retry_mode = "full"
        retry_failed_items = []
        retry_cleanup = None
        if prefer_failed_subset:
            subset = _build_retry_subset_input(app, source)
            if isinstance(subset, dict) and subset.get("input"):
                retry_input = subset.get("input")
                retry_mode = str(subset.get("mode") or "subset")
                retry_failed_items = list(subset.get("failed_items") or [])
                retry_cleanup = subset.get("cleanup")
        task = _queue_build_task(app, retry_input, source.get("task_type"), retry_source=source)
        if isinstance(source.get("task_result"), dict):
            task["snapshot"]["task_result"] = dict(source.get("task_result"))
        task["history_source_id"] = source.get("id")
        task["retry_mode"] = retry_mode
        if retry_failed_items:
            task["retry_failed_items"] = list(retry_failed_items)
        if retry_cleanup:
            task["retry_staging_root"] = retry_cleanup
        app._fx_task_queue.append(task)
        if prefer_failed_subset and retry_mode != "full":
            app.log(f"🔁 [队列] 已加入{action_name}：{task['title']}（仅失败项）")
        else:
            app.log(f"🔁 [队列] 已加入{action_name}：{task['title']}")
        _refresh_queue_panel(app)
        return task
    except Exception as exc:
        try:
            app.log(f"❌ [队列] {action_name}失败：{exc}")
        except Exception:
            pass
    _refresh_queue_panel(app)
    return None


def _queue_retry_failed_history(app):
    _ensure_queue_state(app)
    failed = [item for item in getattr(app, "_fx_task_history", []) if item.get("status") == "failed"]
    if not failed:
        try:
            app.log("ℹ️ [队列] 暂无失败历史可重试。")
        except Exception:
            pass
        return
    for item in failed:
        _queue_retry_history_task(app, item)


def _run_task_queue_worker(app):
    _ensure_queue_state(app)
    app._fx_task_queue_running = True
    try:
        while True:
            task = next((item for item in app._fx_task_queue if item.get("status") == "queued"), None)
            if task is None:
                break
            task["started_at"] = time.time()
            task["logs"] = []
            _queue_set_task_status(app, task, "running")
            try:
                app.after(0, lambda target=app, current=task: _queue_restore_app_state(target, current))
            except Exception:
                _queue_restore_app_state(app, task)
            time.sleep(0.05)
            original_log = _queue_capture_task_logs(app, task)
            try:
                _clear_last_task_result(app)
                _start_task_result(app, task.get("input"), task.get("task_type"))
                app.stop_event = False
                app.is_running = True
                try:
                    app.progress_bar.set(0)
                except Exception:
                    pass
                app.run_process(task.get("input"), task.get("task_type"))
                task_result = _infer_task_result_from_context(
                    app,
                    task.get("input"),
                    task.get("task_type"),
                    return_value=None,
                    logs=task.get("logs"),
                )
                if isinstance(task_result, dict):
                    task["task_result"] = dict(task_result)
                    _queue_set_task_status(app, task, task_result.get("status", "unknown"), task_result.get("detail", ""))
                elif getattr(app, "stop_event", False):
                    _queue_set_task_status(app, task, "stopped", "用户停止")
                elif _queue_task_had_errors(task):
                    _queue_set_task_status(app, task, "failed", "执行日志中包含失败或错误信息")
                else:
                    _queue_set_task_status(app, task, "success", "执行完成")
            except Exception as exc:
                task["exception"] = str(exc)
                _queue_set_task_status(app, task, "failed", exc)
                try:
                    app.log(f"🔥 [队列] {task.get('title', '')} 执行异常：{exc}")
                except Exception:
                    pass
            finally:
                _queue_restore_task_logs(app, original_log)
                try:
                    app.is_running = False
                except Exception:
                    pass
                _append_queue_history(app, task)
                _clear_last_task_result(app)
                retry_cleanup = task.get("retry_staging_root")
                if retry_cleanup:
                    try:
                        shutil.rmtree(retry_cleanup, ignore_errors=True)
                    except Exception:
                        pass
                try:
                    app._fx_task_queue = [item for item in app._fx_task_queue if item.get("id") != task.get("id")]
                except Exception:
                    pass
                _refresh_queue_panel(app)
                _refresh_history_panel(app)
        try:
            app.log("✅ [队列] 队列执行完成。")
        except Exception:
            pass
    finally:
        app._fx_task_queue_running = False
        try:
            app.reset_ui()
        except Exception:
            pass
        _refresh_queue_panel(app)
        _refresh_history_panel(app)


def _start_task_queue(app):
    _ensure_queue_state(app)
    if getattr(app, "_fx_task_queue_running", False):
        try:
            app.log("ℹ️ [队列] 队列已经在执行中。")
        except Exception:
            pass
        return
    if not any(item.get("status") == "queued" for item in app._fx_task_queue):
        try:
            app.log("ℹ️ [队列] 当前没有等待执行的任务。")
        except Exception:
            pass
        return
    try:
        app.log("🚦 [队列] 开始顺序执行任务。")
    except Exception:
        pass
    threading.Thread(target=_run_task_queue_worker, args=(app,), daemon=True).start()


def _install_queue_bottom_actions(app):
    _ensure_queue_state(app)
    if getattr(app, "_fx_queue_actions_ready", False):
        return
    action_row = None
    try:
        for child in app.bottom_bar.winfo_children():
            if isinstance(child, customtkinter.CTkFrame) and child.winfo_children():
                action_row = child
                break
    except Exception:
        action_row = None
    if action_row is None:
        return
    app._fx_queue_summary_var = tkinter.StringVar(value="")
    try:
        app.btn_queue_add = customtkinter.CTkButton(
            action_row,
            text="加入队列",
            command=lambda target=app: _queue_add_current_task(target),
            height=40,
            width=104,
            corner_radius=10,
            fg_color="transparent",
            hover_color="#303030",
            border_width=1,
            border_color="#B89352",
            text_color="#F6E2B2",
        )
        app.btn_queue_add.pack(side="left", padx=(0, 12))
        app.btn_queue_panel = customtkinter.CTkButton(
            action_row,
            text="队列历史",
            command=lambda target=app: _show_task_queue_window(target),
            height=40,
            width=104,
            corner_radius=10,
            fg_color="transparent",
            hover_color="#303030",
            border_width=1,
            border_color="#566274",
            text_color="#E8EDF5",
        )
        app.btn_queue_panel.pack(side="left", padx=(0, 18))
    except Exception as exc:
        _debug(f"queue:bottom_actions_error:{exc}")
        return
    app._fx_queue_actions_ready = True
    _refresh_queue_status_summary(app)


def _patch_task_queue_history():
    try:
        original_setup_main_area = FengxiToolboxApp.setup_main_area
        original_on_start_click = FengxiToolboxApp.on_start_click
    except Exception as exc:
        _debug(f"queue:patch_missing:{exc}")
        return
    if getattr(original_setup_main_area, "__fx_queue_history_patch__", False):
        return

    def patched_setup_main_area(self, *args, **kwargs):
        result = original_setup_main_area(self, *args, **kwargs)
        try:
            _install_queue_bottom_actions(self)
        except Exception as exc:
            _debug(f"queue:install_after_main_area_error:{exc}")
        return result

    def patched_on_start_click(self):
        if getattr(self, "_fx_start_via_queue", False):
            return original_on_start_click(self)
        return original_on_start_click(self)

    patched_setup_main_area.__fx_queue_history_patch__ = True
    patched_on_start_click.__fx_queue_history_patch__ = True
    FengxiToolboxApp.setup_main_area = patched_setup_main_area
    FengxiToolboxApp.on_start_click = patched_on_start_click
    _debug("queue:patch_installed")


_patch_task_queue_history()


def _patch_runtime_progress_reporting():
    try:
        original_run_process = FengxiToolboxApp.run_process
    except Exception as exc:
        _debug(f"patch_runtime_progress:missing:{exc}")
        return

    if getattr(original_run_process, "__fx_runtime_progress_patch__", False):
        return

    runtime_run_process = _unwrap_runtime_run_process(original_run_process)
    if runtime_run_process is None:
        _debug("patch_runtime_progress:no_runtime_run_process")
        return
    site_map = _build_runtime_progress_site_map(runtime_run_process)

    def patched_run_process(self, input_folder, task_type):
        _start_task_result(self, input_folder, task_type)
        tracker = None
        result = None
        try:
            tracker = _install_run_progress_tracker(
                self,
                input_folder,
                task_type,
                runtime_run_process=runtime_run_process,
                site_map=site_map,
            )
            result = original_run_process(self, input_folder, task_type)
            return result
        except Exception as exc:
            _finalize_current_task_result(
                self,
                "failed",
                message=str(exc),
                detail=str(exc),
                error=str(exc),
            )
            raise
        finally:
            if tracker is not None:
                try:
                    tracker.finalize_pending()
                except Exception:
                    pass
                try:
                    tracker.restore()
                except Exception as exc:
                    _debug(f"patch_runtime_progress:restore_error:{exc}")
            try:
                _infer_task_result_from_context(
                    self,
                    input_folder,
                    task_type,
                    return_value=result,
                    logs=getattr(self, "_fx_last_task_logs", None),
                )
            except Exception as exc:
                _debug(f"patch_runtime_progress:finalize_result_error:{exc}")

    patched_run_process.__fx_runtime_progress_patch__ = True
    FengxiToolboxApp.run_process = patched_run_process
    _debug(
        "patch_runtime_progress:installed:"
        f"process={sorted(site_map.get('before_process_single', set()))}:"
        f"direct={sorted(site_map.get('direct_pre', set()))}:"
        f"pass={sorted(site_map.get('pass_through', set()))}"
    )


_patch_runtime_progress_reporting()


def _get_internal_attr(obj, name, default=None):
    try:
        return object.__getattribute__(obj, name)
    except AttributeError:
        return default


def _guess_lazy_tab_for_attr(name):
    for prefix, task_name in LAZY_ATTR_PREFIXES:
        if name.startswith(prefix):
            return task_name
    return None


def _ensure_lazy_tab_initialized(app, task_name):
    spec = LAZY_TAB_SPECS.get(task_name)
    if spec is None:
        return False

    lazy_state = _get_internal_attr(app, "_fx_lazy_tabs_state", None)
    if not lazy_state:
        return False
    if lazy_state.get(task_name):
        return True

    initializers = _get_internal_attr(app, "_fx_lazy_tab_initializers", {})
    initializer = initializers.get(task_name)
    if not callable(initializer):
        initializer = getattr(app, spec["init"], None)
    if not callable(initializer):
        return False

    _debug(f"lazy_tab:init:{task_name}:start")
    initializer()
    lazy_state[task_name] = True
    try:
        _tighten_layout(app, task_name=task_name)
    except Exception as exc:
        _debug(f"lazy_tab:layout_refresh_error:{task_name}:{exc}")
    try:
        app.update_idletasks()
    except Exception:
        pass
    _debug(f"lazy_tab:init:{task_name}:done")
    return True


def _show_ready_window(app):
    _install_fast_close_protocol(app)
    try:
        app.update_idletasks()
    except Exception as exc:
        _debug(f"startup:update_idletasks_error:{exc}")
    try:
        app.deiconify()
        app.lift()
        _debug("startup:window_shown")
    except Exception as exc:
        _debug(f"startup:window_show_error:{exc}")


def _request_fast_close(app):
    if getattr(app, "_fx_fast_close_started", False):
        return
    app._fx_fast_close_started = True
    try:
        _flush_watermark_text_persistence(app)
    except Exception as exc:
        _debug(f"fast_close:wm_text_flush_error:{exc}")
    try:
        _flush_watermark_filename_rule_persistence(app)
    except Exception as exc:
        _debug(f"fast_close:wm_filename_rule_flush_error:{exc}")
    try:
        app.stop_event = True
    except Exception:
        pass
    try:
        app.is_running = False
    except Exception:
        pass
    try:
        app.withdraw()
        app.update_idletasks()
        _debug("fast_close:window_hidden")
    except Exception as exc:
        _debug(f"fast_close:withdraw_error:{exc}")

    def finish_destroy():
        try:
            app.quit()
        except Exception:
            pass
        try:
            app.destroy()
            _debug("fast_close:destroy_done")
        except Exception as exc:
            _debug(f"fast_close:destroy_error:{exc}")
            try:
                os._exit(0)
            except Exception:
                pass

    def force_exit_if_needed():
        try:
            if getattr(app, "_fx_fast_close_force_done", False):
                return
            app._fx_fast_close_force_done = True
            _debug("fast_close:force_exit")
            os._exit(0)
        except Exception:
            pass

    if not getattr(app, "_fx_disable_fast_close_force_exit", False):
        try:
            timer = threading.Timer(0.9, force_exit_if_needed)
            timer.daemon = True
            timer.start()
        except Exception as exc:
            _debug(f"fast_close:force_timer_error:{exc}")

    try:
        app.after_idle(finish_destroy)
    except Exception:
        finish_destroy()


def _install_fast_close_protocol(app):
    if getattr(app, "_fx_fast_close_protocol_ready", False):
        return
    try:
        app.protocol("WM_DELETE_WINDOW", lambda target=app: _request_fast_close(target))
        app._fx_fast_close_protocol_ready = True
        _debug("fast_close:protocol_installed")
    except Exception as exc:
        _debug(f"fast_close:protocol_error:{exc}")


def _patch_startup_performance():
    try:
        original_setup_main_area = FengxiToolboxApp.setup_main_area
        original_switch_tab = FengxiToolboxApp.switch_tab
        original_ctk_init = customtkinter.CTk.__init__
    except Exception as exc:
        _debug(f"patch_startup_performance:missing:{exc}")
        return

    original_getattr = getattr(FengxiToolboxApp, "__getattr__", None)

    if getattr(original_setup_main_area, "__fx_lazy_startup_patch__", False):
        return

    def patched_show_readme(self):
        return _show_inline_help(self)

    def patched_ctk_init(self, *args, **kwargs):
        original_ctk_init(self, *args, **kwargs)
        if _get_internal_attr(self, "_fx_start_hidden", False):
            return
        try:
            self.withdraw()
            self._fx_start_hidden = True
            _debug("startup:window_hidden")
        except Exception as exc:
            _debug(f"startup:window_hidden_error:{exc}")

    def patched_setup_main_area(self):
        self._fx_lazy_tabs_state = {name: False for name in LAZY_TAB_SPECS}
        self._fx_lazy_tab_initializers = {}
        self._fx_lazy_startup_in_progress = True
        try:
            for task_name, spec in LAZY_TAB_SPECS.items():
                init_name = spec["init"]
                initializer = getattr(self, init_name, None)
                if callable(initializer):
                    self._fx_lazy_tab_initializers[task_name] = initializer
                if task_name == DEFAULT_STARTUP_TAB:
                    continue

                def deferred_init(_task_name=task_name):
                    _debug(f"lazy_tab:deferred:{_task_name}")
                    return None

                setattr(self, init_name, deferred_init)

            result = original_setup_main_area(self)
            self._fx_lazy_tabs_state[DEFAULT_STARTUP_TAB] = True
            self._fx_lazy_startup_ready = True
            return result
        finally:
            self._fx_lazy_startup_in_progress = False
            for task_name, initializer in self._fx_lazy_tab_initializers.items():
                try:
                    setattr(self, LAZY_TAB_SPECS[task_name]["init"], initializer)
                except Exception:
                    pass

    def patched_switch_tab(self, task_name, btn_obj):
        try:
            if not (
                _get_internal_attr(self, "_fx_lazy_startup_in_progress", False)
                and task_name == DEFAULT_STARTUP_TAB
            ):
                _ensure_lazy_tab_initialized(self, task_name)
        except Exception as exc:
            _debug(f"lazy_tab:switch_error:{task_name}:{exc}")
        result = original_switch_tab(self, task_name, btn_obj)
        try:
            _set_help_button_selected(self, False)
            _set_help_action_state(self, False)
            self.update_idletasks()
            _refresh_visible_tab_layout(self, task_name)
            self.update_idletasks()
        except Exception as exc:
            _debug(f"lazy_tab:visible_layout_refresh_error:{task_name}:{exc}")
        return result

    def patched_getattr(self, name):
        task_name = _guess_lazy_tab_for_attr(name)
        if task_name is not None:
            try:
                _ensure_lazy_tab_initialized(self, task_name)
                return object.__getattribute__(self, name)
            except AttributeError:
                pass
            except Exception as exc:
                _debug(f"lazy_tab:getattr_error:{name}:{exc}")
        if callable(original_getattr):
            return original_getattr(self, name)
        raise AttributeError(f"{type(self).__name__!s} object has no attribute {name!r}")

    patched_ctk_init.__fx_hidden_startup_patch__ = True
    patched_setup_main_area.__fx_lazy_startup_patch__ = True
    patched_switch_tab.__fx_lazy_startup_patch__ = True
    patched_getattr.__fx_lazy_startup_patch__ = True
    patched_show_readme.__fx_inline_help_patch__ = True
    customtkinter.CTk.__init__ = patched_ctk_init
    FengxiToolboxApp.setup_main_area = patched_setup_main_area
    FengxiToolboxApp.switch_tab = patched_switch_tab
    FengxiToolboxApp.__getattr__ = patched_getattr
    FengxiToolboxApp.show_readme = patched_show_readme
    _debug("patch_startup_performance:installed")


_patch_startup_performance()


def _patch_sidebar_build_performance():
    try:
        original_setup_sidebar = FengxiToolboxApp.setup_sidebar
    except Exception as exc:
        _debug(f"patch_sidebar_build_performance:missing:{exc}")
        return

    if getattr(original_setup_sidebar, "__fx_fast_sidebar_build_patch__", False):
        return

    def patched_setup_sidebar(self, *args, **kwargs):
        return _run_with_fast_sidebar_button_construction(
            self,
            lambda: original_setup_sidebar(self, *args, **kwargs),
        )

    patched_setup_sidebar.__fx_fast_sidebar_build_patch__ = True
    FengxiToolboxApp.setup_sidebar = patched_setup_sidebar
    _debug("patch_sidebar_build_performance:installed")


_patch_sidebar_build_performance()

try:
    _wrap_callable(customtkinter.CTk, "__init__", "ctk_init")
    _wrap_callable(pywinstyles, "apply_style", "pywinstyles.apply_style")
    _wrap_callable(pywinstyles, "change_header_color", "pywinstyles.change_header_color")
    _wrap_callable(windnd, "hook_dropfiles", "windnd.hook_dropfiles")
    _wrap_callable(Image, "open", "Image.open")
    _wrap_callable(FengxiToolboxApp, "scan_fonts", "app.scan_fonts")
    _wrap_callable(FengxiToolboxApp, "setup_sidebar", "app.setup_sidebar")
    _wrap_callable(FengxiToolboxApp, "setup_main_area", "app.setup_main_area")
    _wrap_callable(FengxiToolboxApp, "log", "app.log")
except Exception as _wrap_exc:
    _debug(f"bootstrap:wrap_error:{_wrap_exc}")


if __name__ == "__main__":
    diag_path = (os.environ.get("FX_OCR_DIAG_PATH") or "").strip()
    if diag_path:
        from tools.fx_pdf_ocr import run_packaged_ocr_diagnostics

        run_packaged_ocr_diagnostics(diag_path)
        raise SystemExit(0)
    _debug("main:create_app")
    app = FengxiToolboxApp()
    _debug("main:app_created")
    _apply_app_icon(app)
    _debug("main:icon_applied")
    _apply_release_identity(app)
    _debug("main:release_identity_applied")
    _tighten_layout(app)
    _debug("main:layout_tightened")
    _show_ready_window(app)
    app.mainloop()
