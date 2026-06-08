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

## 自动蒸馏 2026-05-22 14:45:37
- 覆盖变更：第 61 到第 90 条
- 当前覆盖结论：用户已取消独立预设中心方向；最终状态以 `last settings automatic memory` 为准，软件不再显示预设中心入口或窗口。
- [progress] 摘要：true progress status text
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md
- [release] 摘要：发布基线提升到 4.0.0，并补齐 README、LICENSE、NOTICE 与 GitHub Release 口径；公开仓库隐私清理，并准备为 v4.0.0 Release 补传 Windows 打包资产；公开仓库已清理隐私信息，并为 v4.0.0 Release 补传 Windows 打包资产；全量自检输出与 Release 上传链路稳健化
  关联文件：VERSION, README.md, README.txt, CHANGELOG.md, LICENSE, NOTICE, Fengxi_Toolbox.py, .github/workflows/publish-release.yml, agent.md, memory.md, memory/architecture.md, memory/categories/repo-sync-release.md, memory/load-order.md, memory/constraints.md, dist_release_ascii/fengxi-toolbox-4.0.0-windows.zip, full_debug_test.py, smoke_test.py, memory/debug-status.md, memory/recent-changes.md
- [remove_wm] 摘要：remove_wm graded modes
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/architecture.md, memory/debug-status.md
- [runtime] 摘要：新增任务队列、历史记录与失败重试；统一任务结果模型并接入队列历史；任务历史增加筛选与回放入口；失败重试支持失败项子集回放；任务历史增加详情查看入口；history detail export；history detail log export；history detail open output location；history detail failure grouping and highlighting；history failure classification preview；subwindow app icon and history failure filter；task history report export；remove_wm single-file overwrite output strategy fix；queue history auto pruning；preset center；last settings automatic memory
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md, memory/categories/watermark-and-remove.md, memory/categories/pdf-file-meta-zip.md
- [ui] 摘要：使用教程改为应用内滚动帮助页，侧栏按钮与show_readme统一重定向到内置页面；帮助页期间禁用开始按钮，避免误执行。；侧栏品牌头部将 FX 文本占位替换为风兮图标，直接复用现有 app icon 资源；仅改品牌区 UI。；同步发布目录图标资源：将 dist_release_ascii\\fx_toolbox\\assets 下的 fengxi_app_icon.png/ico 更新为用户新放入的品牌图，避免源码资源与已打包目录不一致。；清理品牌图标四角黑底，改为透明圆角，并同步重生 PNG/ICO；make preset center visible in sidebar
  关联文件：assets/fengxi_app_icon.png, assets/fengxi_app_icon.ico, dist_release_ascii/fx_toolbox/assets/fengxi_app_icon.png, dist_release_ascii/fx_toolbox/assets/fengxi_app_icon.ico, Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md
- [watermark] 摘要：批量水印文本框新增本地记忆与自动回填；保存时机覆盖输入防抖、失焦、开始执行前和关闭前，未改加水印业务逻辑。；批量水印文件名跳过规则提示与本地记忆修复
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md, memory/recent-changes.md
- [zip] 摘要：更新批量压缩页智能混合模式说明文案，仅改加载器/UI补丁层，不动ZIP业务逻辑；说明与当前smart_recursive实际行为对齐。
  关联文件：-

## 自动蒸馏 2026-05-22 19:55:35
- 覆盖变更：第 91 到第 94 条
- [runtime] 摘要：truthful batch parallel mode UI；enable parallel processing for safe custom workflows；audio parallel and remove_wm COM export fallback
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, memory\architecture.md, memory\debug-status.md, memory/architecture.md, memory/categories/watermark-and-remove.md, memory/categories/convert-audio-image.md, memory/debug-status.md
- [ui] 摘要：inline donate page
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, memory\architecture.md, memory\debug-status.md

