# 水印与去水印

## 批量水印
- 任务类型：`watermark`
- 关键参数：
  - 水印文本
  - 字体
  - 字号
  - 透明度
  - 旋转角度
  - 页范围：`all` / `first`
  - 防重模式：`smart` / `force`
  - 是否按文件名规则跳过文件
  - 是否先转 PDF 再加水印
  - 是否删除源文件
- 关键函数：
  - `create_watermark_packet`
  - `add_watermark_to_pdf`
  - `add_watermark_to_word`
- 2026-05-23：
  - 在用户明确授权“稳定区核心逻辑也可以拆模块”的前提下，新增 `tools/fx_watermark_core.py` 承接加水印核心实现。
  - `Fengxi_Toolbox.py` 仍保留 `create_watermark_packet(...)`、`add_watermark_to_pdf(...)`、`add_watermark_to_word(...)` 同名薄包装，负责把加载器层已有的字体解析、Word 兼容字体、COM 缓存禁用 context 注入核心模块。
  - `_ns` 继续暴露原函数名，避免 `fengxi_runtime.bin` 旧调用点感知模块迁移。
  - 当前拆分不改变 UI 参数、不改变智能跳过规则、不改变输出路径和任务调度行为。
  - 回归覆盖：`watermark_core_module_exports`、`pdf_watermark`、`word_watermark`，并随全量 `full_debug_test.py` 131/131 通过。
- 2026-05-09：
  - 水印文本框 `wm_text` 现已具备“用户填写后自动记忆，下次启动自动回填”的 UI 层持久化能力。
  - 实现仍限定在 `Fengxi_Toolbox.py` 加载器层，不修改 `fengxi_runtime.bin` 内的加水印业务逻辑。
  - 当前仅持久化“水印内容文本”，存储到用户本地偏好文件中，而不是项目记忆文件。
  - 保存时机包括：输入防抖、文本框失焦、开始执行前、窗口关闭前。
  - 若文本被清空，则会移除已保存的文本内容，下次启动回到运行时默认文案。

## 2026-05-02 批量水印文件名跳过规则补丁
- 历史逻辑只支持一个固定规则：
  - 启用开关后，跳过“文件名去掉扩展名后以 `-` 结尾”的文件
- 用户新要求是：
  - 仍然保留“智能跳过”思路
  - 但允许在 UI 里选择“开头”或“结尾”
  - 并允许输入自定义字符或字符串
- 当前实现策略：
  - 不修改 `fengxi_runtime.bin`
  - 只在 `Fengxi_Toolbox.py` 加载器层做最小补丁
  - 保留原有 `wm_skip_hyphen_var` 开关作为是否启用规则的总开关
  - 新增两个 UI 变量：
    - `wm_skip_name_position_var`
    - `wm_skip_name_text_var`
  - 默认值保持旧行为兼容：
    - 位置：`结尾`
    - 字符：`-`
- 运行时补丁策略：
  - 在 `collect_input_files()` 包装层按“开头/结尾 + 自定义字符”过滤文件
  - 在 `run_process()` 包装层临时关闭运行时内建的固定 `-` 结尾判断
  - 这样既保留原水印主体逻辑，又把跳过规则改为用户可配置
- 这一补丁只应影响 `watermark` 任务，不得影响其他任务类型

## 2026-05-20 批量水印文件名规则记忆与提示修复
- 用户反馈：
  - `按文件名规则跳过` 下方的 `留空默认` 提示显示不全。
  - 该处的开关、匹配位置和字符输入也需要像水印文本一样具备记忆功能。
- 当前修复：
  - 仍限定在 `Fengxi_Toolbox.py` 加载器/UI/偏好层，不修改 `fengxi_runtime.bin` 和添加水印核心业务逻辑。
  - 文件名规则控件改为两行布局：
    - 第一行：`匹配位置`、`开头/结尾` 下拉框、自定义字符输入框。
    - 第二行：完整显示 `留空默认 “-”，可填写任意开头或结尾字符`。
  - 布局收紧函数会识别该控件的 `_fx_wm_filename_rule_controls` 标记并保留 56px 高度，避免后续统一压缩布局时再次裁切提示。
  - 本地用户偏好新增 `watermark.filename_skip_rule`：
    - `enabled`
    - `position`
    - `marker`
  - 保存时机包括变量变更防抖、输入框失焦/回车、执行水印任务前、窗口关闭前。
  - 若用户把 marker 清空，下次启动仍回填为空；实际执行时继续沿用旧兼容行为，空 marker 默认按 `-` 匹配。
- 新增回归：
  - `watermark_filename_rule_memory_save`
  - `watermark_filename_rule_memory_load`
  - `watermark_filename_rule_hint_layout`
- 边界：
  - `run_process()` 内部为绕开运行时固定 `-` 结尾判断而临时关闭旧开关时，会设置 `_fx_wm_filename_rule_loading`，避免该内部切换被误保存成用户偏好。
  - 这次没有改 `create_watermark_packet`、`add_watermark_to_pdf`、`add_watermark_to_word` 等核心水印函数。

## 2026-05-22 批量水印上次设置自动记忆
- 当前不再提供独立预设中心；批量水印页会自动保存并恢复上次使用的常用参数。
- 当前记忆范围：
  - 水印文本
  - 字体
  - 页范围
  - 防重/覆盖模式
  - 是否允许宋体兜底
  - 是否删除源文件
  - 是否先转 PDF
  - 文件名跳过规则开关、开头/结尾、匹配字符
  - 字号、透明度、旋转角度
  - 输出策略
- 该能力只改加载器层 UI/偏好，不改 `create_watermark_packet`、`add_watermark_to_pdf`、`add_watermark_to_word`。
- 回归：`last_settings_watermark_save_restore`。

