"""End-to-end checks for single-save finishing and transactional publishing."""

import statistics
import time

import pikepdf
from pypdf import PdfWriter
from reportlab.pdfgen import canvas

from tools.fx_edit_password import protect_pdf_editing
from tools.fx_watermark_finish import verify_pdf_output
import tools.fx_watermark_core as core


def run_watermark_finish_tests(mod, app, root, record):
    folder = root / "watermark_finish"
    folder.mkdir()
    source = folder / "source.pdf"
    writer = canvas.Canvas(str(source))
    for page in range(16):
        for line in range(45):
            writer.drawString(40, 800 - line * 16, f"Page {page + 1} line {line + 1}: Sample source text for watermark finishing.")
        writer.showPage()
    writer.save()
    template = folder / "template.pdf"
    writer = canvas.Canvas(str(template))
    writer.drawString(40, 700, "INSERTED TEMPLATE")
    writer.save()
    password = "finish-test-password"
    settings = dict(mod._get_watermark_settings(app), force_mode=True, insert_page_enabled=True,
                    insert_page_path=str(template), insert_page_position="end",
                    edit_password_enabled=True, edit_password=password)
    settings = mod._prepare_watermark_insert_page_settings(settings)

    original_save, original_write = pikepdf.Pdf.save, PdfWriter.write
    counts = {"save": 0, "write": 0}
    def counted_save(*args, **kwargs):
        counts["save"] += 1
        return original_save(*args, **kwargs)
    def counted_write(*args, **kwargs):
        counts["write"] += 1
        return original_write(*args, **kwargs)

    for guard in (False, True):
        settings["copy_guard_enabled"] = guard
        counts.update(save=0, write=0)
        pikepdf.Pdf.save, PdfWriter.write = counted_save, counted_write
        output = folder / f"output_{guard}.pdf"
        try:
            status = mod._watermark_process_pdf(source, output, settings)
        finally:
            pikepdf.Pdf.save, PdfWriter.write = original_save, original_write
        with pikepdf.open(output) as doc:
            correct = len(doc.pages) == 17 and doc.is_encrypted and not doc.allow.modify_other
        record(f"watermark_pdf_single_save_insert_password_guard_{guard}",
               status == "SUCCESS" and correct and sum(counts.values()) == 1, dict(counts))

    original_fast = core._add_watermark_and_copy_guard_to_pdf
    core._add_watermark_and_copy_guard_to_pdf = lambda *args, **kwargs: "ERROR:simulate fast-path failure"
    fallback = folder / "fallback.pdf"
    try:
        status = mod._watermark_process_pdf(source, fallback, settings)
    finally:
        core._add_watermark_and_copy_guard_to_pdf = original_fast
    verify_pdf_output(fallback, password)
    with pikepdf.open(fallback) as doc:
        fallback_ok = len(doc.pages) == 17 and str(doc.docinfo.get("/FXInsertedWatermarkPage")) == "Fengxi Toolbox"
    record("watermark_finish_compatibility_fallback", status == "SUCCESS" and fallback_ok)

    existing = folder / "existing.pdf"
    original_content = source.read_bytes()
    existing.write_bytes(original_content)
    original_verify = mod.verify_pdf_output
    def reject_output(*args):
        raise ValueError("simulate verification failure after encryption")
    mod.verify_pdf_output = reject_output
    try:
        status = mod._watermark_process_pdf(source, existing, settings)
        missing = folder / "must_not_be_published.pdf"
        missing_status = mod._watermark_process_pdf(source, missing, settings)
    finally:
        mod.verify_pdf_output = original_verify
    record("watermark_finish_failure_preserves_existing_and_hides_partial_output",
           status.startswith("ERROR:") and missing_status.startswith("ERROR:")
           and existing.read_bytes() == original_content and not missing.exists()
           and not list(folder.glob("fx_wm_pending_*")))

    # Compare the previous three-save sequence with the integrated pipeline,
    # including output validation in both measurements.
    settings["copy_guard_enabled"] = True
    old_times, new_times = [], []
    for repeat in range(4):
        baseline = folder / f"baseline_{repeat}.pdf"
        begin = time.perf_counter()
        status = mod.add_watermark_to_pdf(
            source, baseline, mod._watermark_make_pdf_packet(settings),
            check_text=settings["text"], force_mode=True, copy_guard=True,
            copy_guard_strength=settings["copy_guard_strength"],
        )
        if status != "SUCCESS":
            raise AssertionError(status)
        mod._insert_watermark_page_into_pdf(baseline, settings)
        protect_pdf_editing(baseline, password)
        verify_pdf_output(baseline, password)
        old_times.append(time.perf_counter() - begin)
        begin = time.perf_counter()
        status = mod._watermark_process_pdf(source, folder / f"integrated_{repeat}.pdf", settings)
        new_times.append(time.perf_counter() - begin)
        if status != "SUCCESS":
            raise AssertionError(status)
    record("watermark_finish_benchmark_16_pages",
           True, {"previous_median_seconds": round(statistics.median(old_times), 4),
                  "integrated_median_seconds": round(statistics.median(new_times), 4),
                  "sample": "synthetic 16-page text PDF; watermark + guard + insert + password + verification"})