## 自动蒸馏 2026-05-28 15:50:46
- 覆盖变更：第 95 到第 124 条
- [convert] 摘要：convert imgs2pdf task adapter modularization；convert single-file adapter seam；Office COM gen_py safe dispatch
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, tools/fx_convert_core.py, tools/fx_convert_task.py, memory/architecture.md, memory/categories/convert-audio-image.md, memory/debug-status.md, memory/recent-changes.md, memory.md, Fengxi_Toolbox.py,tools\fx_convert_task.py,full_debug_test.py,memory\architecture.md,memory\categories\convert-audio-image.md,memory\debug-status.md
- [image] 摘要：image pdf task modularization
  关联文件：Fengxi_Toolbox.py, tools/fx_image_pdf_task.py, full_debug_test.py, memory.md, memory/architecture.md, memory/categories/convert-audio-image.md, memory/debug-status.md, memory/recent-changes.md
- [pdf_file] 摘要：OCR 图像增强与质量回退；pdf compress core modularization；pdf ocr task modularization；meta core modularization
  关联文件：Fengxi_Toolbox.py, tools\fx_pdf_ocr.py, full_debug_test.py, memory\categories\pdf-file-meta-zip.md, memory\debug-status.md, tools/fx_pdf_compress_core.py, memory/architecture.md, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md, tools/fx_pdf_ocr_task.py, memory.md, tools/fx_meta_core.py, memory/recent-changes.md
- [runtime] 摘要：开始前任务预览确认；任务历史一键诊断包；功能注册表一期；启动性能 profiling 与补丁模块拆分一期；启动补丁安装器模块化；任务历史导出与诊断包模块化；队列历史纯逻辑模块化；stable core modularization；stable core exception guardrail；packaged and opened release build；文件管家重命名核心模块化；file dedup core run_process route；file dedup task adapter modularization；audio module cleanup and OCR test stabilization；packaged and opened convert modularization build；user prefs storage modularization；last settings storage seam；legacy presets storage seam；packaged and opened latest build after prefs modularization
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, memory\architecture.md, memory\debug-status.md, memory\recent-changes.md, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md, memory/categories/pdf-file-meta-zip.md, tools/fx_performance.py, tools/fx_runtime_patches.py, tools/fx_startup_patches.py, tools\fx_task_history_exports.py, tools\fx_queue_history.py, tools/fx_watermark_core.py, tools/fx_zip_core.py, memory/categories/watermark-and-remove.md, agent.md, memory/constraints.md, memory/changes.jsonl, package.bat, VERSION, dist_release_ascii/fx_toolbox/fx_toolbox.exe, tools/fx_file_manager_core.py, memory.md, tools/fx_file_manager_task.py, tools/fx_audio_task.py, memory/categories/convert-audio-image.md, tools/fx_user_prefs.py, dist_release_ascii\fx_toolbox\fx_toolbox.exe,tools\fx_user_prefs.py,Fengxi_Toolbox.py,memory\recent-changes.md,memory\changes.jsonl
- [ui] 摘要：remove parallel status hint and restore queue actions；使用教程内嵌示例流程；bottom progress status moved out of action row
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md, memory.md, memory/categories/pdf-file-meta-zip.md

## 自动蒸馏 2026-05-30 00:17:04
- 覆盖变更：第 125 到第 154 条
- [convert] 摘要：audio video speech-to-text；packaged and opened speech-to-text build；speech-to-text model hint；packaged and opened model hint build；speech-to-text realtime preview；packaged and opened realtime preview build；speech-to-text preview compact layout；packaged and opened compact preview build；speech-to-text preview roomy layout；packaged and opened roomy preview build；speech-to-text near-zero top spacing；remove speech-to-text outer tab gap
  关联文件：Fengxi_Toolbox.py, tools/fx_audio_task.py, tools/fx_speech_to_text.py, fx_toolbox.spec, requirements.txt, full_debug_test.py, memory/categories/convert-audio-image.md, memory/debug-status.md, dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl
- [pdf] 摘要：OCR realtime preview
  关联文件：Fengxi_Toolbox.py, tools/fx_pdf_ocr.py, tools/fx_pdf_ocr_task.py, full_debug_test.py, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md
