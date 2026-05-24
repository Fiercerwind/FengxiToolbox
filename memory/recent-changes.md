# 最近变更

## 2026-05-24 20:03:54 | runtime
- 摘要：packaged and opened latest build after prefs modularization
- 文件：dist_release_ascii\fx_toolbox\fx_toolbox.exe,tools\fx_user_prefs.py,Fengxi_Toolbox.py,memory\recent-changes.md,memory\changes.jsonl
- 说明：Built the onedir release successfully with package.bat after the user-preferences modularization pass, then opened dist_release_ascii/fx_toolbox/fx_toolbox.exe for manual testing. The build completed cleanly and the app process was started from the release directory.

## 2026-05-24 20:00:59 | runtime
- 摘要：legacy presets storage seam
- 文件：Fengxi_Toolbox.py, full_debug_test.py, tools/fx_user_prefs.py, memory.md, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Moved legacy preset storage helpers into tools/fx_user_prefs.py without adding any dedicated preset center UI. Fengxi_Toolbox.py keeps compatibility wrappers; last_settings_no_dedicated_preset_center remains covered. Validation passed with py_compile, smoke_test 14/14, and full_debug_test 149/149.

## 2026-05-24 19:53:02 | runtime
- 摘要：last settings storage seam
- 文件：Fengxi_Toolbox.py, full_debug_test.py, tools/fx_user_prefs.py, memory.md, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Moved pure last_settings storage helpers into tools/fx_user_prefs.py: category normalization, load/save last settings entries, and active category resolution. UI capture/apply logic remains in Fengxi_Toolbox.py. Validation passed with py_compile, smoke_test 14/14, and full_debug_test 148/148.

## 2026-05-24 19:43:11 | runtime
- 摘要：user prefs storage modularization
- 文件：Fengxi_Toolbox.py, full_debug_test.py, tools/fx_user_prefs.py, memory.md, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Added tools/fx_user_prefs.py with UserPrefsContext for user_prefs.json storage, output strategy, remove-watermark mode, watermark text, and watermark filename rule persistence. Fengxi_Toolbox.py keeps compatibility wrappers and UI trace bindings unchanged. Validation passed with py_compile, smoke_test 14/14, and full_debug_test 147/147.

## 2026-05-24 19:24:29 | convert
- 摘要：convert single-file adapter seam
- 文件：Fengxi_Toolbox.py, full_debug_test.py, tools/fx_convert_core.py, tools/fx_convert_task.py, memory.md, memory/architecture.md, memory/categories/convert-audio-image.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Added ConvertFileContext and process_convert_file for word2pdf/pdf2word/ppt2pdf single-file adapter routing while keeping real Office COM/pdf2docx conversion on runtime-injected functions. imgs2pdf remains on the dedicated task adapter. Validation passed with py_compile, smoke_test 14/14, and full_debug_test 146/146.

## 2026-05-24 18:45:56 | runtime
- 摘要：packaged and opened convert modularization build
- 文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Built release onedir after convert imgs2pdf task adapter modularization and opened dist_release_ascii/fx_toolbox/fx_toolbox.exe for manual testing. Source validation before packaging: py_compile passed, smoke_test 14/14, full_debug_test 145/145.

## 2026-05-24 18:40:37 | convert
- 摘要：convert imgs2pdf task adapter modularization
- 文件：Fengxi_Toolbox.py, full_debug_test.py, tools/fx_convert_core.py, tools/fx_convert_task.py, memory/architecture.md, memory/categories/convert-audio-image.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Added tools/fx_convert_task.py to route only convert/imgs2pdf through a dedicated task adapter over the new convert core. Fengxi_Toolbox.py now keeps a thin convert imgs2pdf adapter while word/pdf/ppt conversion stays on the runtime path. Added regression coverage for the convert task module and real imgs2pdf workflow. Validation passed with py_compile, smoke_test 14/14, and full_debug_test 145/145.

## 2026-05-24 12:51:28 | runtime
- 摘要：audio module cleanup and OCR test stabilization
- 文件：Fengxi_Toolbox.py, full_debug_test.py, tools/fx_audio_task.py, memory.md, memory/architecture.md, memory/categories/convert-audio-image.md, memory/debug-status.md, memory/recent-changes.md, agent.md
- 说明：Removed the dead post-return legacy audio implementation from Fengxi_Toolbox.py so audio now stays on the new task module seam only. Also stabilized full_debug_test OCR coverage by avoiding network-dependent rapidocr model-download behavior in the workflow test, while keeping the real OCR engine code unchanged. Validation passed with py_compile, smoke_test 14/14, and full_debug_test 142/142.