## 2026-05-29 批量水印参数配置即时记忆
- 用户要求右侧“参数配置”区域也能记忆。
- 已在加载器层给批量水印参数加防抖自动保存，不再只依赖开始任务或关闭软件时保存。
- 当前即时记忆范围：
  - 字体
  - 每一页/仅第一页
  - 智能防重/强制添加
  - 跳过文件名规则开关、位置、字符
  - 兼容模式（Word/宋体）
  - 成功后删除源文件
  - 先转 PDF 再加水印
  - 水印颜色
  - 字号、透明度、旋转角度
  - 当前输出策略
- 实现边界：只改 `Fengxi_Toolbox.py` 的 UI/偏好保存绑定，不改 `tools/fx_watermark_core.py` 和水印处理核心逻辑。
- 回归：`watermark_parameters_auto_memory` 覆盖截图参数的自动写入；`last_settings_watermark_save_restore` 继续覆盖恢复。

## 去水印
- 任务类型：`remove_wm`
- Word 去水印通过扫描页眉中的艺术字 / 图片水印处理
- PDF 去水印走“PDF -> Word -> 去水印 -> PDF”的重构链路
- 关键开关：`保留我的水印 (XMU_DONE)`

## 2026-04-22 去水印单线程约束
- `remove_wm` 必须稳定走单线程 Word COM 专用分支
- 如果误落到 `process_single_file()` 普通路径，PDF/Word 只会被复制并写“跳过”日志，不会真正去水印

## 2026-04-22 去水印误删修复
- `remove_watermark_from_word()` 旧实现过于激进
- 当前原则是“宁可少删，也不要误删正常内容”
- 重点修复：
  - 页眉 `InlineShapes` 图片型水印漏删
  - 正常页眉 logo / 标题图形被误删
- 当前回归重点：
  - `word_remove_wm_header_inline_image`
  - `word_remove_wm_preserve_header_assets`

## 2026-04-22 到 2026-04-24 PDF 去水印稳健性补丁
- PDF 去水印与 Word 去水印是两类不同问题
- PDF 链路当前由加载器层兜底为：
  - `PDF -> ASCII 临时 DOCX -> 安全版 remove_watermark_from_word(..., is_pdf_source=True) -> Word 转回 PDF`
- 为避免批量处理中的 COM 污染：
  - `_create_hidden_word_app()` 使用 `DispatchEx("Word.Application")`
  - 去水印和转回 PDF 分别使用独立 Word 会话
- 单文件去水印当前规则：
  - 默认在同目录输出新文件
  - 可选“成功时覆盖原文件”
  - 失败时原文件保持不变

## 稳定性标记
- 这一块是用户明确标记的稳定区
- 非必要不改水印主体逻辑
- 如必须修改，优先做加载器层外围补丁、兼容性补丁或测试增强

## 2026-05-22 去水印分级模式
- `remove_wm` 现在新增三档强度：`保守（推荐）` / `标准` / `激进`，默认是 `保守（推荐）`。
- 三档只改加载器层识别阈值与 UI/偏好，不改 `fengxi_runtime.bin`，也不触碰批量压缩和添加水印核心逻辑。
- `标准` 保持上一版去水印阈值口径：普通形状约 `width>=35% page` 或 `height>=20% page`，内联图片约 `45% x 16%`。
- `保守` 提高普通形状尺寸、居中、旋转和透明度要求，降低误删正常图文风险；但内联大图水印保留可删能力，避免漏掉页眉图片型水印。
- `激进` 降低阈值并允许超大居中对象进入候选，适合顽固水印，但必须提示用户更可能误删正常元素。
- 用户选择会保存到本地偏好 `watermark.remove_wm_mode`，下次进入去水印页面自动恢复。
- 执行链路通过线程本地上下文把当前模式传给 runtime 内部的 Word 去水印调用；PDF roundtrip 也显式传入当前模式。
- 新增回归：
  - `remove_wm_mode_memory_save_load`
  - `remove_wm_mode_memory_trace_save`
  - `remove_wm_mode_shape_thresholds`
  - `remove_wm_mode_inline_thresholds`
- 关键回归仍需覆盖：
  - `pdf_remove_wm_workflow`
  - `pdf_remove_wm_single_file_output`
  - `pdf_remove_wm_single_file_overwrite`
  - `word_remove_wm_header_inline_image`
  - `word_remove_wm_preserve_header_assets`

