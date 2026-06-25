# 调试状态

## 2026-05-24 用户偏好存储模块化
- 本轮目标：
  - 从 `Fengxi_Toolbox.py` 中抽出 `user_prefs.json` 基础读写与小型偏好字段，给后续“上次设置”继续拆分建立更清晰的 seam。
- 关键修复：
  - 新增 `tools/fx_user_prefs.py` 和 `UserPrefsContext`。
  - 主加载器中的 `_load_user_prefs(...)`、`_save_user_prefs(...)`、`_get_saved_output_strategy(...)`、`_save_output_strategy(...)`、`_get_saved_remove_wm_mode(...)`、`_save_remove_wm_mode(...)`、`_get_saved_watermark_text(...)`、`_save_watermark_text(...)`、`_get_saved_watermark_filename_rule_settings(...)` 等改为薄包装。
  - 水印文件名跳过规则保存仍由主文件读取 app 控件，再把 normalized 数据交给 `fx_user_prefs`；UI 绑定行为不变。
- 新增回归：
  - `user_prefs_module_context`
- 关键既有回归继续通过：
  - `output_strategy_memory_save_load`
  - `remove_wm_mode_memory_save_load`
  - `last_settings_watermark_save_restore`
  - `last_settings_ocr_save_restore`
  - `last_settings_pdf_compress_save_restore`
  - `last_settings_rename_save_restore`
  - `watermark_filename_rule_memory_save`
  - `watermark_filename_rule_memory_load`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_user_prefs.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：147/147 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未改稳定区批量压缩和添加水印核心业务。
  - 未删除项目外文件。

## 2026-05-24 last_settings 存储 seam 下沉
- 本轮目标：
  - 在 `tools/fx_user_prefs.py` 已接管基础偏好后，继续下沉 `last_settings` 的纯 JSON schema 和 active-category 选择逻辑。
- 关键修复：
  - `tools/fx_user_prefs.py` 新增 `normalize_pref_category(...)`、`load_last_settings(...)`、`save_last_settings_entry(...)`、`get_active_last_settings_category(...)`。
  - `Fengxi_Toolbox.py` 的 `_load_last_settings(...)`、`_save_last_settings_entry(...)`、`_get_active_last_settings_category(...)` 改为薄包装。
  - 保留主文件里的 `_capture_preset_settings(...)` 和 `_apply_preset_settings(...)`，因为这两块仍然依赖 UI 控件、懒加载页面和 app 当前状态。
- 新增回归：
  - `user_prefs_last_settings_module_context`
- 关键既有回归继续通过：
  - `last_settings_watermark_save_restore`
  - `last_settings_ocr_save_restore`
  - `last_settings_pdf_compress_save_restore`
  - `last_settings_rename_save_restore`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_user_prefs.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：148/148 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未改稳定区批量压缩和添加水印核心业务。
  - 未删除项目外文件。

## 2026-05-24 legacy presets 存储 helper 下沉
- 本轮目标：
  - 继续收口 `user_prefs.json` schema，把残留的 legacy `presets` 读写 helper 从主加载器挪到 `tools/fx_user_prefs.py`。
- 关键修复：
  - `tools/fx_user_prefs.py` 新增 `make_preset_id(...)`、`load_presets(...)`、`save_presets(...)`、`save_preset_entry(...)`、`delete_preset_entry(...)`、`find_preset_entry(...)`。
  - `Fengxi_Toolbox.py` 保留同名 `_load_presets(...)` 等薄包装，兼容潜在旧调用。
  - 未新增“预设中心”UI；`last_settings_no_dedicated_preset_center` 继续确认页面和入口不存在。
- 新增回归：
  - `user_prefs_presets_module_context`
- 关键既有回归继续通过：
  - `last_settings_no_dedicated_preset_center`
  - `user_prefs_module_context`
  - `user_prefs_last_settings_module_context`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_user_prefs.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：149/149 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未改稳定区批量压缩和添加水印核心业务。
  - 未删除项目外文件。

## 2026-05-24 格式转换单文件 adapter seam
- 本轮目标：
  - 在已有 `convert` 核心规则与 `imgs2pdf` 任务 adapter 基础上，继续为 `word2pdf` / `pdf2word` / `ppt2pdf` 建立更窄的单文件 adapter seam。
- 关键修复：
  - `tools/fx_convert_task.py` 新增 `ConvertFileContext` 和 `process_convert_file(...)`。
  - `Fengxi_Toolbox.py` 新增 `_patch_convert_file_adapter()`，在 `task_type == "convert"` 且模式为 `word2pdf` / `pdf2word` / `ppt2pdf` 时路由到新 adapter。
  - `imgs2pdf` 仍由 `_patch_convert_imgs_to_pdf_task()` 接管；单文件 adapter 不抢多图合并路径。
  - 复杂 PDF 跳过策略在 adapter 中保持：检测为复杂/大文件时复制原 PDF 到输出目录并返回 `skipped_complex`，避免强转导致乱码。
- 新增/增强回归：
  - `convert_file_adapter_module_exports`
- 关键既有回归继续通过：
  - `convert_task_imgs2pdf_module_exports`
  - `imgs2pdf_workflow`
  - `pdf_to_word`
  - `word_to_pdf`
  - `ppt_to_pdf`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_convert_core.py tools\fx_convert_task.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：146/146 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未重写 Office COM / `pdf2docx` 真实转换后端。
  - 未改稳定区批量压缩和添加水印核心业务。
  - 未删除项目外文件。

## 2026-05-24 格式转换核心与 imgs2pdf 任务适配
- 本轮目标：
  - 继续拆 `Fengxi_Toolbox.py` 的转换页补丁层，把低风险的 `convert + imgs2pdf` 先收进独立任务适配模块。
- 关键修复：
  - 新增 `tools/fx_convert_core.py`，统一 `convert` 的模式归一化、模式描述、文件收集和输出规划。
  - 新增 `tools/fx_convert_task.py`，当前只接管 `imgs2pdf` 多图合并 PDF 任务适配，复用图片 PDF 核心的合并执行。
  - `Fengxi_Toolbox.py` 新增 `_run_convert_imgs_to_pdf_task(...)` 与 `_patch_convert_imgs_to_pdf_task()`，只在 `task_type == "convert"` 且 `cv_mode == "imgs2pdf"` 时触发，其他转换模式继续走原 runtime。
- 新增/增强回归：
  - `convert_core_module_exports`
  - `convert_task_imgs2pdf_module_exports`
  - `convert_preview_uses_core_rules`
  - `imgs2pdf_workflow` 现在追踪真实 `run_convert_imgs_to_pdf_task_core(...)` 调用和结构化 `task_result`。
- 关键既有回归继续通过：
  - `pdf_to_word`
  - `word_to_pdf`
  - `ppt_to_pdf`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_convert_core.py tools\fx_convert_task.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：145/145 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未迁移 `word2pdf` / `pdf2word` / `ppt2pdf` 的实际执行。
  - 未改稳定区批量压缩和添加水印核心业务。
  - 未删除项目外文件。

## 2026-05-24 属性隐私核心模块化
- 本轮目标：
  - 继续拆 `Fengxi_Toolbox.py` 补丁层，把 `meta` 属性隐私的时间修改、PDF 作者写入和 Office 作者 helper 收进独立核心模块。
- 关键修复：
  - 新增 `tools/fx_meta_core.py`，提供 `modify_file_timestamp(...)`、`modify_pdf_author(...)`、`modify_office_meta(...)`、`build_meta_output_path(...)`、`process_meta_file(...)`。
  - `Fengxi_Toolbox.py` 保留同名薄包装并回写 `_ns`，让运行时旧入口和测试入口继续可用。
  - `_patch_meta_core()` 接管 `task_type == "meta"` 的 `process_single_file(...)`；同时继承 `__fx_file_manager_core_patch__`，避免外层 wrapper 遮住文件管家回归标记。
- 新增回归：
  - `meta_core_module_exports`
  - `meta_core_process_file`
- 关键既有回归继续通过：
  - `modify_timestamp`
  - `meta_time`
  - `meta_author_pdf`
  - `word_meta_author`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_meta_core.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：141/141 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未改稳定区批量压缩和添加水印核心业务。
  - 未删除项目外文件。

## 2026-05-24 音频任务清尾与 OCR 回归稳定
- 本轮目标：
  - 清掉 `Fengxi_Toolbox.py` 里 `audio` 任务的旧实现死代码，只保留新模块 seam。
  - 让 `full_debug_test.py` 的 OCR 工作流不再受 `rapidocr` 模型下载波动影响。
- 关键修复：
  - 已删除 `Fengxi_Toolbox.py` 中 `return run_audio_task_core(...)` 后面的 legacy audio implementation。
  - `audio` 继续只走 `tools/fx_audio_task.py`。
  - `full_debug_test.py` 的 `pdf_ocr_searchable` / `pdf_ocr_compare_report` / 单文件 OCR / 拖拽 OCR 改为本地稳定假引擎路径，保留真实工作流外壳，但不再依赖网络下载模型。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：142/142 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未改 OCR 引擎实现。
  - 未删除项目外文件。

## 2026-05-24 文件管家去重任务适配层补齐
- 本轮目标：
  - 继续文件管家拆分，把 `file + dedup` 再收进 `tools/fx_file_manager_task.py` 的任务适配层，让 UI/app 依赖注入和核心去重算法之间的 seam 更深。
- 关键修复：
  - 新增 `run_file_dedup_task_core(...)`，负责把 `collect_input_files`、`progress_tracker`、`set_task_result_*`、`set_progress_status` 等 app 依赖串起来，再调用 `tools.fx_file_manager_core.run_file_dedup_task(...)`。
  - `Fengxi_Toolbox.py` 的 `_run_file_dedup_task(...)` 现为薄 adapter，`_patch_file_dedup_core_task()` 继续接管 `task_type == "file"` 且 `file_mode_var == "dedup"` 的真实工作流。
- 新增回归：
  - `file_manager_task_module_exports`
- 关键既有回归继续通过：
  - `file_dedup`
  - `file_dedup_core_module_exports`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_file_manager_core.py tools\fx_file_manager_task.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：139/139 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未改稳定区批量压缩和添加水印核心业务。
  - 未删除项目外文件。

## 2026-05-24 文件管家去重核心路由
- 本轮目标：
  - 继续文件管家模块化，把 `file + dedup` 的真实 `run_process(...)` 工作流从原 runtime 单线程分支接到 `tools/fx_file_manager_core.py` 的去重核心。
- 关键修复：
  - `Fengxi_Toolbox.py` 新增 `_patch_file_dedup_core_task()`，当 `task_type == "file"` 且 `file_mode_var == "dedup"` 时调用 `_run_file_dedup_task(...)`。
  - `_run_file_dedup_task(...)` 继续负责输入收集、进度状态、日志、输出根目录、结构化 task_result 和失败/停止收口。
  - `tools/fx_file_manager_core.py` 的 `run_file_dedup_task(...)` 继续负责 MD5 去重核心语义：保留首个文件，删除后续重复文件。
- 回归增强：
  - `file_dedup` 现在追踪 `mod._file_core_run_file_dedup_task` 调用，确认真实 `app.run_process(str(folder), "file")` 命中新核心。
  - `file_dedup_core_module_exports` 继续验证核心模块可独立删除重复文件并返回统计。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_file_manager_core.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：138/138 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未改稳定区批量压缩和添加水印核心业务。
  - 未删除项目外文件。

## 2026-05-24 底部进度状态布局修复
- 本轮目标：
  - 修复 PDF 压缩等长文件名场景下，底部进度状态文本挤压 `批量并行`、开始/停止、`加入队列`、`队列历史` 的显示问题。
- 关键修复：
  - `_install_progress_status_label(...)` 不再把 `_fx_progress_status_label` pack 到按钮 action row。
  - 进度条改为 `bottom_bar` 第 0 行左侧，进度状态文本改为第 0 行右侧，按钮行继续独立放在第 1 行。
  - `_apply_shell_layout_tightening(...)` 同步识别 `_fx_progress_status_label` 并保持同一 grid 布局，防止后续布局刷新把它挤回按钮行。
- 新增回归：
  - `progress_status_separate_from_action_row`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：138/138 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未改 PDF 压缩业务逻辑。
  - 未触碰稳定区批量压缩和添加水印核心业务。
  - 未删除项目外文件。

## 2026-05-23 OCR 任务编排模块化
- 本轮目标：
  - 继续拆 `Fengxi_Toolbox.py` 补丁层，把 PDF OCR 的任务编排从 UI/历史/结果模型 adapter 中分离。
  - 保持 OCR 引擎、多后端、图像增强、对比报告、单文件/拖拽路径和结果模型行为不变。
- 关键修复：
  - 新增 `tools/fx_pdf_ocr_task.py`，提供 `PdfOcrTaskOptions`、`PdfOcrTaskCallbacks`、`build_pdf_ocr_output_path(...)`、`build_pdf_ocr_compare_report_path(...)`、`run_pdf_ocr_task_core(...)`。
  - `Fengxi_Toolbox.py` 的 `_run_pdf_ocr_task(...)` 改为任务 adapter，只负责读取 UI 参数、连接 progress tracker、写失败报告和结构化 task_result。
  - `tools/fx_pdf_ocr.py` 引擎内部未重构，继续保留多后端、预处理、质量回退和对比报告内容生成。
- 新增回归：
  - `pdf_ocr_task_module_exports`
- 关键既有回归继续通过：
  - `pdf_ocr_searchable`
  - `pdf_ocr_compare_report`
  - `single_file_input_pdf_ocr`
  - `drag_drop_single_file_pdf_ocr`
  - `pdf_ocr_backend_runtime_probe`
  - `pdf_ocr_preprocess_candidates`
  - `pdf_ocr_auto_quality_fallback`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_pdf_ocr_task.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：134/134 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未改 OCR 引擎后端算法。
  - 未触碰稳定区批量压缩和添加水印核心业务。
  - 未删除项目外文件。

## 2026-05-23 PDF 压缩核心模块化
- 本轮目标：
  - 继续拆 `Fengxi_Toolbox.py` 补丁层，把 PDF 压缩算法从 UI/任务编排中分离。
  - 保持现有 PDF 压缩入口、输出命名、并行执行、进度、结果模型和测试兼容。
- 关键修复：
  - 新增 `tools/fx_pdf_compress_core.py`，承接 PDF 压缩档位、图片压缩档位、图片重压缩/降采样、输出路径生成和单文件压缩。
  - `Fengxi_Toolbox.py` 改为从新模块导入 `PDF_COMPRESS_LEVELS`、`PDF_IMAGE_COMPRESS_LEVELS`、`build_pdf_compress_output_path(...)` 和 `compress_pdf_file(...)`。
  - 主加载器保留 `_build_pdf_compress_output_path(...)` 与 `compress_pdf_file(...)` 薄包装，确保旧 smoke/full debug 调用不变。
  - `_run_pdf_compress_task(...)` 仍在加载器层，继续负责 app 状态、进度 tracker、并行、失败报告、删除源文件和 task_result。
