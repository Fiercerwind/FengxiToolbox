# 最近变更

## 2026-05-29 16:08:00 | convert
- 摘要：packaged and opened compact preview build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt and opened the release after compacting the audio/video speech-to-text realtime preview layout. Packaged EXE is running. PyInstaller pycparser/AppKit warnings were non-blocking optional/cross-platform probe noise.

## 2026-05-29 16:04:31 | convert
- 摘要：speech-to-text preview compact layout
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/convert-audio-image.md, memory/debug-status.md
- 说明：Reordered audio/video speech-to-text realtime preview before the model hint, reduced preview height to 96px, preserved model-hint key phrases, and added compact-layout regression. Validation: py_compile passed, targeted UI probe passed, smoke_test 14/14, full_debug_test 169/169.

## 2026-05-29 15:50:31 | convert
- 摘要：packaged and opened realtime preview build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt and opened the release after adding audio/video speech-to-text realtime preview. Packaged process is running. PyInstaller optional pycparser/cross-platform probe warnings were non-blocking; quick _internal check did not show torch/tensorflow/tensorboard/paddle heavy directories.

## 2026-05-29 15:45:40 | convert
- 摘要：speech-to-text realtime preview
- 文件：Fengxi_Toolbox.py, tools/fx_audio_task.py, tools/fx_speech_to_text.py, full_debug_test.py, memory/categories/convert-audio-image.md, memory/debug-status.md
- 说明：Added scrollable realtime transcript preview for audio/video speech-to-text. Faster-Whisper segment progress now flows through the audio task callback into the UI preview via Tk after(). Validation: py_compile passed, targeted UI probe passed, smoke_test 14/14, full_debug_test 168/168.

## 2026-05-29 15:24:11 | convert
- 摘要：packaged and opened model hint build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt and opened the release after adding the speech-to-text model explanation hint. Packaged process is running. PyInstaller optional pycparser/cross-platform probe warnings were non-blocking; quick _internal check did not show torch/tensorflow/tensorboard/paddle heavy directories.

## 2026-05-29 15:21:18 | convert
- 摘要：speech-to-text model hint
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/convert-audio-image.md, memory/debug-status.md
- 说明：Added inline model tradeoff explanation to the audio/video speech-to-text UI and a regression check. Validation: py_compile passed, targeted UI probe passed, smoke_test 14/14, full_debug_test 165/165.

## 2026-05-29 15:03:01 | convert
- 摘要：packaged and opened speech-to-text build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt the onedir release after adding Fengxi audio/video speech-to-text and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe. Packaged process is running. PyInstaller optional pycparser/cross-platform probe warnings were non-blocking; quick _internal check did not show torch/tensorflow/tensorboard/paddle heavy directories.

## 2026-05-29 14:59:50 | convert
- 摘要：audio video speech-to-text
- 文件：Fengxi_Toolbox.py, tools/fx_audio_task.py, tools/fx_speech_to_text.py, fx_toolbox.spec, requirements.txt, full_debug_test.py, memory/categories/convert-audio-image.md, memory/debug-status.md
- 说明：Added native Fengxi audio/video speech-to-text mode with Faster-Whisper backend, txt/srt outputs, last-settings memory, model cache under user prefs, packaging hooks, and regression coverage. Validation: py_compile passed, smoke_test 14/14, full_debug_test 164/164.

## 2026-05-29 00:41:09 | watermark
- 摘要：packaged and opened watermark parameter memory build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt the onedir release after adding automatic batch-watermark parameter memory and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe. Packaged process is running.

## 2026-05-29 00:37:06 | watermark
- 摘要：watermark parameter auto memory
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md
- 说明：Added debounced automatic last-settings persistence for the batch-watermark parameter panel: font, page range, smart/force mode, filename skip rule, Simsun compatibility, delete source, convert-to-PDF first, color, size, opacity, angle, and output strategy. Validation: py_compile passed; targeted probe confirmed saved values; full_debug_test 160/160; smoke_test 14/14.

## 2026-05-29 00:11:35 | watermark
- 摘要：packaged and opened watermark preview repair
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt the onedir release after the real watermark color preview visibility repair and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe. Packaged process is running.

## 2026-05-29 00:08:08 | watermark
- 摘要：watermark color preview real visibility repair
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md
- 说明：Fixed the second visibility failure by anchoring the color preview to the actual app.wm_text panel instead of tab child index, destroying stale preview frames, and repairing after main-area setup. Validation: py_compile passed; targeted UI probe showed one preview before the textbox; full_debug_test 159/159; smoke_test 14/14.

## 2026-05-28 23:33:47 | watermark
- 摘要：watermark color preview visibility fix
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md, dist_release_ascii/fx_toolbox/fx_toolbox.exe
- 说明：Moved batch-watermark color picker and preview from the clipped right-side parameter panel to the left watermark-content panel below the text editor, compacted preview image to 360x92, and strengthened regression to assert the preview frame is packed under the left panel. Validation: py_compile passed; full_debug_test 159/159; package.bat succeeded; packaged EXE launched and running.