## 2026-05-24 10:59:01 | pdf_file
- 摘要：meta core modularization
- 文件：Fengxi_Toolbox.py, tools/fx_meta_core.py, full_debug_test.py, memory.md, memory/architecture.md, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Added tools/fx_meta_core.py for metadata/privacy helpers: file timestamp copying, PDF author metadata writing, Office author helper, output path planning, and meta process_single_file adapter. Fengxi_Toolbox.py now keeps thin wrappers and routes task_type=meta through the module while preserving legacy semantics. Verified with py_compile, smoke_test 14/14, and full_debug_test 141/141.

## 2026-05-24 09:35:32 | runtime
- 摘要：file dedup task adapter modularization
- 文件：Fengxi_Toolbox.py, tools/fx_file_manager_task.py, tools/fx_file_manager_core.py, full_debug_test.py, memory.md, memory/architecture.md, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Added tools/fx_file_manager_task.py as the file + dedup task adapter layer. Fengxi_Toolbox.py now routes real file dedup work through _run_file_dedup_task_core -> run_file_dedup_task while tools/fx_file_manager_core.py keeps the MD5 dedup core. Added regression coverage for the task adapter seam and verified with py_compile, smoke_test 14/14, and full_debug_test 139/139.

## 2026-05-24 01:17:42 | runtime
- 摘要：file dedup core run_process route
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory.md, memory/architecture.md, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Routed file + dedup through the loader adapter and tools.fx_file_manager_core.run_file_dedup_task while preserving single-thread whole-folder MD5 duplicate deletion semantics. Strengthened the real app.run_process file_dedup regression to prove the core module path is used. Verified with py_compile, smoke_test 14/14, and full_debug_test 138/138.

## 2026-05-24 00:43:45 | ui
- 摘要：bottom progress status moved out of action row
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory.md, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md, memory/categories/pdf-file-meta-zip.md
- 说明：Moved the bottom progress status label out of the button action row and into an independent grid slot on the bottom bar so long file names no longer squeeze the multithread switch, start/stop buttons, or queue actions. Added a regression that asserts the status label uses grid on the bottom bar, not pack inside the action row. Verified with py_compile, smoke_test 14/14, and full_debug_test 138/138.

## 2026-05-23 20:13:42 | runtime
- 摘要：文件管家重命名核心模块化
- 文件：Fengxi_Toolbox.py, tools/fx_file_manager_core.py, full_debug_test.py, memory.md, memory/architecture.md, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md, memory/recent-changes.md
- 说明：新增 tools/fx_file_manager_core.py，承接 file + rename 的规则解析、输出路径规划和单文件改名复制；Fengxi_Toolbox.py 仅在 file + rename 路由到新模块，dedup 继续保留在原 run_process() 单线程分支。验证：py_compile 通过，smoke_test 14/14，full_debug_test 136/136。

## 2026-05-23 19:02:47 | image
- 摘要：image pdf task modularization
- 文件：Fengxi_Toolbox.py, tools/fx_image_pdf_task.py, full_debug_test.py, memory.md, memory/architecture.md, memory/categories/convert-audio-image.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Moved image-to-PDF and image-merge-PDF orchestration into tools/fx_image_pdf_task.py. Fengxi_Toolbox.py remains an adapter for UI parsing, output strategy adaptation, progress/history callbacks, and failed report handling. Validation: py_compile passed, smoke_test 14/14, full_debug_test 135/135. No fengxi_runtime.bin change and no project-external deletion.

## 2026-05-23 18:01:12 | pdf_file
- 摘要：pdf ocr task modularization
- 文件：Fengxi_Toolbox.py, tools/fx_pdf_ocr_task.py, full_debug_test.py, memory.md, memory/architecture.md, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md
- 说明：Moved PDF OCR task orchestration into tools/fx_pdf_ocr_task.py. Fengxi_Toolbox.py now keeps UI parameter parsing, progress adapter, failed report, and structured task_result handling while tools/fx_pdf_ocr.py remains the OCR engine/backend module. Validation: py_compile passed, smoke_test 14/14, full_debug_test 134/134. No fengxi_runtime.bin change, no OCR engine algorithm change, and no project-external deletion.