- 新增回归：
  - `pdf_compress_core_module_exports`
  - `pdf_compress_core_helper`
- 关键既有回归继续通过：
  - `pdf_compress_helper`
  - `single_file_input_pdf_compress`
  - `single_file_input_pdf_compress_result_model`
  - `pdf_compress_parallel_executor`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_pdf_compress_core.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：133/133 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未触碰批量压缩和添加水印用户可见行为。
  - 未删除项目外文件。

## 2026-05-23 稳定核心模块化例外
- 本轮目标：
  - 在用户明确授权下，把稳定区 `添加水印` 与 `批量压缩` 的核心实现拆成独立模块，提高 locality 和独立测试能力。
  - 保持现有 UI、输出、队列、历史、进度和旧 runtime 调用入口兼容。
- 关键修复：
  - 新增 `tools/fx_watermark_core.py`，承接 `create_watermark_packet(...)`、`add_watermark_to_pdf(...)`、`add_watermark_to_word(...)`。
  - `Fengxi_Toolbox.py` 保留水印同名薄包装，把字体解析、Word 兼容字体和 `_DisableWin32ComGenCache()` 作为 adapter 注入核心模块，并回写 `_ns` 兼容旧调用。
  - 新增 `tools/fx_zip_core.py`，承接 `plan_zip_archives(...)`、`estimate_zip_progress_units(...)`、`run_zip_task(...)`。
  - `Fengxi_Toolbox.py` 新增 `_run_zip_task_with_core(...)` 和 `_patch_zip_core_task()`，让 `zip` 任务走新模块，同时继续写入现有结构化任务结果和进度状态。
- 新增回归：
  - `watermark_core_module_exports`
  - `zip_core_module_semantics`
- 关键既有回归继续通过：
  - `pdf_watermark`
  - `word_watermark`
  - `zip_total`
  - `zip_recursive`
  - `zip_smart_recursive`
  - `single_file_input_zip_total`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_watermark_core.py tools\fx_zip_core.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：131/131 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未删除项目外文件。
  - 本轮是用户授权的稳定区模块化例外；后续默认仍不要随意修改 `批量压缩` 与 `添加水印` 的用户可见行为。

## 2026-05-23 启动性能 profiling 与补丁模块拆分一期
- 本轮目标：
  - 建立启动耗时、切换功能耗时、首次加载耗时的常态化记录。
  - 在有性能基线后，先做一层小而安全的补丁模块拆分。
- 关键修复：
  - 新增 `tools/fx_performance.py`，提供 `FxPerformanceRecorder` 和 `load_performance_entries(...)`。
  - `Fengxi_Toolbox.py` 接入 `_record_performance(...)`，记录 `runtime_load`、`main_create_app`、`main_icon_apply`、`main_release_identity`、`main_layout_tighten`、`startup_show_ready`、`startup_total`、`lazy_tab_init`、`switch_tab`。
  - 性能日志写入用户偏好目录 `performance.jsonl`，自动裁剪，避免污染项目源码与仓库。
  - 诊断包环境信息新增 `performance.recent`，方便后续定位启动或切页变慢的阶段。
  - 新增 `tools/fx_runtime_patches.py`，把通用 `wrap_callable(...)` 从主加载器中抽出，形成补丁层模块化的第一条 seam。
- 新增回归：
  - `performance_log_path_under_user_prefs`
  - `performance_record_helper_jsonl`
  - `performance_recorder_prune`
  - `runtime_patch_wrap_callable_module`
  - `task_history_diagnostic_export_package` 扩展验证性能样本结构。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_performance.py tools\fx_runtime_patches.py` 通过。
  - `python -c "import importlib.util; ... exec_module(...)"` 真实导入探针通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：126/126 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未动 `批量压缩` 与 `添加水印` 的核心处理逻辑。
  - 未删除项目外文件。
- 后续补丁模块拆分：
  - 新增 `tools/fx_startup_patches.py`，通过 `StartupPatchContext` + `install_startup_performance_patch(...)` 承接启动补丁 implementation。
  - `Fengxi_Toolbox.py` 的 `_patch_startup_performance()` 缩减为 context 装配函数，主加载器不再直接保存整段启动补丁闭包实现。
  - 新增回归 `startup_patch_installer_module`，用 fake CTK/App 验证隐藏启动、懒加载 deferral、切页刷新、性能记录、help/donate 内联重定向和二次安装幂等。
  - 追加验证：`python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_performance.py tools\fx_runtime_patches.py tools\fx_startup_patches.py` 通过；真实导入探针通过；`python smoke_test.py` 14/14；`python full_debug_test.py` 127/127。
- 任务历史导出/诊断包模块拆分：
  - 新增 `tools/fx_task_history_exports.py`，通过 `TaskHistoryExportContext` 承接任务历史结果导出、日志导出、报告导出、诊断包组装、脱敏和最近历史快照。
  - `Fengxi_Toolbox.py` 保留原函数名作为薄包装，详情窗口按钮与旧测试入口继续按原方式调用。
  - 环境探测仍留在主加载器，避免把 ffmpeg/OCR/Office COM/性能日志依赖塞进纯导出模块。
  - 新增回归 `task_history_exports_module_context`，直接构造模块 context 验证报告文本和导出文件名。
  - 追加验证：`python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py tools\fx_task_history_exports.py tools\fx_performance.py tools\fx_runtime_patches.py tools\fx_startup_patches.py` 通过；真实导入探针通过；`python smoke_test.py` 14/14；`python full_debug_test.py` 128/128。
- 队列历史纯逻辑模块拆分：
  - 新增 `tools/fx_queue_history.py`，通过 `QueueHistoryContext` 承接队列历史读写、过期清理、最大条数裁剪、运行态字段清理、状态文案、搜索 blob 和筛选逻辑。
  - `Fengxi_Toolbox.py` 保留原函数名作为薄包装，队列 UI、历史窗口、失败重试和诊断包加载最近历史仍按原入口调用。
  - 新增回归 `queue_history_module_context`，直接构造模块 context 验证模块级读写裁剪、搜索和失败分类筛选。
  - 追加验证：`python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_queue_history.py` 通过；真实导入探针通过；`python smoke_test.py` 14/14；`python full_debug_test.py` 129/129。

## 2026-05-23 功能注册表一期
- 本轮目标：
  - 建立功能注册表，把功能名、输入能力、输出策略、并行策略、开始前预览模式、风险标记和稳定区标记统一收口，减少历史、队列、进度、失败重试各写一套规则的分裂。
- 关键修复：
  - `Fengxi_Toolbox.py` 新增 `FEATURE_REGISTRY`，覆盖 `watermark`、`remove_wm`、`convert`、`audio`、`zip`、`pdf`、`image`、`meta`、`file`。
  - `QUEUE_TASK_LABELS`、输出策略支持集合、并行安全集合、强制单线程详情、并行提示文案均改为从注册表派生。
  - 开始前任务预览、输出策略判断、并行提示、历史记录功能名展示统一改用注册表 helper。
  - 删除被注册表覆盖的旧硬编码策略集合，避免未来维护时出现双来源。
  - OCR 回归测试补充状态隔离：OCR 工作流测试显式关闭方向纠正，避免继承上一个“上次设置记忆”用例造成 RapidOCR 分类模型在线下载波动。
  - OCR 对比报告生成失败改为警告并跳过，不再阻断主 OCR PDF 生成；主 OCR 失败仍按原失败结果处理。
- 新增回归：
  - `feature_registry_core_tasks`
  - `feature_registry_derived_policy_sets`
  - `feature_registry_preview_labels`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：122/122 通过。
- 诊断记录：
  - 首次全量回归时 `pdf_ocr_searchable` 与 `pdf_ocr_compare_report` 曾因 RapidOCR 方向分类模型从 `modelscope.cn` 下载失败而红灯。
  - 根因不是功能注册表，而是测试状态继承让 OCR 用例打开了方向纠正；隔离后回归恢复通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未动 `批量压缩` 与 `添加水印` 的核心处理逻辑。

## 2026-05-23 一键诊断包
- 本轮目标：
  - 在已有任务结果、历史记录、日志导出、报告导出的基础上，新增一键诊断包，便于后续排查失败任务，不再每次从头猜环境和日志。
- 关键修复：
  - 任务历史详情窗口新增 `诊断包` 按钮。
  - 新增 zip 诊断包导出链路，包内包含 `README.md`、`task_history_entry.json`、`task_result.json`、`task_report.md`、`task_log.txt`、`environment.json`、`recent_history.json`。
  - 诊断包复用现有任务报告和日志导出口径，避免失败原因与历史详情口径分裂。
  - 新增环境探测：软件版本、系统/Python、ffmpeg、OCR 后端状态、Word/PowerPoint COM 可用性。
  - 诊断包内容做基础路径脱敏：项目目录替换为 `<PROJECT_ROOT>`，用户主目录替换为 `<USER_HOME>`。
  - 诊断包不复制原始输入文件，只包含文本、JSON、Markdown 信息，降低隐私和体积风险。
- 新增回归：
  - `task_history_diagnostic_filename`
  - `task_history_diagnostic_export_package`
  - `task_history_diagnostic_export_empty`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：119/119 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未动 `批量压缩` 与 `添加水印` 的核心处理逻辑。

## 2026-05-22 使用教程内嵌示例流程
- 本轮目标：
  - 继续完成上一轮产品体验清单里的“帮助页按功能内嵌示例流程”，让用户不用读外部 README，也能在应用内按功能理解怎么操作、输出到哪里、失败后怎么排查。
- 关键修复：
  - `Fengxi_Toolbox.py` 的 `INLINE_HELP_SECTIONS` 重写为按任务场景组织的 13 个章节。
  - 新帮助页覆盖三步上手、输出与安全确认、任务队列与历史记录、PDF OCR、PDF 压缩/合并/拆分/加密、批量水印、去除水印、图片工厂、格式转换/音频、属性隐私/文件管家、批量压缩、性能进度排障、重要约束。
  - OCR 说明同步最新能力：`auto` 后端、`auto/off/light/scan` 图像增强、质量回退、透明文字层、对比报告和常见失败原因。
  - 队列历史说明同步最新能力：筛选、失败重试、成功回放、打开输出位置、导出结果/日志/报告、过期历史自动清理。
  - 输出策略说明同步最新能力：原目录新文件、覆盖原文件、【处理完成】结果文件夹，以及删除源文件/覆盖/去重风险提示。
- 新增回归：
  - `inline_help_workflow_sections`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：116/116 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未动 `批量压缩` 与 `添加水印` 的核心处理逻辑。

## 2026-05-22 开始前任务预览确认
- 本轮目标：
  - 批处理前增加“本次将处理 N 个文件”的预览确认，尤其让覆盖原文件、删除源文件、去重等高风险选项在执行前被看见。
- 关键修复：
  - `Fengxi_Toolbox.py` 新增 `_build_start_preview(...)`、`_format_start_preview_message(...)`、`_confirm_start_preview(...)` 和 `_patch_start_preview_confirmation()`。
  - 人工点击开始前会弹出任务预览确认框，显示功能、模式、输入类型、处理数量、跳过数量、输出策略和风险提示。
  - 队列执行期间通过 `_fx_start_via_queue` 跳过弹窗，避免任务队列被确认框阻塞。
  - 水印预览会估算文件名规则跳过数量，但不改水印运行时业务逻辑。
- 新增回归：
  - `start_preview_counts_and_risks`
  - `start_preview_confirmation_cancel`
  - `start_preview_skips_queue_worker`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：115/115 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未动 `批量压缩` 与 `添加水印` 的核心处理逻辑。

## 2026-05-22 OCR 图像增强与质量回退
- 本轮目标：
  - 继续完成 OCR 部分，让 OCR 搜索版 PDF 不只支持多后端切换，还能对低质量扫描件做预处理，并在识别质量不佳时自动尝试备用后端。
- 关键修复：
  - `tools/fx_pdf_ocr.py` 新增 OCR 图像增强策略：`auto`、`off`、`light`、`scan`。
  - 新增灰度增强、自动对比度、锐化、轻度纠偏、扫描件黑白化候选生成。
  - 新增 `score_ocr_rows()` 质量评分，用识别置信度、有效字符数和识别块数综合判断结果。
  - `FengxiPdfOcrEngine` 的 `auto` 后端现在会在质量不足时继续尝试备用后端，不再只按“第一个可导入后端”固定运行。
  - OCR 对比报告增加图像增强模式、每个后端质量评分和采用的增强候选。
  - PDF OCR 页面新增“图像增强”下拉框，并纳入上次设置自动保存/恢复。
- 新增回归：
  - `pdf_ocr_preprocess_candidates`
  - `pdf_ocr_auto_quality_fallback`
  - `last_settings_ocr_save_restore` 扩展覆盖 `pdf_ocr_preprocess`
- 验证结果：
  - `python -m py_compile tools\fx_pdf_ocr.py Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：112/112 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未动 `批量压缩` 与 `添加水印` 的核心处理逻辑。

## 2026-05-22 赞助作者内联页回归
- 本轮目标：
  - 用户要求 `赞助作者` 不再弹窗，直接显示在右侧内容区，并补一句希望赞助的话。
- 关键修复：
  - 新增 `DONATE_TAB_TITLE`、`DONATE_SUPPORT_SENTENCE` 和右侧内联赞助页构建函数。
  - 侧栏 `btn_donate` 重新绑定到 `_show_inline_donate(...)`。
  - 旧入口 `FengxiToolboxApp.show_donate_window` 也补丁为内联页，避免其他调用路径重新打开弹窗。
  - 页面直接读取 `assets/donate_qr.png` 显示赞助二维码；缺失时显示替代说明。
  - 赞助页期间禁用开始按钮并显示“查看赞助作者中”，`on_start_click` 对 `help` / `donate` 都只提示切回功能页。
- 新增回归：
  - `inline_donate_page_no_popup`
  - `inline_donate_sidebar_button`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：108/108 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未动 `批量压缩` 与 `添加水印` 的核心处理逻辑。

## 2026-05-22 批量并行提速说明回归
- 本轮目标：
  - 回答“极速模式/多线程是否有用，是否应该清除”，并让软件界面真实展示哪些功能支持提速。
- 关键结论：
  - 不建议删除底层多线程能力；它对多文件、逐文件、彼此独立的任务仍有价值。
  - 原“极速模式（多线程）”文案容易误导，已改为 `批量并行（部分生效）`。
  - 新增当前功能提示，说明本页是“可提速”还是“稳定单线程”。
- 当前可提速范围：
  - 批量水印：多文件可并行，遇到 Word/PDF 特殊链路时自动保护。
  - PDF 拆分/加密/压缩：多文件可并行；合并、OCR 不并行。
  - 图片格式转换/压缩/逐张转 PDF：多文件可并行；多图合并 PDF 不并行。
  - 音视频逐文件转换：可并行，但实际速度受 ffmpeg 与磁盘吞吐限制。
  - 文件重命名：可并行；文件去重不并行。
  - 普通文件时间修改：可并行；Office 元数据修改不并行。
