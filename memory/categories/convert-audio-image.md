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
- 支持目标格式：
  - `JPG`
  - `PNG`
  - `BMP`
  - `WEBP`