## 2026-05-22 PDF 去水印 Word COM 导出兜底
- `remove_wm` 的 PDF round-trip 仍保持 `PDF -> DOCX -> remove_watermark_from_word(..., is_pdf_source=True) -> PDF`，但 DOCX 回写 PDF 阶段新增加载层兜底 `_export_word_docx_to_pdf_safely(...)`。
- 根因：本机 pywin32 `win32com.gen_py` Word 缓存可能损坏，症状是 `CLSIDToClassMap` 缺失；运行时 `convert_doc_to_pdf(...)` 会吞掉细节并返回 `ERROR`，导致 `【处理完成】结果文件夹` 不生成目标 PDF。
- 修复策略：先保留原 `convert_doc_to_pdf(...)` 尝试；若失败或未落盘，则用动态 Word COM 直接 `ExportAsFixedFormat(..., 17)` 导出 PDF。
- `_dispatch_com_app_dynamic("Word.Application")` 对 Word 改为 `pythoncom.CoCreateInstance + win32com.client.dynamic.Dispatch` 新实例路径，避免 `DispatchEx` 触发损坏的 `gen_py` 包装缓存。
- 重要约束：凡是访问 Word 子对象（`Documents`、`Sections`、`Headers`、`InlineShapes` 等）时都要包在 `_DisableWin32ComGenCache()` 内，不只是在创建 Word 实例时包一次。
- 回归覆盖：`pdf_remove_wm_workflow`、`pdf_remove_wm_single_file_output`、`pdf_remove_wm_single_file_overwrite`、`word_to_pdf`、`word_watermark`、`word_remove_wm`、`word_remove_wm_header_inline_image`、`word_remove_wm_preserve_header_assets`、`word_meta_author`。
- 边界：本次仍只改 `Fengxi_Toolbox.py` 加载层与 `full_debug_test.py`，未修改 `fengxi_runtime.bin`，未触碰稳定区的批量压缩和添加水印核心逻辑。
## 2026-05-28 Batch watermark Word COM Dispatch guard
- User report: batch add-watermark on a single `.docx` still logged `Word COM 初始化失败` with pywin32 `win32com.gen_py ... CLSIDToClassMap/CLSIDToPackageMap`, then misleadingly printed a perfect completion message.
- Root cause: the embedded runtime batch-watermark branch creates Word through `win32com.client.Dispatch("Word.Application")`, while the first Office COM cache fix only patched `DispatchEx`.
- Fix boundary: keep add-watermark business logic unchanged; install a loader-layer guard for both `win32com.client.Dispatch` and `DispatchEx`, routing Word creation through `_dispatch_com_app_dynamic("Word.Application")` when pywin32 gen_py cache is damaged.
- Regression: `watermark_docx_run_process_safe_word_dispatch` runs the real `app.run_process(..., "watermark")` workflow on a generated `.docx`, verifies an output `.docx` exists, and rejects logs containing `Word COM 初始化失败`.
- Validation: `python -m py_compile Fengxi_Toolbox.py full_debug_test.py`; direct Word dispatch probe; `python smoke_test.py` 14/14; `python full_debug_test.py` 152/152.

## 2026-05-28 Batch watermark real task runner
- User confirmed both direct Word watermark and "convert to PDF then watermark" failed in real use; this was explicitly authorized as a necessary exception to the stable add-watermark protection.
- Root causes:
  - runtime `convert_doc_to_pdf(...)` could return `ERROR` or fail to write a PDF under damaged Word COM cache, then the old branch copied/preserved the source and still ended as a false success
  - single-file watermark output/result modeling was not aligned with the unified task result model, so outputs/counts could be empty even when a file was written
- Fix:
  - `watermark` now supports the shared output strategy UI (`same_dir`, `overwrite`, `result_folder` semantics)
  - loader-layer `_run_watermark_task(...)` owns collection, output planning, direct PDF watermark, direct Word watermark, Word/PPT to PDF then PDF watermark, delete-source option, failure report, progress updates, and structured result counts
  - `_convert_doc_to_pdf_safely(...)` first tries the runtime converter and then falls back to `_export_word_docx_to_pdf_safely(...)` if no valid PDF lands
  - Word direct mode now creates same-directory `*_加水印.docx` for single-file default output; convert-to-PDF mode creates `*_加水印.pdf`
  - real failures now produce `status=failed` with failed item details instead of a fake perfect completion
- Regression:
  - `watermark_docx_single_same_dir_output_model`
  - `watermark_docx_convert_pdf_safe_fallback`
- Real-user probe passed on `《习近平经济思想概论》复习纲要2026B_答案.docx`:
  - direct Word output had `XMU_DONE` marker and watermark text
  - convert-to-PDF output had 25 pages and contained the watermark text
- Validation: `python -m py_compile Fengxi_Toolbox.py full_debug_test.py`; real document direct/convert probes; `python smoke_test.py` 14/14; `python full_debug_test.py` 154/154.

## 2026-05-28 Word direct watermark visibility fix
- User verified "convert to PDF first" watermark works, but direct Word watermark still only looked successful and was not visible in Word.
- Reproduction:
  - A minimal direct Word watermark output contained `XMU_DONE` shapes and watermark text in the `.docx`, but exporting that `.docx` through Word to PDF showed only body text and no visible watermark.
  - The old regression was insufficient because it only checked XML/text existence, not rendered visibility.
- Root cause:
  - WordArt watermark shapes were inserted into headers, but their fill attributes were not explicit enough for stable Word rendering.
  - Default UI opacity `0.08` mapped to Word `Fill.Transparency ~= 0.92`, which can be effectively invisible in Word direct mode.
- Fix:
  - `tools/fx_watermark_core.py` now explicitly sets WordArt fill visible, solid, gray (`0xC0C0C0`), no line, and allow-overlap wrapping.
  - Word direct mode clamps visible opacity to a minimum `0.18`, preserving a light gray watermark while avoiding "written but invisible" output.
  - PDF watermark behavior is unchanged; the minimum visibility clamp is only inside the Word watermark helper.
- Regression:
  - `word_watermark_visible_when_exported` verifies helper output is visible after Word exports it to PDF.
  - `watermark_docx_direct_visible_when_exported` verifies the real `app.run_process(..., "watermark")` direct Word path is visible after export.
- Validation: `python -m py_compile Fengxi_Toolbox.py tools/fx_watermark_core.py full_debug_test.py`; targeted Word visibility probe; `python smoke_test.py` 14/14; `python full_debug_test.py` 156/156.

## 2026-05-28 Watermark color picker and preview
- Batch watermark now supports a selectable watermark color for both PDF and direct Word output.
- `tools/fx_watermark_core.py` keeps backward-compatible default gray behavior, and only changes color when the loader passes an explicit `#RRGGBB` value.
- `Fengxi_Toolbox.py` adds a loader-layer color row on the watermark page: color swatch, hex entry, system color chooser, and lightweight PIL preview. The preview does not invoke Office/PDF rendering, so it should stay fast.
- The selected color participates in last-settings memory through `wm_color_var`, so the next session restores the previous watermark color.
- Regression coverage added:
  - `pdf_watermark_custom_color`
  - `word_watermark_custom_color`
  - `watermark_color_preview_ui`
  - existing `last_settings_watermark_save_restore` now checks color restore.
