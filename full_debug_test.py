import importlib.util
import json
import subprocess
import time
from pathlib import Path

from PIL import Image
from pypdf import PdfReader
from reportlab.pdfgen import canvas


def load_module():
    spec = importlib.util.spec_from_file_location("fengxi_toolbox", "Fengxi_Toolbox.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.messagebox.showinfo = lambda *args, **kwargs: None
    module.messagebox.showwarning = lambda *args, **kwargs: None
    module.messagebox.showerror = lambda *args, **kwargs: None
    return module


class DummyApp:
    stop_event = False

    def __init__(self):
        self.logs = []

    def log(self, msg):
        self.logs.append(msg)


def make_pdf(path, lines):
    pdf = canvas.Canvas(str(path))
    for index, line in enumerate(lines):
        pdf.drawString(100, 700, line)
        if index != len(lines) - 1:
            pdf.showPage()
    pdf.save()


def wait_for(condition, timeout=15, interval=0.2):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return True
        time.sleep(interval)
    return condition()


def office_available(progid):
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    try:
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
    root = Path(f"tmp_full_debug_{int(time.time())}").resolve()
    root.mkdir(exist_ok=True)
    dummy = DummyApp()
    results = []

    def record(name, ok, detail="", skipped=False):
        payload = {"case": name, "ok": bool(ok), "detail": str(detail), "skipped": bool(skipped)}
        results.append(payload)
        print(json.dumps(payload, ensure_ascii=True))

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

    app = mod.FengxiToolboxApp()
    app.withdraw()
    record("app_init", True, "current_task=" + str(getattr(app, "current_task", None)))

    close_probe = type("FastCloseProbe", (), {})()
    close_destroy_called = []
    close_withdraw_called = []
    close_quit_called = []
    close_probe.stop_event = False
    close_probe.withdraw = lambda: close_withdraw_called.append(True)
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
    single_compress_text = ""
    if wait_for(lambda: single_compress_out.exists()):
        single_compress_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(single_compress_out)).pages)
    record(
        "single_file_input_pdf_compress",
        single_compress_out.exists() and "single compress input" in single_compress_text,
        single_compress_out,
    )

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

    inp = root / "meta_in"
    out = root / "meta_out"
    inp.mkdir()
    out.mkdir()
    src = inp / "a.txt"
    src.write_text("meta", encoding="utf-8")
    failed = []
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "meta", ("time", "2024-05-06 07:08:09"), failed)
    record("meta_time", (out / "a.txt").exists() and not failed, str(failed))

    inp = root / "meta_pdf_in"
    out = root / "meta_pdf_out"
    inp.mkdir()
    out.mkdir()
    src = inp / "m.pdf"
    make_pdf(src, ["meta pdf"])
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "meta", ("author", "Tester"), [])
    meta_reader = PdfReader(str(out / "m.pdf"))
    record("meta_author_pdf", meta_reader.metadata.get("/Author") == "Tester", meta_reader.metadata)

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
    app.run_process(str(fd), "file")
    wait_for(lambda: len(list(fd.glob("*.txt"))) == 1)
    record("file_dedup", len(list(fd.glob("*.txt"))) == 1, [p.name for p in fd.glob("*.txt")])

    img_root = root / "imgs2pdf"
    img_root.mkdir()
    Image.new("RGB", (60, 60), "red").save(img_root / "1.png")
    Image.new("RGB", (60, 60), "blue").save(img_root / "2.jpg")
    app.current_task = "convert"
    app.cv_mode.set("imgs2pdf")
    app.run_process(str(img_root), "convert")
    imgs_pdf = img_root / "【处理完成】结果文件夹" / "imgs2pdf_图集合并.pdf"
    record("imgs2pdf_workflow", wait_for(lambda: imgs_pdf.exists()), imgs_pdf)

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

    ocr_root = root / "pdf_ocr"
    ocr_root.mkdir()
    scan_pdf = ocr_root / "scan.pdf"
    make_pdf(scan_pdf, ["Hello OCR PDF"])
    app.current_task = "pdf"
    app.pdf_mode_var.set("ocr")
    if getattr(app, "_fx_pdf_ocr_backend_map", None):
        for display, backend_key in app._fx_pdf_ocr_backend_map.items():
            if backend_key == "rapidocr":
                app.pdf_ocr_backend.set(display)
                break
    if hasattr(app, "pdf_ocr_compare_report"):
        app.pdf_ocr_compare_report.set(True)
    app.pdf_ocr_mode.set("fullPage | 整页强制 OCR")
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

    import pythoncom
    import win32com.client

    for progid, name in [("Word.Application", "word"), ("PowerPoint.Application", "ppt")]:
        ok, detail = office_available(progid)
        record(f"{name}_com_available", ok, detail, skipped=not ok)

    word_available, _ = office_available("Word.Application")
    if word_available:
        pythoncom.CoInitialize()
        try:
            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            docx_src = root / "office_src.docx"
            doc = word.Documents.Add()
            doc.Content.Text = "hello word feature test"
            doc.SaveAs2(str(docx_src.resolve()), FileFormat=16)
            doc.Close(False)

            pdf_out = root / "office_word2pdf.pdf"
            status = mod.convert_doc_to_pdf(word, str(docx_src.resolve()), str(pdf_out.resolve()))
            record("word_to_pdf", status == "SUCCESS" and pdf_out.exists(), status)

            wm_docx = root / "office_word_wm.docx"
            status = mod.add_watermark_to_word(word, str(docx_src.resolve()), str(wm_docx.resolve()), "XMU TEST", "SmileySans-Oblique", 24, 0.2, 45)
            record("word_watermark", status == "SUCCESS" and wm_docx.exists(), status)

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

            word.Quit()
        finally:
            pythoncom.CoUninitialize()
    else:
        for name in ["word_to_pdf", "word_watermark", "word_remove_wm", "word_remove_wm_header_inline_image", "word_remove_wm_preserve_header_assets", "word_meta_author"]:
            record(name, True, "skipped_no_word_com", skipped=True)

    ppt_available, _ = office_available("PowerPoint.Application")
    if ppt_available:
        pythoncom.CoInitialize()
        try:
            ppt = win32com.client.DispatchEx("PowerPoint.Application")
            pres = ppt.Presentations.Add()
            slide = pres.Slides.Add(1, 11)
            slide.Shapes.AddTextbox(1, 50, 50, 400, 50).TextFrame.TextRange.Text = "hello ppt"
            pptx_src = root / "office_src.pptx"
            pres.SaveAs(str(pptx_src.resolve()))
            pres.Close()

            ppt_pdf = root / "office_ppt2pdf.pdf"
            status = mod.convert_ppt_to_pdf(ppt, str(pptx_src.resolve()), str(ppt_pdf.resolve()))
            record("ppt_to_pdf", status == "SUCCESS" and ppt_pdf.exists(), status)
            ppt.Quit()
        finally:
            pythoncom.CoUninitialize()
    else:
        record("ppt_to_pdf", True, "skipped_no_ppt_com", skipped=True)

    failed_cases = [item["case"] for item in results if not item["ok"]]
    print(json.dumps({"total": len(results), "failed": failed_cases}, ensure_ascii=True))


if __name__ == "__main__":
    main()