## 2026-05-23 17:33:19 | pdf_file
- 摘要：pdf compress core modularization
- 文件：Fengxi_Toolbox.py, tools/fx_pdf_compress_core.py, full_debug_test.py, memory/architecture.md, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md
- 说明：Moved PDF compression profiles, image recompression/downsampling, output naming, and single-file compression into tools/fx_pdf_compress_core.py. Fengxi_Toolbox.py keeps thin compatibility wrappers and task-level UI/progress/history orchestration. Validation: py_compile passed, smoke_test 14/14, full_debug_test 133/133. No fengxi_runtime.bin change and no project-external deletion.

## 2026-05-23 17:18:24 | runtime
- 摘要：packaged and opened release build
- 文件：package.bat, VERSION, dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- 说明：Built the onedir release with package.bat after the stable-core modularization split, then opened dist_release_ascii/fx_toolbox/fx_toolbox.exe. Build succeeded with pyinstaller and runtime asset copy. Version file remains 4.0.0; no fengxi_runtime.bin change.

## 2026-05-23 17:16:39 | runtime
- 摘要：stable core exception guardrail
- 文件：agent.md, memory/constraints.md, memory/recent-changes.md, memory/changes.jsonl
- 说明：Documented the narrow 2026-05-23 exception: stable batch-compress and add-watermark core logic may be touched only for explicit modularization work, with thin compatibility wrappers and regression validation; it does not relax the default no-behavior-change rule. No project-external deletion.

## 2026-05-23 17:14:01 | runtime
- 摘要：stable core modularization
- 文件：Fengxi_Toolbox.py, tools/fx_watermark_core.py, tools/fx_zip_core.py, full_debug_test.py, memory/architecture.md, memory/categories/watermark-and-remove.md, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md
- 说明：Moved add-watermark core helpers into tools/fx_watermark_core.py and ZIP planning/execution into tools/fx_zip_core.py under explicit user authorization for stable-core modularization. Fengxi_Toolbox.py keeps compatibility wrappers and routes zip tasks through the new core while preserving progress/history/result semantics. Validation: py_compile passed, smoke_test 14/14, full_debug_test 131/131. No fengxi_runtime.bin change and no project-external deletion.

## 2026-05-23 16:00:00 | runtime
- 摘要：队列历史纯逻辑模块化
- 文件：Fengxi_Toolbox.py, full_debug_test.py, tools\fx_queue_history.py, memory\architecture.md, memory\debug-status.md
- 说明：新增 tools/fx_queue_history.py，通过 QueueHistoryContext 将队列历史读写、90天自动清理、最大条数裁剪、运行态字段清理、状态文案、搜索 blob 和筛选逻辑从主加载器抽出；Fengxi_Toolbox.py 保留薄包装兼容队列 UI/历史/失败重试/诊断包。新增 queue_history_module_context 回归。验证：py_compile、真实导入探针、smoke_test 14/14、full_debug_test 129/129。未改 fengxi_runtime.bin，未改批量压缩/添加水印核心逻辑。

## 2026-05-23 12:18:30 | runtime
- 摘要：任务历史导出与诊断包模块化
- 文件：Fengxi_Toolbox.py, full_debug_test.py, tools\fx_task_history_exports.py, memory\architecture.md, memory\debug-status.md
- 说明：新增 tools/fx_task_history_exports.py，通过 TaskHistoryExportContext 将任务历史 JSON/日志/报告/诊断包组装与脱敏从主加载器抽出；Fengxi_Toolbox.py 保留薄包装兼容现有 UI/测试；新增 task_history_exports_module_context 回归。验证：py_compile、真实导入探针、smoke_test 14/14、full_debug_test 128/128。未改 fengxi_runtime.bin，未改批量压缩/添加水印核心逻辑。

## 2026-05-23 11:29:09 | runtime
- 摘要：启动补丁安装器模块化
- 文件：Fengxi_Toolbox.py, full_debug_test.py, tools/fx_startup_patches.py, memory/architecture.md, memory/debug-status.md
- 说明：新增 tools/fx_startup_patches.py，将启动隐藏窗口、懒加载页签、切页刷新、help/donate 内联重定向和切页性能记录的补丁 implementation 移出主加载器；Fengxi_Toolbox.py 仅装配 StartupPatchContext 并调用 install_startup_performance_patch。新增 startup_patch_installer_module 回归；验证 py_compile、真实导入探针、smoke_test 14/14、full_debug_test 127/127。