- 当前稳定单线程范围：
  - 去水印、Office/PDF 转换、批量压缩、PDF 合并、PDF OCR、多图合并 PDF、文件去重。
- 新增回归：
  - `parallel_mode_label_truthful`
  - `parallel_mode_forced_single_hints`
  - `parallel_mode_pdf_compress_available`
  - `parallel_mode_image_to_pdf_available`
  - `pdf_compress_parallel_executor`
  - `image_to_pdf_parallel_executor`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：106/106 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未动 `批量压缩` 与 `添加水印` 的核心处理逻辑。
  - 本轮只给安全的独立文件工作流接入并行：`PDF 压缩`、`图片转 PDF（逐张生成）`。

## 2026-05-22 上次设置自动记忆回归
- 本轮目标：
  - 按用户要求取消独立“预设中心”，改为各功能自动保存/恢复上一次使用的参数。
- 关键修复：
  - 移除用户可见的预设中心入口和窗口函数，不再显示底部或侧栏预设按钮。
  - `Fengxi_Toolbox.py` 新增 `last_settings` 保存/恢复链路，复用参数捕获与应用能力。
  - 启动默认页、懒加载页面、开始执行前、快速关闭前都会保存或恢复当前已初始化功能的最后设置。
  - PDF 页继续通过 `app._fx_select_pdf_mode` 同步恢复 OCR/PDF 压缩右侧具体功能面板。
  - 上次设置数据保存在用户偏好 JSON 的 `last_settings` / `last_settings_active` 字段。
  - 水印上次设置只保存/恢复 UI 与偏好参数，没有修改加水印核心业务逻辑。
- 新增回归：
  - `last_settings_no_dedicated_preset_center`
  - `last_settings_watermark_save_restore`
  - `last_settings_ocr_save_restore`
  - `last_settings_pdf_compress_save_restore`
  - `last_settings_rename_save_restore`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：100/100 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未动 `批量压缩` 与 `添加水印` 的核心处理逻辑。

## 2026-05-21 任务历史报告导出
- 本轮目标：
  - 把任务历史从“能看结果、能导 JSON、能导日志”推进到“能导出完整任务报告”。
- 关键修复：
  - `Fengxi_Toolbox.py` 新增 `_build_task_history_report_text(...)`，统一输出 Markdown 报告。
  - 新增 `_build_task_history_report_export_filename(...)`、`_export_task_history_report(...)`、`_prompt_export_task_history_report(...)`。
  - 任务历史详情窗口新增 `导出报告` 按钮，与 `导出结果 / 打开位置 / 导出日志 / 复制详情` 并列。
  - 报告内容已统一收口到结构化结果模型、失败分类和关键日志摘要，不再单独发明另一套语义。
- 新增回归：
  - `task_history_report_export_filename`
  - `task_history_report_export_result`
  - `task_history_report_export_empty`
  - `task_history_failed_report_sections`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：87/87 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未动 `批量压缩` 与 `添加水印` 的核心处理逻辑。

## 2026-05-21 子窗口图标与失败原因筛选
- 本轮目标：
  - 让子页面窗口也统一使用风兮自己的应用图标。
  - 把上一步未完成的“失败原因筛选”正式接入任务历史窗口。
- 关键修复：
  - `Fengxi_Toolbox.py` 新增 `_apply_window_icon(...)`，统一给子窗口应用 `assets/fengxi_app_icon.ico/png`。
  - 统一文件/文件夹选择器、任务历史详情窗口、任务队列与历史窗口都改为使用风兮图标。
  - 历史筛选新增失败类别维度：路径缺失、权限问题、超时、依赖问题、部分失败、日志失败、普通失败、未知失败。
  - `_filter_queue_history_entries(...)`、`_get_queue_history_filters(...)`、`_get_filtered_queue_history(...)`、重置逻辑与 UI 状态变量均已接入失败筛选。
  - `full_debug_test.py` 新增 `task_history_failure_filter_path_missing` 与 `task_history_failure_filter_state_vars` 回归。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：83/83 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未动 `批量压缩` 与 `添加水印` 的核心处理逻辑。

## 2026-05-21 任务历史失败分类预览
- 本轮目标：
  - 在失败详情分组之后，再把失败原因做一层轻量分类，让历史列表能先看出是路径、权限、超时、依赖还是普通失败。
- 关键修复：
  - `Fengxi_Toolbox.py` 新增 `_classify_failure_reason(...)`，对失败记录做轻量分类预览。
  - 历史搜索 blob 现在会带上失败类别和失败原因，方便按关键字直接检索。
  - 历史列表详情行会显示失败分类提示，帮助快速判断问题类型。
  - `full_debug_test.py` 新增 `task_history_failure_reason_classification` 与 `task_history_failure_reason_search_blob` 回归。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：81/81 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未动 `批量压缩` 与 `添加水印` 的核心处理逻辑。

## 2026-05-21 任务历史失败详情归类
- 本轮目标：
  - 让任务历史详情对失败记录更直观，分出失败概览、失败原因、失败项和关键日志，并在详情框内高亮失败相关文本。
- 关键修复：
  - `Fengxi_Toolbox.py` 的 `_build_task_history_detail_text(...)` 新增失败概览分组，单独展示失败原因、失败项数量与关键失败日志。
  - 新增 `_apply_task_history_detail_highlights(...)`，为历史详情文本框中的失败标题、错误行、失败项和错误日志添加标签高亮。
  - `_show_task_history_detail(...)` 在写入详情文本后立即应用高亮标签。
  - `full_debug_test.py` 新增 `task_history_failed_detail_groups` 与 `task_history_failed_detail_highlight_tags` 回归。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：79/79 通过。
- 改动边界：
  - 未改 `fengxi_runtime.bin`。
  - 未动 `批量压缩` 与 `添加水印` 的核心处理逻辑。

## 2026-05-21 统一任务结果模型回归
- 本轮目标：
  - 统一任务执行后的结构化结果口径，不再让队列历史主要依赖日志关键词猜成功/失败。
- 关键修复：
  - `Fengxi_Toolbox.py` 新增统一 `task_result` 结构，并挂载到 `app._fx_last_task_result`。
  - `run_process()` 最外层补丁会在任务开始时创建结果对象，在任务结束时统一补齐状态、耗时和错误信息。
  - 自定义工作流已接入结构化结果写入：
    - `remove_wm`
    - `pdf -> ocr`
    - `pdf -> compress`
    - `image -> to_pdf / merge_pdf`
    - 单文件 `zip` 包装路径
  - 队列 worker 与历史记录现在优先消费 `task_result`，日志关键词退为兜底。
  - 历史记录保存裁剪后的 `task_result` 快照，新增结果导出辅助函数 `_export_task_result(...)`。
- 新增回归：
  - `task_queue_structured_result`
  - `single_file_input_pdf_compress_result_model`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py tools\fx_pdf_ocr.py tools\fx_workspace_tools.py tools\generate_fengxi_icon.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：61/61 通过。
- 改动边界：
  - 本轮仍不修改 `fengxi_runtime.bin`。
  - `批量压缩` 与 `添加水印` 核心业务逻辑未改。

## 2026-05-20 批量水印文件名规则 UI 与记忆回归
- 本轮目标：
  - 修复 `按文件名规则跳过` 行里的 `留空默认` 提示显示不全。
  - 让该处设置具备本地记忆功能。
- 关键修复：
  - 文件名规则控件改为两行布局，并在水印页布局收紧时保留 56px 高度，避免提示再次被裁切。
  - 新增 `watermark.filename_skip_rule` 用户偏好，保存 `enabled`、`position`、`marker`。
  - 保存时机覆盖变量变更防抖、失焦/回车、执行前和关闭前。
  - 水印执行中临时关闭旧固定跳过开关时，会屏蔽偏好写入，避免把内部状态误保存为用户设置。
- 新增回归：
  - `watermark_filename_rule_memory_save`
  - `watermark_filename_rule_memory_load`
  - `watermark_filename_rule_hint_layout`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py tools\fx_pdf_ocr.py tools\fx_workspace_tools.py tools\generate_fengxi_icon.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：59/59 通过。
- 改动边界：
  - 本轮只改加载器 UI/偏好层和测试记忆，不改 `fengxi_runtime.bin`。
  - 未改 `批量压缩` / `添加水印` 核心业务逻辑。

## 2026-05-20 任务队列功能回归
- 本轮新增“任务队列 + 历史记录 + 失败重试”：
  - 底部操作区新增 `加入队列` 与 `队列历史`。
  - 队列窗口左侧显示等待执行，右侧显示历史与失败重试。
  - 队列任务保存输入路径、任务类型和参数快照，执行前自动恢复快照。
  - 历史持久化到用户配置目录的 `queue_history.json`。
- 新增回归：
  - `task_queue_snapshot`：验证 PDF 加密模式、密码框和底部队列按钮均能正确快照。
  - `task_queue_success_history`：验证队列 worker 执行后写入成功历史，并恢复快照参数。
  - `task_queue_retry_failed`：验证失败历史能重新加入队列。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py tools\fx_pdf_ocr.py tools\fx_workspace_tools.py tools\generate_fengxi_icon.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：56/56 通过。
  - `cmd /c "set FX_NO_PAUSE=1 && package.bat"` 通过。
  - `dist_release_ascii\fx_toolbox\fx_toolbox.exe` 已生成并打开。
  - 打包产物 `_internal` 未发现 OCR/onnxruntime 冲突 DLL。
- 注意：
  - 队列当前是顺序执行，不做并发。
  - 失败判定目前是日志关键词 + 异常 + stop_event 的实用版，后续可升级为结构化结果。
  - 本轮未改 `批量压缩` / `添加水印` 业务逻辑。

## 2026-05-20 全面自检与工程可靠性回归
- 本轮目标：全面检查项目代码/文件、优化工程架构、debug，并保持稳定区安全。
- 关键修复：
  - 修复 `full_debug_test.py` 中快关探针可能触发真实 `os._exit(0)` 的问题，避免全量测试 0 退出但没有最终 JSON 输出。
  - `smoke_test.py` / `full_debug_test.py` 成功时自动清理本轮新建的项目内 `tmp_*` 测试目录，防止后续 debug 继续制造垃圾目录。
  - JSON 测试记录改为 `flush=True`，长流程时能稳定看到逐项进度。
  - GitHub Release zip 上传改为 `curl.exe --data-binary` 并检查 HTTP 状态码，提升大文件资产上传可靠性。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py tools\fx_pdf_ocr.py tools\fx_workspace_tools.py tools\generate_fengxi_icon.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：53/53 通过。
  - `cmd /c "set FX_NO_PAUSE=1 && package.bat"` 通过，生成 `dist_release_ascii\fx_toolbox\fx_toolbox.exe`。
  - 打包产物 `_internal` 中未发现会和 OCR/onnxruntime 冲突的 `msvcp140*.dll`、`vcruntime140*.dll`、`ucrtbase.dll`、`api-ms-win-crt-*.dll`。
  - 敏感信息扫描仅命中测试里的假文本 `secret`，未发现 token/真实密钥。
- 注意：
  - 本轮没有删除历史 `tmp_*` 目录，只阻止新测试继续留下成功样本。
  - 旧版 `风兮文件批量处理工具箱2.0.spec`、`package_legacy_backup.bat`、`fx_toolbox_diag.spec` 仍是可清理/归档候选，但本轮未删除。
  - `批量压缩` 与 `添加水印` 业务逻辑未改。

## 2026-04-26 侧栏创建阶段加速回归
- 用户继续反馈：打开软件和切功能时仍希望更快。
- 新定位：
  - 上一轮已证明懒加载页切换后的重复布局不再是主热点
  - 剩余主要热点仍在 `setup_sidebar` 与默认 `watermark` 页创建
- 这轮修复：
  - 在 `setup_sidebar()` 执行期间，临时把侧栏按钮改成轻量占位文本/字体
  - 在窗口显示前再通过 `_tighten_layout(...)` 恢复正式图标和文案
- 结果：
  - 真实启动测量约 `3.7786s -> 3.0694s`
  - cProfile 中 `setup_sidebar` 约 `1.505s -> 0.183s`
  - 侧栏按钮最终状态已校验：`btn_nav_wm`、`btn_nav_pdf`、`btn_help_proxy`、`btn_donate` 均恢复正常文本且带图标
- 回归结果：
  - `python -m py_compile Fengxi_Toolbox.py` 通过
  - `python smoke_test.py` 12/12 通过
  - `python full_debug_test.py` 47/47 通过

## 2026-04-25 启动/切页性能复测
- 用户反馈：软件“打开时”和“第一次切换功能页时”仍有明显迟滞。
- 这轮修复：
  - 将 `Fengxi_Toolbox.py` 的 `_tighten_layout(...)` 拆分为“外框一次性样式”与“目标页局部布局收紧”
  - 懒加载页初始化后不再重复重排整套侧栏与底部区域
- 同口径基准结论：
  - 冷启动整体时间基本持平，约 `4.41s`
  - 首次切页明显改善，尤其是 `remove_wm`、`meta`、`file`
  - 说明当前剩余启动热点主要不在懒加载补丁，而在 `setup_sidebar` 与默认 `watermark` 页创建
- 回归结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
  - `python smoke_test.py` 12/12 通过
  - `python full_debug_test.py` 47/47 通过

## 2026-04-25 进度条统一回归
- 用户反馈：几乎所有功能的进度条都存在“不准确、提前跳格”的问题。
- 根因定位：
  - 嵌入式原始 `run_process()` 的多个分支在真正处理文件之前就执行了 `progress_bar.set((i + 1) / total)`
  - 自定义工作流 `_run_remove_wm_pdf_roundtrip()` 与 `_run_pdf_ocr_task()` 也复用了同样的“开工先加进度”写法
  - OCR 底层其实已有页级回调，但此前没有接回 UI
- 本轮修复：
  - `Fengxi_Toolbox.py` 新增统一进度跟踪补丁 `_patch_runtime_progress_reporting()`
  - OCR 改为页级总进度
  - PDF 去水印改为文件完成后推进
  - `full_debug_test.py` 新增 3 条进度相关回归
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
  - `python smoke_test.py` 12/12 通过
  - `python full_debug_test.py` 47/47 通过

## 2026-04-20 当前环境
- 操作系统：Windows
- Office COM：
  - Word.Application 16.0 可用
  - PowerPoint.Application 16.0 可用
- `moviepy/ffmpeg`：可用
- 字体扫描：`SmileySans-Oblique`

## 已验证
- `smoke_test.py` 12 项通过：
  - PDF 水印
  - 多图转 PDF
  - 修改时间
  - PDF 拆分
  - PDF 加密
  - 图片转码
  - 图片压缩
  - 重命名 add
  - meta time
  - PDF 转 Word
  - 视频提取音频
  - 音频格式互转
