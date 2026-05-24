# 风兮工具箱记忆入口

## 目的
- 让后续会话先读取少量高价值记忆，再按任务类别补充上下文，避免每次都重新扫描整个项目。

## 首读顺序
1. [agent.md](agent.md)
2. [memory/load-order.md](memory/load-order.md)
3. [memory/distilled-memory.md](memory/distilled-memory.md)
4. [memory/recent-changes.md](memory/recent-changes.md)

## 再按类别加载
- 运行时 / 架构：[memory/architecture.md](memory/architecture.md)
- 稳定区与风险：[memory/constraints.md](memory/constraints.md)
- 水印 / 去水印：[memory/categories/watermark-and-remove.md](memory/categories/watermark-and-remove.md)
- 转换 / 音频 / 图片：[memory/categories/convert-audio-image.md](memory/categories/convert-audio-image.md)
- PDF / 文件 / 元数据 / 压缩：[memory/categories/pdf-file-meta-zip.md](memory/categories/pdf-file-meta-zip.md)
- GitHub 同步 / 版本发布：[memory/categories/repo-sync-release.md](memory/categories/repo-sync-release.md)
- 调试现状：[memory/debug-status.md](memory/debug-status.md)
- GitHub 功能调研：[memory/research/github-feature-opportunities-2026-04-20.md](memory/research/github-feature-opportunities-2026-04-20.md)
- OCR 多后端调研：[memory/research/ocr-backend-paths-2026-04-20.md](memory/research/ocr-backend-paths-2026-04-20.md)

## 当前项目快照
- 项目主程序文件：`Fengxi_Toolbox.py`
- 运行时载荷：`fengxi_runtime.bin`
- 快速测试：`smoke_test.py`
- 全功能测试：`full_debug_test.py`
- 备份与记忆工具：`tools/fx_workspace_tools.py`
- OCR 引擎模块：`tools/fx_pdf_ocr.py`
- GitHub 自动同步脚本：`tools/fx_git_sync.ps1`
- 版本发布脚本：`tools/fx_release_version.ps1`
- 当前稳定区：批量压缩、添加水印
- 当前新增 PDF 能力：OCR 搜索版 PDF
- 当前 OCR 架构：`tools/fx_pdf_ocr.py` 引擎后端 + `tools/fx_pdf_ocr_task.py` 任务编排 + 风兮自有工作流多后端可切换
- 当前图片 PDF 架构：`tools/fx_image_pdf_task.py` 任务核心 + `Fengxi_Toolbox.py` UI/进度/历史适配层
- 当前格式转换架构：`tools/fx_convert_core.py` 承接转换模式、文件收集和输出规划；`tools/fx_convert_task.py` 承接 `convert + imgs2pdf` 任务适配，并提供 `ConvertFileContext` / `process_convert_file(...)` 单文件转换 adapter seam；`word2pdf` / `pdf2word` / `ppt2pdf` 的真实转换仍复用 runtime 注入的 Office COM / `pdf2docx` 能力
- 当前音频架构：`tools/fx_audio_task.py` 承接音频任务编排与逐文件处理，`Fengxi_Toolbox.py` 只保留薄包装和 `run_process` 路由；主文件里不应再保留旧音频死代码
- 当前文件管家架构：`tools/fx_file_manager_task.py` 承接 `file + dedup` 任务适配，`tools/fx_file_manager_core.py` 承接重命名核心与去重核心；`file + dedup` 已由加载器路由到 `_run_file_dedup_task(...)` / `run_file_dedup_task(...)`，继续保持单线程全局 MD5 比对与删除重复文件语义
- 当前属性隐私架构：`tools/fx_meta_core.py` 承接时间修改、PDF 作者写入、Office 作者 helper 和 `meta` 单文件处理；`Fengxi_Toolbox.py` 只保留兼容包装与 `process_single_file` 路由
- 当前用户偏好架构：`tools/fx_user_prefs.py` 承接 `user_prefs.json` 读写、输出策略、去水印模式、水印文本、水印文件名跳过规则、`last_settings` 纯存储和 legacy `presets` 存储 helper；`Fengxi_Toolbox.py` 保留同名薄包装、UI trace/控件绑定、上次设置捕获/应用逻辑；不要新增专门“预设中心”UI
- 当前底部进度 UI：进度条在底部第 0 行左侧，进度状态文本在第 0 行右侧；不要再把进度状态 pack 进按钮 action row，避免挤压 `批量并行`、开始/停止、`加入队列`、`队列历史`
- 当前发布基线：`4.0` / `v4.0.0`
