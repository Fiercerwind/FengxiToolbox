# 蒸馏记忆

## 初始蒸馏
- 这是一个“加载器 + 封装运行时”项目，真正业务逻辑不直接写在 `Fengxi_Toolbox.py`，而是来自 `fengxi_runtime.bin`。
- 后续修改应优先落在加载器补丁层、测试层、记忆层，避免贸然深入稳定业务体。
- `批量压缩` 与 `添加水印` 是用户明确标记的稳定区，默认不能动。
- 很多功能不能只测 helper，必须测 `FengxiToolboxApp.run_process()` 的真实工作流。
- `PDF 合并` 和 `文件去重` 都依赖 `run_process()` 内的专用单线程分支；若分流错误，会出现“功能看似存在但实际不执行”的假象。
- Office、音频、拖拽、窗体样式在当前机器可用，但跨机器仍受环境影响。


## 自动蒸馏 2026-04-25 16:03:11
- 覆盖变更：第 1 到第 30 条
- [constraints] 摘要：新增最高优先级约束：不得删除项目外文件
  关联文件：agent.md, memory\constraints.md
- [debug] 摘要：新增并通过 30 项全功能增强自检
  关联文件：full_debug_test.py, smoke_test.py, memory\debug-status.md
- [pdf_file] 摘要：修复 PDF 合并与文件去重的任务分流；新增 OCR 搜索版 PDF (Umi-OCR 桥接实现)；OCR 搜索版 PDF 独立化为风兮 OCR 工作流；OCR 升级为多后端可切换架构；OCR 面板新增后端探测状态展示；OCR 新增多后端对比报告输出；修复OCR单文件与拖拽输入路径拼接；修复OCR打包版 onnxruntime DLL 初始化失败；OCR 页面改为按需检测并取消状态预判拦截；修复打包版 OCR 的 onnxruntime 运行库冲突
  关联文件：Fengxi_Toolbox.py, tools\fx_umi_ocr.py, full_debug_test.py, memory.md, memory\categories\pdf-file-meta-zip.md, memory\debug-status.md, tools\fx_pdf_ocr.py, fx_toolbox.spec, 风兮文件批量处理工具箱2.0.spec, agent.md, memory\recent-changes.md, memory\research\ocr-backend-paths-2026-04-20.md, memory\architecture.md, package.bat
- [remove_wm] 摘要：修复页眉图片型水印漏删并锁定去水印单线程调度；收紧去水印判定，修复误删正常图文；修复PDF去水印回退失败并保留Word安全删除；修复PDF去水印批量COM污染，改为独立Word会话；修复去水印单文件输出规则并阻止PDF失败伪成功
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, memory\categories\watermark-and-remove.md, memory\architecture.md, memory\debug-status.md, memory\recent-changes.md
- [research] 摘要：整理 GitHub 相关项目并提炼风兮工具箱可新增功能
  关联文件：memory.md, memory\research\github-feature-opportunities-2026-04-20.md
- [runtime] 摘要：建立项目记忆与备份体系；启动改为延迟建页并切换为快速目录式打包；输入入口新增单文件支持并补齐单文件调度；启动性能优化：对 pdf2docx 与 moviepy 引入运行时懒加载代理；浏览入口改回 Windows 原生选择器，并保持文件/文件夹同选；修复系统选择器返回字节路径导致的脏路径与去水印卡住；修复拖拽单文件被降级为文件夹，并修正去水印单文件结果目录拼接
  关联文件：agent.md, memory.md, memory\load-order.md, memory\architecture.md, memory\constraints.md, memory\categories\watermark-and-remove.md, memory\categories\convert-audio-image.md, memory\categories\pdf-file-meta-zip.md, memory\debug-status.md, memory\distilled-memory.md, memory\recent-changes.md, tools\fx_workspace_tools.py, Fengxi_Toolbox.py, fx_toolbox.spec, package.bat, full_debug_test.py
- [ui] 摘要：收紧左侧导航并将 OCR 配置改为右侧双栏；进一步压紧左侧导航并重构 PDF OCR 双栏布局；左侧导航改为固定图标槽并统一按钮节奏；左侧导航恢复真实图标并保留统一对齐；统一底部教程赞助卡片并新增风兮应用图标
  关联文件：Fengxi_Toolbox.py, memory\categories\pdf-file-meta-zip.md, memory\debug-status.md, memory\recent-changes.md, memory\architecture.md, tools\generate_fengxi_icon.py, fx_toolbox.spec

## 自动蒸馏 2026-05-09 16:15:33
- 覆盖变更：第 31 到第 60 条
- [image] 摘要：图片模块新增图片转PDF和多图合并PDF
  关联文件：Fengxi_Toolbox.py, smoke_test.py, full_debug_test.py, memory/categories/convert-audio-image.md
- [pdf_file] 摘要：PDF 模块新增 PDF 压缩并改为功能入口式布局
  关联文件：Fengxi_Toolbox.py, smoke_test.py, full_debug_test.py, memory/categories/pdf-file-meta-zip.md
- [progress] 摘要：统一修复运行时进度条并接入OCR页级进度
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, memory/recent-changes.md, memory/architecture.md, memory/debug-status.md
- [repo] 摘要：初始化本地 Git 仓库并建立首个 .gitignore 上传基线；接入 GitHub 远端并完成首次推送；补齐 GitHub 首页说明、依赖清单与 Windows 自动打包工作流；将 GitHub 打包工作流升级为缓存依赖并使用新版 artifact action；建立 GitHub 定时同步与 3.0 标签发布链路
  关联文件：.gitignore, memory/architecture.md, README.md, requirements.txt, .github/workflows/build-windows-exe.yml, VERSION, CHANGELOG.md, README.txt, tools/fx_git_sync.ps1, tools/register_github_sync_task.ps1, tools/unregister_github_sync_task.ps1, tools/fx_release_version.ps1, .github/workflows/publish-release.yml, memory.md, memory/load-order.md, memory/categories/repo-sync-release.md
- [runtime] 摘要：收敛懒加载布局刷新范围，降低首次切页开销；为setup_sidebar增加创建阶段快路径，继续优化启动速度；修复打包版关闭窗口消失慢；兼容 moviepy 2.2 打包并清理 PyInstaller 噪声日志
  关联文件：Fengxi_Toolbox.py, memory/recent-changes.md, memory/architecture.md, memory/debug-status.md, full_debug_test.py, fx_toolbox.spec
- [ui] 摘要：优化水印页黑色横带与功能框显示不全；修复水印页黑色横条与下方功能框裁切；恢复底部栏原高度并保留黑线修复；底部运行信息框高度增加一倍；修复属性页与PDF页显示裁切；统一功能页内标题图标并移除乱码符号；重绘侧栏与标题图标并提升清晰度；按参考图逐项贴齐侧栏图标线稿；将音频工具图标改为标准双音符轮廓；将批量水印与去除水印图标改成标准盾牌和橡皮擦；将批量水印盾牌图标收敛到参考盾牌轮廓；将批量水印盾牌改为白描边蓝色填充样式；将音频工具图标改为更标准的单旗音符轮廓；将音频工具图标改为更接近参考图的实心音符；将音频工具图标改为双横梁实心音符；继续收敛音频工具图标到双横梁实心音符比例；继续将批量水印盾牌贴齐参考图的白边蓝芯比例
  关联文件：Fengxi_Toolbox.py, memory/architecture.md, memory\architecture.md, agent.md
- [watermark] 摘要：稳定区批量水印新增可配置文件名跳过规则
  关联文件：Fengxi_Toolbox.py, memory/categories/watermark-and-remove.md