- 手工增强验证通过：
  - App 初始化
  - Word -> PDF
  - PPT -> PDF
  - Word 水印
  - Word 去水印
  - Word 元数据修改
  - PDF 去水印工作流
  - 图片集合并 PDF 工作流
  - 压缩三模式
  - 文件重命名 replace / cut
  - PDF OCR 搜索版工作流

## 本次发现并修复
- `PDF 合并`：源码工作流会误走多线程单文件路径，导致输出失败清单。已修复为强制进入单线程专用分支。
- `文件去重`：源码工作流会误走多线程普通文件路径，导致不执行真正的 MD5 去重。已修复为强制进入单线程专用分支。

## 后续验证入口
- 快速：`python smoke_test.py`
- 全量：`python full_debug_test.py`

## 2026-04-20 OCR 增量结果
- 新增 `PDF 工具 -> OCR 搜索版 PDF`。
- 回归结果：
  - `full_debug_test.py` 现为 35 项通过。
  - 新增用例：`pdf_ocr_searchable`
  - 新增用例：`pdf_ocr_compare_report`
  - 新增用例：`pdf_ocr_brand_independent`
  - 新增用例：`pdf_ocr_multi_backend_ui`
  - 新增用例：`pdf_ocr_backend_status_panel`
- 当前 OCR 依赖：
  - `RapidOCR`
  - `onnxruntime`
  - `PyMuPDF`
  - 风兮模型目录：`FX_OCR_MODEL_ROOT` 或 `%LOCALAPPDATA%\FengxiToolbox\ocr_models\rapidocr`
- 当前 OCR 架构：
  - 默认后端：`RapidOCR`
  - 可选后端：`PaddleOCR` / `EasyOCR` / `Tesseract CLI`
  - 运行时支持手动切换或 `auto` 自动选择
  - UI 已显示后端探测状态，并支持手动刷新
  - 勾选后可额外生成首页多后端对比 Markdown 报告

## 2026-04-21 UI 布局回归
- 调整范围：
  - 左侧功能区压紧间距，赞助按钮与底部信息重新进入稳定可见范围
  - PDF 页 OCR 改为左侧 PDF 基础选项 + 右侧紧凑 OCR 配置卡片的双栏布局
- 改动边界：
  - 仅修改 `Fengxi_Toolbox.py` 加载器层布局补丁
  - 未改动批量压缩与添加水印业务逻辑
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过
  - `python full_debug_test.py` 35 项通过，`failed: []`
  - 实机截图确认左侧赞助按钮可见，OCR 右栏中的模式、后端、识别配置、方向纠正、对比报告与说明均进入可见区

## 2026-04-21 启动性能回归
- 问题定位：
  - 运行时原本会在 `setup_main_area()` 启动阶段一次性初始化全部功能页
  - 打包配置原本等价于 `onefile`，会带来额外解包延迟
- 已做修改：
  - `Fengxi_Toolbox.py` 新增延迟建页补丁，只初始化默认首屏 `watermark`
  - 页面切换与变量访问会自动触发所属页面补建，兼容既有工作流与测试
  - 主窗口启动阶段先隐藏，布局收束后再显示，减少多界面闪屏
  - `fx_toolbox.spec` 改为 `onedir` 目录式输出，并关闭 `upx`
- 量化结果：
  - 源码态测得 `import` 约 `1.52s`
  - `FengxiToolboxApp()` 初始化约 `3.47s`
  - 启动到窗口可见约 `4.29s`
  - 打包版 `dist_release_ascii\fx_toolbox\fx_toolbox.exe` 两次实测窗口可见约 `5.82s`、`5.40s`
- 回归结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过
  - `python smoke_test.py` 12 项通过
  - `python full_debug_test.py` 35 项通过，`failed: []`
- 改动边界：
  - 未改动批量压缩与添加水印业务逻辑

## 2026-04-22 左侧导航统一化
- 问题表现：
  - 左侧导航虽然间距已压紧，但图标直接写在按钮文本里，受不同符号字宽影响，视觉起始线不一致
  - 教程、赞助与导航主按钮的内部节奏也不够统一
- 已做修改：
  - `Fengxi_Toolbox.py` 改为为左侧按钮生成固定尺寸的图标图片，再配合独立文本标签显示
  - 主导航、使用教程、赞助作者统一为同一高度、同一 `border_spacing`、同一字号
  - 不再依赖 emoji 字符本身的字宽做视觉对齐
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py` 通过
  - `python full_debug_test.py` 35 项通过，`failed: []`
  - 样式检查确认 `btn_nav_wm`、`btn_nav_pdf`、`btn_help_proxy`、`btn_donate` 均已带固定图标图片并统一为 `height=40`
- 改动边界：
  - 仅修改 `Fengxi_Toolbox.py` 的侧边栏样式补丁和打包产物
  - 未改动批量压缩与添加水印业务逻辑

## 2026-04-22 图标恢复
- 用户反馈：
  - 字母缩写图标槽虽然整齐，但“图标没了”
- 已做修正：
  - 将字母缩写图标槽替换为加载器层动态绘制的 11 个线稿小图标：
    - shield / eraser / swap / music / box / document / image / lock / folder / book / coffee
  - 保留统一对齐的固定图标槽与按钮节奏，不回退到 emoji 文本前缀
- 验证结果：
  - 本地图标唯一性校验为 11/11 唯一图形
  - `python -m py_compile Fengxi_Toolbox.py` 通过
  - `python full_debug_test.py` 35 项通过，`failed: []`
  - 已重打包 `dist_release_ascii\fx_toolbox\fx_toolbox.exe`

## 2026-04-22 底部卡片与应用图标回归
- 用户反馈：
  - 左侧最下面的 `使用教程` 和 `赞助作者` 风格不一致，不够好看
  - 需要一个和“风兮”有关的新图标
- 已做修改：
  - `Fengxi_Toolbox.py` 新增 `_style_sidebar_aux_button(...)`，把 `使用教程` 与 `赞助作者` 收口为同一套卡片式按钮壳体
  - 两个按钮统一为 `corner_radius=14`、`height=40`、一致的图标槽与文字对齐，仅保留赞助按钮的暖色强调
  - 新增 `tools\\generate_fengxi_icon.py`，本地生成 `assets\\fengxi_app_icon.png` 与 `assets\\fengxi_app_icon.ico`
  - 源码态通过 `_apply_app_icon(app)` 设置窗口图标，打包态通过 `fx_toolbox.spec` 设置 exe 图标
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py tools\\generate_fengxi_icon.py full_debug_test.py` 通过
  - `python full_debug_test.py` 35 项通过，`failed: []`
  - `cmd /c "set FX_NO_PAUSE=1 && package.bat"` 通过，生成 `dist_release_ascii\\fx_toolbox\\fx_toolbox.exe`
- 改动边界：
  - 未改动批量压缩与添加水印业务逻辑

## 2026-04-22 去水印稳健性回归
- 新定位到的真实问题：
  - `remove_wm` 的真正处理逻辑只在 `run_process()` 的单线程 Word COM 分支里；普通 `process_single_file()` 路径对 PDF/Word 去水印仅复制原文件并记录跳过日志
  - `remove_watermark_from_word()` 原始实现会漏删 `页眉 Range.InlineShapes` 类型的图片水印，导致返回 `SUCCESS` 但文档里仍残留图片水印
- 已做修改：
  - `Fengxi_Toolbox.py` 的 `_patch_task_routing()` 现显式将 `remove_wm` 强制锁定到单线程专用分支
  - 新增 `_patch_remove_watermark_robustness()`，在原始去水印成功后再次打开输出文档，补扫并清理页眉 `InlineShapes`
  - `full_debug_test.py` 新增 `word_remove_wm_header_inline_image` 回归用例
- 复现样本：
  - 手工构造带 `header.Range.InlineShapes.AddPicture(...)` 的 Word 文档
  - 修复前：`remove_watermark_from_word()` 返回 `SUCCESS`，但 `InlineShapes.Count` 仍为 `1`
  - 修复后：`InlineShapes.Count == 0`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过
  - `python full_debug_test.py` 36 项通过，`failed: []`
  - `cmd /c "set FX_NO_PAUSE=1 && package.bat"` 通过，已更新 `dist_release_ascii\\fx_toolbox\\fx_toolbox.exe`
- 改动边界：
  - 未改动批量压缩与添加水印业务逻辑

## 2026-04-22 单文件输入支持回归
- 用户需求：
  - 不再只能选择文件夹；选择单个文件时也要能处理
- 已做修改：
  - `Fengxi_Toolbox.py` 新增 `_patch_single_input_support()`，统一接管浏览入口、启动入口、文件收集与运行入口
  - 浏览按钮现在支持选择“单个文件”或“文件夹”
  - 普通任务的单文件模式通过 `_fx_single_input_target` 只放行选中的那一个文件
  - 单文件任务会自动临时关闭多线程，避免 `process_single_file()` 在工作线程里写 UI 日志触发 `main thread is not in main loop`
  - 单文件 `zip` 走临时隔离目录包装，不直接改动稳定压缩主体逻辑
  - `full_debug_test.py` 新增：
    - `single_file_input_pdf_encrypt`
    - `single_file_input_zip_total`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过
  - `python full_debug_test.py` 38 项通过，`failed: []`
  - `cmd /c "set FX_NO_PAUSE=1 && package.bat"` 通过，已更新 `dist_release_ascii\\fx_toolbox\\fx_toolbox.exe`
- 改动边界：
  - 未改动批量压缩与添加水印业务逻辑
## 2026-04-22 去水印误删回归
- 问题定位：
- 运行时原始 `remove_watermark_from_word()` 会直接删页眉全部 `Shapes`。
- `is_pdf_source=True` 时还会额外删除文档级 `Shapes` 与页眉 `InlineShapes`。
- 这会造成正常页眉图片、页眉装饰形状，甚至部分 PDF 转 Word 后的正常内容被一起删掉。
- 已做修改：
- 加载层改为安全版 `_remove_watermark_from_word_safely(...)`。
- 删除规则从“整类全删”改成“逐对象水印特征判定”。
- 新增/更新回归：
- `word_remove_wm_header_inline_image`：大尺寸页眉图片水印应被删除。
- `word_remove_wm_preserve_header_assets`：正常页眉 logo、页眉文字与小型标题 shape 必须保留。
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
- `python full_debug_test.py` 39 项通过，`failed: []`。
## 2026-04-22 PDF 去水印回归
- 问题定位：
- Word 去水印修复后，`pdf_remove_wm_workflow` 仍失败。
- 进一步排查确认：PDF 转出的中间 DOCX 本身不含 `XMU TEST`，说明水印内容其实在 `PDF -> DOCX` 这一步就已经被抹掉。
- 失败根因是运行时原始 PDF 去水印链路不稳定，失败后回退成保留原 PDF，因此最终结果仍带水印。
- 已做修改：
- 新增加载层 `_patch_remove_wm_pdf_fallback()`。
- PDF 去水印改走 ASCII 临时目录 round-trip：`convert_pdf_to_word -> remove_watermark_from_word(is_pdf_source=True) -> convert_doc_to_pdf`。
- Word 去水印的保守删除修复保持不变。
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
- `python full_debug_test.py` 39 项通过，`failed: []`。
- 关键回归同时覆盖：
- `pdf_remove_wm_workflow`
- `word_remove_wm_header_inline_image`
- `word_remove_wm_preserve_header_assets`

## 2026-04-24 PDF 去水印批量稳定性回归
- 新定位到的问题：
- `pdf_remove_wm_workflow` 在某些轮次会重新失败，不是算法退化，而是 PDF 去水印链路里复用同一个 `Word.Application` 时，前一个文件的 COM 异常会污染后一个文件。
- 典型日志：
- `Open.Sections`
- `RPC 服务器不可用`
- 已做修改：
- `_create_hidden_word_app()` 改为 `DispatchEx("Word.Application")`
- `_run_remove_wm_pdf_roundtrip(...)` 改成“每个 PDF 独立 Word 会话”，且“去水印阶段”和“导出 PDF 阶段”各自独立
- 专项验证：
- 连续两份带 `XMU TEST` 水印的 PDF 连续处理均成功，输出文本均不再包含 `XMU TEST`
- 全量验证：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过
- `python full_debug_test.py` 39 项通过，`failed: []`
## 2026-04-22 浏览入口去掉类型弹窗
- 用户反馈：
- 点击“浏览文件/文件夹”后，不要再弹“请选择输入类型：单个文件 / 文件夹”的 yes/no/cancel 对话框。
- 已做修改：
- 新增 `_UnifiedInputPathPicker`，替换 `_choose_input_path_interactive()` 内的 `askyesnocancel + askopenfilename/askdirectory` 前置分流。
- 现在浏览入口会直接打开统一选择器，让用户直接点文件或文件夹。
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
- 代码检查已确认 `_choose_input_path_interactive()` 只再依赖 `_UnifiedInputPathPicker(...).show()`，不再调用 `askyesnocancel`。
- 当前额外说明：
- 本轮 `python full_debug_test.py` 未能完整通过，不是由浏览入口引起，而是当前环境里的 `Word COM` 会话异常，报“指定的登录会话不存在”，导致 `pdf_remove_wm_workflow` 无法完成。

## 2026-04-24 启动性能复测
- 本轮目标：
- 检查当前项目是否存在显著回归 bug，并继续优化源码态启动速度。
- 现状结论：
- 本轮未复现功能性回归；`smoke_test.py` 与 `full_debug_test.py` 均完整通过。
- 启动热点主要在两段：
- `fengxi_runtime.bin` 执行期导入 `pdf2docx` / `moviepy`
- `FengxiToolboxApp()` 首屏 GUI 构建
- 已做修改：
- `Fengxi_Toolbox.py` 在 `_load_runtime_namespace()` 前临时安装懒加载代理，仅延后 `pdf2docx` / `moviepy` / `moviepy.editor` 的真实导入时机。
- 真实首次用到这些能力时，仍会自动导入原模块，不影响 PDF 转 Word、OCR 搜索版 PDF、视频转音频等工作流。
- 量化结果：
- 代码载入：约 `1.743s -> 1.267s`
- 启动到窗口 ready：约 `4.923s -> 3.560s`
- 仅启动后半段：约 `3.158s -> 2.293s`
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
- `python smoke_test.py` 12 项通过，`failed: []`
- `python full_debug_test.py` 39 项通过，`failed: []`
- 改动边界：
- 未改动批量压缩与添加水印业务逻辑

## 2026-04-24 浏览入口原生化回归
- 用户反馈：
- 不要再弹自定义的大型“选择文件或文件夹”窗口，希望恢复成系统原生风格，但仍需同时支持文件和文件夹。
- 已做修改：
- `_choose_input_path_interactive()` 不再调用 `_UnifiedInputPathPicker(...).show()`。
- 当前改为调用 `_choose_input_path_via_shell_dialog(...)`，底层使用 Windows Shell `SHBrowseForFolder` 并开启 `BIF_BROWSEINCLUDEFILES`。
- 打开时会尽量定位到当前输入目录，且在同一系统窗口中允许直接选文件或文件夹。
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
- `python smoke_test.py` 12 项通过，`failed: []`
- `python full_debug_test.py` 39 项通过，`failed: []`
- 改动边界：
- 未改动批量压缩与添加水印业务逻辑
- 未改动单文件/文件夹调度逻辑，只替换浏览入口的 UI 实现