## 2026-05-28 23:12:04 | runtime
- 摘要：default package and open workflow
- 文件：agent.md, memory/architecture.md, memory/debug-status.md, dist_release_ascii/fx_toolbox/fx_toolbox.exe
- 说明：User requested future work to automatically package and open the app. Added the default behavior to agent and memory: after implementation/debug tasks, validate as appropriate, stop only this repo's packaged fx_toolbox.exe, run package.bat, and open dist_release_ascii/fx_toolbox/fx_toolbox.exe unless explicitly told not to. Rebuilt release and launched packaged EXE; process is running.

## 2026-05-28 22:26:02 | runtime
- 摘要：startup recursion and packaged startup speed fix
- 文件：Fengxi_Toolbox.py, tools/fx_startup_patches.py, fx_toolbox.spec, full_debug_test.py, memory/architecture.md, memory/debug-status.md, dist_release_ascii/fx_toolbox/fx_toolbox.exe
- 说明：Fixed packaged EXE startup RecursionError by blocking lazy-tab reentrant initialization, deferring hidden-window layout refresh until after deiconify, adding a Windows single-instance mutex, delaying watermark preview refresh, and excluding RapidOCR optional PyTorch/Paddle/TensorRT plus torch/paddle/tensorflow/tensorboard packages from PyInstaller. Validation: py_compile passed; smoke_test 14/14; full_debug_test 159/159; package.bat succeeded; packaged EXE launched; duplicate launch exits with single_instance:already_running; _internal has no torch/paddle/tensorflow/tensorboard dirs.

## 2026-05-28 20:36:32 | watermark
- 摘要：watermark color picker and preview
- 文件：Fengxi_Toolbox.py, tools/fx_watermark_core.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md, memory/architecture.md
- 说明：Added selectable #RRGGBB watermark color for PDF and Word output, inline PIL preview UI, and last-settings memory for wm_color_var. Validation: py_compile passed, smoke_test 14/14, full_debug_test 159/159.

## 2026-05-28 18:19:39 | runtime
- 摘要：packaged and opened direct Word watermark visibility build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt and opened the onedir release after fixing direct Word watermark visible rendering. Build completed successfully; PyInstaller warnings were non-blocking optional dependency/cross-platform probe noise.

## 2026-05-28 18:13:06 | watermark
- 摘要：direct Word watermark visible rendering fix
- 文件：tools/fx_watermark_core.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md, memory/architecture.md
- 说明：Fixed direct Word watermark success-but-invisible output by explicitly setting WordArt fill visibility, solid gray fill, no outline, overlap wrapping, and a Word-only minimum visible opacity. Added rendered Word export regressions for helper and app.run_process direct watermark paths. Validation: py_compile passed, smoke_test 14/14, full_debug_test 156/156.

## 2026-05-28 17:45:21 | runtime
- 摘要：packaged and opened watermark real fix build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt the onedir release after the batch watermark direct/convert-PDF fix and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe. Packaging completed successfully; PyInstaller warnings were non-blocking optional dependency and cross-platform probe noise.

## 2026-05-28 17:40:29 | watermark
- 摘要：batch watermark direct and PDF conversion real fix
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md, memory/architecture.md
- 说明：Added loader-layer watermark task runner so single-file Word direct watermark and Word-to-PDF watermark produce real outputs, structured results, and real failures instead of false success. Word-to-PDF conversion now falls back to safe Word ExportAsFixedFormat when runtime conversion fails. Validated with real user document, smoke_test 14/14, full_debug_test 154/154.

## 2026-05-28 16:58:57 | runtime
- 摘要：packaged and opened batch watermark COM fix build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Rebuilt the onedir release after the Dispatch/DispatchEx Office COM guard and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe. Packaging completed successfully; launched process is running.

## 2026-05-28 16:54:29 | watermark
- 摘要：batch watermark Word COM Dispatch guard
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md, memory/architecture.md
- 说明：Patched both win32com.client.Dispatch and DispatchEx at the loader layer so the runtime batch-watermark .docx branch cannot hit damaged pywin32 gen_py Word wrappers. Added real app.run_process watermark .docx regression; py_compile passed, smoke_test 14/14, full_debug_test 152/152.

## 2026-05-28 16:38:42 | runtime
- 摘要：packaged and opened Office COM fix build
- 文件：dist_release_ascii\fx_toolbox\fx_toolbox.exe,memory\recent-changes.md,memory\changes.jsonl
- 说明：Built the onedir release after the Office COM gen_py safe dispatch fix and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe for manual testing. Build completed successfully; PyInstaller warnings were non-blocking optional dependency/cross-platform probes.
