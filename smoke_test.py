import importlib.util
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import Image
from reportlab.pdfgen import canvas


def load_module():
    spec = importlib.util.spec_from_file_location("fengxi_toolbox", "Fengxi_Toolbox.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DummyApp:
    stop_event = False

    def __init__(self):
        self.logs = []

    def log(self, msg):
        self.logs.append(msg)


def main():
    mod = load_module()
    root = Path(tempfile.mkdtemp(prefix="tmp_test_artifacts_", dir=Path.cwd())).resolve()
    dummy = DummyApp()
    results = []

    def record(name, ok, detail=""):
        results.append((name, ok, detail))
        print(json.dumps({"case": name, "ok": ok, "detail": detail}, ensure_ascii=True), flush=True)

    pdf_src = root / "sample.pdf"
    c = canvas.Canvas(str(pdf_src))
    c.drawString(100, 700, "hello fengxi")
    c.save()
    pkt = mod.create_watermark_packet("CONFIDENTIAL", "SmileySans-Oblique", 36, 0.2, 45)
    pdf_out = root / "sample_wm.pdf"
    status = mod.add_watermark_to_pdf(str(pdf_src), str(pdf_out), pkt, page_range="all", check_text="CONFIDENTIAL")
    record("pdf_watermark", status == "SUCCESS" and pdf_out.exists(), status)

    img1 = root / "1.png"
    img2 = root / "2.png"
    Image.new("RGB", (100, 100), "red").save(img1)
    Image.new("RGB", (100, 100), "blue").save(img2)
    merged = root / "images.pdf"
    status = mod.merge_images_to_pdf([str(img1), str(img2)], str(merged))
    record("images_to_pdf", status == "SUCCESS" and merged.exists(), status)

    single_img_pdf = root / "single_image.pdf"
    status = mod._image_file_to_pdf(str(img1), str(single_img_pdf))
    record("image_to_pdf", status == "SUCCESS" and single_img_pdf.exists(), status)

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
    c = canvas.Canvas(str(src))
    c.drawString(100, 700, "p1")
    c.showPage()
    c.drawString(100, 700, "p2")
    c.save()
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "pdf", ("split", "", False), [])
    split_folder = out / "multi"
    record("pdf_split", split_folder.exists() and len(list(split_folder.glob("*.pdf"))) == 2, "ok")

    page_delete_out = out / "multi_删除第2页.pdf"
    page_delete_result = mod._delete_pdf_page_range(str(src), str(page_delete_out), 2, 2)
    page_delete_reader = mod.PdfReader(str(page_delete_out))
    page_delete_text = "\n".join(page.extract_text() or "" for page in page_delete_reader.pages)
    try:
        mod._delete_pdf_page_range(str(src), str(out / "invalid_delete.pdf"), 3, 3)
        page_delete_invalid_rejected = False
    except ValueError:
        page_delete_invalid_rejected = True
    record(
        "pdf_delete_single_page",
        page_delete_result["remaining_pages"] == 1
        and len(page_delete_reader.pages) == 1
        and "p1" in page_delete_text
        and "p2" not in page_delete_text
        and page_delete_invalid_rejected,
        "ok",
    )

    inp = root / "pdf_enc_in"
    out = root / "pdf_enc_out"
    inp.mkdir()
    out.mkdir()
    src = inp / "enc.pdf"
    c = canvas.Canvas(str(src))
    c.drawString(100, 700, "secret")
    c.save()
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "pdf", ("encrypt", "1234", False), [])
    enc = out / "enc.pdf"
    reader = mod.PdfReader(str(enc))
    record("pdf_encrypt", enc.exists() and reader.is_encrypted, "encrypted=" + str(reader.is_encrypted))

    inp = root / "pdf_compress_in"
    out = root / "pdf_compress_out"
    inp.mkdir()
    out.mkdir()
    src = inp / "compress.pdf"
    c = canvas.Canvas(str(src))
    c.drawString(100, 700, "compress me")
    c.save()
    compressed = out / "compress_out.pdf"
    status = mod.compress_pdf_file(str(src), str(compressed), "标准", "保留原图")
    record("pdf_compress", status.startswith("SUCCESS") and compressed.exists() and compressed.stat().st_size > 0, status)

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

    inp = root / "rename_in"
    out = root / "rename_out"
    inp.mkdir()
    out.mkdir()
    src = inp / "demo.txt"
    src.write_text("x", encoding="utf-8")
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "file", ("rename", "add", "pre_", "_suf"), [])
    record("file_rename_add", (out / "pre_demo_suf.txt").exists(), "ok")
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "file", ("rename", "cut_range", "2", "3"), [])
    record("file_rename_cut_range", (out / "do.txt").exists(), "ok")
    collision_src = inp / "dexo.txt"
    collision_src.write_text("y", encoding="utf-8")
    mod.FengxiToolboxApp.process_single_file(
        dummy, str(collision_src), str(inp), str(out), "file", ("rename", "cut_range", "2", "3"), []
    )
    record("file_rename_cut_range_collision", (out / "do (2).txt").exists(), "ok")

    inp = root / "meta_in"
    out = root / "meta_out"
    inp.mkdir()
    out.mkdir()
    src = inp / "a.txt"
    src.write_text("meta", encoding="utf-8")
    failed = []
    mod.FengxiToolboxApp.process_single_file(dummy, str(src), str(inp), str(out), "meta", ("time", "2024-05-06 07:08:09"), failed)
    record("meta_time", (out / "a.txt").exists() and not failed, str(failed))

    pdf_src = root / "pdf2word_src.pdf"
    c = canvas.Canvas(str(pdf_src))
    c.drawString(100, 700, "pdf to word test")
    c.save()
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

    failed_cases = [name for name, ok, _ in results if not ok]
    print(json.dumps({"total": len(results), "failed": failed_cases}, ensure_ascii=True), flush=True)
    if not failed_cases:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
