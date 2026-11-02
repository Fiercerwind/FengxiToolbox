"""Integration checks for batch watermark editing passwords."""

from pathlib import Path

import pikepdf
from reportlab.pdfgen import canvas


def run_edit_password_tests(mod, app, root, record):
    folder = root / "watermark_edit_password"
    folder.mkdir()
    password = "FX-edit-2026"

    def pdf(path):
        writer = canvas.Canvas(str(path))
        writer.drawString(72, 720, "EDIT PASSWORD SOURCE")
        writer.save()

    def protected(path):
        with pikepdf.open(path) as doc:
            can_view = len(doc.pages) == 1 and doc.is_encrypted
            restrictions = not any((doc.allow.modify_other, doc.allow.modify_annotation,
                                    doc.allow.modify_assembly, doc.allow.modify_form))
            user_access = doc.user_password_matched and not doc.owner_password_matched
        with pikepdf.open(path, password=password) as doc:
            owner_access = doc.owner_password_matched
        try:
            with pikepdf.open(path, password="wrong-password") as doc:
                wrong_not_owner = not doc.owner_password_matched
        except pikepdf.PasswordError:
            wrong_not_owner = True
        return can_view and restrictions and user_access and owner_access and wrong_not_owner

    saved = mod._capture_preset_settings(app, "watermark")
    old_parallel = app.enable_multithread.get()
    try:
        mod._safe_named_widget_set(app, "wm_text", "EDIT PASSWORD WATERMARK")
        for name, value in {
            "wm_edit_password_enabled_var": True, "wm_edit_password_var": password,
            "wm_delete_var": False, "wm_convert_pdf": False,
            "wm_insert_page_enabled_var": False, "wm_skip_hyphen_var": True,
            "wm_skip_name_position_var": "开头", "wm_skip_name_text_var": "SKIP",
            "wm_copy_skipped_var": True, "wm_skip_pdf_type_var": False,
            "wm_skip_word_type_var": True, "wm_skip_ppt_type_var": False,
            "wm_overwrite_var": "force", "wm_copy_guard_enabled_var": False,
        }.items():
            mod._safe_var_set(app, name, value)
        app.enable_multithread.set(True)
        for name in ("normal_a.pdf", "normal_b.pdf", "SKIP.pdf"):
            pdf(folder / name)
        (folder / "type_skip.docx").write_bytes(b"type skipped source unchanged")
        output = folder / mod.RESULT_FOLDER_NAME
        output.mkdir()
        pdf(output / "normal_a.pdf")  # Existing output must gain protection.
        app.run_process(str(folder), "watermark")
        result = mod._get_last_task_result(app)
        record("watermark_edit_password_parallel_and_existing_output",
               result.get("success_count") == 2 and result.get("failed_count") == 0
               and protected(output / "normal_a.pdf") and protected(output / "normal_b.pdf"),
               "PDF opens without password; owner password matches; editing permissions denied")
        record("watermark_edit_password_rule_and_type_skips_unchanged",
               result.get("skipped_count") == 2
               and (output / "SKIP.pdf").read_bytes() == (folder / "SKIP.pdf").read_bytes()
               and (output / "type_skip.docx").read_bytes() == (folder / "type_skip.docx").read_bytes())

        settings = mod._get_watermark_settings(app)
        template = folder / "insert.pdf"
        pdf(template)
        settings.update(insert_page_enabled=True, insert_page_path=str(template))
        settings = mod._prepare_watermark_insert_page_settings(settings)
        inserted = folder / "inserted_output.pdf"
        status = mod._watermark_process_pdf(folder / "normal_a.pdf", inserted, settings)
        with pikepdf.open(inserted) as doc:
            insert_ok = len(doc.pages) == 2 and doc.is_encrypted and not doc.allow.modify_other
        record("watermark_edit_password_after_insert_page", status == "SUCCESS" and insert_ok)

        app.enable_multithread.set(False)
        single = folder / "serial.pdf"
        pdf(single)
        app.run_process(str(single), "watermark")
        serial_result = mod._get_last_task_result(app)
        serial_pdf = next((Path(p) for p in serial_result.get("outputs", []) if str(p).endswith(".pdf")), None)
        record("watermark_edit_password_serial", serial_result.get("success_count") == 1
               and serial_pdf is not None and protected(serial_pdf))
        password = "FX-edit-changed"
        mod._safe_var_set(app, "wm_edit_password_var", password)
        app.run_process(str(single), "watermark")
        record("watermark_edit_password_changed_password_reprocesses",
               mod._get_last_task_result(app).get("success_count") == 1 and protected(serial_pdf))

        mod._safe_var_set(app, "wm_overwrite_var", "smart")
        smart = folder / "smart_skip.pdf"
        settings = mod._get_watermark_settings(app)
        settings["edit_password_enabled"] = False
        mod._watermark_process_pdf(folder / "normal_a.pdf", smart, settings)
        smart_dst = folder / "smart_skipped_output.pdf"
        settings["edit_password_enabled"] = True
        status = mod._watermark_process_pdf(smart, smart_dst, settings)
        record("watermark_edit_password_smart_skip_unchanged", status.startswith("SKIP:") and not smart_dst.exists())

        mod._safe_var_set(app, "wm_edit_password_var", "")
        blank = folder / "blank.pdf"
        pdf(blank)
        app.run_process(str(blank), "watermark")
        blank_result = mod._get_last_task_result(app)
        record("watermark_edit_password_empty_rejected", blank_result.get("status") == "failed"
               and blank_result.get("processed_count") == 0 and not blank_result.get("outputs"))
        mod._safe_var_set(app, "wm_edit_password_var", password)
        snapshot = mod._capture_preset_settings(app, "watermark")
        mod._safe_var_set(app, "wm_edit_password_var", "changed")
        mod._apply_preset_settings(app, {"category": "watermark", "settings": snapshot}, switch_task=False)
        record("watermark_edit_password_settings_restore",
               app.wm_edit_password_var.get() == password and app.wm_edit_password_enabled_var.get())
        row = app._fx_wm_edit_password_row
        siblings = row.master.pack_slaves()
        before = siblings[siblings.index(row) - 1]
        record("watermark_edit_password_ui_position_and_mask",
               getattr(before, "_fx_wm_filename_rule_controls", False)
               and app.wm_edit_password_entry.cget("show") == "*")

        import pythoncom
        pythoncom.CoInitialize()
        word = None
        try:
            word = mod._create_hidden_word_app()
            doc = word.Documents.Add()
            doc.Content.Text = "Word edit password source"
            word_src = folder / "word_source.docx"
            doc.SaveAs2(str(word_src), FileFormat=16)
            doc.Close(False)
            settings = mod._get_watermark_settings(app)
            settings["force_mode"] = True
            for suffix in (".docx", ".doc"):
                dst = folder / ("word_protected" + suffix)
                source = word_src
                if suffix == ".doc":
                    legacy = word.Documents.Open(str(word_src))
                    source = folder / "word_source.doc"
                    legacy.SaveAs2(str(source), FileFormat=0)
                    legacy.Close(False)
                status = mod._watermark_process_word(source, dst, settings, word)
                check = word.Documents.Open(str(dst), ReadOnly=False, AddToRecentFiles=False)
                try:
                    read_ok = "Word edit password source" in check.Content.Text
                    restricted = check.ProtectionType == 3
                    try:
                        check.Unprotect(Password="wrong-password")
                    except Exception:
                        pass
                    wrong_rejected = check.ProtectionType == 3
                    check.Unprotect(Password=password)
                    editable = check.ProtectionType == -1
                    check.Content.InsertAfter(" Edited after password.")
                    check.Save()
                    record("watermark_edit_password_word" + suffix,
                           status == "SUCCESS" and read_ok and restricted and wrong_rejected and editable)
                finally:
                    check.Close(False)

            # Exercise the real Word-to-PDF task path, including final encryption.
            mod._safe_var_set(app, "wm_skip_word_type_var", False)
            mod._safe_var_set(app, "wm_convert_pdf", True)
            app.run_process(str(word_src), "watermark")
            converted = mod._get_last_task_result(app)
            paths = [Path(p) for p in converted.get("outputs", []) if str(p).endswith(".pdf")]
            record("watermark_edit_password_word_converted_pdf",
                   converted.get("success_count") == 1 and bool(paths) and protected(paths[0]))
        finally:
            if word is not None:
                word.Quit()
            pythoncom.CoUninitialize()

        import win32com.client
        pythoncom.CoInitialize()
        ppt = None
        try:
            ppt = win32com.client.DispatchEx("PowerPoint.Application")
            presentation = ppt.Presentations.Add()
            presentation.Slides.Add(1, 11)
            ppt_source = folder / "slides.pptx"
            presentation.SaveAs(str(ppt_source))
            presentation.Close()
            app.run_process(str(ppt_source), "watermark")
            ppt_result = mod._get_last_task_result(app)
            outputs = [Path(p) for p in ppt_result.get("outputs", []) if str(p).endswith(".pdf")]
            record("watermark_edit_password_ppt_converted_pdf",
                   ppt_result.get("success_count") == 1 and bool(outputs) and protected(outputs[0]))
        finally:
            if ppt is not None:
                ppt.Quit()
            pythoncom.CoUninitialize()

        original_protect = mod.protect_pdf_editing
        def fail_protection(*args):
            raise OSError("simulated protection failure")
        fail_source = folder / "fail.pdf"
        pdf(fail_source)
        mod._safe_var_set(app, "wm_delete_var", True)
        mod._safe_var_set(app, "wm_overwrite_var", "force")
        mod.protect_pdf_editing = fail_protection
        try:
            app.run_process(str(fail_source), "watermark")
            failed = mod._get_last_task_result(app)
            record("watermark_edit_password_failure_keeps_source",
                   failed.get("status") == "failed" and failed.get("success_count") == 0
                   and fail_source.exists())
        finally:
            mod.protect_pdf_editing = original_protect
    finally:
        mod._apply_preset_settings(app, {"category": "watermark", "settings": saved}, switch_task=False)
        app.enable_multithread.set(old_parallel)
