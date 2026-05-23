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
