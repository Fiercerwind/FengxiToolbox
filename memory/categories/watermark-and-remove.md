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