## 2026-04-24 去水印卡住与脏路径回归
- 用户反馈：
- 去水印时卡住，且导入后的输入框路径出现 `b'...'`、`\x..`、以及被错误拼进项目目录前缀的异常字符串。
- 根因定位：
- Windows Shell 原生选择器在当前环境下可能返回 `bytes` 路径。
- 旧版 `_normalize_input_path_value()` 直接 `str(value)`，把字节路径转成了字节字面量文本。
- 随后 `os.path.abspath(...)` 又把这段字面量当成相对路径拼到项目目录下，导致输入框显示异常路径，`remove_wm` 等任务拿到脏路径后表现为卡住或异常日志。
- 已做修改：
- 新增 `_decode_input_path_bytes(...)`，按 `utf-8 / mbcs / gbk / filesystemencoding` 顺序解码路径字节。
- 新增 `_coerce_input_path_text(...)`，兼容原始 `bytes`、`b'...'` 字面量字符串、以及 `...\\b'真实路径'` 这类已污染字符串。
- `_normalize_input_path_value()` 现统一先解码再归一化。
- 专项验证：
- 三类输入样本均被还原为同一真实路径：
- `bytes`
- `b'...'`
- `项目目录\\b'真实路径'`
- 回归结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
- `python smoke_test.py` 12 项通过，`failed: []`
- `python full_debug_test.py` 39 项通过，`failed: []`
- 改动边界：
- 未改动批量压缩与添加水印业务逻辑
- 未改动去水印算法主体，只修复输入路径规范化层

## 2026-04-24 拖拽单文件精确选中回归
- 用户反馈：
- 现在浏览选择模式已经可以精准选文件，但把单个文件直接拖进窗口时，仍然只会锁定到父文件夹。
- 进一步暴露的问题：
- 当单文件被错误降级成文件夹后，`remove_wm` 的单文件专用链路会把输出目录错拼成：
- `某文件.pdf\\【处理完成】结果文件夹`
- 日志表现为 `[WinError 3] 系统找不到指定的路径`
- 根因定位：
- 运行时原始 `accept_drag_drop()` 在检测到拖入的是文件时，会直接改写成 `os.path.dirname(path)`。
- 加载层 `_run_remove_wm_task(...)` 之前也默认把 `input_folder` 当目录来拼输出目录和算相对路径。
- 已做修改：
- 新增 `_patch_drag_drop_input_support()`，拖拽单文件时保留文件本体路径，不再强制转父目录。
- `_run_remove_wm_task(...)` 新增 `input_root`：
- 若输入是文件，则输出目录落在该文件父目录下
- `other_files` 的 `relpath()` 与 PDF round-trip 也统一改用 `input_root`
- 专项验证：
- 拖拽字节路径样本后，`input_path` 保持为精确文件路径，`_fx_input_pick_mode == 'file'`
- 单文件 PDF 去水印探针确认：
- `input_folder` 传给 PDF round-trip 的是父目录
- `output_folder` 为 `父目录\\【处理完成】结果文件夹`
- 回归结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
- `python smoke_test.py` 12 项通过，`failed: []`
- `python full_debug_test.py` 39 项通过，`failed: []`
- 改动边界：
- 未改动批量压缩与添加水印业务逻辑
- 未改动去水印算法主体，只修复拖拽输入与单文件输出根目录计算

## 2026-04-24 去水印单文件输出与失败伪成功回归
- 用户反馈：
- 去水印结束后没有拿到符合预期的结果产物
- 原 PDF 仍带水印，存在“看似处理完成、实际未生效”的风险
- 本轮新增修复：
- `remove_wm` 单文件默认改为同目录输出新文件，不再强制创建 `【处理完成】结果文件夹`
- 新增可选开关：单文件时可直接覆盖原文件，但只在处理成功后才执行替换
- PDF round-trip 不再允许 `remove_watermark_from_word()` 失败后继续把原样文档转回 PDF 伪装成功
- PDF round-trip 失败时不再复制原 PDF 充当结果文件
- 新增回归：
- `pdf_remove_wm_single_file_output`
- `pdf_remove_wm_single_file_overwrite`
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
- `python smoke_test.py` 12 项通过，`failed: []`
- `python full_debug_test.py` 41 项通过，`failed: []`
- 改动边界：
- 未改动批量压缩与添加水印业务逻辑
- 去水印仍优先走加载层补丁，不直接重写 `fengxi_runtime.bin`

## 2026-04-25 OCR 单文件与拖拽路径回归
- 用户反馈：
- 批量水印已经能正确找到单文件位置
- 但 `PDF 工具 -> OCR 搜索版 PDF` 在单文件输入时仍报 `[WinError 3]`，路径被拼成 `文件.pdf\\【处理完成】结果文件夹`
- 根因定位：
- `_run_pdf_ocr_task(...)` 仍直接 `os.path.join(input_folder, RESULT_FOLDER_NAME)`
- 这在文件夹输入时正常，但在单文件输入时会把文件当文件夹
- 本轮修复：
- OCR 输出目录改为基于 `input_root` 计算，单文件时取父目录
- OCR 文件收集改为先规范化输入，再走统一 `collect_input_files(...)`
- 新增回归：
- `single_file_input_pdf_ocr`
- `drag_drop_single_file_pdf_ocr`
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
- OCR 专项探针：单文件拖拽后可生成 `probe.pdf` 的 OCR 输出且文本可检索
- `python smoke_test.py` 12 项通过，`failed: []`
- `python full_debug_test.py` 43 项通过，`failed: []`
- 当前结论：
- 源码层自定义工作流里，已知会误把单文件当文件夹拼输出路径的问题，`remove_wm` 与 `pdf OCR` 都已修复
## 2026-04-25 OCR 打包版 onnxruntime 修复回归
- 问题现象：
  - 打包版 `PDF 工具 -> OCR 搜索版 PDF` 在实际执行时失败。
  - 典型报错：`DLL load failed while importing onnxruntime_pybind11_state: 动态链接库(DLL)初始化例程失败。`
- 根因定位：
  - PyInstaller 打包产物中，`onnxruntime` 的二进制位于 `_internal\onnxruntime\capi`。
  - 仅有 `_internal` 被纳入默认运行时环境并不足以让 `onnxruntime_pybind11_state.pyd` 完成初始化。
  - 该问题会导致 UI 状态面板误判“rapidocr 可用”，但真正 OCR 时才失败。
- 本轮修复：
  - `tools/fx_pdf_ocr.py` 新增 Windows 运行时 DLL 目录准备逻辑，显式注册 `onnxruntime\capi`。
  - 后端状态改为真实导入探测，失败时会直接显示导入失败原因。
  - `full_debug_test.py` 新增 `pdf_ocr_backend_runtime_probe`。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_pdf_ocr.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：12/12 通过。
  - `python full_debug_test.py`：44/44 通过。
  - 模拟冻结环境探针：
    - 对 `dist_release_ascii\fx_toolbox\_internal\onnxruntime\capi\onnxruntime_pybind11_state.pyd` 导入成功。
  - 已重打包：
    - `dist_release_ascii\fx_toolbox\fx_toolbox.exe`

## 2026-04-25 OCR 页面卡顿与后端误判回归
- 用户反馈：
  - 打开程序后 OCR 相关操作仍提示“当前环境没有可用的 OCR 后端”。
  - 程序整体偏卡，尤其是 OCR 页。
- 本轮定位：
  - OCR 页初始化时会立即执行 `build_backend_status_text()`，从而触发真实导入探测，带来额外卡顿。
  - `auto` 选后端也依赖 `discover_backend_status()` 预判；一旦打包环境里的轻量判断失真，就会把后端提前判死，根本不进入真正导入尝试。
- 本轮修复：
  - OCR 页初始文案改为按需检测，不再在页面初始化时自动做重探测。
  - `刷新状态` 改为手动触发详细检测。
  - `_resolve_backend_key()` 改成真正执行时逐个后端实试，并在失败时汇总每个后端的真实错误原因。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_pdf_ocr.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：12/12 通过。
  - `python full_debug_test.py`：44/44 通过。
  - 已重打包新版：
    - `dist_release_ascii\fx_toolbox\fx_toolbox.exe`
## 2026-04-25 打包版 OCR 运行库冲突回归
- 正式打包版 `dist_release_ascii\fx_toolbox\fx_toolbox.exe` 已重新验证：
  - `run_packaged_ocr_diagnostics(...)` 成功写出 `tmp_ocr_diag\packaged_ocr_diag_fixed.json`
  - `module_checks.onnxruntime.import_ok == true`
  - `backend_resolution.rapidocr == rapidocr`
  - `backend_resolution.auto == rapidocr`
  - `rapidocr_backend_init.ok == true`
- 本次关键验证点：
  - 打包目录 `_internal` 中已不再保留会和 `onnxruntime` 冲突的本地 MSVC/UCRT DLL。
  - 诊断中 `available_providers` 已返回 `AzureExecutionProvider`、`CPUExecutionProvider`，说明冻结环境里的 ORT 初始化完成。
- 源码侧回归：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_pdf_ocr.py full_debug_test.py smoke_test.py` 通过
  - `python smoke_test.py` 12/12 通过
  - `python full_debug_test.py` 44/44 通过
- 当前结论：
  - “找不到库”问题已从打包版复现状态转为已修复状态。
  - 若后续再次复发，优先比对新包 `_internal` 中是否重新出现 `msvcp140*.dll`、`vcruntime140*.dll`、`ucrtbase.dll`、`api-ms-win-crt-*.dll`。

## 2026-05-21 任务历史筛选与回放回归
- 本轮目标：
  - 让任务历史变成可检索、可筛选、可回放的入口，而不是只列出历史和失败重试。
- 关键修复：
  - 历史窗口新增状态筛选、功能筛选、关键词筛选。
  - 成功历史也支持回放入队，失败历史保留重试。
  - 历史摘要会显示“当前可见条数 / 总条数”。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py` 14/14 通过。
  - `python full_debug_test.py` 65/65 通过。
- 改动边界：
  - 仍只改 `Fengxi_Toolbox.py` 加载器层与 `full_debug_test.py`。
  - 未触碰 `批量压缩` / `添加水印` 核心业务实现。


## 2026-05-21 16:48:24
- Status: history detail export done
- Scope: task history detail dialog
- Result: export button added; it saves structured task_result JSON for the current history entry and rejects empty entries cleanly. Test suite: py_compile passed, smoke_test 14/14, full_debug_test 71/71.


## 2026-05-21 16:59:33
- Status: history detail log export done
- Scope: task history detail dialog
- Result: added 导出日志 beside 导出结果. The exported TXT is a plain text snapshot of the current entry's title, task, status, timestamps, and log lines, with a safe default filename and clean empty-log fallback. Test suite: py_compile passed, smoke_test 14/14, full_debug_test 74/74.


## 2026-05-21 18:14:31
- Status: history detail open output location done
- Scope: task history detail dialog
- Result: added 打开位置 beside 导出结果/导出日志/复制详情. The action opens the best available target for the current entry, preferring output_root and falling back to an output file's parent directory. Test suite: py_compile passed, smoke_test 14/14, full_debug_test 77/77.
## 2026-05-22 10:01:00
- Status: output strategy tail fix done
- Scope: remove_wm single-file overwrite path
- Result:
  - fixed the last failing `full_debug_test.py` case: `pdf_remove_wm_single_file_overwrite`
  - single-file remove_wm overwrite now stages output in a temporary result folder and only then safely replaces the original file
  - single-file remove_wm success/failure branches now explicitly finalize structured `task_result`
  - remove_wm aggregate counts now use `total_items`, keeping history/export/retry semantics aligned
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed
  - `python smoke_test.py` passed: `14/14`
  - `python full_debug_test.py` passed: `88/88`

## 2026-05-22 11:15:00
- Status: remove_wm graded mode done
- Scope: remove_wm detection thresholds, UI setting, local preference memory
- Result:
  - added `保守（推荐）` / `标准` / `激进` remove-watermark modes
  - default mode is conservative to reduce accidental removal of normal text/images
  - standard mode keeps previous threshold behavior for compatibility
  - aggressive mode expands candidate detection for stubborn watermarks
  - mode is persisted under `watermark.remove_wm_mode`
  - fixed an accidental stale result-model block that had been inserted inside `_UnifiedInputPathPicker._refresh_entries`
  - conservative inline-image threshold was tuned after regression caught a missed header image watermark
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed
  - `python full_debug_test.py` passed: `92/92`
  - `python smoke_test.py` passed: `14/14`

## 2026-05-22 11:50:00
- Status: queue history auto pruning done
- Scope: task queue/history persistence
- Result:
  - added `QUEUE_HISTORY_RETENTION_DAYS = 90`
  - queue history load/save/append now share one pruning path
  - stale entries older than the retention window are removed from both memory and the persisted history file
  - undated legacy entries are retained to avoid accidental data loss
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed
  - `python smoke_test.py` passed: `14/14`
  - `python full_debug_test.py` passed: `93/93`

## 2026-05-22 11:58:00
- Status: true progress status done
- Scope: runtime progress tracker and bottom progress UI
- Result:
  - bottom action row now shows progress status text beside the progress bar
  - progress status includes current file, current stage, completed/total files, total percentage, and ETA
  - `_FxRunProgressTracker` now owns stage/file/ETA state while preserving the previous runtime progress correction behavior
  - OCR, PDF compression, image-to-PDF, image merge, and PDF remove-watermark round-trip now report clearer stage names without changing business logic
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed
  - `python smoke_test.py` passed: `14/14`
  - `python full_debug_test.py` passed: `95/95`