## 2026-05-23 09:34:41 | runtime
- 摘要：启动性能 profiling 与补丁模块拆分一期
- 文件：Fengxi_Toolbox.py, full_debug_test.py, tools/fx_performance.py, tools/fx_runtime_patches.py, memory/architecture.md, memory/debug-status.md
- 说明：新增轻量性能 JSONL recorder，记录 runtime_load、main_create_app、startup_total、lazy_tab_init、switch_tab 等启动/切页/首次加载耗时；性能日志写入用户配置目录 performance.jsonl 并自动裁剪；诊断包加入最近性能样本；新增 fx_runtime_patches 模块并将通用 wrap_callable seam 从主加载器抽出。验证 py_compile、真实导入探针、smoke_test 14/14、full_debug_test 126/126。

## 2026-05-23 01:00:02 | runtime
- 摘要：功能注册表一期
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/categories/pdf-file-meta-zip.md
- 说明：新增 FEATURE_REGISTRY 统一描述各功能 label、icon、输入支持、输出策略、并行策略、预览模式、风险标记和稳定区标记；QUEUE_TASK_LABELS、输出策略集合、并行安全/强制单线程集合与提示均从注册表派生；开始前预览、输出策略判断、并行提示、历史功能名展示改用注册表 helper；删除被覆盖的旧硬编码策略来源。OCR 回归测试隔离 pdf_ocr_cls 状态，避免外部模型下载波动；OCR 对比报告失败改为警告跳过，不阻断主 OCR 产物。验证 py_compile、smoke_test 14/14、full_debug_test 122/122。

## 2026-05-23 00:21:54 | runtime
- 摘要：任务历史一键诊断包
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：任务历史详情窗口新增诊断包按钮，可导出 zip 问题反馈包，包含 README、当前历史条目、结构化 task_result、任务报告、任务日志、环境探测和最近历史摘要；环境探测覆盖版本、系统/Python、ffmpeg、OCR 后端、Word/PowerPoint COM；诊断包内容会将项目目录脱敏为 <PROJECT_ROOT>、用户目录脱敏为 <USER_HOME>，且不复制原始输入文件；新增 task_history_diagnostic_filename、task_history_diagnostic_export_package、task_history_diagnostic_export_empty 回归；验证 py_compile、smoke_test 14/14、full_debug_test 119/119。

## 2026-05-22 23:32:33 | ui
- 摘要：使用教程内嵌示例流程
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：将内嵌使用教程重写为按任务场景组织的滚动说明页，覆盖三步上手、输出策略与安全确认、任务队列与历史记录、PDF OCR 图像增强与质量回退、PDF 压缩/合并/拆分/加密、批量水印、去除水印、图片工厂、格式转换/音频、属性隐私/文件管家、批量压缩和性能排障；新增 inline_help_workflow_sections 回归；验证 py_compile、smoke_test 14/14、full_debug_test 116/116。

## 2026-05-22 23:21:01 | runtime
- 摘要：开始前任务预览确认
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory\architecture.md, memory\debug-status.md, memory\recent-changes.md
- 说明：人工点击开始前新增任务预览确认，展示功能、模式、输入类型、处理文件数、跳过数量、输出策略和风险提示；队列执行跳过确认框；新增 start_preview_counts_and_risks、start_preview_confirmation_cancel、start_preview_skips_queue_worker 回归；验证 py_compile、smoke_test 14/14、full_debug_test 115/115。

## 2026-05-22 23:03:32 | pdf_file
- 摘要：OCR 图像增强与质量回退
- 文件：Fengxi_Toolbox.py, tools\fx_pdf_ocr.py, full_debug_test.py, memory\categories\pdf-file-meta-zip.md, memory\debug-status.md
- 说明：OCR 搜索版 PDF 新增 auto/off/light/scan 图像增强；auto 后端按质量评分低质回退备用后端；对比报告记录质量与增强候选；OCR 图像增强纳入上次设置记忆；验证 py_compile、smoke_test 14/14、full_debug_test 112/112。

## 2026-05-22 20:09:57 | ui
- 摘要：remove parallel status hint and restore queue actions
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md
- 说明：Removed the visible bottom-row 并行状态 hint label so it no longer consumes space beside 加入队列 / 队列历史. Kept the 批量并行（部分生效） switch label and underlying parallel capability; _refresh_parallel_mode_hint now clears the hint variable and destroys stale labels. Added regression parallel_hint_removed_queue_actions_kept. Validation: py_compile passed, smoke_test 14/14, full_debug_test 110/110.