- Validation: `python -m py_compile Fengxi_Toolbox.py tools\fx_watermark_core.py full_debug_test.py`; `python smoke_test.py` 14/14; `python full_debug_test.py` 159/159.
- Boundaries: no changes to `fengxi_runtime.bin`; batch-compress untouched; add-watermark core changed only to accept optional color while preserving default behavior.
## 2026-05-28 23:33:16 Watermark color preview visibility fix
- User screenshot showed the color picker and preview were not visible on the batch-watermark page because the controls were appended at the bottom of the right-side parameter panel, below the visible area.
- Fix: move _fx_wm_color_preview_controls to the left-side watermark-content panel, below the watermark text editor; shrink the editor height when the preview exists and use a compact 360x92 preview card.
- Regression strengthened: watermark_color_preview_ui now asserts the preview frame is packed under the left panel and refreshes successfully.
- Validation: python -m py_compile Fengxi_Toolbox.py full_debug_test.py; python full_debug_test.py 159/159; package.bat; packaged EXE launched.

## 2026-05-29 Watermark color preview real visibility repair
- User still could not see the color picker/preview after the first move.
- Cause: the runtime can build overlapping watermark panel pairs during startup; the first visibility patch placed preview controls into an old panel, while the real `app.wm_text` textbox lived in a newer panel.
- Fix: locate the target panel by walking up from the actual `app.wm_text`, remove stale `_fx_wm_color_preview_controls` frames, and run a repair pass after main-area setup plus last-settings restore.
- Regression: `watermark_color_preview_ui` now checks the preview frame is under the actual text panel, is packed before the textbox via `pack_slaves()`, refreshes successfully, and has no duplicate stale preview frames.
- Validation: `python -m py_compile Fengxi_Toolbox.py full_debug_test.py`; targeted UI hierarchy probe; `python full_debug_test.py` 159/159; `python smoke_test.py` 14/14.

## 2026-06-01 Batch watermark skipped-file copy option
- Request: on top of the existing filename-rule skip feature, user needs a choice for whether skipped files should be copied into the output/result folder.
- UI:
  - Batch watermark filename-rule block now has `跳过文件复制到输出文件夹`.
  - The option is saved/restored with watermark last-settings and local `watermark.filename_skip_rule.copy_skipped`.
- Runtime behavior:
  - Files matched by the skip rule are not watermarked.
  - If copy is enabled, skipped originals are copied to the output folder, preserving relative folder structure.
  - Folder input still uses `【处理完成】结果文件夹`; single/same-dir cases use that result folder for skipped copies to avoid overwriting the source.
  - Result model counts skipped files in `skipped_count`, watermarked files in `success_count`, and includes copied skipped files in `outputs`.
- Boundaries:
  - Did not change `add_watermark_to_pdf`, `add_watermark_to_word`, or watermark rendering core.
  - This is a loader/UI/task-runner extension around the existing stable batch watermark workflow.
- Validation:
  - Targeted probe: `normal.pdf` was watermarked, `FX_skip.pdf` was skipped and copied byte-for-byte to `【处理完成】结果文件夹`.
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_user_prefs.py full_debug_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 181/181.

## 2026-06-01 Batch watermark prefix/suffix skip rule restoration
- Request: restore the existing filename-rule skip choice so users can choose `开头` or `结尾/末尾` and type a marker; example `结尾` + `-` skips files whose basename ends with `-`.
- Fix:
  - Added loader-layer normalization for watermark filename-rule positions.
  - Accepted values now include `开头`, `结尾`, `末尾`, `前缀`, `后缀`, `prefix`, `suffix`, `start`, and `end`.
  - Preferences are saved back as canonical `开头` or `结尾`, so old/English/non-standard values do not silently break the rule.
  - The `跳过文件复制到输出文件夹` option remains compatible with both prefix and suffix skips.
- Regression:
  - Added `watermark_filename_rule_position_normalization`.
  - Added `watermark_suffix_dash_rule_skips_files`: `skip-.pdf` is skipped by `结尾` + `-`, copied byte-for-byte when enabled, while `normal.pdf` is watermarked.
- Boundaries:
  - No changes to `tools/fx_watermark_core.py`.
  - No changes to watermark rendering core or batch compression.

## 2026-06-01 Batch watermark skip-rule UI active-panel fix
- Symptom:
  - User screenshot showed the page still displayed the old switch `跳过文件名以 '-' 结尾的文件`, and the new prefix/suffix/marker/copy controls were not visible.
- Cause:
  - The watermark page can contain two similar parameter panels during loader-layer startup/layout repair.
  - The previous UI patch inserted the filename-rule controls into the first hidden/stale panel, while the actually visible right-side parameter panel still kept the old switch.
- Fix:
  - Filename-rule UI lookup now targets the active/latest skip switch.
  - During watermark layout tightening, the loader ensures the visible right-side parameter panel has the controls row and renames the switch to `按文件名规则跳过`.
  - Added a regression that verifies the controls row and the active skip switch share the same parent panel, preventing invisible/stale-panel UI regressions.
- Validation:
  - Targeted UI probe: active controls row and active skip switch are in the same right-side parameter panel.
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 184/184.

## 2026-06-01 Batch watermark skip-rule adjacent layout fix
- Symptom:
  - User screenshot showed `按文件名规则跳过` was visible, but its related controls (`匹配位置`, marker entry, copy skipped checkbox) were separated below font, compatibility, PDF-convert, and slider controls.
- Fix:
  - The active filename-rule controls row is now explicitly packed immediately after the active skip switch.
  - Watermark layout tightening now treats the filename-rule controls row by marker, not by fragile child index, so slider/font compaction no longer moves it away.