## 2026-05-22 19:50:00
- Status: PDF remove-watermark COM export fallback done
- Scope: `remove_wm` PDF round-trip DOCX -> PDF export and Word COM regression coverage
- Result:
  - reproduced the failure where `pdf_remove` generated only a failed report and no `【处理完成】结果文件夹\wm.pdf`
  - isolated the cause to `convert_doc_to_pdf(...)` returning `ERROR` while direct Word `ExportAsFixedFormat(..., 17)` succeeded
  - added `_export_word_docx_to_pdf_safely(...)` as a fallback after the original runtime export path
  - changed Word dynamic dispatch to create a fresh COM instance via `pythoncom.CoCreateInstance + win32com.client.dynamic.Dispatch`
  - documented and enforced that Word child-object access must be inside `_DisableWin32ComGenCache()` because damaged `win32com.gen_py` can otherwise raise `CLSIDToClassMap`
  - updated `full_debug_test.py` so Word COM tests exercise the same safe dynamic COM path instead of plain `DispatchEx`
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` passed
  - `python smoke_test.py` passed: `14/14`
  - `python full_debug_test.py` passed: `109/109`
- Boundaries:
  - no changes to `fengxi_runtime.bin`
  - no changes to stable batch-compress core logic
  - no changes to stable add-watermark core logic

## 2026-05-22 19:50:00
- Status: audio file-level parallel workflow done
- Scope: `audio` task loader-layer custom workflow
- Result:
  - added file-level `ThreadPoolExecutor` execution for audio/video conversion when `enable_multithread` is on and there is more than one input file
  - kept ffmpeg conversion work inside worker threads while aggregating logs/progress/structured results in the main flow
  - added `audio_parallel_executor` regression coverage
- Validation:
  - included in `python full_debug_test.py`: `109/109`

## 2026-05-22 20:10:00
- Status: parallel hint removed and queue actions restored
- Scope: bottom action row UI patch
- Result:
  - removed the visible bottom-row `并行状态` hint label that was consuming space beside the multithread switch
  - kept the `批量并行（部分生效）` switch label and underlying parallel execution capability
  - `_refresh_parallel_mode_hint(...)` now clears the hint variable and destroys any stale hint label
  - task queue/history buttons remain installed as `btn_queue_add` and `btn_queue_panel`
  - added regression case `parallel_hint_removed_queue_actions_kept`
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` passed
  - `python smoke_test.py` passed: `14/14`
  - `python full_debug_test.py` passed: `110/110`
- Boundaries:
  - no changes to `fengxi_runtime.bin`
  - no changes to stable batch-compress core logic
  - no changes to stable add-watermark core logic

## 2026-05-23 19:00:00
- Status: image PDF task modularization done
- Scope: image to PDF / merge PDF task core split
- Result:
  - added `tools/fx_image_pdf_task.py` for image PDF task core orchestration
  - kept `Fengxi_Toolbox.py` as a thin adapter for UI parsing, progress, history, and failure report handling
  - preserved existing image PDF output naming semantics, including unique suffix fallback on collisions
  - fixed a regression test expectation so the module export check no longer assumes an unused output path
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools/fx_image_pdf_task.py full_debug_test.py smoke_test.py` passed
  - `python smoke_test.py` passed: `14/14`
  - `python full_debug_test.py` passed: `135/135`
- Boundaries:
  - no changes to `fengxi_runtime.bin`
  - no changes to stable batch-compress core logic
  - no changes to stable add-watermark core logic

## 2026-05-23 20:12:00
- Status: file manager rename core modularization done
- Scope: `file` task `rename` submode core split
- Result:
  - added `tools/fx_file_manager_core.py` for rename spec parsing, output path planning, filename rewriting, and single-file rename-copy execution
  - patched `FengxiToolboxApp.process_single_file(...)` so only `file + rename` routes into the new module
  - kept `dedup` on the original runtime `run_process()` single-thread branch because it still depends on whole-folder hash comparison and delete-side-effect semantics
  - added `file_manager_core_module_exports` regression coverage while preserving existing `file_rename_*` and `file_dedup` coverage
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_file_manager_core.py full_debug_test.py smoke_test.py` passed
  - `python smoke_test.py` passed: `14/14`
  - `python full_debug_test.py` passed: `136/136`
- Boundaries:
  - no changes to `fengxi_runtime.bin`
  - no changes to stable batch-compress core logic
  - no changes to stable add-watermark core logic
  - no project-external deletion

## 2026-05-28 Office COM gen_py safe dispatch
- Diagnosed a user report where Word conversion logged `[依赖异常] Word COM 初始化失败` with `CLSIDToPackageMap`, then still reported a perfect finish because the adapter copied/preserved the source file.
- Local feedback loop confirmed plain `win32com.client.DispatchEx('Word.Application')` fails on this machine, while dynamic COM via `pythoncom.CoCreateInstance + win32com.client.dynamic.Dispatch` succeeds and returns Word 16.0.
- Added a loader-layer safe DispatchEx patch for Office COM cache failures and strengthened `_DisableWin32ComGenCache` to suppress `GetModuleForCLSID` as well as `GetClassForCLSID`.
- The convert adapter now treats missing Word/PPT COM for matching Office inputs as a real failed item, preventing misleading completion messages.
- Validation: `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_convert_task.py`; direct safe dispatch probe; `python smoke_test.py` 14/14; `python full_debug_test.py` 151/151.
## 2026-05-28 Batch watermark Word COM Dispatch guard
- Status: fixed the remaining `.docx` batch-watermark COM initialization failure after the first `DispatchEx`-only patch.
- Cause: runtime batch watermark used plain `win32com.client.Dispatch("Word.Application")`, which could still enter damaged pywin32 `gen_py` wrappers and raise `CLSIDToClassMap` / `CLSIDToPackageMap`.
- Result: `Fengxi_Toolbox.py` now patches both `Dispatch` and `DispatchEx`; Word goes through dynamic COM creation via `pythoncom.CoCreateInstance + win32com.client.dynamic.Dispatch`, while original dispatch functions are preserved for fallback.
- Regression added: `watermark_docx_run_process_safe_word_dispatch`.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed
  - direct `win32com.client.Dispatch("Word.Application")` probe returned Word 16.0
  - `python smoke_test.py` passed: 14/14
  - `python full_debug_test.py` passed: 152/152
- Boundaries:
  - no changes to `fengxi_runtime.bin`
  - no changes to stable add-watermark core behavior
  - no changes to stable batch-compress core behavior

## 2026-05-28 Batch watermark direct/convert PDF fix
- Status: fixed real single-file `.docx` batch watermark failure for both direct Word output and "convert to PDF first" output.
- Cause:
  - direct mode could write output but old result plumbing reported empty outputs/counts
  - convert-to-PDF mode relied on runtime `convert_doc_to_pdf(...)`; when that failed under Word COM/gen_py issues, the task could preserve/copy the original file and still log a false success
- Result:
  - added a loader-layer watermark task runner with explicit output planning and structured task result population
  - single file default now writes `*_加水印.docx` or `*_加水印.pdf` beside the source, overwrite uses safe staging when extension is unchanged, and folder input still writes to `【处理完成】结果文件夹`
  - Word-to-PDF conversion now falls back to safe Word `ExportAsFixedFormat(..., 17)` if the runtime converter fails or does not create a valid PDF
  - false success is blocked: failed files now create a real failed result and failure report
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed
  - real-user document probe passed for direct Word watermark and convert-to-PDF watermark
  - `python smoke_test.py` passed: 14/14
  - `python full_debug_test.py` passed: 154/154
- Boundaries:
  - no changes to `fengxi_runtime.bin`
  - batch-compress core remains untouched
  - add-watermark changes were made only because the user explicitly authorized fixing this failing stable-area feature

## 2026-05-28 Direct Word watermark visible output fix
- Status: fixed the case where direct Word watermark reported success but the watermark was not visible to the user.
- Cause:
  - `.docx` XML contained `XMU_DONE` WordArt shapes, but Word did not visibly render the watermark with the previous fill/opacity settings.
  - Default opacity `0.08` became Word fill transparency around `0.92`, which was effectively too faint.
- Result:
  - Word watermark core now forces visible solid gray WordArt fill, removes the outline, allows overlap, and clamps minimum visible opacity to `0.18` for Word direct mode.
  - Existing PDF watermark opacity semantics are unchanged.
- Validation:
  - targeted probe: old exported image had no visible watermark; new output rendered a visible gray diagonal watermark
  - `python -m py_compile Fengxi_Toolbox.py tools/fx_watermark_core.py full_debug_test.py` passed
  - `python smoke_test.py` passed: 14/14
  - `python full_debug_test.py` passed: 156/156
- Boundaries:
  - no changes to `fengxi_runtime.bin`
  - no changes to batch-compress
  - this touches add-watermark core only as a necessary bug fix authorized by the user

## 2026-05-28 Watermark color picker and preview
- Status: added selectable watermark color and an inline preview to the batch-watermark page.
- Result:
  - PDF watermark packets accept optional `color="#RRGGBB"` and render with that RGB value.
  - Direct Word watermark passes the same color into WordArt fill while keeping the Word-only minimum visible opacity protection.
  - Watermark UI now includes a color swatch, hex entry, system color chooser, and PIL-based preview image.
  - Last-settings memory saves/restores `wm_color_var`.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_watermark_core.py full_debug_test.py` passed
  - `python smoke_test.py` passed: 14/14
  - `python full_debug_test.py` passed: 159/159
- Note: full debug printed a few non-failing Tkinter callback noise lines while destroying UI test widgets, but all cases passed.
## 2026-05-28 22:25:45 Startup recursion crash fix
- User-facing symptom: packaged EXE opened slowly and could crash with RecursionError inside customtkinter scrollbar drawing (ctk_scrollbar.py / draw_engine.py) near pp.mainloop().
- Cause confirmed by loader log pattern: startup/lazy UI could re-enter page initialization while the hidden startup window was still doing layout refreshes, especially around watermark wm_* attribute access; repeated double-clicks could spawn multiple packaged processes and amplify the issue.
- Fix: lazy tab reentrancy guard, deferred post-show layout refresh, delayed watermark preview refresh, and single-instance mutex before app creation.
- Packaging speed fix: excluded unused RapidOCR PyTorch/Paddle/TensorRT engines and heavy optional ML packages from PyInstaller while preserving ONNXRuntime OCR.
- Validation passed: python -m py_compile Fengxi_Toolbox.py tools\fx_startup_patches.py fx_toolbox.spec full_debug_test.py; python smoke_test.py 14/14; python full_debug_test.py 159/159; package.bat; packaged EXE launch and duplicate-launch guard.

## 2026-05-28 Default package-and-open workflow
- User explicitly requested future work to automatically package and open the app.
- Standard closeout for implementation/debug tasks is now: source validation as appropriate -> stop only this repo's packaged EXE process -> run `package.bat` -> launch `dist_release_ascii\fx_toolbox\fx_toolbox.exe`.
- If the user says "do not package", "do not open", or asks for analysis only, skip this default.
## 2026-05-28 23:33:16 Watermark color preview visibility fix
- Symptom: color picker/preview feature existed but was not visible in the packaged app at the user's current window size.
- Cause: the UI patch inserted the color preview after the right parameter controls; existing switches, font selector, and sliders consumed the visible height.
- Result: moved color controls to the left watermark-content panel and made the preview compact. Packaged app opened successfully after the change.

## 2026-05-29 Watermark color preview real visibility repair
- Symptom: the color picker/preview still did not appear after moving it out of the right parameter panel.
- Reproduction loop:
  - Instantiated `FengxiToolboxApp`, inspected `tab_wm` hierarchy, and found the preview frame under an old left panel while the real `app.wm_text` belonged to a newer left panel.
  - Targeted probe before fix showed `preview_master_is_text_panel=False` and `preview_count=2`.
- Fix:
  - Added helpers to resolve the true watermark text panel from `app.wm_text` instead of using `tab_wm.winfo_children()[0]`.
  - Destroy stale marked preview frames and repack the live preview before the real textbox.
  - Added an after-main-area repair pass so startup duplicate/overlap creation cannot leave the preview in the wrong panel.
- Validation:
  - Targeted probe after fix: `preview_master_is_text_panel=True`, `preview_count=1`, pack order title -> preview -> textbox.
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - `python full_debug_test.py` passed: 159/159.
  - `python smoke_test.py` passed: 14/14.

## 2026-05-29 Watermark parameter auto memory
- User-facing request: the batch-watermark right-side parameter panel should remember its settings.
- Existing state: `_capture_preset_settings(..., "watermark")` already included most fields, but persistence mainly happened on start/close, so casual parameter changes did not feel reliably remembered.
- Fix:
  - Added `_install_watermark_last_settings_memory(...)` to trace watermark parameter variables and wrap/bind the three sliders.
  - Added `_schedule_watermark_last_settings_persistence(...)` with debounce to avoid excessive JSON writes while dragging.
  - Installed the binding after main-area setup, after startup last-settings restore, so restored values are not immediately overwritten.
- Covered fields:
  - font, page range, smart/force mode, filename skip rule, Word/Simsun compatibility, delete source, convert-to-PDF first, color, size, opacity, angle, output strategy.
- Validation:
  - Targeted probe confirmed changed values were saved into `last_settings.watermark`.
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - `python full_debug_test.py` passed: 160/160.
  - `python smoke_test.py` passed: 14/14.

## 2026-05-29 Audio/video speech-to-text
- Status: added and validated Fengxi Toolbox native speech-to-text in the audio module.
- Scope:
  - `tools/fx_speech_to_text.py` provides transcript path planning, SRT timestamp formatting, transcript writers, and lazy `faster_whisper` execution.
  - `tools/fx_audio_task.py` supports `mode == "transcribe"` in the same task-result model used by audio conversion.
  - `Fengxi_Toolbox.py` adds the audio UI controls, start-preview detail, model cache path, and automatic last-settings memory for audio transcription options.
  - `fx_toolbox.spec` and `requirements.txt` include optional packaging/dependency coverage for the Whisper stack.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_audio_task.py tools\fx_speech_to_text.py full_debug_test.py smoke_test.py` passed.
  - Targeted transcript helper probe produced `.txt` and `.srt` outputs.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 164/164, including `speech_to_text_core_outputs`, `audio_transcribe_task_module`, `audio_transcribe_workflow`, and `last_settings_audio_transcribe_save_restore`.
- Notes:
  - No new pip install was performed during this feature pass; existing packages in `D:\Python\Lib\site-packages` were used.
  - First real transcription can be slow because selected Faster-Whisper models are downloaded/cached on demand.
  - Batch compression and add-watermark core logic were not changed for this feature.

## 2026-05-29 Speech-to-text model hint
- Status: added inline model explanation under the audio speech-to-text controls.
- User-facing wording explains `base` as the default recommendation, `tiny` as fastest but less accurate, `small` as steadier, and `medium` as most accurate but slower/resource-heavy.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - Targeted UI probe confirmed the hint text contains the `base`/`tiny`/`medium` tradeoff wording.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 165/165.

