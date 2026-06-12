# 项目架构

## 2026-05-24 用户偏好存储模块化
- 新增 `tools/fx_user_prefs.py`，通过 `UserPrefsContext` 承接 `user_prefs.json` 相关基础存储 seam：
  - `load_user_prefs(...)`
  - `save_user_prefs(...)`
  - `get_saved_output_strategy(...)` / `save_output_strategy(...)`
  - `get_saved_remove_wm_mode(...)` / `save_remove_wm_mode(...)`
  - `get_saved_watermark_text(...)` / `save_watermark_text(...)`
  - `get_saved_watermark_filename_rule_settings(...)` / `save_watermark_filename_rule_settings(...)`
- `Fengxi_Toolbox.py` 保留 `_load_user_prefs(...)`、`_save_output_strategy(...)`、`_get_saved_remove_wm_mode(...)` 等同名薄包装，兼容现有 UI、测试和旧调用。
- 当前抽离边界：新模块只负责 JSON 存取与字段规范化；UI trace、控件读取、上次设置捕获/应用、预设捕获/应用仍留在主加载器层。
- 这样做的收益：
  - `user_prefs.json` schema 集中，后续新增“上次设置”或迁移配置版本时 locality 更好。
  - 现有 UI 入口不变，避免一次重构过大。
  - 测试可以独立覆盖偏好存储模块，不需要启动完整 app。
- 回归新增/确认：
  - `user_prefs_module_context`
  - `output_strategy_memory_save_load`
  - `remove_wm_mode_memory_save_load`
  - `last_settings_watermark_save_restore`
  - `watermark_filename_rule_memory_save`
  - `watermark_filename_rule_memory_load`
- 验证：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_user_prefs.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：147/147 通过。
- 边界：未修改 `fengxi_runtime.bin`，未改稳定区批量压缩/添加水印核心业务，未删除项目外文件。

## 2026-05-24 last_settings 存储 seam 下沉
- `tools/fx_user_prefs.py` 在基础偏好存储之上继续承接 `last_settings` 的纯存储能力：
  - `normalize_pref_category(...)`
  - `load_last_settings(...)`
  - `save_last_settings_entry(...)`
  - `get_active_last_settings_category(...)`
- `Fengxi_Toolbox.py` 的 `_load_last_settings(...)`、`_save_last_settings_entry(...)`、`_get_active_last_settings_category(...)` 现在是薄包装，继续保持原函数名和调用口径。
- 当前边界仍然克制：`_capture_preset_settings(...)`、`_apply_preset_settings(...)`、控件读写和页面切换仍在主加载器层，因为它们强依赖 app/UI 状态；本步只移动 JSON schema 和 active-category 选择逻辑。
- 回归新增/确认：
  - `user_prefs_last_settings_module_context`
  - `last_settings_watermark_save_restore`
  - `last_settings_ocr_save_restore`
  - `last_settings_pdf_compress_save_restore`
  - `last_settings_rename_save_restore`
- 备注：`normalize_pref_category(...)` 保持现有行为，只接受真实 category key 或 `PRESET_LABEL_TO_CATEGORY` 中的完整显示标签；不会新增 `"OCR"` 这类简写别名，避免悄悄改变用户配置 schema。
- 验证：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_user_prefs.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：148/148 通过。
- 边界：未修改 `fengxi_runtime.bin`，未改稳定区批量压缩/添加水印核心业务，未删除项目外文件。

## 2026-05-24 legacy presets 存储 helper 下沉
- `tools/fx_user_prefs.py` 继续承接旧 `presets` 存储 helper：
  - `make_preset_id(...)`
  - `load_presets(...)`
  - `save_presets(...)`
  - `save_preset_entry(...)`
  - `delete_preset_entry(...)`
  - `find_preset_entry(...)`
- `Fengxi_Toolbox.py` 的 `_make_preset_id(...)`、`_load_presets(...)`、`_save_presets(...)`、`_save_preset_entry(...)`、`_delete_preset_entry(...)`、`_find_preset_entry(...)` 均保留为薄包装。
- 重要边界：本步只是清理 legacy 存储 helper，不新增、不恢复任何专门“预设中心”页面或弹窗；`last_settings_no_dedicated_preset_center` 回归继续通过。
- 回归新增/确认：
  - `user_prefs_presets_module_context`
  - `last_settings_no_dedicated_preset_center`
  - `user_prefs_module_context`
  - `user_prefs_last_settings_module_context`
- 验证：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_user_prefs.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：149/149 通过。
- 边界：未修改 `fengxi_runtime.bin`，未改稳定区批量压缩/添加水印核心业务，未删除项目外文件。

## 2026-05-24 格式转换单文件 adapter seam
- `tools/fx_convert_task.py` 现在同时承接两类转换适配：
  - `ConvertFileContext` / `process_convert_file(...)`：单文件 `word2pdf`、`pdf2word`、`ppt2pdf` adapter seam。
  - `ConvertImgsToPdfCallbacks` / `run_convert_imgs_to_pdf_task_core(...)`：`convert + imgs2pdf` 多图合并 PDF 任务适配。
- `process_convert_file(...)` 只做窄适配：输出路径规划、复杂 PDF 跳过复制、日志与统一结果字典；真实转换仍通过 context 注入的 `convert_doc_to_pdf(...)`、`convert_pdf_to_word(...)`、`convert_ppt_to_pdf(...)` 执行。
- `Fengxi_Toolbox.py` 新增 `_patch_convert_file_adapter()`，在 `task_type == "convert"` 且模式为 `word2pdf` / `pdf2word` / `ppt2pdf` 时路由到 `process_convert_file(...)`；`imgs2pdf` 继续由 `_patch_convert_imgs_to_pdf_task()` 接管。
- 这一步的目的不是重写 Office COM / `pdf2docx`，而是先建立更窄、更可测的转换边界。后续若要替换后端、统一输出策略或强化失败报告，应优先扩展 `ConvertFileContext`，不要直接回到 runtime 分支里硬改。
- 回归新增/确认：
  - `convert_file_adapter_module_exports`
  - `pdf_to_word`
  - `word_to_pdf`
  - `ppt_to_pdf`
  - `imgs2pdf_workflow`
- 验证：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_convert_core.py tools\fx_convert_task.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：146/146 通过。
- 边界：未修改 `fengxi_runtime.bin`，未改稳定区批量压缩/添加水印核心业务，未删除项目外文件。

## 2026-05-24 格式转换核心与 imgs2pdf 任务适配
- 新增 `tools/fx_convert_core.py`，集中承接 `convert` 页面纯规则：
  - `CONVERT_MODE_SPECS`
  - `normalize_convert_mode(...)`
  - `describe_convert_mode(...)`
  - `collect_convert_files(...)`
  - `plan_convert_output_path(...)`
- 新增 `tools/fx_convert_task.py`，最初承接 `convert + imgs2pdf` 的任务适配：
  - `ConvertImgsToPdfCallbacks`
  - `run_convert_imgs_to_pdf_task_core(...)`
- `Fengxi_Toolbox.py` 现在通过 `_get_convert_mode(...)`、`_get_convert_preview_detail(...)`、`_collect_convert_files(...)` 使用 `fx_convert_core`；开始前预览、队列描述和文件统计不再散落硬编码转换模式。
- `Fengxi_Toolbox.py` 新增 `_run_convert_imgs_to_pdf_task(...)` 和 `_patch_convert_imgs_to_pdf_task()`，仅在 `task_type == "convert"` 且模式为 `imgs2pdf` 时路由到 `fx_convert_task`；该 adapter 负责进度、日志、失败报告、输出根目录和结构化 `task_result`。
- `word2pdf`、`pdf2word`、`ppt2pdf` 仍保留原 runtime 路径，不在本轮迁移；后续若继续拆，应先为 Office COM / `pdf2docx` 建更窄的 adapter seam。
- 验证：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_convert_core.py tools\fx_convert_task.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：145/145 通过。
- 边界：未修改 `fengxi_runtime.bin`，未改稳定区批量压缩/添加水印核心业务，未删除项目外文件。

## 2026-05-24 属性隐私核心模块化
- 新增 `tools/fx_meta_core.py`，承接属性隐私相关 helper：
  - `modify_file_timestamp(...)`
  - `modify_pdf_author(...)`
  - `modify_office_meta(...)`
  - `build_meta_output_path(...)`
  - `process_meta_file(...)`
- `Fengxi_Toolbox.py` 保留 `modify_file_timestamp(...)`、`modify_office_meta(...)`、`modify_pdf_author(...)` 同名薄包装，并回写 `_ns`，兼容运行时和旧测试入口。
- 新增 `_patch_meta_core()`，在 `task_type == "meta"` 时把真实 `process_single_file(...)` 路由到 `tools.fx_meta_core.process_meta_file(...)`；外层 wrapper 继承 `__fx_file_manager_core_patch__` 标记，避免遮住文件管家模块化回归。
- 当前语义保持运行时一致：时间修改为复制后设置 atime/mtime；PDF 作者写入保留页面并更新 `/Author` 与 `/Creator`；Office 作者 helper 仍使用外部传入的 Word/PPT COM app；`.doc/.docx/.ppt/.pptx` 在 `process_single_file` 路径保持原 runtime 的空处理语义。
- 验证：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_meta_core.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：141/141 通过。
- 边界：未修改 `fengxi_runtime.bin`，未改批量压缩/添加水印核心业务，未删除项目外文件。