- Regression:
  - Added `watermark_filename_rule_controls_below_switch`, asserting the controls row is exactly the next packed widget after the active skip switch.
- Validation:
  - Targeted UI probe: switch index `3`, controls index `4`, adjacent `True`.
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 185/185.

## 2026-06-01 Batch watermark output-path failure isolation
- Symptom: a folder batch could stop halfway with [批量水印] 严重错误: [WinError 3] when a nested output path could not be created, especially suspicious paths with trailing spaces in a folder name.
- Rule going forward: batch watermark task-runner/output-path failures must be per-file failures, not whole-task crashes. Continue processing remaining files and write a failed-file report when possible.
- Implementation: _run_watermark_task now catches target parent creation failures before processing each file and records them in ailed_items; skipped-file copy root and failure report creation also log graceful failures.
- Regression: watermark_output_path_failure_does_not_abort_batch.
- Do not fix this by changing 	ools/fx_watermark_core.py; this is an output planning/task-runner resilience issue, not watermark rendering.

## 2026-06-01 Batch watermark progress bar sync
- Symptom: batch watermark bottom status text could show real progress while the blue progress bar did not move.
- Rule going forward: watermark task progress updates must update both progress_bar.set(fraction) and _set_progress_status(...); do not update status text alone.
- Implementation: _watermark_update_progress(...) is the watermark runner helper for synchronized progress updates.
- Regression: watermark_progress_bar_syncs_with_status.
- Boundaries: do not fix this by editing watermark rendering core; this is a loader/UI progress synchronization issue.

## 2026-06-01 Watermark core modification rule update
- New user instruction: watermark rendering core is no longer an absolute no-touch area.
- It may be modified when necessary, including 	ools/fx_watermark_core.py, but must preserve stable processing behavior, output rules, skip rules, color/preview settings, Word/PDF compatibility, and task result semantics unless the user explicitly asks for behavior changes.
- Any core change must include regression coverage and validation notes. Prefer minimal, explainable patches over broad rewrites.
- This supersedes older notes saying not to touch watermark rendering core except for modularization.

## 2026-06-01 Batch watermark trailing-space directory output fix
- Symptom: real batch run failed at [WinError 3] under a result path containing a source directory segment with trailing space, e.g. 系解人体结构神经系统资料试卷 .
- Root cause: result-folder output mirrored source relative directories verbatim; Windows may reject path segments ending with spaces or dots when creating/accessing nested directories.
- Fix: _watermark_safe_relative_parent(...) now sanitizes each relative directory segment for result-folder outputs by stripping trailing spaces/dots. _copy_watermark_skipped_files(...) applies the same sanitization to copied skipped files.
- Important: do not rename or delete source files/folders. Only generated result-folder paths are normalized for Windows safety.
- Regressions: watermark_result_path_strips_trailing_space_dirs, watermark_output_path_failure_does_not_abort_batch, watermark_progress_bar_syncs_with_status.
- Validation: smoke_test 14/14; full_debug_test 188/188.

## 2026-06-03 Watermark And Remove-Watermark Resume Rules
- Batch watermark: if the planned output already exists and is nonempty, skip that file, reuse the output, and count it as success + skipped. Do not delete the source for resumed items.
- Folder PDF remove-watermark: `_run_remove_wm_pdf_roundtrip(...)` skips a PDF when the planned output in `【处理完成】结果文件夹` already exists and is nonempty.
- Single-file remove-watermark: same-directory resume checks the base `*_去水印.pdf` path only.
- Do not use `_build_single_remove_wm_output_path(...)` for resume detection, because it intentionally returns a unique new name such as `*_去水印_2.pdf` when the base output exists.
- Actual new single-file processing still uses `_finalize_single_remove_wm_output(...)` and the unique-output helper, preserving no-overwrite behavior.
- Regression: `pdf_remove_wm_single_resume_existing_output`.
## 2026-06-04 Batch watermark real-world failure sweep
- Request: fix a real Archive failure list where batch watermark previously failed on path-mismatched PDFs, protected PDFs, damaged PDFs, and damaged Office files.
- Fix:
  - `tools/fx_watermark_core.py` now has `open_word_document_safely(...)` and uses repair-style open attempts before giving up on Word sources.
  - Damaged/unreadable Word sources now return `SKIP:damaged word source` instead of hard failure.
  - Loader-layer preserve-original logic now treats `SKIP:damaged word source` the same way as protected PDFs: copy the original into output and continue the batch.
- Real-file validation:
  - Mixed Archive probe with 7 representative files finished as `success`, with `4 success / 3 skipped / 0 failed / no failure report`.
  - Skip cases were:
    - protected PDF copied through unchanged;
    - broken `.doc` copied through unchanged;
    - broken `.docx` copied through unchanged.
- Regression:
  - `word_open_repair_fallback`
  - `watermark_damaged_word_preserves_original`
- Rule going forward:
  - If a Word source is unreadable/corrupted and cannot be safely opened even with repair fallback, batch watermark must not mark the whole run failed. Preserve the original file in output, count it as skipped, and keep processing the rest.
## 2026-06-04 批量水印“未处理文件复制”补齐
- 用户需求：
  - 之前 `跳过文件复制到输出文件夹` 只稳定覆盖了“按文件名规则跳过”的文件。
  - 现在需要把所有“未处理文件”也纳入复制范围，例如 `txt`、`zip` 这类不会加水印的文件。
- 当前规则：
  - 文件名规则跳过文件继续沿用 `_copy_watermark_skipped_files(...)`，按原相对路径复制。
  - 主循环里被判定为 `SKIP:*` 的未处理文件，只要开启 `wm_copy_skipped_var`，也会在任务结束后统一复制到输出/结果目录。
  - 受保护 PDF、损坏 Word 这类本来就会保留原文件的跳过项，仍按原保留逻辑走，不重复改写。
  - 额外保留 `_collect_watermark_input_files(...)` + `unsupported_skipped_files` 兜底，用来覆盖收集阶段就被排除的未来边界情况。