## 2026-05-29 Speech-to-text realtime preview
- Status: added scrollable realtime transcript preview for audio/video speech-to-text.
- Implementation:
  - `transcribe_media_file(...)` emits optional progress events while segments stream from Faster-Whisper.
  - `run_audio_task_core(...)` wraps those events per source file and sends them through `AudioTaskCallbacks.on_transcript_progress`.
  - `Fengxi_Toolbox.py` owns the visible preview box and updates it via `after(0, ...)` for Tk safety.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_audio_task.py tools\fx_speech_to_text.py full_debug_test.py` passed.
  - Targeted UI probe confirmed preview insertion with timestamped text.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 168/168.
- Boundaries:
  - No changes to `fengxi_runtime.bin`.
  - No changes to stable batch-compress or add-watermark core logic.

## 2026-05-29 Speech-to-text preview compact layout
- Symptom: after adding realtime preview, the lower part of the audio speech-to-text page was clipped at the user's current window size.
- Cause: the model hint plus a 150px preview box consumed too much vertical space, and the preview was inserted after the hint.
- Fix:
  - Reordered the audio transcription UI so the realtime preview appears before the model hint.
  - Reduced preview box height to 96px and tightened header/padding.
  - Kept model-hint key phrases stable for regression coverage.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - Targeted UI probe: `height=96`, `preview_before_hint=True`, `hint_ok=True`.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 169/169.
- Boundaries:
  - No changes to `fengxi_runtime.bin`.
  - No changes to stable batch-compress or add-watermark core logic.

## 2026-05-29 Speech-to-text preview roomy layout
- Symptom: after the compact fix, the audio page still had excessive blank space above the audio card content, and the realtime preview box felt too short.
- Cause: the base card/title layout kept large audio-page padding (`title pady=(45, 30)`, settings-frame `pady=15`) while the preview box was capped at 96px.
- Fix:
  - Added `_tighten_audio_tab_layout(...)` and called it from `_tighten_single_tab_layout(..., "audio")`.
  - Audio card/title/settings now use tighter vertical spacing.
  - Realtime transcript preview height is now 150px.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - Targeted UI probe: `height=150`, `preview_before_hint=True`, `title_pady=(22, 14)`, `settings_pady=(0, 12)`.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 169/169.
- Boundaries:
  - No changes to `fengxi_runtime.bin`.
  - No changes to stable batch-compress or add-watermark core logic.

## 2026-05-29 Speech-to-text near-zero top spacing
- Symptom: user still could not see the lower part of the speech-to-text page and pointed to the remaining upper blank band as the area to shrink.
- Cause: the audio-specific layout was improved but still left nonzero card/title top spacing above the input content.
- Fix:
  - Audio card top padding is now effectively zero: `pady=(0, 8)`.
  - Audio title top padding is now effectively zero: `pady=(0, 10)`.
  - Audio settings-frame top padding remains effectively zero: `pady=(0, 12)`.
  - Realtime preview stays at `height=150` and remains before the model hint.
- Validation:
  - Targeted UI probe: `card_pady=(0, 8)`, `title_pady=(0, 10)`, `settings_pady=(0, 12)`, `preview_height=150`.
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 169/169.
- Boundaries:
  - No changes to `fengxi_runtime.bin`.
  - No changes to stable batch-compress or add-watermark core logic.

## 2026-05-29 Speech-to-text outer tab gap removal
- Symptom: user screenshot showed a large purple-circled blank strip between the top file/output controls and the audio/video content card.
- Cause: not audio-card padding. The remaining height came from `CTkTabview` reserving rows for its segmented tab buttons inside `main_panel`, even though Fengxi Toolbox uses sidebar navigation.
- Fix:
  - Added `_compact_main_tabview_header(app)`.
  - It hides the internal segmented button, zeros the tabview's top reserved rows, keeps the canvas covering the full panel, and patches tab switching so the selected tab is always gridded at `row=0`, `pady=0`.
  - Audio preview remains `height=150`.
- Validation:
  - Targeted UI probe: `tab_grid row=0`, `pady=0`, segmented manager empty, preview height `150`.
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 169/169.
- Boundaries:
  - No changes to `fengxi_runtime.bin`.
  - No changes to stable batch-compress or add-watermark core logic.
## 2026-05-30 OCR realtime preview
- Request: OCR 搜索版 PDF should have a realtime preview like the audio/video speech-to-text page.
- Implementation:
  - Added page-level preview payloads in `tools/fx_pdf_ocr.py` after each page is processed.
  - Added `PdfOcrTaskCallbacks.on_page_preview` in `tools/fx_pdf_ocr_task.py`.
  - Added `实时 OCR 预览` textbox and clear button to the PDF OCR panel.
  - UI updates use `app.after(0, ...)` so OCR worker callbacks do not write Tk widgets directly.
- Validation:
  - Targeted probe: task core emitted 2 page-preview events and the last line was `OCR: page two`.
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_pdf_ocr.py tools\fx_pdf_ocr_task.py full_debug_test.py` passed.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 170/170, including `pdf_ocr_realtime_preview_ui`.
- Boundaries:
  - No changes to `fengxi_runtime.bin`.
  - No changes to stable batch-compress or add-watermark core logic.

## 2026-05-30 PDF OCR nav visibility fix
- Request: user reported the OCR function disappeared from the PDF page.
- Reproduction:
  - Runtime UI probe showed the OCR button still existed but was outside the visible PDF left nav before the fix: OCR was below the parent panel and not mapped.
  - After compaction, all five PDF nav buttons are visible; OCR button measured `y=222`, `height=42`, `bottom=264`, with parent height >= 300.
- Fix:
  - PDF mode buttons are single-line compact buttons.
  - PDF left-nav layout tightening now uses smaller button height and padding.
- Regression:
  - Added `pdf_ocr_nav_button_visible` to `full_debug_test.py`.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 171/171.
- Boundaries:
  - No changes to OCR backend logic.
  - No changes to `fengxi_runtime.bin`.
  - No changes to stable batch-compress or add-watermark core logic.

## 2026-05-30 PDF encrypt password entry visibility fix
- Request: user reported the PDF encrypt page did not show a password box.
- Reproduction:
  - Screenshot showed `PDF 加密 (Encrypt)` selected and the right panel only contained descriptive text.
  - Code inspection confirmed the password entry was only in the left shared panel.
- Fix:
  - Added `_fx_pdf_encrypt_pwd_entry` inside the `PDF 加密` detail panel.
  - Introduced `pdf_pwd_var` shared by both the left shared password entry and the right encrypt password entry.
  - Kept `pdf_pwd_entry` as the active entry used by execution/history code, now pointing at the right encrypt entry.
- Regression:
  - Added `pdf_encrypt_password_entry_visible`.
- Validation:
  - Targeted UI probe passed: right encrypt entry visible and shared password value synchronized.
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 172/172.
- Boundaries:
  - No changes to PDF encryption processing logic.
  - No changes to `fengxi_runtime.bin`.
  - No changes to stable batch-compress or add-watermark core logic.

## 2026-05-31 ZIP smart mode root-only folder notice
- Request: user asked why batch compression could not compress `D:\Users\CHEER\xwechat_files\wxid_3q9imbf73w2l32_f9cb\msg\file\2026-05\计量（大类）期末(1)`.
- Reproduction:
  - Read-only probe confirmed the folder exists and has two direct child folders but no direct files.
  - `plan_zip_archives(..., "total")` planned 1 root archive.
  - `plan_zip_archives(..., "recursive")` planned 4 archives.
  - `plan_zip_archives(..., "smart_recursive")` planned 2 child-folder archives.
- Cause:
  - Not a path-not-found or permission issue.
  - The target folder shape triggers smart mode's intended "only subfolders -> keep descending" behavior, so no root zip appears in the selected root folder.
- Fix:
  - Added ZIP pre-run plan messages in the loader layer.
  - Smart mode now warns when the selected root has only subfolders and explains to choose `仅压缩总文件` for a single whole-folder zip.
  - It also logs the planned output count and first output paths.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_zip_core.py` passed.
  - Targeted ZIP notice probe passed.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 173/173.
- Boundaries:
  - No changes to `tools/fx_zip_core.py` compression core.
  - No changes to stable ZIP semantics.
  - No project-external files were deleted or modified.

## 2026-05-31 ZIP smart mode revised layer semantics and max depth
- Request:
  - User clarified the previous smart mode logic was wrong.
  - New smart mode must be like recursive compression, but stop descending after a layer that contains both ordinary files and child folders.
  - If a layer only has child folders, it must be zipped and then scanned deeper.
  - Archive files such as existing `.zip` files are exceptions and should not block continued descent.
  - Root package is written inside root; non-root folder packages are written to their parent.
  - Add a shared max-depth input for recursive and smart modes.
- Implementation:
  - Updated `tools/fx_zip_core.py` planning semantics for `smart_recursive`.
  - Added `max_depth` support to `plan_zip_archives`, `estimate_zip_progress_units`, and `run_zip_task`.
  - Added `normalize_zip_max_depth`.
  - Updated recursive/smart output placement so non-root folder packages go to their parent.
  - Added `最多压缩层数` entry to the ZIP UI and documented the full logic on the page.
  - Added last-settings memory for ZIP mode and max depth.
- Read-only real-folder probe:
  - Modified WeChat folder smart plan now has 5 packages:
    - root package
    - `大物C期末卷.zip`
    - `计量（大类）期末.zip`
    - `【处理完成】结果文件夹.zip`
    - `新建文件夹.zip`
  - With max depth 2, it plans only 3 packages: root + two first-level children.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_zip_core.py tools\fx_user_prefs.py full_debug_test.py` passed.
  - Targeted ZIP write probe passed.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 177/177.
- Boundaries:
  - This is an explicitly user-requested change to batch-compress visible behavior.
  - No changes to batch watermark logic.
  - No project-external files were modified or deleted; the WeChat folder was only probed read-only.

## 2026-06-01 ZIP start preview and max-depth UI placement fix
- Request:
  - User reported ZIP start preview incorrectly showed no processable files.
  - User also asked that `最多压缩层数` be placed on the right side rather than below.
- Diagnosis:
  - The ZIP core plan was valid, but the unified pre-start preview used the generic file collector before ZIP planning.
  - Folder-based ZIP modes must count planned archive jobs, not generic collected files.
- Fix:
  - ZIP preview now uses `plan_zip_archives(...)` with the active mode and `max_depth`.
  - ZIP UI places mode options on the left and max-depth settings on the right, with the full logic description below.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - Targeted probe: folder-only ZIP preview returned 2 jobs; max-depth frame is gridded in column 1.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 179/179.
- Boundaries:
  - ZIP compression core rules were not changed in this fix.
  - No batch-watermark logic was changed.

## 2026-06-01 Batch watermark skipped-file copy option
- Request:
  - User wanted the existing filename-rule skip feature to optionally copy skipped files into the output folder.
- Diagnosis:
  - The existing skip rule filtered files out before the batch watermark runner, so skipped files disappeared from the result folder.
  - Later watermark task routing bypassed the older `run_process` wrapper that temporarily installed the filename-rule runtime state, so the task runner now sets that runtime state directly before collecting files.
- Fix:
  - Added `wm_copy_skipped_var` and a visible `跳过文件复制到输出文件夹` checkbox.
  - Added local preference persistence under `watermark.filename_skip_rule.copy_skipped` and included it in watermark last-settings.
  - The watermark runner now copies skipped originals into the output/result folder when enabled, preserving relative paths.
  - Result counts now include skipped-rule files in `skipped_count` and copied files in `outputs`.
