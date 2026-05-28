# 转换、音频、图片

## 文档转换
- 任务类型：`convert`
- 模式：
  - `word2pdf`
  - `pdf2word`
  - `ppt2pdf`
  - `imgs2pdf`
- `convert` 任务整体走单线程安全路径。
- `pdf2word` 支持复杂/大文件跳过策略，避免乱码。

## 2026-05-24 格式转换单文件 adapter seam
- `tools/fx_convert_task.py` 新增 `ConvertFileContext` 与 `process_convert_file(...)`，用于单文件 `word2pdf` / `pdf2word` / `ppt2pdf` 的窄适配。
- adapter 负责统一输出路径规划、复杂 PDF 跳过复制、日志、返回字典和测试注入；真实转换仍调用 context 注入的 runtime 能力：
  - `convert_doc_to_pdf(...)`
  - `convert_pdf_to_word(...)`
  - `convert_ppt_to_pdf(...)`
- `Fengxi_Toolbox.py` 的 `_patch_convert_file_adapter()` 只接管 `task_type == "convert"` 且模式为 `word2pdf` / `pdf2word` / `ppt2pdf` 的 `process_single_file(...)`；`imgs2pdf` 继续走专用任务 adapter。
- 当前边界：这一步没有重写 Office COM 或 `pdf2docx` 后端，只把可测试 seam 先建立起来。后续如果某个转换后端失败，应优先在 `ConvertFileContext` 或 `process_convert_file(...)` 外围补能力。
- 回归：`convert_file_adapter_module_exports`，并确认 `pdf_to_word`、`word_to_pdf`、`ppt_to_pdf`、`imgs2pdf_workflow` 继续通过。
- 验证：`py_compile` 通过，`smoke_test.py` 14/14，`full_debug_test.py` 146/146。

## 2026-05-24 格式转换核心与 imgs2pdf 任务适配
- `tools/fx_convert_core.py` 已承接纯规则：`CONVERT_MODE_SPECS`、模式归一化、模式描述、输入文件收集、输出路径规划。
- `Fengxi_Toolbox.py` 的 `FEATURE_REGISTRY["convert"].preview_modes` 已覆盖 `word2pdf`、`pdf2word`、`ppt2pdf`、`imgs2pdf`；开始前预览和队列描述通过 `_get_convert_preview_detail(...)` / `_collect_convert_files(...)` 使用该核心。
- `tools/fx_convert_task.py` 新增 `ConvertImgsToPdfCallbacks` 与 `run_convert_imgs_to_pdf_task_core(...)`，当前只接管 `convert + imgs2pdf`，复用图片 PDF 核心的合并能力和结果统计。
- `Fengxi_Toolbox.py` 新增 `_run_convert_imgs_to_pdf_task(...)` 与 `_patch_convert_imgs_to_pdf_task()`，仅在 `task_type == "convert"` 且模式为 `imgs2pdf` 时路由到新模块；输出继续固定到 `【处理完成】结果文件夹`，保持原 `imgs2pdf_图集合并.pdf` 命名语义。
- `word2pdf`、`pdf2word`、`ppt2pdf` 暂不下沉到新模块，仍保留原 `fengxi_runtime.bin` / runtime `run_process()` 路径，因为依赖 Office COM 与 `pdf2docx` 细节。
- 回归：`convert_core_module_exports`、`convert_task_imgs2pdf_module_exports`、`convert_preview_uses_core_rules`、`imgs2pdf_workflow`。验证：`py_compile` 通过，`smoke_test.py` 14/14，`full_debug_test.py` 145/145。

## 音频工具
- 任务类型：`audio`
- 模式：
  - `video2mp3`
  - `convert`
- 输出格式常见值：
  - `mp3`
  - `wav`
  - `flac`
  - `m4a`
- 当前源码层用 ffmpeg 版 `_ffmpeg_convert` 覆盖了运行时里的 `convert_audio_format`。

## 2026-05-22 音视频逐文件并行
- `audio` 任务已在加载器层接入逐文件 `ThreadPoolExecutor` 并行，仅在 `enable_multithread` 开启且待处理文件数大于 1 时生效。
- 支持扩展名集中在 `AUDIO_VALID_AUDIO_EXTS` 与 `AUDIO_VALID_VIDEO_EXTS`；视频源会抽取音频到目标格式，音频源会转换格式，其他文件原样复制。
- 线程数上限继续使用 `PARALLEL_MAX_WORKERS = 4`，实际并行度取文件数与上限的较小值。
- 线程内只做文件转换/复制，日志、进度、统一任务结果仍在主流程汇总，避免 Tk UI 跨线程写入。
- 结构化结果会写回 `processed_count`、`success_count`、`failed_count`、`outputs`、`output_root`，失败时保留相对路径失败项。
- 回归：`audio_parallel_executor` 会 monkeypatch `convert_audio_format` 与 `ThreadPoolExecutor`，确认多 worker、输出 `a.mp3`/`b.mp3`，且 `task_result.status == success`。