## 2026-05-24 音频任务清尾收口
- `tools/fx_audio_task.py` 已成为音频任务唯一任务层实现：负责文件收集、输出路径、逐文件处理、并行调度和统一 task_result 回写。
- `Fengxi_Toolbox.py` 里音频相关 wrapper 只保留薄包装，不应再保留 `return run_audio_task_core(...)` 后面的旧实现死代码。
- 2026-05-24 的收尾确认：主文件里已删除那段重复的音频 legacy implementation，`audio` 继续走新模块 seam。
- 这次顺手把 OCR workflow 测试稳定化：`full_debug_test.py` 的 OCR 三段工作流改为本地稳定假引擎，不再依赖 `rapidocr` 模型下载波动；产品 OCR 代码未改。
- 验证：`python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过，`python smoke_test.py` 14/14 通过，`python full_debug_test.py` 142/142 通过。
- 边界：未改 `fengxi_runtime.bin`，未改 OCR 引擎实现，未删除项目外文件。

## 2026-05-24 文件管家去重任务适配层补齐
- `tools/fx_file_manager_task.py` 新增 `run_file_dedup_task_core(...)`，把 `file + dedup` 的 app 侧输入收集、进度跟踪、日志、输出根目录和结构化 task_result 收口，从核心去重算法里再剥离一层。
- `tools/fx_file_manager_core.py` 继续只负责 MD5 去重核心语义：保留首个文件、删除后续重复文件、返回统计结果。
- `Fengxi_Toolbox.py` 的 `_run_file_dedup_task(...)` 现在只是 adapter；`_patch_file_dedup_core_task()` 仍在 `task_type == "file"` 且 `file_mode_var == "dedup"` 时接管真实 `run_process(...)` 工作流。
- `file_dedup` 回归现在追踪 `_run_file_dedup_task_core` 调用，`file_manager_task_module_exports` 则验证任务适配层能独立驱动去重核心。
- 验证：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_file_manager_core.py tools\fx_file_manager_task.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：139/139 通过。
- 边界：未改 `fengxi_runtime.bin`，未动稳定区批量压缩/添加水印核心业务，未删除项目外文件。

## 2026-05-24 文件管家去重核心路由
- `tools/fx_file_manager_core.py` 已承接 `deduplicate_files(...)` 与 `run_file_dedup_task(...)`；`Fengxi_Toolbox.py` 新增 `_patch_file_dedup_core_task()`，在 `task_type == "file"` 且 `file_mode_var == "dedup"` 时直接路由到 `_run_file_dedup_task(...)`。
- 去重仍保持稳定单线程：全局 MD5 比对、保留首个文件、删除后续重复文件，不并行、不走 `process_single_file(...)`。
- `_run_file_dedup_task(...)` 负责连接 app 输入收集、进度状态、日志、输出路径、结构化 task_result 和失败/停止/跳过收口；算法本体仍在 `tools/fx_file_manager_core.py`。
- 回归 `file_dedup` 现在会追踪 `mod._file_core_run_file_dedup_task` 调用次数，确认真实 `app.run_process(str(folder), "file")` 已命中新核心，而不是退回原 runtime 分支。
- 验证：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_file_manager_core.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：138/138 通过。
- 边界：未修改 `fengxi_runtime.bin`，未改稳定区批量压缩/添加水印核心业务，未删除项目外文件。

## 2026-05-23 文件管家重命名核心模块化
- 新增 `tools/fx_file_manager_core.py`，把文件管家的批量重命名规则解析、输出路径规划和单文件复制改名执行从主加载器中拆出。
- 新模块当前导出：
  - `FileRenameSpec`
  - `normalize_file_rename_spec(...)`
  - `rename_file_name(...)`
  - `plan_renamed_output_path(...)`
  - `apply_rename_to_file(...)`
  - `deduplicate_files(...)`
- `Fengxi_Toolbox.py` 新增 `_patch_file_manager_core()`，仅在 `task_type == "file"` 且子模式为 `rename` 时把 `process_single_file(...)` 路由到新模块。
- `dedup` 在 2026-05-24 已完成后续接管，真实 UI 工作流现在通过加载器专用 `run_process` patch 路由到新模块去重核心。
- 验证：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_file_manager_core.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：136/136 通过。
- 边界：未修改 `fengxi_runtime.bin`，未改 `dedup` UI 工作流，未删除项目外文件。

## 2026-05-23 PDF 压缩核心模块化
- 新增 `tools/fx_pdf_compress_core.py`，把 PDF 压缩档位、图片重压缩/降采样、输出命名和单文件压缩 implementation 从主加载器拆出。
- 新模块当前导出：
  - `PDF_COMPRESS_LEVELS`
  - `PDF_IMAGE_COMPRESS_LEVELS`
  - `build_pdf_compress_output_path(...)`
  - `compress_pdf_file(...)`
- `Fengxi_Toolbox.py` 继续保留 `_build_pdf_compress_output_path(...)` 和 `compress_pdf_file(...)` 作为薄包装，兼容现有 UI、smoke/full debug 测试和外部调用。
- `PDF 压缩` 的任务编排仍留在加载器层：输入收集、输出策略、并行执行、进度条、失败报告、删除源文件和结构化任务结果都不下沉。
- 这一步的 seam 目标是让压缩算法与 UI/队列调度分离；后续调整压缩质量、图片阈值或保存参数时优先改 `tools/fx_pdf_compress_core.py`。
- 验证：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_pdf_compress_core.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：133/133 通过。
- 边界：未修改 `fengxi_runtime.bin`，未触碰批量压缩/添加水印用户可见行为，未删除项目外文件。

## 2026-05-23 OCR 任务编排模块化
- 新增 `tools/fx_pdf_ocr_task.py`，把 OCR 搜索版 PDF 的任务编排从主加载器中抽离出来，形成比纯引擎更深的一层 seam。
- 新模块承接的职责：
  - 任务级 `PdfOcrTaskOptions` / `PdfOcrTaskCallbacks`
  - 输出路径生成与 `_ocr_compare_reports` 路径生成
  - 逐文件 OCR 循环
  - 对比报告触发与失败容错
  - 页级进度回调与停止检查
  - 文件级成功/失败/完成回调
- `tools/fx_pdf_ocr.py` 继续只管 OCR 引擎、后端探测、预处理、评分和比较报告内容，不再承担主任务循环。
- `Fengxi_Toolbox.py` 中 `_run_pdf_ocr_task(...)` 现在只做 adapter：读取 UI 变量、输出策略、progress tracker、失败报告和结构化任务结果收口。
- 这样做的收益：
  - OCR 引擎、OCR 任务和 UI 各自的 interface 更窄。
  - 以后改后端选择、compare report 或输出策略时，locality 更好。
  - 测试可以分别覆盖引擎层与任务层，而不是只能碰一个很厚的函数。

## 2026-05-23 稳定核心模块化例外
- 本轮用户明确授权在“模块拆分”目的下触碰稳定区 `批量压缩` 和 `添加水印` 核心逻辑；目标是把业务实现从主加载器抽成独立模块，而不是改变功能行为。
- 新增 `tools/fx_watermark_core.py`，集中承接：
  - `create_watermark_packet(...)`
  - `add_watermark_to_pdf(...)`
  - `add_watermark_to_word(...)`
- `Fengxi_Toolbox.py` 继续保留同名薄包装，负责注入项目已有的字体解析、Word 字体兼容、`_DisableWin32ComGenCache()` 等 adapter；运行时 `_ns` 里也继续暴露原函数名，兼容旧调用点。
- 新增 `tools/fx_zip_core.py`，集中承接 ZIP 计划与执行：
  - `plan_zip_archives(...)`
  - `estimate_zip_progress_units(...)`
  - `run_zip_task(...)`
- `zip` 任务现在由 `_patch_zip_core_task()` 接管到 `fx_zip_core.run_zip_task(...)`，同时继续接入现有进度追踪、日志、结构化任务结果和历史记录口径。
- ZIP 语义保持现有用户可见行为：
  - `total`：根目录生成 `<folder>_Backup.zip`。
  - `recursive`：根目录和各级子目录分别生成 zip。
  - `smart_recursive`：含文件的目录直接打包并停止向下；只有子目录且无文件时继续递归。
  - 单文件输入：同目录生成 `<原文件名>_Backup.zip`。
- 这次拆分形成两个更深的 Module seam：水印核心和 ZIP 核心以后可以独立测试、独立定位，但 UI/偏好/队列/历史仍留在加载器层协调。
- 验证：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_watermark_core.py tools\fx_zip_core.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：131/131 通过。
- 边界：
  - 未修改 `fengxi_runtime.bin`。
  - 没有删除项目外文件。
  - 本轮虽然触碰稳定区，但仅为模块化搬迁和包装兼容；后续仍默认不随意改 `批量压缩` / `添加水印` 行为。

## 2026-05-23 启动性能 profiling 与补丁模块拆分一期
- 新增 `tools/fx_performance.py`，把启动/切页/首次加载的轻量性能样本收口成 JSONL 记录，日志写入用户偏好目录下的 `performance.jsonl`，不落源码目录。
- 当前记录的关键事件：
  - `runtime_load`：加载 `fengxi_runtime.bin` 的耗时。
  - `lazy_tab_init`：某个懒加载页面首次初始化的耗时。
  - `switch_tab`：切换功能页的耗时。
  - `startup_show_ready`：主窗口显示 ready 的耗时。
  - `startup_total`：从启动进入到窗口 ready 的总耗时。
- 性能记录器带自动裁剪，保持最近一小段样本，避免性能文件无限增长。
- 新增 `tools/fx_runtime_patches.py`，把通用补丁包装器从 `Fengxi_Toolbox.py` 中拆出，作为后续继续拆补丁层的安全 seam。
- 主加载器现在通过导入模块方式复用 `wrap_callable(...)`，但业务补丁仍然留在 `Fengxi_Toolbox.py`，没有碰 `fengxi_runtime.bin`。
- 诊断包额外携带最近性能样本，便于以后排查“变慢了”到底慢在哪一段。
- 维护原则：
  - 批量压缩和添加水印核心业务逻辑继续不动。
  - 性能记录失败必须静默，不影响启动。
  - 后续继续拆补丁层时，优先迁移工具性函数，不先碰业务流程。
- 2026-05-23 后续推进：
  - 新增 `tools/fx_startup_patches.py`，把 `_patch_startup_performance()` 的核心 implementation 移出主加载器。
  - 新模块通过 `StartupPatchContext` 接收 app class、CTk class、懒加载规格、debug/performance callbacks 和 UI 刷新 callbacks，不直接 import `Fengxi_Toolbox.py`。
  - `Fengxi_Toolbox.py` 中的 `_patch_startup_performance()` 现在只负责装配 context 并调用 `install_startup_performance_patch(...)`。
  - 这一步让启动隐藏窗口、懒加载页签、切页刷新、help/donate 内联重定向、切页性能记录集中在独立 Module 中，后续继续拆补丁层时可以沿用这种 context seam。
- 2026-05-23 任务历史导出继续模块化：
  - 新增 `tools/fx_task_history_exports.py`，把任务历史导出文件名、结构化结果 JSON 导出、日志 TXT 导出、Markdown 报告、诊断包 ZIP、诊断脱敏和最近历史快照集中到独立模块。
  - 新模块通过 `TaskHistoryExportContext` 接收主加载器能力，包括路径归一化、任务结果写出、功能名/状态文案、失败分类、历史加载、环境探测、项目根目录与用户目录脱敏范围。
  - `Fengxi_Toolbox.py` 保留原 `_build_task_history_*` / `_export_task_history_*` / `_diagnostic_*` 名称作为薄包装，任务历史详情窗口和现有测试入口不用改调用方式。
  - 诊断包的环境探测仍留在主加载器，因为它依赖本机 ffmpeg、OCR 后端、Office COM 和性能日志；诊断包组装与脱敏已下沉到模块，形成更清晰的 seam。
  - 新增 `task_history_exports_module_context` 回归，直接用模块 context 构造报告与文件名，确认模块可独立测试。
  - 验证：`python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py tools\fx_task_history_exports.py tools\fx_performance.py tools\fx_runtime_patches.py tools\fx_startup_patches.py`、真实导入探针、`python smoke_test.py` 14/14、`python full_debug_test.py` 128/128。
  - 边界：未修改 `fengxi_runtime.bin`，未改稳定区 `批量压缩` / `添加水印` 核心业务。
- 2026-05-23 队列历史纯逻辑模块化：
  - 新增 `tools/fx_queue_history.py`，把队列历史读写、90 天自动清理、最大条数裁剪、运行态字段清理、状态文案、搜索 blob 和筛选逻辑集中到独立模块。
  - 新模块通过 `QueueHistoryContext` 接收历史文件路径、保留天数、最大条数、状态/任务/失败筛选映射、失败分类函数和任务结果快照函数。
  - `Fengxi_Toolbox.py` 保留 `_load_queue_history`、`_save_queue_history`、`_filter_queue_history_entries` 等原函数名作为薄包装；队列 UI、历史窗口、失败重试与诊断包仍按原入口调用。
  - 新增 `queue_history_module_context` 回归，直接验证模块级读写裁剪、运行态字段清理、状态文案、搜索 blob、失败分类筛选和时间戳读取。
  - 验证：`python -m py_compile Fengxi_Toolbox.py full_debug_test.py tools\fx_queue_history.py`、真实导入探针、`python smoke_test.py` 14/14、`python full_debug_test.py` 129/129。
  - 边界：未修改 `fengxi_runtime.bin`，未改稳定区 `批量压缩` / `添加水印` 核心业务。

## 2026-05-23 功能注册表一期
- 新增 `FEATURE_REGISTRY`，把各功能的元数据集中到 `Fengxi_Toolbox.py` 加载器层，作为后续进度、历史、失败重试、输出策略、功能入口和调试报告的统一描述来源。
- 当前注册的任务类型：
  - `watermark`：批量水印，稳定核心。
  - `remove_wm`：去除水印。
  - `convert`：格式转换。
  - `audio`：音频工具。
  - `zip`：批量压缩，稳定核心。
  - `pdf`：PDF 工具。
  - `image`：图片工厂。
  - `meta`：属性隐私。
  - `file`：文件管家。
- 注册表字段当前覆盖：
  - `label`：统一功能名。
  - `icon`：功能图标语义名。
  - `page`：页面/功能入口名。
  - `input`：是否支持文件、文件夹、拖拽。
  - `output_strategy`：是否支持输出策略、是否强制结果文件夹。
  - `parallel`：安全并行、强制单线程、子模式例外说明。
  - `preview_modes`：开始前任务预览的模式名。
  - `risk_flags`：覆盖、删除、去重等风险标记。
  - `stable_core`：稳定区标记，当前用于明确批量水印和批量压缩核心不轻易动。
- 派生策略现在统一从注册表生成，不再保留第二套硬编码来源：
  - `QUEUE_TASK_LABELS`
  - `OUTPUT_STRATEGY_SUPPORTED_TASKS`
  - `OUTPUT_STRATEGY_FORCE_RESULT_FOLDER_TASKS`
  - `PARALLEL_SAFE_TASKS`
  - `PARALLEL_FORCED_SINGLE_TASKS`
  - `PARALLEL_FORCED_SINGLE_DETAILS`
  - `PARALLEL_SUPPORTED_HINTS`
- 新增辅助函数：
  - `_get_feature_spec(...)`
  - `_get_feature_label(...)`
  - `_get_feature_preview_mode_label(...)`
  - `_feature_supports_output_strategy(...)`
  - `_feature_forces_result_folder(...)`
  - `_build_parallel_sets_from_registry(...)`
  - `_get_feature_registry_errors(...)`
- 已替换的调用点：
  - 开始前任务预览的功能名和模式名。
  - 输出策略支持范围和强制结果文件夹判断。
  - 并行状态说明和强制单线程提示。
  - 历史记录详情、筛选和展示里的功能名。
- 维护原则：
  - 后续新增功能或子模式，优先补 `FEATURE_REGISTRY`，再让 UI/队列/历史/进度从注册表读取。
  - 不要重新散落新增 `QUEUE_TASK_LABELS.get(...)`、手写并行集合或手写输出策略集合。
  - 注册表仍在加载器层，不改 `fengxi_runtime.bin`。
  - 本轮未改 `批量压缩` 与 `添加水印` 的核心业务逻辑。

## 2026-05-23 一键诊断包
- 任务历史详情窗口新增 `诊断包` 按钮，和 `导出结果`、`导出报告`、`打开位置`、`导出日志`、`复制详情` 并列。
- 实现仍在 `Fengxi_Toolbox.py` 加载器层，不修改 `fengxi_runtime.bin`。
- 核心函数：
  - `_build_task_history_diagnostic_filename(entry)` 生成安全 zip 文件名。
  - `_export_task_history_diagnostic_package(entry, output_path)` 生成诊断 zip。
  - `_prompt_export_task_history_diagnostic_package(app, entry, output_path=None)` 负责保存对话框、消息框和日志提示。
  - `_probe_diagnostic_environment()` 探测软件版本、Python/系统、ffmpeg、OCR 后端、Word/PowerPoint COM 可用性。
  - `_redact_diagnostic_payload(...)` / `_redact_diagnostic_text(...)` 对路径做基础脱敏。
- 诊断包内容固定为文本/JSON/Markdown，不复制原始 PDF、Word、图片、音视频等输入文件：
  - `README.md`：诊断包说明、当前任务摘要、环境摘要。
  - `task_history_entry.json`：当前历史条目快照。
  - `task_result.json`：结构化任务结果。
  - `task_report.md`：复用现有任务报告口径。
  - `task_log.txt`：复用现有任务日志导出口径。
  - `environment.json`：版本、系统、Python、ffmpeg、OCR、Office COM 探测。
  - `recent_history.json`：最近历史摘要，便于判断是否连续失败。
- 路径脱敏规则：
  - 当前项目根目录替换为 `<PROJECT_ROOT>`。
  - 用户主目录替换为 `<USER_HOME>`。
  - 该脱敏只用于诊断包内容，不改真实历史记录与任务结果。
- 回归覆盖：
  - `task_history_diagnostic_filename`
  - `task_history_diagnostic_export_package`
  - `task_history_diagnostic_export_empty`
- 本次未改稳定区 `批量压缩` / `添加水印` 核心业务逻辑。

## 2026-05-22 使用教程内嵌示例流程
- `使用教程` 继续保持应用内右侧滚动页，不再打开外部 README 或弹窗。
- `INLINE_HELP_SECTIONS` 已重写为按用户任务场景组织的内嵌说明，重点覆盖：
  - 三步上手：拖入/选择文件或文件夹、选择功能、开始前任务预览、真进度文字、上次设置自动记忆。
  - 输出与安全确认：原目录新文件、覆盖原文件、【处理完成】结果文件夹、删除源文件/去重等高风险提醒。
  - 任务队列与历史记录：加入队列、历史筛选、失败重试、成功回放、打开输出位置、导出结果/日志/报告、过期历史自动清理。
  - PDF OCR：auto 后端、图像增强、质量回退、透明文字层、对比报告和常见失败原因。
  - PDF 压缩/合并/拆分/加密、批量水印、去除水印、图片工厂、格式转换/音频、属性隐私/文件管家、批量压缩、性能进度排障。
- 帮助页构建函数仍是 `_build_inline_help_page(app, help_tab)`，只是替换内容结构，不改变业务执行路径。
- 新增回归 `inline_help_workflow_sections`，要求帮助页必须覆盖 OCR 图像增强/质量回退、任务队列历史、开始前预览、输出策略、覆盖原文件、保守去水印和批量并行等关键词。
- 本次未改 `fengxi_runtime.bin`，未改稳定区 `批量压缩` / `添加水印` 核心业务逻辑。

## 2026-05-22 开始前任务预览确认
- 人工点击“开始处理”前会先生成任务预览，展示功能、子模式、输入类型、预计处理文件数、预计跳过数、输出策略和覆盖/删除源文件风险。
- 实现位置仍在 `Fengxi_Toolbox.py` 加载器层：
  - `_build_start_preview(...)` 负责统计预览对象。
  - `_format_start_preview_message(...)` 负责生成确认文案。
  - `_confirm_start_preview(...)` 负责日志提示与确认弹窗。
  - `_patch_start_preview_confirmation()` 只包装人工 `on_start_click`。
- 队列后台执行通过 `_fx_start_via_queue` 跳过确认弹窗，避免队列执行被人工确认框卡住。
- 预览统计尽量复用当前功能的收集逻辑：
  - PDF 仅统计 `.pdf`。
  - 图片转 PDF / 多图合并 PDF 复用 `_collect_image_to_pdf_files(...)`。
  - 音频复用 `_collect_audio_files(...)`。
  - 水印会额外估算“按文件名规则跳过”的数量，但不提前改动水印运行时规则。
- 风险提示覆盖输出策略覆盖原文件、去水印覆盖原文件、PDF/图片/音频/水印删除源文件、文件去重等高风险选项。
- 本次仍未改 `fengxi_runtime.bin`，未改稳定区 `批量压缩` / `添加水印` 核心业务逻辑。

## 2026-05-22 赞助作者内联页
- `赞助作者` 不再走弹窗/独立窗口，侧栏按钮和旧的 `show_donate_window` 统一重定向到右侧内容页 `赞助作者`。
- 赞助页复用主内容区的内联页面模式，和“使用教程”保持同一种右侧信息页表达，不打断当前工作流。
- 页面内容直接内嵌一条赞助文案和 `assets/donate_qr.png` 二维码图片，二维码缺失时会显示可读替代文本。
- 进入赞助页时会把开始按钮切为“查看赞助作者中”，并把 `current_task` 置为 `donate`，避免误触发任务执行。
- 本次只改 `Fengxi_Toolbox.py` 加载器/UI 入口层和回归测试，不改 `fengxi_runtime.bin`，也不影响 `批量压缩` / `添加水印` 的稳定业务逻辑。
- 验证：`python -m py_compile Fengxi_Toolbox.py full_debug_test.py`、`python smoke_test.py`、`python full_debug_test.py` 通过，完整自检 `108/108`。

## 2026-05-22 批量并行提速口径
- 不删除原有 `enable_multithread` / 运行时 `ThreadPoolExecutor` 能力，因为嵌入式运行时仍会在部分多文件工作流中使用它。
- UI 文案不再称为“极速模式（多线程）”，统一改为 `批量并行（部分生效）`，避免用户误以为所有功能都会提速。
- 底部会按当前功能显示并行状态提示：
  - 可提速：批量水印、多文件 PDF 拆分/加密、PDF 压缩、图片格式转换/压缩、图片逐张转 PDF、音视频逐文件转换、文件重命名、普通文件时间修改。
  - 稳定单线程：去水印、Office/PDF 转换、批量压缩、PDF 合并、PDF OCR、多图合并 PDF、文件去重。
  - 单文件输入会临时关闭并行，避免 UI 日志线程冲突。
- 这层只调整加载器 UI/提示与回归测试，不改 `fengxi_runtime.bin`，也不改变 `批量压缩`、`添加水印` 的核心业务逻辑。
- 后续如继续做性能优化，优先做任务级调度/分阶段并行，而不是把所有功能强行塞进多线程；Office COM、OCR、PDF 重构、文件覆盖类任务需要继续保守。
- 2026-05-22 后续增强：加载器层自定义工作流已给 `PDF 压缩` 和 `图片转 PDF（逐张生成）` 接入真正的 `ThreadPoolExecutor` 并行处理；仅在 `enable_multithread` 开启且文件数大于 1 时启用，线程数上限为 `PARALLEL_MAX_WORKERS = 4`。工作线程只做文件处理，日志、进度、任务结果仍在主流程汇总，避免 Tk UI 跨线程写入风险。

## 2026-05-22 上次设置自动记忆
- 用户明确不要独立 `预设中心`，当前改为“各功能自动记住上次设置”，不再提供单独的预设管理窗口或入口。
- 保存与恢复发生在页面初始化、开始执行前和关闭前，用户不需要额外点击保存。
- 实现仍限定在 `Fengxi_Toolbox.py` 加载器/UI/偏好层，不修改 `fengxi_runtime.bin`。
- 上次设置存储在用户本地偏好 JSON 的 `last_settings` / `last_settings_active` 字段中，不写入项目源码目录。
- 当前支持四类上次设置：
  - `watermark`：批量水印文本、字体、页范围、防重/覆盖、跳过规则、字号、透明度、角度、输出策略。
  - `ocr`：PDF OCR 模式、后端、识别配置、提取模式、模型目录、方向纠正、对比报告、密码/删除源文件兼容项。
  - `pdf_compress`：PDF 压缩程度、图片压缩程度、密码/删除源文件兼容项。
  - `rename`：文件重命名模式、前缀、后缀、查找、替换、裁剪头尾字符数。
- 应用 OCR 或 PDF 压缩上次设置时，会通过 `app._fx_select_pdf_mode` 切换 PDF 右侧详情面板，避免只改变量但 UI 面板不同步。
- 水印上次设置只保存/恢复 UI 和偏好层参数，不改 `create_watermark_packet`、`add_watermark_to_pdf`、`add_watermark_to_word` 等核心加水印逻辑。
- 回归覆盖：
  - `last_settings_no_dedicated_preset_center`
  - `last_settings_watermark_save_restore`
  - `last_settings_ocr_save_restore`
  - `last_settings_pdf_compress_save_restore`
  - `last_settings_rename_save_restore`

## 2026-05-21 统一任务结果模型
- 本轮开始收口任务执行的统一结果语义，目标是为后续的真进度条、历史记录、失败重试、结果导出提供稳定基础。
- 实现仍限定在 `Fengxi_Toolbox.py` 加载器层，不修改 `fengxi_runtime.bin`。
- 当前新增统一结果对象，实例级挂载在 `app._fx_last_task_result`，基础字段包括：
  - `task_type`
  - `input`
  - `status`
  - `success`
  - `stopped`
  - `skipped`
  - `message`
  - `detail`
  - `error`
  - `outputs`
  - `output_root`
  - `failed_items`
  - `processed_count`
  - `success_count`
  - `failed_count`
  - `skipped_count`
  - `started_at`
  - `finished_at`
  - `duration_seconds`
- 当前接入策略：
  - `run_process()` 最外层补丁在每次任务开始时创建结果对象。
  - 自定义工作流优先主动写入结果：
    - `remove_wm`
    - `pdf -> ocr`
    - `pdf -> compress`
    - `image -> to_pdf / merge_pdf`
    - 单文件 `zip` 包装路径
  - 若底层流程没有主动完成结果对象，则在 `run_process()` 和队列 worker 收尾时通过输入、日志、返回值、停止状态做统一推断。
- 当前队列/历史调整：
  - 队列任务执行后优先消费 `task_result`，不再只靠日志关键词猜测成功失败。
  - 历史记录会保存裁剪后的 `task_result` 快照，便于后续做结果导出与更稳定的失败重试。
  - `task_result` 必须和当前 `task_type + input` 匹配后才可被队列条目采用，避免串到上一个任务的结果。
- 当前保留的兼容策略：
  - 旧的日志关键词失败判断仍保留为兜底，不与结构化结果硬冲突。
  - 未完全接入统一结果对象的运行时原生分支，暂时仍允许通过推断补齐状态。
- 后续扩展方向：
  - 把运行时原生批处理分支也逐步映射到统一结果对象。
  - 基于 `task_result` 增加 JSON 导出、历史详情弹窗、失败原因筛选与真正的任务报告。

## 2026-05-21 任务历史筛选与回放
- 在统一任务结果模型之上，任务历史窗口进一步收口为“可检索 + 可回放”的单一入口。
- 2026-05-22 起，任务历史增加自动过期清理：加载、追加、保存历史时都会统一清理超出 `QUEUE_HISTORY_RETENTION_DAYS = 90` 天的记录，并继续保留 `QUEUE_HISTORY_LIMIT = 80` 的数量上限。
- 过期判断优先使用历史条目的 `finished_at`，其次 `created_at` / `started_at`，再尝试结构化 `task_result` 时间；缺少时间戳的旧记录暂时保留，避免误删用户仍可能需要的历史。
- 当前历史层新增三类筛选条件：
  - 状态筛选：全部状态、仅完成、仅失败、仅跳过、仅停止。
  - 功能筛选：按 `QUEUE_TASK_LABELS` 对应的功能类型过滤。
  - 关键词筛选：可按路径、错误、输出位置、结果信息做模糊检索。
- 当前历史条目展示更偏结构化结果：
  - 会显示功能名称、输入路径、完成时间、耗时、输出位置、错误原因。
  - 成功历史也支持“回放”重新加入队列，失败历史保留“重试”语义。
- 当前详情层已形成三种导出能力：
  - `导出结果`：导出结构化 `task_result` JSON。
  - `导出日志`：导出任务日志文本快照。
  - `导出报告`：导出 Markdown 任务报告，统一汇总基本信息、结果统计、输出位置、失败分类、失败项、关键日志与结构化结果摘要。
- `导出报告` 复用统一结果模型与 `_classify_failure_reason(...)`，避免历史详情、筛选、导出三套口径分裂。
- 这层实现仍限定在 `Fengxi_Toolbox.py` 加载器层，历史过滤态通过实例变量保存，不侵入 `fengxi_runtime.bin`。
- 回归已经补到 `full_debug_test.py`，覆盖筛选、重置、回放、失败重试，以及结果/日志/报告导出链路。

## 2026-05-20 任务队列 / 历史记录 / 失败重试
- 本轮新增“任务队列 + 历史记录 + 失败重试”，实现仍限定在 `Fengxi_Toolbox.py` 加载器层，不修改 `fengxi_runtime.bin`。
- UI 入口：
  - 底部操作区新增 `加入队列` 与 `队列历史` 两个按钮。
  - `加入队列` 会把当前输入路径、当前功能类型、以及已初始化页面上的参数变量/输入框内容保存为任务快照。
  - `队列历史` 打开独立窗口，左侧显示等待执行队列，右侧显示历史记录与失败重试。
- 调度策略：
  - 队列只做顺序执行，不做并发，避免 Office COM、OCR、PDF 去水印等重任务互相污染。
  - 每个队列任务执行前会恢复保存的参数快照，再调用现有 `run_process(input, task_type)`。
  - 这样用户可以先配置多个不同功能任务入队，再统一执行。
- 历史与重试：
  - 历史记录保存到用户配置目录 `FengxiToolbox/queue_history.json`，不写入项目源码目录。
  - 历史最多保留 `QUEUE_HISTORY_LIMIT = 80` 条。
  - 失败判断目前基于异常捕获、用户停止状态、以及任务日志中的错误关键词。
  - 失败重试会把失败历史的原始快照重新加入等待队列，避免只重试路径却丢失当时配置。
- 测试隔离：
  - `full_debug_test.py` 会临时替换 `_get_user_pref_root()` 到本轮 `tmp_full_debug_*/user_prefs`，避免队列回归污染真实用户历史。
- 维护边界：
  - 后续若增强队列，不要改稳定业务区的 `批量压缩` / `添加水印` 核心逻辑。
  - 若要支持并发队列，必须先重新评估 Office COM、OCR、去水印、文件覆盖等副作用风险。
  - 若要提高失败判断准确度，优先让各自工作流返回结构化结果，而不是继续扩大日志关键词列表。

## 2026-05-20 自检与快关测试架构稳健化
- 本轮未改 `批量压缩` 与 `添加水印` 的业务实现，只在加载器外围、测试脚本和发布链路做工程可靠性优化。
- `Fengxi_Toolbox.py` 的 `_request_fast_close(app)` 保持真实应用快速关闭逻辑不变：先 `withdraw()` 隐藏窗口，再异步 `quit()/destroy()`，必要时强制退出。
- 为避免自动化测试中的快关探针触发真实 `os._exit(0)` 导致测试进程提前结束，新增实例级开关 `_fx_disable_fast_close_force_exit`：
  - 默认不存在或为 `False`，真实应用行为不变。
  - `full_debug_test.py` 会在测试 app 和 close probe 上设置为 `True`，只关闭“兜底强退定时器”，不关闭快关本身。
- `smoke_test.py` 与 `full_debug_test.py` 现在统一使用项目根目录内的 `tmp_*` 临时目录，并在全部通过后自动删除本轮新建目录。
- 测试输出现在对每条 JSON 记录使用 `flush=True`，避免长测试或异常退出时丢失关键进度。
- 边界：历史遗留 `tmp_*` 目录没有在本轮批量删除；后续如要清理，应作为单独维护任务处理，并只限项目目录内。

## 2026-05-20 Release 大文件上传稳健化
- `.github/workflows/publish-release.yml` 仍保留原有 Release 创建/更新 API 流程。
- 最后的 zip 资产上传步骤已从 PowerShell `Invoke-WebRequest -InFile` 改为 `curl.exe --data-binary`。
- 原因：之前补传正式 Windows zip 资产时，手动验证 `curl.exe --data-binary` 上传更稳定；`Invoke-WebRequest` 在大文件上传时有卡住/超时风险。
- 新上传步骤会：
  - 使用 `GITHUB_TOKEN`、GitHub API headers 和 `application/zip`。
  - 将响应写入同目录临时 response json。
  - 检查 `curl.exe` 退出码。
  - 只接受 HTTP `200` 或 `201`，否则输出响应体并失败。
- 后续维护 Release 工作流时，优先保留这条 `curl.exe --data-binary` 路线，不要轻易回退到 `Invoke-WebRequest -InFile` 上传大 zip。

## 2026-05-09 使用教程改为应用内滚动页
- `使用教程` 不再通过 `show_readme()` 调用系统打开 `README.txt / README.md`，而是被加载器层重定向为应用内页面。
- 实现仍限定在 `Fengxi_Toolbox.py`，不修改 `fengxi_runtime.bin`。
- 当前方案：
  - 新增 `HELP_TAB_TITLE = "使用教程"` 与 `INLINE_HELP_SECTIONS`，将帮助内容直接内置为结构化章节。
  - 通过 `_ensure_inline_help_tab()` 在 `main_panel` 上懒创建帮助页 tab。
  - 帮助内容使用 `CTkScrollableFrame` 承载，页面显示不下时可直接纵向滚动。
  - 左侧 `btn_help_proxy` 的命令已改为 `_show_inline_help(...)`，不再走外部文档打开链路。
  - `show_readme()` 也被补丁层接管，任何旧入口最终都会切到应用内帮助页。
- 交互约束：
  - 进入帮助页时会高亮 `使用教程` 按钮。
  - 帮助页显示期间，底部开始按钮会禁用，避免 `current_task="help"` 误进入业务处理分支。
  - 切回任意功能页后，帮助按钮高亮取消，开始按钮恢复正常状态。
- 维护要求：
  - 后续功能有新增或行为变化时，需要同步更新 `INLINE_HELP_SECTIONS` 文案。
  - 如果继续扩展帮助页，优先沿用“应用内 tab + scrollable 内容”的路线，不要退回外部 README 打开方式。

## 2026-05-09 侧栏与标题图标清晰度重绘
- 用户反馈：左侧功能区图标线条发糊、细节乱，想按新的视觉参考图把图标做得更清晰、更规整。
- 当前修复仍限定在 `Fengxi_Toolbox.py` 加载器层，不改 `fengxi_runtime.bin`，不触碰稳定区 `批量压缩` / `添加水印` 的业务处理逻辑。
- 当前方案：
  - `_draw_sidebar_icon(...)` 不再沿用旧的低分辨率直接描线方案，而是统一改成更规整的几何线稿。
  - `_build_sidebar_icon_image(...)` 改为先按高分辨率画布超采样绘制，再用 `LANCZOS` 缩回实际显示尺寸，提升边缘清晰度。
  - 由于页面内标题图标复用同一套自绘逻辑，侧栏图标与功能页标题图标会同步变清晰，不需要分别维护两套素材。
  - `水印内容` 小标题图标已按参考图切换为文档语义，和页面布局更一致。
- 后续边界：
  - 若继续调整图标观感，优先改 `_draw_sidebar_icon(...)` 的几何路径与 `_build_sidebar_icon_image(...)` 的渲染策略，不要回退到 22px 画布直接硬描边。
  - 若引入新的图标种类，默认继续走“统一线稿 + 超采样缩放”路线，保持侧栏与页面标题风格一致。
  - 2026-05-09 起，侧栏头部原来的 `FX` 文本占位也已改为直接显示 `assets/fengxi_app_icon.png` 品牌图标；如果后续再调品牌头部，优先复用 `_get_sidebar_brand_image(...)`，不要重新塞回字母占位。

## 2026-05-09 页面内标题图标统一
- 用户反馈：左侧功能区图标与点击进入后的页面标题图标不一致，且部分页面标题/小标题使用 emoji 或符号时会出现乱码或观感不统一。
- 当前修复仍限定在 `Fengxi_Toolbox.py` 加载器层，不改 `fengxi_runtime.bin`，也不触碰稳定区 `批量压缩` / `添加水印` 业务处理逻辑。
- 当前方案：
  - 侧栏继续使用 PIL 自绘图标缓存 `_draw_sidebar_icon(...)` / `_get_sidebar_icon_images(...)`。
  - 新增页面内标题图标映射 `INLINE_TITLE_ICON_SPECS`，统一为主功能标题与关键小标题分配与侧栏同风格的自绘图标。
  - 通过 `_apply_inline_title_icons(...)` 递归扫描当前页 `CTkLabel`，把运行时自带的 emoji/符号标题改写为“纯文本标题 + 自绘 CTkImage”。
  - 该逻辑接入 `_tighten_single_tab_layout(...)` 与 `_refresh_visible_tab_layout(...)`，保证默认页和懒加载后的页签都会应用一致化图标。
  - `zip` 页残留的单字符闪电标签也已纳入同一映射，改为仅显示自绘图标，避免不同机器下出现符号观感差异。
- 当前边界：
  - 后续如继续调整功能页标题视觉，优先修改 `INLINE_TITLE_ICON_SPECS` 与 `_draw_sidebar_icon(...)`，不要回退到把 emoji 直接写进标题文本。
  - 页面内标题若要做到“只显示图标不显示旧字符”，应复用 `display_text` 机制，而不是保留原符号字符。

## 2026-04-26 侧栏构建快路径
- 继续沿加载器层优化启动性能，不改 `fengxi_runtime.bin`，也不碰稳定区 `批量压缩` / `添加水印` 业务逻辑。
- `Fengxi_Toolbox.py` 新增 `FAST_SIDEBAR_BUILD_FONT`、`_run_with_fast_sidebar_button_construction(...)` 与 `_patch_sidebar_build_performance()`。
- 当前策略是：只在 `setup_sidebar()` 的“构建阶段”临时把侧栏直系 `CTkButton` 做成轻量占位版本：
  - `text=""`
  - `font=("Microsoft YaHei UI", 12)`
- 真正展示给用户之前，仍然由 `_tighten_layout(...) -> _apply_shell_layout_tightening(...)` 统一恢复正式文案、图标和字体，所以最终可见 UI 不变。
- 这一层优化的核心边界：
  - 只影响 `setup_sidebar()` 运行时的按钮创建开销
  - 不改变按钮命令绑定
  - 不改变后续图标、对齐和视觉样式
  - 不能绕开 `_tighten_layout(...)`，否则窗口若被外部直接显示，侧栏可能还停留在占位态
- 本轮复测中，`setup_sidebar` 的累计耗时从约 `1.505s` 降到约 `0.183s`；同轮新进程里整体启动约 `3.78s -> 3.07s`。

## 2026-05-05 快速关闭补丁
- 用户反馈打包版点击关闭后窗口很久才消失。
- 排查发现默认水印页的文件名规则补丁中，`CTkOptionMenu` 误用了 `CTkComboBox` 支持的 `border_width` / `border_color` 参数。
- 这会导致下拉控件半初始化，窗口销毁时抛出 `_variable` 缺失异常，并拖慢关闭。
- 当前修复：
  - 新增 `_get_option_menu_style(...)`，只把 `CTkOptionMenu` 支持的样式参数传入水印规则下拉框。
  - 新增 `_install_fast_close_protocol(...)` 与 `_request_fast_close(...)`。
  - 点击窗口关闭时先设置 `stop_event=True` 并 `withdraw()` 隐藏窗口，再异步 `quit()` / `destroy()`。
- 目标是让用户点击关闭后窗口立即消失，即使后台 Tk 控件树清理仍需要一点时间。
- 当前回归：`full_debug_test.py` 的 `app_fast_close_hides_first`，验证关闭请求约毫秒级隐藏并进入销毁流程。

## 2026-05-05 水印页可视高度优化
- 用户截图反馈默认水印页中间出现一条明显黑色横带，挤压下方功能框，导致右侧参数区底部控件显示不全。
- 当前判断为外壳布局与水印页固定请求高度共同造成：
  - `main_panel` 与 `bottom_bar` 之间原有外壳背景间隙会露出黑色横带。
  - 默认水印页左右两列卡片原始请求高度约 `692px`，在常见 1360x768 视窗下可视高度不足。
  - 底部进度/按钮/日志区请求高度偏大，继续压缩主功能区。
- 当前修复仍只在加载器层做 UI 布局补丁，不改水印业务处理：
  - 将 `watermark -> tab_wm` 加入 `TAB_LAYOUT_ATTRS`，让默认水印页也走 `_tighten_single_tab_layout(...)`。
  - `_apply_shell_layout_tightening(...)` 收紧顶部栏、主区域和底部栏外距，移除主区域与底部栏之间的黑色间隙。
  - `_tighten_watermark_tab_layout(...)` 直接收紧 `tab_wm` 左右两列，压缩文本框、参数行、字体下拉框和三组滑块的垂直占位。
  - 在 1360x768 窗口模拟测量中，水印页可视高度从约 `577px` 提升到约 `664px`，右侧三组滑块完整显示。

## 2026-04-25 懒加载布局收敛
- 这轮启动/切页性能优化继续坚持“优先改 `Fengxi_Toolbox.py` 加载器层，不碰 `fengxi_runtime.bin`，不动稳定的添加水印/批量压缩业务”。
- `_tighten_layout(...)` 已拆成三层：
  - `_get_sidebar_button_font(...)`：缓存侧栏字体，避免重复创建
  - `_apply_shell_layout_tightening(...)`：只负责侧栏、顶部、底部这些一次性外框样式
  - `_tighten_single_tab_layout(...)`：只对刚初始化的目标页做局部收紧
- `_ensure_lazy_tab_initialized(...)` 不再在每个懒加载页初始化后重跑整套侧栏重排；现在是“初始化目标页 -> 针对该页做局部布局收紧 -> 再刷新 idle tasks”。
- 同口径冷启动基准里，整体启动时间基本持平（约 `4.41s -> 4.41s`），说明当前启动主热点仍然在 `setup_sidebar` 和默认 `watermark` 页构建，而不再是懒加载页切换后的重复布局。
- 同口径首次切页基准里，局部收益明确：
  - `remove_wm`: `0.6425s -> 0.5288s`
  - `convert`: `0.3632s -> 0.3380s`
  - `zip`: `0.4306s -> 0.4258s`
  - `pdf`: `0.7645s -> 0.7504s`
  - `meta`: `0.3068s -> 0.2573s`
  - `file`: `0.5073s -> 0.2685s`
- 后续如果还要继续压启动速度，优先研究 `setup_sidebar` 的按钮构建/绘制成本；默认不要为了提速去动 `watermark` 业务页本体，因为该功能属于用户明确要求的稳定区。

## 2026-04-25 统一进度条修复架构
- 进度条修复继续坚持“优先改加载器层，不改 `fengxi_runtime.bin`”。
- 2026-05-22 起，进度条升级为“进度条 + 状态文本”的真进度显示：
  - 底部操作区新增进度状态文本，显示当前文件、当前阶段、已完成文件数/总数、总进度百分比、预计剩余时间。
  - `_FxRunProgressTracker` 统一维护 `started_at`、`current_file`、`current_stage`、`completed_units` 与 ETA 估算。
  - 运行时 `process_single_file()` 包装会自动识别当前文件名；自定义工作流会主动上报阶段，例如 OCR 页进度、PDF 压缩、图片转 PDF、多图合并 PDF、PDF 去水印 round-trip。
  - 仍不修改 `fengxi_runtime.bin`，也不改批量压缩/添加水印核心业务逻辑。
- 2026-05-24 起，底部进度状态文本不再放入按钮 action row；`_install_progress_status_label(...)` 改为把 `_fx_progress_status_label` 直接 grid 到 `bottom_bar` 第 0 行右侧，进度条在同一行左侧，按钮行仍独立保留 `批量并行`、开始/停止、`加入队列`、`队列历史`。
- 回归 `progress_status_separate_from_action_row` 要求进度状态标签使用 `grid` 且父级是 `bottom_bar`，不能再用 `pack` 插入 action row。
- `Fengxi_Toolbox.py` 新增 `_patch_runtime_progress_reporting()`：
  - 先沿补丁链剥离出嵌入式原始 `run_process()`
  - 再用 `_build_runtime_progress_site_map(...)` 分析字节码中的进度调用点，区分三类：
    - `before_process_single`：处理前预写进度，改为等 `process_single_file()` 返回后再累计
    - `direct_pre`：直接循环分支，改为在下一轮开始或任务收尾时补记上一项完成
    - `pass_through`：原本就是完成后进度，保持直通
- 运行期通过实例级 `_FxRunProgressTracker` 临时接管：
  - `progress_bar.set`
  - `process_single_file`
  - `reset_ui`
- 这样可以统一修复大多数封装在运行时里的“提前跳进度”问题，同时不去反编译或重写运行时主体。

## 2026-04-25 OCR 页级进度接回 UI
- `tools/fx_pdf_ocr.py` 的 `FengxiPdfOcrEngine.ocr_pdf_to_searchable_pdf(...)` 原本已经支持 `progress_callback(page_done, total_pages)`。
- 当前 `Fengxi_Toolbox.py` 中的 `_run_pdf_ocr_task()` 已正式接入这个回调，并把页进度映射到整体批处理进度。
- 后续如果继续改 OCR 工作流，优先复用这个回调，不要再退回到“按文件开始就直接 +1”的粗粒度进度写法。

## 总体形态
- 仓库表面上是单文件应用，但真实结构是“加载器 + 封装运行时 + 测试脚本 + 打包产物”。
- `Fengxi_Toolbox.py` 不是完整业务源码，它负责：
  1. 载入 `fengxi_runtime.bin`
  2. 将运行时对象注入全局
  3. 用 ffmpeg 版音频转换函数覆盖原音频转换入口
  4. 在加载器层补 UI、OCR、启动性能等外围补丁
  5. 对部分调用做 debug 包装
  6. 在 `__main__` 中创建 `FengxiToolboxApp`

## 运行时装载
- `fengxi_runtime.bin` 通过 `marshal.loads(...)` 反序列化。
- 运行时命名空间中的类、函数被拷贝进 `globals()`。
- 当前可见核心对象：
  - `FengxiToolboxApp`
  - `create_watermark_packet`
  - `add_watermark_to_pdf`
  - `add_watermark_to_word`
  - `remove_watermark_from_word`
  - `convert_doc_to_pdf`
  - `convert_pdf_to_word`
  - `convert_ppt_to_pdf`
  - `merge_images_to_pdf`
  - `modify_file_timestamp`
  - `modify_office_meta`

## UI 与任务调度
- 主类：`FengxiToolboxApp`
- 主要方法：
  - `collect_input_files`
  - `resolve_task_config`
  - `process_single_file`
  - `run_process`
  - `on_start_click`
- Tab/页面：
  - 批量水印
  - 去除水印
  - 格式转换
  - 音频工具
  - 批量压缩
  - PDF 工具
  - 图片工厂
  - 属性隐私
  - 文件管家
- 2026-04-21 起，启动流程改为“默认页即时初始化，其余页首次访问时再初始化”：
  - 默认首屏是 `watermark`
  - `switch_tab()` 已被加载器层补丁接管，会在切页前补建目标页面
  - `__getattr__` 也做了延迟补建兼容，因此像 `pdf_mode_var`、`file_mode_var` 这类变量即使在未手动切页前被访问，也会自动触发所属页面初始化
- 启动窗口现在先 `withdraw()`，等布局收束后再 `deiconify()`，用于减少打开时连续闪过多个半成品界面的问题

## 入口与依赖
- GUI：`customtkinter`
- PDF：`pypdf`, `reportlab`, `pdf2docx`
- 图像：`Pillow`
- Office COM：`pythoncom`, `win32com.client`
- 拖拽/窗体样式：`windnd`, `pywinstyles`
- 音视频：优先使用 `imageio_ffmpeg` 提供的 ffmpeg 二进制

## 当前源码层补丁
- 由于运行时内部把 `PDF 合并` 和 `文件去重` 的专用分支放在单线程路径，而原配置分流未强制切换，源码层在加载器中增加了任务路由补丁：
  - `pdf_mode == "merge"` 时强制单线程
  - `file_mode == "dedup"` 时强制单线程
- 2026-04-22 起，`remove_wm` 也在加载器层显式强制单线程：
  - 真正的 Word/PDF 去水印逻辑只存在于 `run_process()` 的单线程 COM 工作流里
  - 一旦误落到 `process_single_file()` 普通路径，去水印只会复制原文件并写“跳过”日志
- 2026-04-22 起，输入入口支持“单文件或文件夹”双模式：
  - `_patch_single_input_support()` 接管了 `select_folder` / `collect_input_files` / `on_start_click` / `run_process`
  - 普通任务的单文件模式做法是：把 `run_process()` 根路径切到目标文件父目录，再通过 `_fx_single_input_target` 只放行这一份文件
  - 为避免 `process_single_file()` 在工作线程里写 UI 日志时触发 `main thread is not in main loop`，单文件输入会自动临时关闭多线程，强制走单线程稳定模式
  - `zip` 是例外：单文件压缩不改稳定压缩主体，而是先把文件复制到临时隔离目录，调用原始 `run_process('zip')` 后再把生成的 zip 移回原目录
- 这样无需改动稳定业务实现，只修正调度入口。
- OCR 搜索版 PDF、左侧导航布局、PDF OCR 双栏布局、启动性能优化都优先通过 `Fengxi_Toolbox.py` 的加载器层补丁完成，不直接改 `fengxi_runtime.bin`。
- 2026-04-22 起，左侧导航不再依赖“emoji 直接拼进按钮文字”的方案：
  - 改为加载器层动态生成固定尺寸的图标图片 + 独立文本标签
  - 当前实现使用 PIL 画线稿风格的小图标，不依赖系统 emoji 字体，避免缺字或宽度不一致
  - 目标是让所有导航项、教程按钮、赞助按钮的起始线和内部间距保持统一，同时保留真正的图形图标
  - 后续如果继续调左侧视觉，优先改这套 icon image + `border_spacing` 的样式，不要回退到 emoji 文本前缀或字母缩写占位符
- 2026-04-22 起，左侧底部辅助入口也有单独约束：
  - `使用教程` 与 `赞助作者` 统一通过 `_style_sidebar_aux_button(...)` 收口样式
  - 两者必须保持同一高度、同一圆角、同一边框宽度、同一图标槽与文字对齐节奏
  - `赞助作者` 只允许通过暖色填充/边框做轻强调，不要再回退到另一套控件观感
- 2026-04-22 起，Word 去水印还有一个加载器层稳健性补丁：
  - `_patch_remove_watermark_robustness()` 会在原始 `remove_watermark_from_word()` 成功后，对输出 doc/docx 再做一轮 `页眉 Range.InlineShapes` 清理
  - 这是为了解决原始实现只删 `header.Shapes`、却漏删 `页眉图片水印` 的问题
  - 该补丁属于外围兜底，不重写原始去水印主体逻辑

## 品牌图标资产
- 2026-04-22 起，应用图标由项目内脚本 `tools/generate_fengxi_icon.py` 生成：
  - `assets/fengxi_app_icon.png`
  - `assets/fengxi_app_icon.ico`
- 当前品牌图标语义：
  - 主体是“流风回旋”形态
  - 配合暖金印章感点缀，表达“风兮”品牌感
- 接入位置：
  - 运行时窗口图标由 `Fengxi_Toolbox.py` 中的 `_apply_app_icon(app)` 负责加载
  - 发布版窗口标题由 `Fengxi_Toolbox.py` 中的 `_apply_release_identity(app)` 在启动时统一设置，当前展示口径为 `风兮文件批量处理工具箱 4.0`
  - 打包 exe 图标由 `fx_toolbox.spec` 的 `icon='assets\\fengxi_app_icon.ico'` 负责接入
- 2026-05-09：
  - 用户已直接替换 `assets/fengxi_app_icon.png` 为新的品牌图。
  - `assets/fengxi_app_icon.ico` 也必须同步由该 `png` 重生成，否则侧栏品牌头、窗口图标与打包 exe 图标会不一致。
  - 当前这版品牌图已清理四角黑底，根资产与打包产物都应保持“透明圆角”状态；若后续再次替换源图，需同时验证 PNG/ICO 左上角 alpha 为 0，避免黑角回归。
- 若后续继续改品牌图标，优先改生成脚本并重新生成 PNG/ICO，不要只手工替换其中一个产物，避免源码态与打包态图标不一致

## 打包策略
- 2026-04-21 起，发布包优先采用 `onedir` 目录式输出，而不是 `onefile`。
- 原因：
  - `onefile` 每次启动都需要额外解包，桌面工具首启和重复启动都会更慢。
  - 当前项目本身还要加载 `fengxi_runtime.bin`、OCR 依赖和 GUI 资源，`onefile` 叠加后启动感知会更差。
- 当前推荐发布入口：
  - `dist_release_ascii\fx_toolbox\fx_toolbox.exe`
- `package.bat` 与 `fx_toolbox.spec` 都应围绕目录式输出维护，不要再改回单文件思路，除非用户明确接受启动变慢。
## 2026-04-22 去水印安全补丁
- `Fengxi_Toolbox.py` 不再通过“先调用原始 `remove_watermark_from_word()` 再补删 header inline shapes”的方式处理 Word 去水印。
- 当前改为直接在加载层接管 `remove_watermark_from_word()`，使用 `_remove_watermark_from_word_safely(...)`。
- 安全版流程会先读取页面尺寸，再对 header `Shapes`、header `InlineShapes`、以及 `is_pdf_source=True` 时的文档级 `Shapes` 做逐项判定。
- 只有命中 `XMU_DONE` / watermark 关键词，或满足“大尺寸 + 居中/越界 + 斜向/半透明”特征时才删除。
- 这样做的目标是保留正常页眉图文和 PDF 转 Word 后的正常 shape 内容，避免历史上的“去水印成功但内容一起被删掉”。
## 2026-04-22 PDF 去水印兜底补丁
- `Fengxi_Toolbox.py` 新增 `_patch_remove_wm_pdf_fallback()`，在 `run_process()` 层拦截 `task_type == "remove_wm"` 且输入中包含 PDF 的情况。
- 拦截后不再完全依赖运行时原始 PDF 去水印链路，而是交给 `_run_remove_wm_task(...)`。
- 其中 PDF 文件走 `_run_remove_wm_pdf_roundtrip(...)`：
- 使用 ASCII 临时目录生成 `from_pdf.docx` / `cleaned.docx`。
- 先 `convert_pdf_to_word()`，再调用加载层安全版 `remove_watermark_from_word(..., is_pdf_source=True)`，最后 `convert_doc_to_pdf()` 输出到正式结果目录。
- 非 PDF 文件仍保留原有去水印路径；混合输入时会把非 PDF 放进临时 staging 目录交给原始 `run_process()` 处理，再把结果并回真实输出目录。
- 结果目录必须统一复用 `RESULT_FOLDER_NAME`，不要手写字符串，避免编码或目录名漂移导致测试/运行找不到结果文件。

## 2026-04-24 PDF 去水印 Word 会话隔离
- `Fengxi_Toolbox.py` 中的 `_create_hidden_word_app()` 现已改为 `DispatchEx("Word.Application")`，不再复用共享 Word 进程。
- `_run_remove_wm_pdf_roundtrip(...)` 里，每个 PDF 会：
- 先用独立 Word 实例执行 `remove_watermark_from_word(..., is_pdf_source=True)`。
- 再用另一个独立 Word 实例执行 `convert_doc_to_pdf(...)`。
- 这样即使去水印阶段出现 COM 异常，也不会把同一批次后续 PDF 或后续导出阶段一起拖坏。
## 2026-04-22 统一输入选择器
- `Fengxi_Toolbox.py` 的浏览入口不再使用 `askyesnocancel` 先问“文件还是文件夹”。
- 当前改为 `_UnifiedInputPathPicker` 自定义统一路径选择器：
- 同一窗口内直接列出文件和文件夹。
- 双击文件可直接确认。
- 双击文件夹可进入。
- 也可以选中文件夹后点“确定”或“选择当前文件夹”。
- 这一改动只发生在加载层浏览入口，不改动后续单文件/文件夹调度逻辑。
## 2026-04-24 浏览入口回退到系统原生选择器
- 用户明确不接受自定义的大型 `CTkToplevel` 路径选择器观感。
- 当前默认浏览入口已改为 Windows Shell 原生选择器 `_choose_input_path_via_shell_dialog(...)`。
- 技术路径：
- 使用 `SHBrowseForFolder` + `BIF_BROWSEINCLUDEFILES`
- 允许在同一个系统窗口里直接点文件或文件夹
- 通过回调在打开时定位到当前输入目录
- 设计边界：
- 只替换“浏览入口 UI”，不改动后续 `_patch_single_input_support()` 的单文件/文件夹调度逻辑。
- 拖拽输入、单文件处理、文件夹处理、压缩/加水印稳定区都不应受这次改动影响。
- 后续若继续优化输入入口，优先保持“系统原生窗口 + 文件/文件夹同选”方向，不要再把自定义大窗口重新设为默认入口。

## 2026-04-24 输入路径字节解码修复
- Windows Shell 选择器在某些环境下返回的路径可能是 `bytes`，而不是普通 `str`。
- 旧版 `_normalize_input_path_value()` 直接做 `str(value)`，会把字节路径污染成：
- `b'...'`
- `\x..` 转义片段
- 甚至被 `os.path.abspath(...)` 错误拼成 `项目目录\\b'真实路径'`
- 这会进一步导致：
- 输入框显示脏路径
- `os.path.isfile()` / `os.path.isdir()` 误判
- `remove_wm` 等任务拿着错误路径执行，表现成卡住、无法停止或日志乱码
- 当前修复：
- 新增 `_decode_input_path_bytes(...)` 与 `_coerce_input_path_text(...)`
- `_normalize_input_path_value()` 统一先做字节解码，再做路径归一化
- 同时兼容三类脏输入：
- 原始 `bytes`
- 形如 `b'...'` 的字节字面量字符串
- 已被错误拼到当前工作目录前缀里的 `...\\b'真实路径'`
- 后续凡是浏览、拖拽、日志回填、单文件调度涉及路径规范化，都应继续复用 `_normalize_input_path_value()`，不要绕开这层直接 `str(...)`

## 2026-04-24 拖拽单文件与去水印单文件输出根目录修复
- 运行时原始 `accept_drag_drop()` 会把拖入的单文件自动改写成其父目录。
- 这会导致：
- UI 看起来像“拖入成功了”，但实际只锁定到文件夹
- 桌面单个 PDF 拖入后会退化成处理整个桌面目录
- 单文件任务无法做到精准选中目标文件
- 当前加载层已新增 `_patch_drag_drop_input_support()`：
- 拖入单个文件时保留文件本体路径
- 拖入文件夹时保持文件夹路径
- 同步更新 `_fx_input_pick_mode` 与 `_fx_last_input_dir`
- 多项目拖拽时暂时只取第 1 个，并在日志里明确提示
- 同时，`remove_wm` 的加载层专用链路 `_run_remove_wm_task(...)` 现已区分：
- `normalized_input`：用户真实输入，可能是文件也可能是文件夹
- `input_root`：用于输出目录和相对路径计算的根目录；若输入是文件，则取其父目录
- 这样可避免把结果目录错误拼成 `某文件.pdf\\【处理完成】结果文件夹`
- 后续凡是新增“单文件专用工作流”，都要警惕：
- 输出目录不能直接 `os.path.join(输入文件路径, RESULT_FOLDER_NAME)`
- `relpath()` 的基准目录也不能直接拿“文件路径”来算

## 2026-04-24 启动性能懒加载
- `Fengxi_Toolbox.py` 的 `_load_runtime_namespace()` 现在会在执行 `fengxi_runtime.bin` 前，临时安装运行时懒加载代理。
- 当前仅对启动期开销大的可选依赖做懒加载：
- `pdf2docx`
- `moviepy`
- `moviepy.editor`
- 代理入口由 `_install_runtime_lazy_imports()`、`_LazyImportModule`、`_LazyImportSymbol`、`_resolve_lazy_runtime_module()` 组成。
- 设计边界：
- 只延后“首次真正调用”时再导入重依赖，不改动运行时业务函数签名。
- 执行完 `fengxi_runtime.bin` 后会通过 `_restore_runtime_lazy_imports()` 清理 `sys.modules` 中仍是代理的占位项，避免污染常规导入环境。
- 2026-05-09 起需兼容 `moviepy==2.2.x` 已不再提供 `moviepy.editor` 实体模块这一事实：
  - 加载器层仍保留 `moviepy.editor` 代理名，避免嵌入运行时里的旧导入路径失效。
  - 但其真实符号解析已回退到 `moviepy` 根模块上的 `AudioFileClip` / `VideoFileClip`。
  - `fx_toolbox.spec` 不再无条件写死 `moviepy.editor` hidden import，而是仅在当前环境存在该模块时才加入；同时显式补入新版可用的 `moviepy.audio.io.AudioFileClip` 与 `moviepy.video.io.VideoFileClip`。
- 后续如果还要继续优化启动速度，优先沿着“可选重依赖懒加载”思路做；不要轻易动 `customtkinter`、首屏 `watermark` UI、批量压缩、添加水印的稳定业务逻辑。

## 2026-04-24 去水印单文件输出与失败防伪成功
- `去除水印` 页现已由加载层补入 `rm_wm_overwrite_original` 开关，文案为“单文件时直接覆盖原文件（谨慎）”。
- 当前去水印输出规则固定为：
- 文件夹输入：继续输出到 `RESULT_FOLDER_NAME`
- 单文件输入：默认在同目录输出 `原文件名_去水印.ext`
- 单文件输入且开启覆盖：仅在处理成功后替换原文件
- `_run_remove_wm_task(...)` 现已允许单文件先写入临时结果目录，再通过 `_finalize_single_remove_wm_output(...)` 落到最终位置，避免在单文件模式下误生成 `【处理完成】结果文件夹`。
- `_run_remove_wm_pdf_roundtrip(...)` 现已严格要求 `remove_watermark_from_word(...) == "SUCCESS"` 且 `cleaned.docx` 真实存在，否则直接按失败处理。
- 后续凡是继续改 `remove_wm`，都必须保持这个边界：失败时宁可不产出结果，也不能把原文件重新导出后冒充“去水印成功”。

## 2026-04-25 OCR 单文件路径规则补齐
- `_run_pdf_ocr_task(...)` 现已改为复用统一的结果根目录解析：
- 若输入是文件夹，则输出到 `输入文件夹\\RESULT_FOLDER_NAME`
- 若输入是单个文件，则输出到 `该文件父目录\\RESULT_FOLDER_NAME`
- 这样可避免旧逻辑把结果目录错误拼成 `某个.pdf\\【处理完成】结果文件夹`
- OCR 现在与单文件支持补丁 `_patch_single_input_support()`、拖拽补丁 `_patch_drag_drop_input_support()` 的路径语义保持一致。
- 后续凡是新增“加载层自定义工作流”时，都不要直接 `os.path.join(input_folder, RESULT_FOLDER_NAME)`，必须先判断 `input_folder` 是文件还是文件夹。
## 2026-04-25 OCR 打包运行时补丁
- 打包版 OCR 的 RapidOCR/onnxruntime 不能只依赖 PyInstaller 默认注入的 `_internal` 路径。
- `onnxruntime_pybind11_state.pyd` 在冻结环境里真正需要显式注册 `onnxruntime\capi` 目录，否则会报：
  - `DLL load failed while importing onnxruntime_pybind11_state: 动态链接库(DLL)初始化例程失败。`
- 当前修复落在 `tools/fx_pdf_ocr.py`：
  - 新增 `_prepare_windows_ocr_runtime_dirs()`，仅注册 `onnxruntime\capi`，不把整层 `_internal` 当作 OCR DLL 兜底路径塞进去，避免额外 DLL 冲突。
  - `discover_backend_status()` 不再只做 `find_spec` 级别判断，而是对 `rapidocr` / `onnxruntime` 做真实导入探测。
  - `RapidOcrBackend.__init__()` 在导入 `rapidocr` 前先执行运行时 DLL 路径准备。
- 调试结论：
  - `_internal` 单独在 PATH 中时，导入 dist 里的 `onnxruntime_pybind11_state.pyd` 仍会失败。
  - 显式加入 `_internal\onnxruntime\capi` 后，dist 里的扩展模块可成功导入。

## 2026-04-25 OCR 状态探测与自动选后端解耦
- OCR 页面状态栏不能作为真正执行时的唯一准入门槛。
- 当前策略改为：
  - UI 初始状态不再自动做重导入探测，避免一打开 PDF/OCR 页就卡顿。
  - `刷新状态` 按钮才触发详细后端检测。
  - 真正执行 OCR 时，`auto` 会按 `rapidocr -> paddleocr -> easyocr -> tesseract_cli` 逐个做真实导入/可用性尝试，而不是先被 `discover_backend_status()` 的预判拦死。
- 这样即使冻结环境里 `find_spec()`/状态面板判断有偏差，也不会提前把本可运行的后端误判成不可用。
## 2026-04-25 OCR 打包运行库冲突修复
- 这次真正的根因不在 `tools/fx_pdf_ocr.py` 的识别逻辑，而在打包产物 `_internal` 目录里随包带出的 MSVC/UCRT 运行库。
- 已确认会和 `onnxruntime` 冲突的 DLL 组：
  - `msvcp140.dll`
  - `MSVCP140_1.dll`
  - `vcruntime140.dll`
  - `vcruntime140_1.dll`
  - `ucrtbase.dll`
  - `api-ms-win-crt-*.dll`
- 现行发布策略：
  - `fx_toolbox.spec` 会在 `Analysis(...)` 后过滤上述冲突 DLL，避免被收进最终产物。
  - `package.bat` 在收尾阶段还会再次清理 `%APP_ROOT%\\_internal` 中的同名 DLL，防止历史构建残留。
- 诊断结论：
  - 保留这些本地运行库时，冻结环境里 `onnxruntime_pybind11_state.pyd` 会报 `DLL 初始化例程失败`。
  - 去掉这组 DLL 后，同一份 `onnxruntime` 二进制即可在打包版 EXE 中成功导入，`RapidOCR` 初始化也恢复正常。
- 后续如果 OCR 只在打包版失败，优先检查：
  - `fx_toolbox.spec`
  - `package.bat`
  - `tmp_ocr_diag/*.json`
  - `_internal` 下是否重新混入了上述运行库
## 2026-05-01 GitHub 仓库协作层补强
- 仓库根目录现已新增 `README.md`，作为 GitHub 首页主说明文档；原有 `README.txt` 继续保留给打包产物随包分发使用。
- `README.md` 当前覆盖的重点包括：
  - 功能总览
  - 源码运行方式
  - Windows 打包方式
  - 测试入口
  - 项目结构
  - 维护约束
- 仓库根目录现已新增 `requirements.txt`，使用当前本机已验证可导入/可打包的一组固定版本依赖，供源码运行与 CI 构建复用。
- 仓库现已新增 `.github/workflows/build-windows-exe.yml`：
  - 触发方式为 `workflow_dispatch`
  - 运行环境为 `windows-latest`
  - Python 版本固定为 `3.11`
  - `actions/setup-python` 已启用 `pip` 缓存并绑定 `requirements.txt`
  - 直接复用现有 `package.bat`
  - 构建成功后通过 `actions/upload-artifact@v7` 上传 `dist_release_ascii/fx_toolbox` 为 artifact
- 后续若继续维护 GitHub 发布能力，默认顺序应为：
  1. 先更新 `requirements.txt`
  2. 再确认 `package.bat` / `fx_toolbox.spec`
  3. 最后再调整 Actions 工作流
- 这层改动只属于仓库协作与发布层，不涉及业务代码回归；默认无需触碰稳定区 `批量压缩` / `添加水印`。

## 2026-04-30 Git 仓库初始化与上传准备
- 项目根目录现已执行 `git init -b main`，后续工作可以基于本地 Git 历史推进。
- 新增仓库级 `.gitignore`，当前明确忽略：
  - `.session_backups/`
  - `__pycache__/`
  - `build*`
  - `dist*`
  - `tmp_*`
  - `Fengxi_Toolbox_corrupted_backup.py`
- 现阶段可以安全执行 `git add` / `git commit`，不会把打包产物、临时调试目录和会话备份一并纳入版本库。
- 本机当前已确认：
  - `git` 可用
  - `gh` CLI 不可用
  - SSH 到 GitHub 当前不可用：22 端口连接被关闭，443 端口可连通但目标账号未接受本机公钥
  - HTTPS 远端可用，已成功配置 `origin -> https://github.com/Fiercerwind/FengxiToolbox.git`
- 本地首个提交 `2a48666` 已成功推送到 GitHub 私有仓库 `Fiercerwind/FengxiToolbox`，`main` 分支已建立跟踪关系。
- 后续继续发布时，默认基线路径就是当前 `origin/main`，无需再次初始化仓库；优先直接 `git status` -> `git add/commit` -> `git push`。

## 2026-05-05 水印页黑色横条与底部占位修复
- 用户反馈默认水印页中部有一条黑色横条，导致下方功能框显示不全。
- 根因确认仍属于外壳布局问题，不是添加水印业务逻辑：主窗口背景为 `#000000`，`top_bar` / `main_panel` / `bottom_bar` 间距露出时形成黑线；同时底部栏在高 DPI 下实际占位过高，压缩了水印页主区域。
- 当前修复仍只在 `Fengxi_Toolbox.py` 加载器层处理：
  - `_apply_shell_layout_tightening()` 将窗口和 `main_panel` 背景统一为 `COLOR_CARD_ALT`，避免布局缝隙露黑。
  - 取消 `bottom_bar.grid_propagate(False)` 的硬固定高度，改为自然紧凑高度。
  - 收紧顶部栏、进度条、操作按钮区和日志框的高度/外边距。
- 复测 1360x768 窗口：底部栏实际高度约从 `246px` 降到 `149px`，水印主面板可视高度约从 `746px` 提升到 `871px`，右侧水印参数控件完整显示并有余量。
- 稳定区提醒：本次没有改 `watermark` 任务处理逻辑、智能水印规则执行逻辑或批量压缩业务逻辑。

## 2026-05-05 底部栏高度恢复
- 用户确认上一轮压缩后底部操作/日志区过小，需要恢复原来的底部高度。
- 当前处理：保留“窗口/主面板背景统一为 `COLOR_CARD_ALT` 以消除黑色横条”的修复，只恢复底部栏高度策略。
- `_apply_shell_layout_tightening()` 中 `bottom_bar` 恢复 `height=164` + `grid_propagate(False)`，进度条/按钮/日志框恢复到原先较舒展的尺寸。
- 1360x768 复测：`bottom_bar` 实际高度恢复到约 `246px`；`tab_wm` 可视高度约 `690px`，仍高于水印页右侧控件请求高度约 `671px`，控件应完整显示。
- 稳定区提醒：本次仍只改 UI 外壳布局，不改添加水印业务逻辑。

## 2026-05-05 底部运行信息框双倍高度
- 用户要求将底部运行信息/日志框高度增加一倍。
- 当前处理仍只在 `Fengxi_Toolbox.py` 加载器层做 UI 布局调整：
  - `_apply_shell_layout_tightening()` 中 `bottom_bar.height` 从 `164` 增至 `228`。
  - `bottom_bar` 第 2 行 `minsize` 从 `64` 增至 `128`。
  - `log_box.configure(height=64)` 改为 `height=128`。
- 高 DPI 下复测：日志框实际高度从约 `96px` 增至约 `192px`，符合“双倍高度”。
- 为避免 1360x768 窗口下默认水印页右侧参数被裁切，同步微调 `_tighten_watermark_tab_layout()` 的右侧控件垂直间距和滑块组高度；只改 UI 排版，不改添加水印业务逻辑。
- 复测：`right_panel` 请求高度约 `589px`，可视高度约 `594px`，右侧控件可完整显示。

## 2026-05-08 属性页与 PDF 页显示裁切修复
- 用户反馈：属性隐私页底部输入区域被裁切，PDF 功能页左侧按钮列与共享控件显示不全。
- 根因：2026-05-05 将 `bottom_bar` 日志区加高到双倍后，主内容区可视高度降到约 `676px`；`meta` 页原始请求高度约 `754px`，`pdf` 页虽然整体请求高度不高，但左侧功能列内部仍保留较大的按钮高度与间距，导致下半部分被裁切。
- 当前修复仍只在 `Fengxi_Toolbox.py` 加载器层做 UI 调整：
  - 新增 `_tighten_meta_tab_layout()`：隐藏属性页中无子控件的 300px 空白占位 frame，并压紧单选区与两个输入区的高度。
  - 新增/修正 `_tighten_pdf_tab_layout()`：压紧 PDF 页卡片边距、左侧功能按钮高度与共享开关/密码框高度；修正了 PDF 页真实内容嵌套在额外一层 frame 中的层级判断。
  - 新增 `_refresh_visible_tab_layout()`，并在 `patched_switch_tab()` 中于原始切页后执行，确保 `meta/pdf` 的紧凑布局是在页签真正显示后应用，而不是在不可见阶段提前失效。
- 1360x768 复测：
  - `meta` 页请求高度约从 `754px` 降到 `424px`，作者/时间两个输入区完整可见。
  - `pdf` 页请求高度约从 `466px` 降到 `398px`；左侧 5 个模式按钮、`OCR` 按钮及共享控件完整显示。
- 本次未改 PDF/OCR/属性处理业务逻辑，仅调整布局与切页后的可见态刷新。


## 2026-05-21 16:48:24 | runtime
- summary: history detail export
- files: Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- note: added an export-result button to the task history detail dialog; it exports the current entry's structured task_result JSON via a save dialog and default filename, keeps the export scope narrow, and binds the dialog to the current entry so reuse does not leak the previous task. Added test coverage for filename generation, successful JSON export, and empty-entry rejection; full_debug_test now tolerates a PowerPoint COM close hiccup during teardown. Validation: py_compile passed, smoke_test 14/14, full_debug_test 71/71.


## 2026-05-21 16:59:33 | runtime
- summary: history detail log export
- files: Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- note: extended the task history detail dialog with a second export path for logs. The dialog now exposes 导出日志 alongside 导出结果 and 复制详情. The log export helper writes a plain text snapshot containing title, task, status, input, timestamps, and current log lines, with a safe default filename and empty-log fallback. Added regression checks for filename safety, successful log export, and empty-log handling. Validation: py_compile passed, smoke_test 14/14, full_debug_test 74/74.


## 2026-05-21 18:14:31 | runtime
- summary: history detail open output location
- files: Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- note: added an 打开位置 action to the task history detail dialog. It resolves the best available target in order: output_root, first output file parent, then input parent, and opens it with os.startfile on Windows. Added regression checks for opening output_root, falling back from an output file to its parent directory, and rejecting empty targets. Validation: py_compile passed, smoke_test 14/14, full_debug_test 77/77.
## 2026-05-22 remove_wm 单文件输出策略补尾
- 单文件 `remove_wm` 的真实语义继续保持三档：
  - 文件夹输入：输出到 `【处理完成】结果文件夹`
  - 单文件输入默认：同目录生成新文件
  - 单文件输入且勾选覆盖：仅在成功时安全替换原文件
- 关键实现边界：
  - 即使是“覆盖原文件”模式，也必须先把去水印结果写入临时 `RESULT_FOLDER_NAME` 目录中的 staged 文件。
  - 最终落地必须通过 `_finalize_single_remove_wm_output(...)` 完成，不能把原文件路径本身当成 staged 结果。
- 这样做的原因：
  - 否则会出现“流程看起来成功、日志也完成，但原文件其实没被真正替换”的假成功。
- 结构化结果模型也已在该链路补齐：
  - 单文件 `same_dir` / `overwrite` 都会明确回写 `output_strategy`
  - 成功/失败都会写回 `outputs`、`output_root`、`processed_count`、`success_count`、`failed_count`
  - 这样任务历史、任务报告、失败重试和后续真进度展示都能吃同一套口径

## 2026-05-22 remove_wm 分级模式架构
- `Fengxi_Toolbox.py` 新增 `REMOVE_WM_MODE_*` 常量和 profile 表，集中描述去水印三档阈值。
- `_shape_looks_like_watermark(...)` 与 `_inline_shape_looks_like_watermark(...)` 增加 `mode` 参数，但保持默认兼容。
- `_remove_watermark_from_word_safely(...)`、patched `remove_watermark_from_word(...)` 和 PDF roundtrip 都支持传入模式。
- 因 runtime 内部 Word 去水印调用无法直接拿到 UI app，加载器层新增线程本地 `_REMOVE_WM_MODE_CONTEXT`，在 `remove_wm` 任务运行期间临时注入当前模式。
- UI 层在 `init_remove_wm_ui` patch 内增加 `rm_wm_mode_var` 和 `rm_wm_mode_hint_var`，偏好持久化复用 `user_prefs.json` 的 `watermark.remove_wm_mode`。
- 回归测试通过假 shape/inline shape 验证：保守会拒绝“标准阈值才命中”的候选，标准保持旧行为，激进也会命中。

## 2026-05-22 Word COM 动态实例与 PDF 去水印导出兜底
- 本机可能出现 pywin32 `win32com.gen_py` Word 缓存损坏，典型错误为 `module ... has no attribute 'CLSIDToClassMap'`。
- 加载器层新增/强化 `_dispatch_com_app_dynamic("Word.Application")`：Word 走 `pythoncom.CoCreateInstance + win32com.client.dynamic.Dispatch`，避免 `DispatchEx` 直接触发损坏缓存。
- `_DisableWin32ComGenCache()` 不能只包 Word 创建；访问 Word 子对象（`Documents`、`Sections`、`Headers`、`InlineShapes` 等）期间也必须保持启用，否则 pywin32 仍会尝试包装子对象并触发 `gen_py`。
- PDF 去水印 round-trip 在 `convert_doc_to_pdf(...)` 返回 `ERROR` 或目标 PDF 未落盘时，会改走 `_export_word_docx_to_pdf_safely(...)`，直接调用 Word `ExportAsFixedFormat(..., 17)` 导出。
- `full_debug_test.py` 的 Word COM 探针也改用项目动态 COM helper 与完整 `gencache` 禁用范围，避免测试被环境缓存噪音误判。
- 验证：`python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py`、`python smoke_test.py` 14/14、`python full_debug_test.py` 109/109。

## 2026-05-22 并行提示移除与队列入口恢复
- 用户反馈“并行状态”提示把之前的任务队列和历史功能挤没了。
- 根因在底部操作行 UI 占位：`_install_parallel_mode_hint()` 把一条长文本标签 pack 到 `chk_multithread` 所在操作行，和 `加入队列` / `队列历史` 按钮抢横向空间。
- 当前修复只在 `Fengxi_Toolbox.py` 加载器 UI 层处理：
  - 保留 `批量并行（部分生效）` 开关文案和底层多线程能力。
  - `_install_parallel_mode_hint()` 不再创建底部并行状态标签。
  - `_refresh_parallel_mode_hint()` 会清空 `_fx_parallel_hint_var`，并销毁历史残留的 `_fx_parallel_hint_label`。
  - `_get_parallel_mode_message(...)` 仍保留给测试、诊断或未来非底部展示使用。
- 回归测试新增 `parallel_hint_removed_queue_actions_kept`，要求并行提示标签不存在、提示变量为空、`btn_queue_add` 与 `btn_queue_panel` 均存在。
- 验证：`python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py`、`python smoke_test.py` 14/14、`python full_debug_test.py` 110/110。
- 边界：未修改 `fengxi_runtime.bin`，未修改稳定区 `批量压缩` / `添加水印` 核心业务逻辑，也未删除任何项目外文件。

## 2026-05-23 图片 PDF 任务编排模块化
- `image` 任务的图片转 PDF 与多图合并 PDF 编排已从 `Fengxi_Toolbox.py` 拆到 `tools/fx_image_pdf_task.py`。
- 新模块负责文件收集、单图输出命名、合并输出命名、单图逐张 PDF 生成、并行调度和统一任务结果汇总。
- `Fengxi_Toolbox.py` 现在只保留 UI 参数解析、输出策略适配、进度回调、失败报告和历史结果写回，旧辅助函数继续保留为兼容薄封装。
- 图片转 PDF 的唯一命名规则保持不变：同名时自动后缀递增，避免覆盖已存在输出。
- 验证：`python -m py_compile Fengxi_Toolbox.py tools/fx_image_pdf_task.py full_debug_test.py smoke_test.py`、`python smoke_test.py` 14/14、`python full_debug_test.py` 135/135。

## 2026-05-28 Office COM dispatch guard
- Added `_safe_office_dispatch_ex(...)` in `Fengxi_Toolbox.py` to route Word COM creation around damaged pywin32 `gen_py` caches. This is a loader-layer patch over runtime behavior; `fengxi_runtime.bin` is unchanged.
- Convert task semantics were tightened in `tools/fx_convert_task.py`: matching Word/PPT inputs fail when the required COM app is unavailable, instead of silently copying the source file and allowing a false success summary.
- The fix is scoped to Office conversion / COM bootstrap and does not touch stable batch-compress or add-watermark core logic.
## 2026-05-28 Office COM Dispatch/DispatchEx safe patch
- The Office COM cache guard is now installed at loader import time for both `win32com.client.Dispatch` and `win32com.client.DispatchEx`.
- Reason: different runtime branches use different COM constructors. Conversion and some helpers use `DispatchEx`, but embedded batch-watermark uses plain `Dispatch("Word.Application")`; both must be guarded against damaged `win32com.gen_py` cache packages.
- Implementation shape:
  - `_FX_ORIGINAL_WIN32COM_DISPATCH` and `_FX_ORIGINAL_WIN32COM_DISPATCH_EX` keep the original pywin32 callables.
  - `_safe_office_dispatch(...)` and `_safe_office_dispatch_ex(...)` route Word through `_dispatch_com_app_dynamic("Word.Application")`.
  - `_install_safe_office_dispatch_patch()` marks the patched functions with `__fx_safe_office_dispatch_patch__` and avoids duplicate installation.
  - `_DisableWin32ComGenCache()` now suppresses both `GetClassForCLSID` and `GetModuleForCLSID`, because child-object wrapping can trigger either path.
- Scope: this is a loader-layer compatibility patch. Do not move it into `fengxi_runtime.bin`; keep future Office COM fixes near these helpers unless a dedicated Office adapter module is created.

## 2026-05-28 Batch watermark task adapter
- `watermark` now has a loader-layer task adapter `_run_watermark_task(app, input_value)` installed through `_patch_watermark_task()`.
- The adapter exists because the embedded runtime branch could not reliably express modern behavior: unified task result counts/outputs, single-file output strategies, safe overwrite staging, real failure status, and Word-to-PDF fallback.
- Responsibilities now owned by the adapter:
  - collect supported PDF/Word/PPT inputs via `app.collect_input_files(...)`
  - read UI settings with `_get_watermark_settings(...)`
  - plan output with `_build_watermark_output_path(...)`
  - call existing watermark core helpers (`create_watermark_packet`, `add_watermark_to_pdf`, `add_watermark_to_word`) rather than reimplementing watermark drawing
  - convert Word/PPT to temporary PDF when requested, then apply the PDF watermark
  - update `_set_progress_status(...)`, task outputs/counts, failed item report, and history-compatible result fields
- Conversion seam:
  - `_FX_RUNTIME_CONVERT_DOC_TO_PDF` preserves the embedded runtime converter
  - `_convert_doc_to_pdf_safely(...)` uses the runtime converter first and falls back to `_export_word_docx_to_pdf_safely(...)` if no valid PDF appears
  - global and runtime namespace `convert_doc_to_pdf`/`convert_ppt_to_pdf` are patched to the safe wrappers for downstream callers
- Keep this adapter as the preferred future maintenance point for batch watermark workflow bugs. Do not edit `fengxi_runtime.bin` for this path unless there is no loader-layer seam left.

## 2026-05-28 Word watermark rendering contract
- Direct Word watermark correctness must mean "visible when Word opens/renders the document", not merely "the `.docx` XML contains watermark text".
- `tools/fx_watermark_core.py` owns WordArt rendering details:
  - `WORD_WATERMARK_GRAY_RGB = 0xC0C0C0`
  - `WORD_WATERMARK_MIN_VISIBLE_OPACITY = 0.18`
  - `_word_visible_opacity(...)` clamps Word direct visible strength before converting to Word `Fill.Transparency`
  - `_add_word_header_watermark(...)` must keep `Fill.Visible = True`, `Fill.Solid()`, `Fill.ForeColor.RGB`, `Line.Visible = False`, and overlap-friendly wrapping
- Future Word watermark tests should include rendered validation:
  - helper-level `word_watermark_visible_when_exported`
  - task-level `watermark_docx_direct_visible_when_exported`
- Do not replace rendered validation with XML-only checks; XML-only checks allowed the "success but invisible" regression.

## 2026-05-28 Watermark color and preview seam
- The watermark color feature is split across the same loader/core seam as the rest of add-watermark:
  - `tools/fx_watermark_core.py` normalizes optional color input and applies it to ReportLab PDF drawing and WordArt fill.
  - `Fengxi_Toolbox.py` owns the UI (`wm_color_var`, swatch, hex entry, color chooser, preview) and passes the selected color through `_get_watermark_settings(...)`.
- Defaults are intentionally conservative:
  - PDF default remains the historical dark gray when no color is passed.
  - Word default remains the visible light gray used by the Word rendering fix.
- The preview is intentionally approximate and fast: PIL draws a mock page with rotated text. It should not call Office, PyMuPDF, or pypdf during UI interaction.
- Last-settings/preset capture now includes `wm_color_var`; queue snapshots may also contain the current watermark color.
## 2026-05-28 22:25:45 Startup recursion and packaged startup speed
- Startup lazy-tab initialization now uses _fx_lazy_tabs_initializing in both 	ools/fx_startup_patches.py and Fengxi_Toolbox.py; if a wm_* or other lazy attribute is accessed while its own page is still initializing, __getattr__ raises AttributeError instead of recursively initializing the same tab.
- Packaged startup no longer runs global _tighten_layout(...) while the CTk window is hidden. __main__ defers layout work, and _show_ready_window(...) schedules _run_startup_layout_refresh(...) after deiconify/lift, reducing CustomTkinter scrollbar redraw recursion risk.
- A Windows local mutex (Local\\FengxiToolboxSingleInstance) is acquired before app creation. Repeated double-clicks now exit the second process cleanly and keep the existing app as the single running instance.
- x_toolbox.spec excludes RapidOCR optional PyTorch/Paddle/TensorRT hidden-import paths plus 	orch, 	orchvision, 	orchaudio, paddle*, 	ensorflow, and 	ensorboard; default RapidOCR/ONNXRuntime OCR remains packaged.
- Packaged validation: dist_release_ascii\fx_toolbox\fx_toolbox.exe launched successfully, _internal no longer contains torch/paddle/tensorflow/tensorboard directories, and duplicate launch logged single_instance:already_running.

## 2026-05-28 Default package-and-open workflow
- User preference: after completing implementation or bug fixes, package the release build and open `dist_release_ascii\fx_toolbox\fx_toolbox.exe` automatically unless the user explicitly says not to.
- Packaging pre-step remains scoped: only stop the existing packaged EXE process whose executable path is this repository's `dist_release_ascii\fx_toolbox\fx_toolbox.exe`; do not touch project-external files or unrelated processes.
- Keep source validation first when code changed, then run `package.bat`, then open the packaged EXE for manual testing.

## 2026-06-03 Task Resume And Background Guard
- Shared resume helper module: `tools/fx_resume.py`.
- Long-running tasks should reuse completed outputs when the expected output already exists and passes the task-specific validator. Log this as `断点续跑`, count it as `success_count += 1` and `skipped_count += 1`, and do not reprocess the item.
- Generic `process_single_file` resume currently covers rename/meta/convert/image convert+compress/PDF encrypt/PDF split. PDF split resumes only when the split folder has at least the source page count of nonempty PDFs.
- Dedicated adapters own resume checks for ZIP, PDF OCR, image PDF, audio conversion/transcription, PDF compression, batch watermark, remove-watermark, and PDF merge.
- Background execution guard wraps patched `run_process` with Windows `SetThreadExecutionState`, preventing long jobs from being paused by idle/sleep while the app is in the background.
- Future feature adapters should join this model instead of inventing separate already-processed logic.

## 2026-06-09 Startup Layout Refresh Optimization
- Startup layout refresh must stay scoped to the current visible tab. Do not call `_tighten_layout(app)` without `task_name` during startup; that can iterate hidden lazy tabs and initialize ZIP/PDF/audio pages before the user opens them.
- `_run_startup_layout_refresh(app)` now resolves `current_task`, falls back to `DEFAULT_STARTUP_TAB`, then calls `_tighten_layout(app, task_name=task_name)` and `_refresh_visible_tab_layout(app, task_name)`.
- Startup layout refresh should not call `app.update_idletasks()` afterward. On CustomTkinter this can synchronously flush heavy pending redraw/layout work and make the opened window feel frozen.
- Switch-tab refresh keeps exactly one `update_idletasks()` after visible layout refresh; do not re-add the earlier duplicate idle flush in `tools/fx_startup_patches.py`.
- Startup post-show layout is staged with `after(...)`: shell layout, current-tab layout, then current-tab visible refresh. Keep this staged shape so the first visible window stays responsive instead of doing all fine layout work in one long callback.
- Performance events to watch after packaging: `startup_layout_refresh` should be `scheduled`; actual work is split into `startup_layout_shell`, `startup_layout_tighten_visible`, and `startup_layout_refresh_visible`.
- Regression anchors: `startup_layout_refresh_current_tab_only` and `startup_switch_tab_single_idle_refresh` in `full_debug_test.py`.