- Validation:
  - Targeted probe: `normal.pdf` got watermarked; `FX_skip.pdf` was skipped and copied byte-for-byte.
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_user_prefs.py full_debug_test.py` passed.
  - `python smoke_test.py` passed: 14/14.
  - `python full_debug_test.py` passed: 181/181.
- Boundaries:
  - No changes to watermark rendering core.
  - No changes to batch compression.

## 2026-06-01 Batch watermark prefix/suffix skip restoration
- Fix: watermark filename-rule position values are normalized before execution and persistence, accepting Chinese labels (`开头`, `结尾`, `末尾`) and internal/English values (`prefix`, `suffix`, `start`, `end`), then saving canonical `开头`/`结尾`.
- Regression:
  - `watermark_filename_rule_position_normalization`
  - `watermark_suffix_dash_rule_skips_files`
- Validation:
  - Targeted probe: `normal.pdf` was watermarked; `skip-.pdf` was skipped by `结尾` + `-` and copied byte-for-byte when copy-skipped was enabled.
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_user_prefs.py full_debug_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 183/183.
- Boundaries: no changes to watermark rendering core or batch compression.

## 2026-06-01 Batch watermark skip-rule UI active-panel fix
- Fix: the filename-rule controls are now ensured on the visible/right-side watermark parameter panel, not the stale duplicate panel. The visible switch is renamed to `按文件名规则跳过`, with the controls row (`匹配位置`, marker entry, `跳过文件复制到输出文件夹`) in the same parent panel.
- Regression:
  - `watermark_filename_rule_controls_on_active_panel`
- Validation:
  - Targeted UI probe confirmed `active_same_parent=True` and exactly one marked controls row on the active panel.
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 184/184.
- Boundaries: no changes to `tools/fx_watermark_core.py`, watermark rendering core, or batch compression.

## 2026-06-01 Batch watermark skip-rule adjacent layout fix
- Fix: the filename-rule controls row is now packed immediately after the active `按文件名规则跳过` switch. Layout tightening uses the `_fx_wm_filename_rule_controls` marker instead of assuming child index 11, so the controls no longer drift below font/sliders.
- Regression:
  - `watermark_filename_rule_controls_below_switch`
- Validation:
  - Targeted UI probe confirmed switch index `3`, controls index `4`, adjacent `True`.
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 185/185.
- Boundaries: no changes to `tools/fx_watermark_core.py`, watermark rendering core, or batch compression.

## 2026-06-01 Batch watermark output-path failure isolation
- Request: batch watermark stopped mid-run with WinError 3 when creating a nested output path under a directory whose name appeared to end with a space.
- Diagnosis: the watermark task runner created target output parent directories before the per-file try/except, so one bad nested path escaped to the outer patched_run_process handler and logged a whole-task severe error.
- Fix: output parent directory creation is now isolated per file; failures are logged as that file's failure and the remaining files continue. Copy-skipped root creation and failure-report writing also now fail gracefully with path diagnostics.
- Regression: watermark_output_path_failure_does_not_abort_batch verifies one bad output path fails while the next PDF still succeeds and no severe error is logged.
- Validation: python -m py_compile Fengxi_Toolbox.py full_debug_test.py; python smoke_test.py passed 14/14; python full_debug_test.py passed 186/186.
- Boundaries: no changes to tools/fx_watermark_core.py, watermark rendering core, batch compression, or project-external files.

## 2026-06-01 Batch watermark progress bar sync
- Request: user screenshot showed batch watermark status text advancing (e.g. file 2088/6713, total 31%) while the blue progress bar stayed near zero.
- Diagnosis: loader-layer _run_watermark_task(...) updated only _set_progress_status(...), which changes the bottom status text but does not call progress_bar.set(...).
- Fix: added _watermark_update_progress(...) to update both the CTk progress bar and progress status text from the same fraction, and routed all watermark runner progress updates through it.
- Regression: watermark_progress_bar_syncs_with_status verifies a batch watermark run pushes progress bar values from 0.0 through an intermediate value to 1.0.
- Validation: python -m py_compile Fengxi_Toolbox.py full_debug_test.py; python smoke_test.py passed 14/14; python full_debug_test.py passed 187/187.
- Boundaries: no changes to 	ools/fx_watermark_core.py, watermark rendering core, batch compression, or project-external files.

## 2026-06-01 Core modification rule update
- User instruction: future work no longer has a forced prohibition on touching watermark or compression rendering/core logic.
- New rule: watermark/compression cores may be modified when needed, but stability of processing logic and existing functionality is the highest priority.
- Required practice: before touching these cores, identify impact scope and prefer minimal patches; after touching them, add/update regression coverage and run at least smoke tests, plus full or targeted workflow tests when behavior/output semantics are involved.
- Updated gent.md from absolute stable-zone wording to 稳定核心修改规则.
- This instruction supersedes older memory notes that said core logic must not be touched except for modularization.

## 2026-06-01 Batch watermark trailing-space path fix and progress sync
- Request: user asked whether the previous progress fix was complete, then asked to re-check [批量水印] 严重错误: [WinError 3] for a path containing 系解人体结构神经系统资料试卷  with a trailing space.
- Diagnosis: the earlier isolation fix stopped one bad path from aborting the whole batch, but Windows can still reject creating/accessing output directories whose path segments end with spaces or dots. The specific failing path had a source folder segment ending in a space, which was mirrored into the result folder.
- Fix: watermark result-folder relative directory mapping now sanitizes each relative path segment by stripping trailing spaces/dots before creating the output path. Skipped-file copy uses the same safe relative path logic.
- Also completed the prior progress-bar fix: watermark runner now updates progress_bar.set(...) and status text from the same fraction via _watermark_update_progress(...).
- Regression: watermark_result_path_strips_trailing_space_dirs, watermark_output_path_failure_does_not_abort_batch, and watermark_progress_bar_syncs_with_status.
- Validation: python -m py_compile Fengxi_Toolbox.py full_debug_test.py; python smoke_test.py passed 14/14; python full_debug_test.py passed 188/188.
- Behavior note: source folders/files are not renamed; only the generated result-folder path is made Windows-safe.

## 2026-06-03 Global Resume And Background Execution Validation
- Request: add breakpoint/resume processing across functions and prevent long jobs from stopping when the app is in the background.
- Implemented resume paths:
  - generic single-file outputs: rename, meta, convert, image convert/compress, PDF encrypt, PDF split;
  - dedicated adapters: ZIP, PDF OCR, image PDF, audio conversion/transcription, PDF compression, batch watermark, remove-watermark, PDF merge;
  - top-level background guard wraps patched `run_process`.
- Important bug fixed during validation: single-file remove-watermark resume must check the base `*_去水印.pdf` output. The unique output helper intentionally returns `*_去水印_2.pdf` when the base output exists, so using it for resume detection caused false misses and duplicate outputs.
- Regressions added/verified: `resume_helper_outputs_complete`, `background_guard_wrapped_run_process`, `pdf_ocr_resume_skips_existing_output`, `image_pdf_resume_skips_existing_output`, `process_single_file_resume_rename`, `audio_transcribe_resume_skips_existing_output`, `zip_resume_skips_existing_archive`, `pdf_split_resume_skips_complete_outputs`, `pdf_remove_wm_single_resume_existing_output`, `pdf_merge_resume_existing_output`.
- Validation: `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_resume.py tools\fx_zip_core.py tools\fx_pdf_ocr_task.py tools\fx_image_pdf_task.py tools\fx_audio_task.py` passed; `python full_debug_test.py` passed 198/198; `python smoke_test.py` passed 14/14.
## 2026-06-04 Batch watermark Archive failure sweep
- Goal:
  - Close a real-world batch watermark failure list from `d:\Users\CHEER\Desktop\Archive`, not just synthetic tests.
- What changed:
  - `tools/fx_watermark_core.py`
    - added `open_word_document_safely(...)` with normal-open + repair-open fallbacks;
    - damaged/unreadable Word errors now return `SKIP:damaged word source`.
  - `Fengxi_Toolbox.py`
    - preserve-original skip handling now also accepts damaged Word skip status.
  - `full_debug_test.py`
    - added `word_open_repair_fallback`;
    - added `watermark_damaged_word_preserves_original`.
- Real-file probe result:
  - Representative 7-file Archive replay finished `success`.
  - Counts: `success_count=4`, `skipped_count=3`, `failed_count=0`.
  - No `!失败文件清单.txt` generated.
  - Skipped-but-preserved cases:
    - protected PDF;
    - unreadable `.doc`;
    - unreadable `.docx`.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_watermark_core.py full_debug_test.py` passed.
  - `python smoke_test.py` previously passed 14/14 after this watermark path work remained green.
  - `python full_debug_test.py` passed `203/203`.
## 2026-06-04 批量水印未处理文件复制修复
- 问题：批量水印页的 `跳过文件复制到输出文件夹` 之前只覆盖文件名规则跳过，`txt`、`zip` 等未处理文件不会被复制。
- 修复：
  - 在 `Fengxi_Toolbox.py` 的 `_run_watermark_task(...)` 中补齐两类路径：
    - 收集阶段已被排除的文件，走 `unsupported_skipped_files` 兜底复制。
    - 主循环里产生 `SKIP:*` 的未处理文件，汇总到 `deferred_skipped_copy_items`，任务结束后统一走 `_copy_watermark_skipped_files(...)`。
  - 这样规则跳过、主循环跳过、未来可能的收集阶段跳过都统一走复制出口。
- 回归：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
  - `python smoke_test.py` 14/14 通过。
  - `python full_debug_test.py` 已重新全量执行；新增用例日志已确认 `notes.txt` 与 `data.zip` 被复制到结果目录，旧用例继续通过。
- 边界：
  - 未修改 `tools/fx_watermark_core.py`。
  - 未删除任何项目外文件。
## 2026-06-04 ZIP 压缩层级范围调试状态
- 已将 ZIP 控件从“最多压缩层数”升级为“压缩层级范围”。
- 兼容旧输入：`4` 等价 `1-4`；新输入 `2-4` 只压第 2 到第 4 层。
- 验证：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_zip_core.py full_debug_test.py` 通过。
  - ZIP 探针确认 `2-4` 对递归/智能混合都只生成第 2/3/4 层输出。
  - `python smoke_test.py` 14/14 通过。
  - `python full_debug_test.py` 204/204 通过。
- 边界：未删除任何项目外文件；未改水印渲染核心。

## 2026-06-04 ZIP depth range two-box UI validation
- Change: ZIP layer range is now entered with two boxes, start and end, with a fixed `-` label between them.
- Probe: start `2` + end `4` returns internal range `2-4`; start entry column is `1`, end entry column is `3`, dash label is visible.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_zip_core.py full_debug_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 205/205.

## 2026-06-05 Batch watermark type-skip options
- Request:
  - Add a way to choose file types that should not receive watermark in batch watermark mode.
  - At minimum support `PDF`, `Word`, `PPT`.
  - Keep old behavior unchanged when no type is selected.
  - If skipped-copy is enabled, type-skipped files must still be copied into the output/result folder.
- Implemented:
  - `Fengxi_Toolbox.py`
    - added `wm_skip_pdf_type_var`, `wm_skip_word_type_var`, `wm_skip_ppt_type_var`;
    - added visible `不添加水印的文件类型` controls under the watermark skip-rule block;
    - added loader helpers to normalize/filter type-skipped files before the watermark processing loop;
    - integrated type-skipped files into preview skip counting, `skipped_count`, logs, and skipped-copy output behavior;
    - wired the three type flags into watermark last-settings capture/apply/install.
  - `full_debug_test.py`
    - added `watermark_type_skip_options_visible`;
    - added `watermark_type_skip_pdf_copies_and_word_processes`;
    - strengthened existing watermark auto-memory regressions to include the new type flags.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 207/207.
- Important rule:
  - Do not change watermark rendering core for this feature.
  - With zero type checkboxes selected, runtime behavior must stay identical to the previous stable batch watermark flow.
## 2026-06-05 ZIP existing archive policy validation
- Goal:
  - Recursive ZIP and smart ZIP can choose how to handle same-name existing output archives.
- Behavior:
  - Default `reuse_existing`: valid planned output zip files are reused for breakpoint/resume and counted as skipped.
  - Optional `rebuild_existing`: planned output zip files are deleted and regenerated.
  - The rebuild policy is limited to planned output paths only; it must not delete unrelated archive files inside the source tree.
- Files changed:
  - `tools/fx_zip_core.py`
  - `Fengxi_Toolbox.py`
  - `full_debug_test.py`
- New/updated regressions:
  - `zip_archive_policy_control_visible`
  - `zip_rebuild_existing_archive_policy`
  - `last_settings_zip_save_restore`
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_zip_core.py full_debug_test.py` passed.
  - Lightweight ZIP probe passed: reuse kept `old.txt` inside an existing zip; rebuild removed it and wrote the fresh `a.txt` content.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 209/209.
## 2026-06-07 Word watermark first-page-only regression
- Fixed direct Word batch watermark scope for `page_range=first`.
- Correct behavior: only the first rendered page receives the watermark; normal subsequent pages remain clean.
- Key regression: `word_watermark_first_page_only_scope` exports a two-page DOCX to PDF and verifies first-page watermark visibility with second-page zero watermark pixels.
- Validation: py_compile passed; smoke_test 14/14; full_debug_test 210/210.

## 2026-06-09 Startup performance debug status
- Issue: opening the app often felt slow and startup/page loading lagged.
- Diagnosis: startup deferred layout refresh still used global `_tighten_layout(app)`, which walked all tab layout attributes and could initialize hidden lazy pages such as ZIP/PDF/audio. It also ended with a synchronous `update_idletasks()`, making CustomTkinter flush pending redraw/layout work in one visible freeze.
- Fix:
  - `_run_startup_layout_refresh(app)` now tightens only the current visible task tab, falling back to `DEFAULT_STARTUP_TAB`.
  - Startup layout refresh no longer forces `update_idletasks()`.
  - `patched_switch_tab(...)` in `tools/fx_startup_patches.py` keeps only one idle refresh after visible layout refresh.
  - Post-show layout refresh is staged through `after(...)`: shell layout, current-tab layout, then current-tab visible refresh. This avoids one long callback immediately after the window appears.
- Performance evidence from existing source probes:
  - Before fix, `startup_layout_refresh` samples reached about `11408 ms`.
  - After current-tab scoping, the source probe dropped to about `4000 ms`.
  - The final no-idle-flush patch is covered by regression; packaged manual timing should be checked from `%LOCALAPPDATA%\FengxiToolbox\performance.jsonl` after launch.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_startup_patches.py full_debug_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 216/216 twice after the no-idle and staged-refresh changes.
- Boundaries: no `fengxi_runtime.bin` change, no watermark/compression/OCR algorithm change, no project-external files deleted.

## 2026-06-20 PDF compression no-growth validation
- Fixed PDF compression enlarging already optimized/vector PDFs.
- Real-world diagnosis: user sample `01-热力学第一定律.pdf` was about 3.95 MB, while the previous standard output was about 12.44 MB. The file had only a few small JPEGs, so the bloat came from PDF object rewriting rather than image compression.
- Core behavior now chooses the smallest valid candidate below source size; if none is smaller, it keeps a same-size copy of the original instead of emitting a larger “compressed” PDF.
- PDF compression resume now requires matching sidecar metadata, preventing stale `_压缩.pdf` outputs from being reused after changing compression/image levels.
- Optional Ghostscript candidate support is present when a local `gswin64c.exe`/`gswin32c.exe`/`gs` is available; absence of Ghostscript is not an error.
- Validation: real user sample probe passed for multiple PDF/image compression levels, py_compile passed, smoke_test.py passed 14/14, full_debug_test.py passed 218/218.

## 2026-06-20 PDF compression sidecar cleanup and multi-candidate validation
- Issue: user saw "many unrelated files" after PDF compression. Diagnosis found hidden `.fx-compress.json` sidecars generated beside compressed PDFs by the previous resume-metadata implementation.
- Fix: PDF compression metadata now goes to a local cache file outside user output folders. New compression runs must not create hidden sidecar JSON files in result folders.
- Compatibility: legacy sidecars are still readable for resume matching, but they are not generated anymore.
- Safety boundary: do not delete old sidecars from external folders without explicit user approval.
- Compression strategy now follows a PDF24-like multi-candidate approach while staying Fengxi-specific:
  - PyMuPDF optimized cleanup candidate.
  - Optional pikepdf object-stream candidate when the library is available.
  - Existing PyMuPDF profile candidate.
  - Optional Ghostscript candidate when a local Ghostscript executable is available.
  - Keep only valid output smaller than source; otherwise keep original bytes to prevent growth.
- Real sample probe: `01-热力学第一定律.pdf` now avoids the old 12.44 MB growth and can shrink slightly from about 3.95 MB to about 3.94 MB depending on profile/candidate.
- Validation: `py_compile` passed, `smoke_test.py` passed 14/14, `full_debug_test.py` passed 220/220.

## 2026-06-21 PDF compression Ghostscript backend validation
- Issue: PDF compression was still weak on the user's physics chemistry PDF folder because the strongest Ghostscript candidate was not actually running on this machine.
- Diagnosis:
  - Local Ghostscript exists at `D:\texlive\2024\tlpkg\tlgs\bin\gswin64c.exe`.
  - TeX Live bundled Ghostscript needs `GS_LIB`; without it, it cannot find files such as `gs_init.ps` and `kfwin32.ps`.
  - The old finder only searched PATH and Program Files Ghostscript installs, so TeX Live Ghostscript was effectively invisible or unusable.
- Fix:
  - Added Ghostscript discovery for env overrides, PATH, Program Files, and TeX Live roots.
  - Added `GS_LIB` construction for TeX Live layouts with `Resource\Init`, `lib`, `kanji`, and font/CMap/CID resource directories.
  - Kept the no-growth guard and multi-candidate selection: Fengxi still only keeps a valid candidate smaller than the source.
- Real sample:
  - `01-热力学第一定律.pdf`: `3,947,231` bytes -> `3,609,246` bytes, status `SUCCESS:2:ghostscript`, about `8.56%` smaller.
  - A direct extreme probe reached `3,577,082` bytes, but strong mode remains conservative to protect readability.
- Regression:
  - `pdf_compress_ghostscript_texlive_env`
  - `pdf_compress_ghostscript_candidate_runs_when_available`
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_pdf_compress_core.py full_debug_test.py smoke_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 222/222.


## 2026-06-24 PDF web-style raster compression validation
- Added a new opt-in PDF compression profile: `图片化压缩`.
- This mode rasterizes PDF pages into JPEG images and rebuilds a new PDF, then lets the normal smallest-valid-candidate selection decide whether it wins.
- Existing non-raster profiles remain unchanged; the new mode does not replace normal optimized/pikepdf/pymupdf/ghostscript behavior.
- Safety rule preserved: if rasterization is not smaller, Fengxi still keeps a smaller non-raster candidate or the original bytes.
- UI/help text now warns that this mode is suitable for upload/share but may lose searchable/editable/vector structure.
- Validation:
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_pdf_compress_core.py full_debug_test.py` passed.
  - `python smoke_test.py` passed 14/14.
  - `python full_debug_test.py` passed 223/223.