- [runtime] 摘要：packaged and opened Office COM fix build；packaged and opened batch watermark COM fix build；packaged and opened watermark real fix build；packaged and opened direct Word watermark visibility build；startup recursion and packaged startup speed fix；default package and open workflow；packaged and opened speech-to-text layout build；packaged and opened outer gap fix build
  关联文件：dist_release_ascii\fx_toolbox\fx_toolbox.exe,memory\recent-changes.md,memory\changes.jsonl, dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl, Fengxi_Toolbox.py, tools/fx_startup_patches.py, fx_toolbox.spec, full_debug_test.py, memory/architecture.md, memory/debug-status.md, agent.md
- [watermark] 摘要：batch watermark Word COM Dispatch guard；batch watermark direct and PDF conversion real fix；direct Word watermark visible rendering fix；watermark color picker and preview；watermark color preview visibility fix；watermark color preview real visibility repair；packaged and opened watermark preview repair；watermark parameter auto memory；packaged and opened watermark parameter memory build
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md, memory/architecture.md, tools/fx_watermark_core.py, dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl

## 自动蒸馏 2026-06-07 19:33:37
- 覆盖变更：第 155 到第 184 条
- [pdf] 摘要：PDF OCR nav visibility fix；PDF encrypt password entry visibility fix
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md
- [project-rules] 摘要：Watermark and compression cores may be modified with stability guardrails
  关联文件：agent.md, memory\debug-status.md, memory\categories\watermark-and-remove.md, memory\categories\pdf-file-meta-zip.md
- [runtime] 摘要：packaged and opened OCR preview build；packaged and opened OCR nav fix build；packaged and opened PDF encrypt password entry build；packaged and opened ZIP notice build；packaged and opened revised ZIP smart mode build；packaged and opened ZIP preview fix build；packaged and opened watermark skip-copy build；packaged and opened watermark skip rule restoration build；packaged and opened visible watermark skip-rule UI build；packaged and opened adjacent watermark skip-rule layout build；global resume and background guard
  关联文件：dist_release_ascii/fx_toolbox/fx_toolbox.exe, memory/recent-changes.md, memory/changes.jsonl, Fengxi_Toolbox.py, full_debug_test.py, tools\fx_user_prefs.py, dist_release_ascii\fx_toolbox\fx_toolbox.exe, tools/fx_resume.py, memory/architecture.md, memory/debug-status.md, memory/categories/watermark-and-remove.md, memory/categories/pdf-file-meta-zip.md, memory/categories/convert-audio-image.md
- [watermark] 摘要：add copy option for filename-rule skipped watermark files；restore batch watermark prefix suffix filename skip rule；fix visible batch watermark skip-rule controls；keep watermark filename skip controls below switch；Batch watermark bad output paths no longer abort whole run；Batch watermark handles trailing-space source directories and syncs progress bar；Batch watermark now preserves damaged Word files instead of failing the whole batch；batch watermark now copies all unprocessed skipped files；batch watermark supports type-based skip options；Word first-page-only watermark scope fix
  关联文件：Fengxi_Toolbox.py, tools\fx_user_prefs.py, full_debug_test.py, memory\categories\watermark-and-remove.md, memory\debug-status.md, tools\fx_watermark_core.py, agent.md
- [zip] 摘要：ZIP smart root-only folder notice；ZIP smart mode revised layer semantics and max depth；fix ZIP preview count and move max-depth control right；ZIP depth control now supports selectable layer ranges；ZIP depth range uses two UI inputs；ZIP existing archive policy
  关联文件：Fengxi_Toolbox.py, full_debug_test.py, memory\categories\pdf-file-meta-zip.md, memory\debug-status.md, tools/fx_zip_core.py, tools/fx_user_prefs.py, memory/categories/pdf-file-meta-zip.md, memory/debug-status.md, tools\fx_zip_core.py, agent.md