- 关键实现边界：
  - 只改 `Fengxi_Toolbox.py` 的批量水印任务调度层和 `full_debug_test.py` 回归。
  - 不改 `tools/fx_watermark_core.py` 渲染核心。
- 新增回归：
  - `watermark_copy_unsupported_files_to_result_folder`
  - 场景：`normal.pdf` 正常加水印，`notes.txt` 和 `data.zip` 作为未处理文件被计入 `skipped_count`，并复制到 `【处理完成】结果文件夹`。

## 2026-06-05 批量水印按文件类型跳过
- 用户需求：
  - 在现有“按文件名规则跳过”基础上，再增加“按文件类型不加水印”的选择。
  - 需要支持至少 `PDF`、`Word`、`PPT` 三类。
  - 如果用户没有勾选任何类型，行为必须与旧版完全一致，不能误改稳定工作流。
  - 如果开启了 `跳过文件复制到输出文件夹`，这些按类型跳过的文件也要进入输出/结果目录。
- 当前实现：
  - `Fengxi_Toolbox.py`
    - 新增 `wm_skip_pdf_type_var`、`wm_skip_word_type_var`、`wm_skip_ppt_type_var`。
    - 在批量水印右侧参数区、“按文件名规则跳过”区域下方，增加 `不添加水印的文件类型` 复选项：`PDF` / `Word` / `PPT`。
    - `_run_watermark_task(...)` 在正式处理前先按类型过滤输入文件；被选中的类型不进入加水印主循环。
    - 这类文件计入 `skipped_count`，并在日志中以 `按文件类型跳过` 说明。
    - 若 `wm_copy_skipped_var` 开启，则按原有 skipped-copy 出口复制到输出位置，保持与文件名规则跳过一致的相对路径行为。
  - 上次设置记忆：
    - 三个类型开关已接入 watermark last-settings 自动保存/恢复。
- 关键兼容规则：
  - 未勾选任何类型时，批量水印行为必须与旧逻辑完全一致。
  - 该功能只影响 batch watermark 的 loader/UI/task-runner 层，不应改变 `tools/fx_watermark_core.py` 的渲染逻辑。
  - 类型跳过与文件名规则跳过、未处理文件复制、受保护 PDF / 损坏 Word 保留原文件逻辑可以并存，最终统一体现在 `skipped_count` 和 `outputs`。
- 新增/增强回归：
  - `watermark_type_skip_options_visible`
  - `watermark_type_skip_pdf_copies_and_word_processes`
  - `watermark_parameters_auto_memory`
  - `last_settings_watermark_save_restore`