## 2026-05-24 音频任务模块化收口
- 新增并接管 `tools/fx_audio_task.py`，当前导出 `AudioTaskCallbacks`、`collect_audio_files(...)`、`get_audio_task_args(...)`、`build_audio_output_path(...)`、`process_one_audio_file(...)`、`run_audio_task_core(...)`。
- `Fengxi_Toolbox.py` 的 `_collect_audio_files(...)`、`_get_audio_task_args(...)`、`_build_audio_output_path(...)`、`_process_one_audio_file(...)`、`_run_audio_task(...)` 都是薄包装或 adapter。
- 已清理主文件里 `return run_audio_task_core(...)` 后面残留的旧音频实现，避免后续维护者误以为主文件还有第二套执行路径。
- 行为边界继续保持：`video2mp3` 只处理视频源；`convert` 只处理音频源；不支持的文件原样复制；缺少后端时复制原文件并记录警告状态。
- 回归：`audio_task_module_exports` 覆盖模块级接口；`audio_parallel_executor` 覆盖真实 `app.run_process(..., "audio")` 并行路径。

## 图片工厂
- 任务类型：`image`
- 模式：
  - `convert`
  - `compress`
  - `to_pdf`
  - `merge_pdf`
- 支持目标格式：
  - `JPG`
  - `PNG`
  - `BMP`
  - `WEBP`
- 2026-05-05 新增图片 PDF 能力：
  - `to_pdf`：每张图片生成一份同名 PDF
  - `merge_pdf`：把输入图片按文件名顺序合并成一份 PDF
  - 支持图片扩展名：`.jpg` / `.jpeg` / `.png` / `.bmp` / `.webp` / `.tif` / `.tiff`
  - 两个新模式由 `Fengxi_Toolbox.py` 加载器层接管 `image` 任务，不修改 `fengxi_runtime.bin`
  - `merge_pdf` 复用现有 `merge_images_to_pdf()` 底座
  - 输出目录继续复用 `RESULT_FOLDER_NAME`
- 如果勾选图片页“处理后删除源文件”，新 PDF 模式成功后也会删除已处理源图

## 2026-05-23 图片转 PDF 任务核心拆分
- `tools/fx_image_pdf_task.py` 作为图片 PDF 任务核心模块，承担文件收集、输出命名、并行执行和统一任务结果回写。
- `to_pdf` 继续保持“每张图片生成一份 PDF”的语义；`merge_pdf` 继续保持“按文件名顺序合并成一份 PDF”的语义。
- 输出命名会在同名冲突时自动递增后缀，测试已专门覆盖这一点，避免误把唯一命名当成回归。
- `Fengxi_Toolbox.py` 只作为适配层，不改变图片 PDF 的可见行为。

## 2026-05-28 Office COM gen_py cache fallback
- User log showed Word COM init failure with `win32com.gen_py ... has no attribute CLSIDToPackageMap`; local repro showed the same family as `CLSIDToClassMap`. Root cause is damaged pywin32 generated COM cache, not broken Word itself.
- `Fengxi_Toolbox.py` now preserves the original `win32com.client.DispatchEx` and installs `_safe_office_dispatch_ex(...)`; `Word.Application` goes through `_dispatch_com_app_dynamic(...)` using `pythoncom.CoCreateInstance + win32com.client.dynamic.Dispatch` to bypass bad gen_py.
- `_DisableWin32ComGenCache` now disables both `GetClassForCLSID` and `GetModuleForCLSID`, so Word child-object access does not re-enter damaged generated modules.
- `word2pdf` / `ppt2pdf` now call `_convert_doc_to_pdf_safely(...)` / `_convert_ppt_to_pdf_safely(...)`, keeping gen cache disabled during conversion.
- `tools/fx_convert_task.py` now marks Word/PPT COM unavailable as `failed` for matching Office inputs instead of copying the source and letting the run end as a false success.
- Regression coverage: `convert_file_missing_office_fails_instead_of_copying` and `word_dispatchex_gen_py_safe_patch`; validation passed with py_compile, smoke_test 14/14, full_debug_test 151/151.
