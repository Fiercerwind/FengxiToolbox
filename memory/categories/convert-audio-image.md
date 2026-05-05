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