- 验证：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py` 14/14 通过。
  - `python full_debug_test.py` 207/207 通过。
## 2026-06-07 Word first-page-only watermark scope fix
- Symptom: direct Word watermark ignored the UI option `????` / `page_range=first`; generated `.docx` files showed the watermark on every page.
- Root cause: Word direct watermark is implemented through headers. The previous core code stopped after adding one shape, but it added that shape to the normal primary header, and Word repeats primary headers across all pages in the section.
- Fix: `tools/fx_watermark_core.py` now maps `page_range=first` to Word's first-page header semantics: enable `DifferentFirstPageHeaderFooter` on the first section and add the watermark to header index `2` only. `page_range=all` still uses the existing all-header behavior.
- Regression: `word_watermark_first_page_only_scope` creates a two-page Word document, applies `page_range=first`, exports the result to PDF, and asserts page 1 has visible watermark pixels while page 2 has none.
- Validation: `python -m py_compile Fengxi_Toolbox.py tools\fx_watermark_core.py full_debug_test.py` passed; `python smoke_test.py` passed 14/14; `python full_debug_test.py` passed 210/210. In the new regression, page 1 pixels were 29205 and page 2 pixels were 0.
- Boundary: no UI/task-runner behavior changed; PDF watermark behavior unchanged; batch compression untouched.

## 2026-06-08 Watermark page range: first page plus one random page
- User request: add a third watermark page-range option next to `all pages` and `first page only`.
- New mode: `first_random`.
- Behavior:
  - For a one-page document, watermark page 1 only.
  - For documents with at least two pages, watermark page 1 plus exactly one randomly selected non-first page.
  - Total watermarked pages should therefore be 2 at most.
- UI:
  - Batch watermark page now shows `第一页 + 随机一页`.
  - The option is wired into the same `wm_range_var` setting and participates in watermark last-settings persistence.
- PDF implementation:
  - `tools/fx_watermark_core.py` normalizes page ranges through `normalize_watermark_page_range(...)`.
  - PDF watermarking now selects target page indexes with `_select_watermark_page_indexes(...)`.
- Word implementation:
  - `first` and `first_random` still use Word first-page header semantics for page 1.
  - `first_random` adds the extra random non-first page via an anchored WordArt shape at that page range, instead of repeating through all headers.
- Regression coverage:
  - `watermark_range_first_random_option_visible`
  - `pdf_watermark_first_random_two_pages`
  - `word_watermark_first_random_two_pages`
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_watermark_core.py full_debug_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 213/213.

## 2026-07-05 PDF-only batch watermark parallel fast path
- Batch watermark can now use the existing `enable_multithread` switch for PDF-only folder runs.
- Fast path conditions are intentionally narrow:
  - input is a folder, not a single file;
  - more than one processable file;
  - every processable file is a PDF;
  - Word/PPT `convert to PDF` watermark setting is off;
  - `_get_parallel_worker_count(...)` returns more than one worker.
- Implementation lives in `Fengxi_Toolbox.py`:
  - `_watermark_pdf_parallel_enabled(...)` gates the path.
  - `_run_watermark_pdf_parallel_task(...)` runs per-PDF watermark jobs in a `ThreadPoolExecutor`.
  - `_watermark_make_pdf_packet(...)` can rebuild the packet from precomputed bytes for each worker.
- Keep Word/PPT watermark and Office conversion paths serial. Office COM remains the risky part for multi-threading.
- Regression anchor: `watermark_pdf_parallel_executor`.

## 2026-07-11 PDF copy-interference layer
- Added an optional `复制干扰层（PDF / Word）` module to Batch Watermark, with `轻度 / 标准 / 强力` strengths and default-off behavior.
- Research references:
  - `Riyoway/pdf-hidden-text` demonstrates ReportLab text rendering mode 3 merged through pypdf: https://github.com/Riyoway/pdf-hidden-text
  - Evaluated the surrounding PDF ecosystem through `pymupdf/PyMuPDF`, `pikepdf/pikepdf`, `py-pdf/pypdf`, and `borb-pdf/borb`.
- Implementation:
  - Reuses the existing ReportLab + pypdf dependencies and the bundled pikepdf backend; no new runtime dependency was added.
  - Inserts 4, 8, or 14 mixed-character text blocks per page for light, standard, or strong mode.
  - Interleaves blocks after complete PDF `BT ... ET` text blocks, so whole-page or whole-document extraction encounters interference during the body text rather than only after the final line. Their coordinates remain on the far-left page edge so ordinary selection/copy of a text block stays clean.
  - Applies to every PDF page independently of the visible watermark page range.
  - Direct PDF input is supported. Direct editable Word inserts 1pt white guard paragraphs only between body paragraphs, so ordinary full-document copy retains the guard while copying one visible paragraph does not cross it. Word/PPT converted to PDF uses the PDF guard.
  - Adds `/FXCopyGuard = Fengxi Copy Guard v1` metadata. An already visibly watermarked PDF can be upgraded with only the missing guard; guarded PDFs are skipped unless force mode is enabled.
- Boundary:
  - PDF display, print, and rendered page pixels are unchanged.
  - This version targets direct PDF text-layer extraction. Screenshots, rasterization, or re-OCR discard the invisible text and are not prevented.
- Regression coverage:
  - `pdf_copy_guard_whole_copy_noise_local_line_clean_visual_unchanged`
  - `pdf_copy_guard_upgrades_existing_watermark_without_duplicate_visible_text`
  - `watermark_copy_guard_module_ui_and_settings`
  - `watermark_pdf_parallel_executor` also verifies copy guard in parallel outputs.
- Validation: `python -m py_compile ...` passed; `python full_debug_test.py` passed 233/233; `python smoke_test.py` passed 14/14.

## 2026-08-05 PDF copy-guard single-write optimization
- Problem: enabling the PDF copy guard previously wrote a complete temporary watermarked PDF with pypdf, then reopened and rewrote it with pikepdf to interleave guard blocks. Large document batches paid for two full output passes.
- Implementation:
  - `_inject_copy_guard_into_pikepdf(...)` owns the existing text-block-preserving guard insertion.
  - `_add_watermark_and_copy_guard_to_pdf(...)` opens the source once with pikepdf, imports the existing visible watermark packet as an overlay, injects guard blocks, writes metadata, and saves once.
  - `add_watermark_to_pdf(...)` uses this path whenever a copy guard is being added. If it cannot complete, it retains the previous pypdf-plus-pikepdf route as a compatibility fallback.
- Scope: PDF only. Word and Office conversion behavior remains unchanged. The guard remains between complete `BT ... ET` text blocks, so local selection behavior is preserved.
- Regression: `pdf_copy_guard_uses_single_write_path` blocks the legacy second-pass helper and verifies the real public API still produces visible text plus guard content.
- Validation: `python full_debug_test.py` passed 238/238. A text-dense fixture measured about 2.5x faster median processing (0.108s to 0.043s); image-only PDFs remain primarily limited by the unavoidable final pikepdf rewrite and disk throughput.

## 2026-07-11 Word paragraph-boundary and mixed-character guard
- User required the guard to preserve normal single-paragraph copying while corrupting whole-document copying for both PDF and Word.
- PDF now uses complete text-block boundaries (`BT ... ET`) instead of individual text-show instructions; PDFs do not encode reliable semantic paragraphs, so this is the safe non-invasive boundary.
- Direct Word output now inserts guard paragraphs only between meaningful main-body paragraphs. A Word `Font.Hidden` implementation was rejected after real COM verification showed that Word omits hidden runs from normal whole-document text reads/copy.
- Word guard paragraphs are standard text-layer runs formatted as 1pt white text with exact 1pt line spacing. This preserves full-document extraction/copy while remaining visually neutral on ordinary white documents; colored or dark pages can reveal white text and are documented in the UI.
- Guard strings are unique mixed noise. PDF uses stable Latin/garbled-style fragments plus digits and symbols for built-in font compatibility; Word additionally uses Chinese fragments and replacement/mojibake-style characters.
- Regression coverage: `copy_guard_mixed_noise_character_families` and `word_copy_guard_between_paragraphs_full_copy_noises_local_copy_clean`, alongside the existing PDF/interleaving/parallel tests.
- Validation: `python full_debug_test.py` passed 235/235; `python smoke_test.py` passed 14/14.

## 2026-07-11 Copy-interference stream-order correction
- User reported that whole-page copy could still obtain all visible content before the appended interference text.
- Root cause: pypdf `merge_page(...)` appended the invisible layer as a final page content stream, and PDF extraction follows content-stream order rather than visual coordinates.
- Fix in `tools/fx_watermark_core.py`:
  - Writes the existing visible-watermark result first, then uses the bundled `pikepdf` backend to parse each page content stream.
  - Inserts invisible left-edge blocks after evenly distributed `Tj` / `TJ` text-show instructions, preserving the page's images, vector graphics, tables, and formulas without rasterizing them.
  - On text-heavy pages, the first block now occurs before the final visible line. Pages with no text still receive a guard layer.
- Regression: `pdf_copy_guard_whole_copy_noise_local_line_clean_visual_unchanged` now creates a 12-line single-page PDF and requires the first noise block to be between the first and final visible lines, while a clipped visible line remains clean and rendered pixels remain identical.
- Validation: failing baseline reproduced first; after the fix `python full_debug_test.py` passed 233/233 and `python smoke_test.py` passed 14/14.

## 2026-08-05 Batch watermark throughput optimization
- PDF copy guard keeps its single-write pikepdf path and now uses pikepdf metadata plus MuPDF first-page fallback for the normal preflight, avoiding a separate pypdf reader on the fast path.
- Pages without direct font resources are scanned/image pages with no selectable text; their content streams are not parsed and rewritten merely to add a copy guard. Visible watermarking and text-page guard behavior remain unchanged.
- PDF-only batches and mixed PDF/Office folders use a bounded PDF queue. At most `workers * 2` PDF jobs are queued, so large folders do not create thousands of pending futures and Stop only waits for the small in-flight window.
- Mixed folders start PDF work in parallel while Word/PPT stay on one Office COM session. This preserves Office stability while avoiding a single Word/PPT file disabling PDF parallelism for the entire folder.
- Watermark UI logs are batched every 160ms or 12 entries. The complete task log is still retained, while large small-file batches spend less time updating the text widget.
- This machine has a 20-logical-core i7 and 16GB RAM with an SSD. PDF watermark concurrency is therefore capped at 5 workers; this is intentionally separate from the generic 4-worker task cap to leave memory and disk bandwidth for large PDF rewrites.
- Regression: `pdf_copy_guard_fast_preflight_avoids_pypdf_reader` and `watermark_mixed_folder_splits_pdf_and_office`.
- Validation: `python smoke_test.py` 14/14 and `python full_debug_test.py` 240/240.

## 2026-08-05 Word copy-guard paragraph scan optimization
- Problem: Direct Word watermarking became very slow when the copy-interference layer was enabled. A 1200-paragraph probe took about 30.4 seconds.
- Root cause: `_word_meaningful_paragraph_ranges(...)` made multiple COM property calls for every paragraph, including `Paragraph.Range`, `Range.Text`, `Range.Start`, and `Range.End`.
- Fix: Read `doc.Content.Text` once, reconstruct meaningful paragraph ranges from Word paragraph marks in Python, and preserve the old COM paragraph scan as a compatibility fallback if the bulk read fails.
- Behavior boundary: Guard placement remains only between meaningful body paragraphs; one-paragraph copy behavior, mixed noise, guard metadata, existing-watermark skip rules, visible watermark rendering, and Word/PDF/PPT task semantics are unchanged.
- Measured result: Real 1200-paragraph Word document with standard guard improved from about 30.4s to 2.6s. The paragraph scan itself dropped from about 39s in the standalone COM probe to about 0.015s.
- Regression: `word_paragraph_scan_reads_body_text_once` rejects access to `Content.Paragraphs` and verifies the reconstructed ranges.
- Validation: `python -m py_compile Fengxi_Toolbox.py tools\\fx_watermark_core.py full_debug_test.py`; `python smoke_test.py` 14/14; `python full_debug_test.py` 242/242.

## 2026-08-05 Batch watermark persistent checkpoint resume
- Added `tools/fx_watermark_checkpoint.py` with a JSONL checkpoint log for batch watermark jobs.
- The checkpoint identity includes input path, output strategy, watermark settings, copy-guard settings, and a version. Changing any of these starts a new plan automatically.
- Each successful or safely skipped file records the source size/mtime, planned output path, and output size/mtime. On the next run, only lightweight filesystem metadata is checked; PDF/Word/PPT files are not reopened just to decide whether to resume.
- User Stop writes `paused`, so the next run resumes the unfinished entries. Normal completion writes `completed`; partial failures write `failed`; an exception writes `interrupted`, and an abrupt process kill leaves `running` so it is distinguishable from a deliberate pause.
- The Batch Watermark panel exposes `清除断点并重新开始`. This is the explicit abandon-resume action; it removes only the checkpoint metadata and does not delete or modify user outputs.
- In-place overwrite intentionally does not enable output-based checkpoint reuse because the source itself is modified.
- Validation: `python -m py_compile Fengxi_Toolbox.py tools\\fx_watermark_checkpoint.py full_debug_test.py`; `python smoke_test.py` 14/14; `python full_debug_test.py` 246/246. No package was created.

## 2026-08-10 Batch watermark adaptive page-size switch
- 批量水印页新增 `适配特殊页面尺寸` 开关，默认开启并纳入上次设置记忆与断点身份。
- 开启后，PDF 水印按每页实际 MediaBox 宽高和方向生成尺寸变体，并按 A4 相对比例调整字号后居中叠加；关闭时保留旧固定 A4 水印行为。
- 同一 PDF 内相同的宽度、高度和旋转角度只生成一次水印层并复用，避免按页生成导致速度下降；标准 A4 页面继续复用原有水印包。
- pikepdf 单次写入路径和 pypdf 兼容回退路径都支持该选项；Word/PPT 路径不改变，只有转换为 PDF 后才使用 PDF 页面适配。
- 回归覆盖：混合横竖特殊尺寸 PDF 的居中比例、尺寸变体缓存次数、UI 开关、上次设置记忆。
