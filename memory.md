# 风兮工具箱记忆入口

## 目的
- 让后续会话先读取少量高价值记忆，再按任务类别补充上下文，避免每次都重新扫描整个项目。

## 首读顺序
1. [agent.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/agent.md)
2. [memory/load-order.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory/load-order.md)
3. [memory/distilled-memory.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory/distilled-memory.md)
4. [memory/recent-changes.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory/recent-changes.md)

## 再按类别加载
- 运行时 / 架构：[memory/architecture.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory/architecture.md)
- 稳定区与风险：[memory/constraints.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory/constraints.md)
- 水印 / 去水印：[memory/categories/watermark-and-remove.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory/categories/watermark-and-remove.md)
- 转换 / 音频 / 图片：[memory/categories/convert-audio-image.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory/categories/convert-audio-image.md)
- PDF / 文件 / 元数据 / 压缩：[memory/categories/pdf-file-meta-zip.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory/categories/pdf-file-meta-zip.md)
- GitHub 同步 / 版本发布：[memory/categories/repo-sync-release.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory/categories/repo-sync-release.md)
- 调试现状：[memory/debug-status.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory/debug-status.md)
- GitHub 功能调研：[memory/research/github-feature-opportunities-2026-04-20.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory/research/github-feature-opportunities-2026-04-20.md)
- OCR 多后端调研：[memory/research/ocr-backend-paths-2026-04-20.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory/research/ocr-backend-paths-2026-04-20.md)

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
- 当前 OCR 架构：风兮自有工作流 + 多后端可切换
- 当前发布基线：`3.0` / `v3.0.0`
