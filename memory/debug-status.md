# 调试状态

## 2026-05-20 批量水印文件名规则 UI 与记忆回归
- 本轮目标：
  - 修复 `按文件名规则跳过` 行里的 `留空默认` 提示显示不全。
  - 让该处设置具备本地记忆功能。
- 关键修复：
  - 文件名规则控件改为两行布局，并在水印页布局收紧时保留 56px 高度，避免提示再次被裁切。
  - 新增 `watermark.filename_skip_rule` 用户偏好，保存 `enabled`、`position`、`marker`。
  - 保存时机覆盖变量变更防抖、失焦/回车、执行前和关闭前。
  - 水印执行中临时关闭旧固定跳过开关时，会屏蔽偏好写入，避免把内部状态误保存为用户设置。
- 新增回归：
  - `watermark_filename_rule_memory_save`
  - `watermark_filename_rule_memory_load`
  - `watermark_filename_rule_hint_layout`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py tools\fx_pdf_ocr.py tools\fx_workspace_tools.py tools\generate_fengxi_icon.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：59/59 通过。
- 改动边界：
  - 本轮只改加载器 UI/偏好层和测试记忆，不改 `fengxi_runtime.bin`。
  - 未改 `批量压缩` / `添加水印` 核心业务逻辑。

## 2026-05-20 任务队列功能回归
- 本轮新增“任务队列 + 历史记录 + 失败重试”：
  - 底部操作区新增 `加入队列` 与 `队列历史`。
  - 队列窗口左侧显示等待执行，右侧显示历史与失败重试。
  - 队列任务保存输入路径、任务类型和参数快照，执行前自动恢复快照。
  - 历史持久化到用户配置目录的 `queue_history.json`。
- 新增回归：
  - `task_queue_snapshot`：验证 PDF 加密模式、密码框和底部队列按钮均能正确快照。
  - `task_queue_success_history`：验证队列 worker 执行后写入成功历史，并恢复快照参数。
  - `task_queue_retry_failed`：验证失败历史能重新加入队列。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py tools\fx_pdf_ocr.py tools\fx_workspace_tools.py tools\generate_fengxi_icon.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：56/56 通过。
  - `cmd /c "set FX_NO_PAUSE=1 && package.bat"` 通过。
  - `dist_release_ascii\fx_toolbox\fx_toolbox.exe` 已生成并打开。
  - 打包产物 `_internal` 未发现 OCR/onnxruntime 冲突 DLL。
- 注意：
  - 队列当前是顺序执行，不做并发。
  - 失败判定目前是日志关键词 + 异常 + stop_event 的实用版，后续可升级为结构化结果。
  - 本轮未改 `批量压缩` / `添加水印` 业务逻辑。

## 2026-05-20 全面自检与工程可靠性回归
- 本轮目标：全面检查项目代码/文件、优化工程架构、debug，并保持稳定区安全。
- 关键修复：
  - 修复 `full_debug_test.py` 中快关探针可能触发真实 `os._exit(0)` 的问题，避免全量测试 0 退出但没有最终 JSON 输出。
  - `smoke_test.py` / `full_debug_test.py` 成功时自动清理本轮新建的项目内 `tmp_*` 测试目录，防止后续 debug 继续制造垃圾目录。
  - JSON 测试记录改为 `flush=True`，长流程时能稳定看到逐项进度。
  - GitHub Release zip 上传改为 `curl.exe --data-binary` 并检查 HTTP 状态码，提升大文件资产上传可靠性。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py tools\fx_pdf_ocr.py tools\fx_workspace_tools.py tools\generate_fengxi_icon.py` 通过。
  - `python smoke_test.py`：14/14 通过。
  - `python full_debug_test.py`：53/53 通过。
  - `cmd /c "set FX_NO_PAUSE=1 && package.bat"` 通过，生成 `dist_release_ascii\fx_toolbox\fx_toolbox.exe`。
  - 打包产物 `_internal` 中未发现会和 OCR/onnxruntime 冲突的 `msvcp140*.dll`、`vcruntime140*.dll`、`ucrtbase.dll`、`api-ms-win-crt-*.dll`。
  - 敏感信息扫描仅命中测试里的假文本 `secret`，未发现 token/真实密钥。
- 注意：
  - 本轮没有删除历史 `tmp_*` 目录，只阻止新测试继续留下成功样本。
  - 旧版 `风兮文件批量处理工具箱2.0.spec`、`package_legacy_backup.bat`、`fx_toolbox_diag.spec` 仍是可清理/归档候选，但本轮未删除。
  - `批量压缩` 与 `添加水印` 业务逻辑未改。

## 2026-04-26 侧栏创建阶段加速回归
- 用户继续反馈：打开软件和切功能时仍希望更快。
- 新定位：
  - 上一轮已证明懒加载页切换后的重复布局不再是主热点
  - 剩余主要热点仍在 `setup_sidebar` 与默认 `watermark` 页创建
- 这轮修复：
  - 在 `setup_sidebar()` 执行期间，临时把侧栏按钮改成轻量占位文本/字体
  - 在窗口显示前再通过 `_tighten_layout(...)` 恢复正式图标和文案
- 结果：
  - 真实启动测量约 `3.7786s -> 3.0694s`
  - cProfile 中 `setup_sidebar` 约 `1.505s -> 0.183s`
  - 侧栏按钮最终状态已校验：`btn_nav_wm`、`btn_nav_pdf`、`btn_help_proxy`、`btn_donate` 均恢复正常文本且带图标
- 回归结果：
  - `python -m py_compile Fengxi_Toolbox.py` 通过
  - `python smoke_test.py` 12/12 通过
  - `python full_debug_test.py` 47/47 通过

## 2026-04-25 启动/切页性能复测
- 用户反馈：软件“打开时”和“第一次切换功能页时”仍有明显迟滞。
- 这轮修复：
  - 将 `Fengxi_Toolbox.py` 的 `_tighten_layout(...)` 拆分为“外框一次性样式”与“目标页局部布局收紧”
  - 懒加载页初始化后不再重复重排整套侧栏与底部区域
- 同口径基准结论：
  - 冷启动整体时间基本持平，约 `4.41s`
  - 首次切页明显改善，尤其是 `remove_wm`、`meta`、`file`
  - 说明当前剩余启动热点主要不在懒加载补丁，而在 `setup_sidebar` 与默认 `watermark` 页创建
- 回归结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
  - `python smoke_test.py` 12/12 通过
  - `python full_debug_test.py` 47/47 通过

## 2026-04-25 进度条统一回归
- 用户反馈：几乎所有功能的进度条都存在“不准确、提前跳格”的问题。
- 根因定位：
  - 嵌入式原始 `run_process()` 的多个分支在真正处理文件之前就执行了 `progress_bar.set((i + 1) / total)`
  - 自定义工作流 `_run_remove_wm_pdf_roundtrip()` 与 `_run_pdf_ocr_task()` 也复用了同样的“开工先加进度”写法
  - OCR 底层其实已有页级回调，但此前没有接回 UI
- 本轮修复：
  - `Fengxi_Toolbox.py` 新增统一进度跟踪补丁 `_patch_runtime_progress_reporting()`
  - OCR 改为页级总进度
  - PDF 去水印改为文件完成后推进
  - `full_debug_test.py` 新增 3 条进度相关回归
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
  - `python smoke_test.py` 12/12 通过
  - `python full_debug_test.py` 47/47 通过

## 2026-04-20 当前环境
- 操作系统：Windows
- Office COM：
  - Word.Application 16.0 可用
  - PowerPoint.Application 16.0 可用
- `moviepy/ffmpeg`：可用
- 字体扫描：`SmileySans-Oblique`

## 已验证
- `smoke_test.py` 12 项通过：
  - PDF 水印
  - 多图转 PDF
  - 修改时间
  - PDF 拆分
  - PDF 加密
  - 图片转码
  - 图片压缩
  - 重命名 add
  - meta time
  - PDF 转 Word
  - 视频提取音频
  - 音频格式互转
- 手工增强验证通过：
  - App 初始化
  - Word -> PDF
  - PPT -> PDF
  - Word 水印
  - Word 去水印
  - Word 元数据修改
  - PDF 去水印工作流
  - 图片集合并 PDF 工作流
  - 压缩三模式
  - 文件重命名 replace / cut
  - PDF OCR 搜索版工作流

## 本次发现并修复
- `PDF 合并`：源码工作流会误走多线程单文件路径，导致输出失败清单。已修复为强制进入单线程专用分支。
- `文件去重`：源码工作流会误走多线程普通文件路径，导致不执行真正的 MD5 去重。已修复为强制进入单线程专用分支。

## 后续验证入口
- 快速：`python smoke_test.py`
- 全量：`python full_debug_test.py`

## 2026-04-20 OCR 增量结果
- 新增 `PDF 工具 -> OCR 搜索版 PDF`。
- 回归结果：
  - `full_debug_test.py` 现为 35 项通过。
  - 新增用例：`pdf_ocr_searchable`
  - 新增用例：`pdf_ocr_compare_report`
  - 新增用例：`pdf_ocr_brand_independent`
  - 新增用例：`pdf_ocr_multi_backend_ui`
  - 新增用例：`pdf_ocr_backend_status_panel`
- 当前 OCR 依赖：
  - `RapidOCR`
  - `onnxruntime`
  - `PyMuPDF`
  - 风兮模型目录：`FX_OCR_MODEL_ROOT` 或 `%LOCALAPPDATA%\FengxiToolbox\ocr_models\rapidocr`
- 当前 OCR 架构：
  - 默认后端：`RapidOCR`
  - 可选后端：`PaddleOCR` / `EasyOCR` / `Tesseract CLI`
  - 运行时支持手动切换或 `auto` 自动选择
  - UI 已显示后端探测状态，并支持手动刷新
  - 勾选后可额外生成首页多后端对比 Markdown 报告

## 2026-04-21 UI 布局回归
- 调整范围：
  - 左侧功能区压紧间距，赞助按钮与底部信息重新进入稳定可见范围
  - PDF 页 OCR 改为左侧 PDF 基础选项 + 右侧紧凑 OCR 配置卡片的双栏布局
- 改动边界：
  - 仅修改 `Fengxi_Toolbox.py` 加载器层布局补丁
  - 未改动批量压缩与添加水印业务逻辑
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过
  - `python full_debug_test.py` 35 项通过，`failed: []`
  - 实机截图确认左侧赞助按钮可见，OCR 右栏中的模式、后端、识别配置、方向纠正、对比报告与说明均进入可见区

## 2026-04-21 启动性能回归
- 问题定位：
  - 运行时原本会在 `setup_main_area()` 启动阶段一次性初始化全部功能页
  - 打包配置原本等价于 `onefile`，会带来额外解包延迟
- 已做修改：
  - `Fengxi_Toolbox.py` 新增延迟建页补丁，只初始化默认首屏 `watermark`
  - 页面切换与变量访问会自动触发所属页面补建，兼容既有工作流与测试
  - 主窗口启动阶段先隐藏，布局收束后再显示，减少多界面闪屏
  - `fx_toolbox.spec` 改为 `onedir` 目录式输出，并关闭 `upx`
- 量化结果：
  - 源码态测得 `import` 约 `1.52s`
  - `FengxiToolboxApp()` 初始化约 `3.47s`
  - 启动到窗口可见约 `4.29s`
  - 打包版 `dist_release_ascii\fx_toolbox\fx_toolbox.exe` 两次实测窗口可见约 `5.82s`、`5.40s`
- 回归结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过
  - `python smoke_test.py` 12 项通过
  - `python full_debug_test.py` 35 项通过，`failed: []`
- 改动边界：
  - 未改动批量压缩与添加水印业务逻辑

## 2026-04-22 左侧导航统一化
- 问题表现：
  - 左侧导航虽然间距已压紧，但图标直接写在按钮文本里，受不同符号字宽影响，视觉起始线不一致
  - 教程、赞助与导航主按钮的内部节奏也不够统一
- 已做修改：
  - `Fengxi_Toolbox.py` 改为为左侧按钮生成固定尺寸的图标图片，再配合独立文本标签显示
  - 主导航、使用教程、赞助作者统一为同一高度、同一 `border_spacing`、同一字号
  - 不再依赖 emoji 字符本身的字宽做视觉对齐
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py` 通过
  - `python full_debug_test.py` 35 项通过，`failed: []`
  - 样式检查确认 `btn_nav_wm`、`btn_nav_pdf`、`btn_help_proxy`、`btn_donate` 均已带固定图标图片并统一为 `height=40`
- 改动边界：
  - 仅修改 `Fengxi_Toolbox.py` 的侧边栏样式补丁和打包产物
  - 未改动批量压缩与添加水印业务逻辑

## 2026-04-22 图标恢复
- 用户反馈：
  - 字母缩写图标槽虽然整齐，但“图标没了”
- 已做修正：
  - 将字母缩写图标槽替换为加载器层动态绘制的 11 个线稿小图标：
    - shield / eraser / swap / music / box / document / image / lock / folder / book / coffee
  - 保留统一对齐的固定图标槽与按钮节奏，不回退到 emoji 文本前缀
- 验证结果：
  - 本地图标唯一性校验为 11/11 唯一图形
  - `python -m py_compile Fengxi_Toolbox.py` 通过
  - `python full_debug_test.py` 35 项通过，`failed: []`
  - 已重打包 `dist_release_ascii\fx_toolbox\fx_toolbox.exe`

## 2026-04-22 底部卡片与应用图标回归
- 用户反馈：
  - 左侧最下面的 `使用教程` 和 `赞助作者` 风格不一致，不够好看
  - 需要一个和“风兮”有关的新图标
- 已做修改：
  - `Fengxi_Toolbox.py` 新增 `_style_sidebar_aux_button(...)`，把 `使用教程` 与 `赞助作者` 收口为同一套卡片式按钮壳体
  - 两个按钮统一为 `corner_radius=14`、`height=40`、一致的图标槽与文字对齐，仅保留赞助按钮的暖色强调
  - 新增 `tools\\generate_fengxi_icon.py`，本地生成 `assets\\fengxi_app_icon.png` 与 `assets\\fengxi_app_icon.ico`
  - 源码态通过 `_apply_app_icon(app)` 设置窗口图标，打包态通过 `fx_toolbox.spec` 设置 exe 图标
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py tools\\generate_fengxi_icon.py full_debug_test.py` 通过
  - `python full_debug_test.py` 35 项通过，`failed: []`
  - `cmd /c "set FX_NO_PAUSE=1 && package.bat"` 通过，生成 `dist_release_ascii\\fx_toolbox\\fx_toolbox.exe`
- 改动边界：
  - 未改动批量压缩与添加水印业务逻辑

## 2026-04-22 去水印稳健性回归
- 新定位到的真实问题：
  - `remove_wm` 的真正处理逻辑只在 `run_process()` 的单线程 Word COM 分支里；普通 `process_single_file()` 路径对 PDF/Word 去水印仅复制原文件并记录跳过日志
  - `remove_watermark_from_word()` 原始实现会漏删 `页眉 Range.InlineShapes` 类型的图片水印，导致返回 `SUCCESS` 但文档里仍残留图片水印
- 已做修改：
  - `Fengxi_Toolbox.py` 的 `_patch_task_routing()` 现显式将 `remove_wm` 强制锁定到单线程专用分支
  - 新增 `_patch_remove_watermark_robustness()`，在原始去水印成功后再次打开输出文档，补扫并清理页眉 `InlineShapes`
  - `full_debug_test.py` 新增 `word_remove_wm_header_inline_image` 回归用例
- 复现样本：
  - 手工构造带 `header.Range.InlineShapes.AddPicture(...)` 的 Word 文档
  - 修复前：`remove_watermark_from_word()` 返回 `SUCCESS`，但 `InlineShapes.Count` 仍为 `1`
  - 修复后：`InlineShapes.Count == 0`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过
  - `python full_debug_test.py` 36 项通过，`failed: []`
  - `cmd /c "set FX_NO_PAUSE=1 && package.bat"` 通过，已更新 `dist_release_ascii\\fx_toolbox\\fx_toolbox.exe`
- 改动边界：
  - 未改动批量压缩与添加水印业务逻辑

## 2026-04-22 单文件输入支持回归
- 用户需求：
  - 不再只能选择文件夹；选择单个文件时也要能处理
- 已做修改：
  - `Fengxi_Toolbox.py` 新增 `_patch_single_input_support()`，统一接管浏览入口、启动入口、文件收集与运行入口
  - 浏览按钮现在支持选择“单个文件”或“文件夹”
  - 普通任务的单文件模式通过 `_fx_single_input_target` 只放行选中的那一个文件
  - 单文件任务会自动临时关闭多线程，避免 `process_single_file()` 在工作线程里写 UI 日志触发 `main thread is not in main loop`
  - 单文件 `zip` 走临时隔离目录包装，不直接改动稳定压缩主体逻辑
  - `full_debug_test.py` 新增：
    - `single_file_input_pdf_encrypt`
    - `single_file_input_zip_total`
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过
  - `python full_debug_test.py` 38 项通过，`failed: []`
  - `cmd /c "set FX_NO_PAUSE=1 && package.bat"` 通过，已更新 `dist_release_ascii\\fx_toolbox\\fx_toolbox.exe`
- 改动边界：
  - 未改动批量压缩与添加水印业务逻辑
## 2026-04-22 去水印误删回归
- 问题定位：
- 运行时原始 `remove_watermark_from_word()` 会直接删页眉全部 `Shapes`。
- `is_pdf_source=True` 时还会额外删除文档级 `Shapes` 与页眉 `InlineShapes`。
- 这会造成正常页眉图片、页眉装饰形状，甚至部分 PDF 转 Word 后的正常内容被一起删掉。
- 已做修改：
- 加载层改为安全版 `_remove_watermark_from_word_safely(...)`。
- 删除规则从“整类全删”改成“逐对象水印特征判定”。
- 新增/更新回归：
- `word_remove_wm_header_inline_image`：大尺寸页眉图片水印应被删除。
- `word_remove_wm_preserve_header_assets`：正常页眉 logo、页眉文字与小型标题 shape 必须保留。
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
- `python full_debug_test.py` 39 项通过，`failed: []`。
## 2026-04-22 PDF 去水印回归
- 问题定位：
- Word 去水印修复后，`pdf_remove_wm_workflow` 仍失败。
- 进一步排查确认：PDF 转出的中间 DOCX 本身不含 `XMU TEST`，说明水印内容其实在 `PDF -> DOCX` 这一步就已经被抹掉。
- 失败根因是运行时原始 PDF 去水印链路不稳定，失败后回退成保留原 PDF，因此最终结果仍带水印。
- 已做修改：
- 新增加载层 `_patch_remove_wm_pdf_fallback()`。
- PDF 去水印改走 ASCII 临时目录 round-trip：`convert_pdf_to_word -> remove_watermark_from_word(is_pdf_source=True) -> convert_doc_to_pdf`。
- Word 去水印的保守删除修复保持不变。
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
- `python full_debug_test.py` 39 项通过，`failed: []`。
- 关键回归同时覆盖：
- `pdf_remove_wm_workflow`
- `word_remove_wm_header_inline_image`
- `word_remove_wm_preserve_header_assets`

## 2026-04-24 PDF 去水印批量稳定性回归
- 新定位到的问题：
- `pdf_remove_wm_workflow` 在某些轮次会重新失败，不是算法退化，而是 PDF 去水印链路里复用同一个 `Word.Application` 时，前一个文件的 COM 异常会污染后一个文件。
- 典型日志：
- `Open.Sections`
- `RPC 服务器不可用`
- 已做修改：
- `_create_hidden_word_app()` 改为 `DispatchEx("Word.Application")`
- `_run_remove_wm_pdf_roundtrip(...)` 改成“每个 PDF 独立 Word 会话”，且“去水印阶段”和“导出 PDF 阶段”各自独立
- 专项验证：
- 连续两份带 `XMU TEST` 水印的 PDF 连续处理均成功，输出文本均不再包含 `XMU TEST`
- 全量验证：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过
- `python full_debug_test.py` 39 项通过，`failed: []`
## 2026-04-22 浏览入口去掉类型弹窗
- 用户反馈：
- 点击“浏览文件/文件夹”后，不要再弹“请选择输入类型：单个文件 / 文件夹”的 yes/no/cancel 对话框。
- 已做修改：
- 新增 `_UnifiedInputPathPicker`，替换 `_choose_input_path_interactive()` 内的 `askyesnocancel + askopenfilename/askdirectory` 前置分流。
- 现在浏览入口会直接打开统一选择器，让用户直接点文件或文件夹。
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py` 通过。
- 代码检查已确认 `_choose_input_path_interactive()` 只再依赖 `_UnifiedInputPathPicker(...).show()`，不再调用 `askyesnocancel`。
- 当前额外说明：
- 本轮 `python full_debug_test.py` 未能完整通过，不是由浏览入口引起，而是当前环境里的 `Word COM` 会话异常，报“指定的登录会话不存在”，导致 `pdf_remove_wm_workflow` 无法完成。

## 2026-04-24 启动性能复测
- 本轮目标：
- 检查当前项目是否存在显著回归 bug，并继续优化源码态启动速度。
- 现状结论：
- 本轮未复现功能性回归；`smoke_test.py` 与 `full_debug_test.py` 均完整通过。
- 启动热点主要在两段：
- `fengxi_runtime.bin` 执行期导入 `pdf2docx` / `moviepy`
- `FengxiToolboxApp()` 首屏 GUI 构建
- 已做修改：
- `Fengxi_Toolbox.py` 在 `_load_runtime_namespace()` 前临时安装懒加载代理，仅延后 `pdf2docx` / `moviepy` / `moviepy.editor` 的真实导入时机。
- 真实首次用到这些能力时，仍会自动导入原模块，不影响 PDF 转 Word、OCR 搜索版 PDF、视频转音频等工作流。
- 量化结果：
- 代码载入：约 `1.743s -> 1.267s`
- 启动到窗口 ready：约 `4.923s -> 3.560s`
- 仅启动后半段：约 `3.158s -> 2.293s`
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
- `python smoke_test.py` 12 项通过，`failed: []`
- `python full_debug_test.py` 39 项通过，`failed: []`
- 改动边界：
- 未改动批量压缩与添加水印业务逻辑

## 2026-04-24 浏览入口原生化回归
- 用户反馈：
- 不要再弹自定义的大型“选择文件或文件夹”窗口，希望恢复成系统原生风格，但仍需同时支持文件和文件夹。
- 已做修改：
- `_choose_input_path_interactive()` 不再调用 `_UnifiedInputPathPicker(...).show()`。
- 当前改为调用 `_choose_input_path_via_shell_dialog(...)`，底层使用 Windows Shell `SHBrowseForFolder` 并开启 `BIF_BROWSEINCLUDEFILES`。
- 打开时会尽量定位到当前输入目录，且在同一系统窗口中允许直接选文件或文件夹。
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
- `python smoke_test.py` 12 项通过，`failed: []`
- `python full_debug_test.py` 39 项通过，`failed: []`
- 改动边界：
- 未改动批量压缩与添加水印业务逻辑
- 未改动单文件/文件夹调度逻辑，只替换浏览入口的 UI 实现

## 2026-04-24 去水印卡住与脏路径回归
- 用户反馈：
- 去水印时卡住，且导入后的输入框路径出现 `b'...'`、`\x..`、以及被错误拼进项目目录前缀的异常字符串。
- 根因定位：
- Windows Shell 原生选择器在当前环境下可能返回 `bytes` 路径。
- 旧版 `_normalize_input_path_value()` 直接 `str(value)`，把字节路径转成了字节字面量文本。
- 随后 `os.path.abspath(...)` 又把这段字面量当成相对路径拼到项目目录下，导致输入框显示异常路径，`remove_wm` 等任务拿到脏路径后表现为卡住或异常日志。
- 已做修改：
- 新增 `_decode_input_path_bytes(...)`，按 `utf-8 / mbcs / gbk / filesystemencoding` 顺序解码路径字节。
- 新增 `_coerce_input_path_text(...)`，兼容原始 `bytes`、`b'...'` 字面量字符串、以及 `...\\b'真实路径'` 这类已污染字符串。
- `_normalize_input_path_value()` 现统一先解码再归一化。
- 专项验证：
- 三类输入样本均被还原为同一真实路径：
- `bytes`
- `b'...'`
- `项目目录\\b'真实路径'`
- 回归结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
- `python smoke_test.py` 12 项通过，`failed: []`
- `python full_debug_test.py` 39 项通过，`failed: []`
- 改动边界：
- 未改动批量压缩与添加水印业务逻辑
- 未改动去水印算法主体，只修复输入路径规范化层

## 2026-04-24 拖拽单文件精确选中回归
- 用户反馈：
- 现在浏览选择模式已经可以精准选文件，但把单个文件直接拖进窗口时，仍然只会锁定到父文件夹。
- 进一步暴露的问题：
- 当单文件被错误降级成文件夹后，`remove_wm` 的单文件专用链路会把输出目录错拼成：
- `某文件.pdf\\【处理完成】结果文件夹`
- 日志表现为 `[WinError 3] 系统找不到指定的路径`
- 根因定位：
- 运行时原始 `accept_drag_drop()` 在检测到拖入的是文件时，会直接改写成 `os.path.dirname(path)`。
- 加载层 `_run_remove_wm_task(...)` 之前也默认把 `input_folder` 当目录来拼输出目录和算相对路径。
- 已做修改：
- 新增 `_patch_drag_drop_input_support()`，拖拽单文件时保留文件本体路径，不再强制转父目录。
- `_run_remove_wm_task(...)` 新增 `input_root`：
- 若输入是文件，则输出目录落在该文件父目录下
- `other_files` 的 `relpath()` 与 PDF round-trip 也统一改用 `input_root`
- 专项验证：
- 拖拽字节路径样本后，`input_path` 保持为精确文件路径，`_fx_input_pick_mode == 'file'`
- 单文件 PDF 去水印探针确认：
- `input_folder` 传给 PDF round-trip 的是父目录
- `output_folder` 为 `父目录\\【处理完成】结果文件夹`
- 回归结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
- `python smoke_test.py` 12 项通过，`failed: []`
- `python full_debug_test.py` 39 项通过，`failed: []`
- 改动边界：
- 未改动批量压缩与添加水印业务逻辑
- 未改动去水印算法主体，只修复拖拽输入与单文件输出根目录计算

## 2026-04-24 去水印单文件输出与失败伪成功回归
- 用户反馈：
- 去水印结束后没有拿到符合预期的结果产物
- 原 PDF 仍带水印，存在“看似处理完成、实际未生效”的风险
- 本轮新增修复：
- `remove_wm` 单文件默认改为同目录输出新文件，不再强制创建 `【处理完成】结果文件夹`
- 新增可选开关：单文件时可直接覆盖原文件，但只在处理成功后才执行替换
- PDF round-trip 不再允许 `remove_watermark_from_word()` 失败后继续把原样文档转回 PDF 伪装成功
- PDF round-trip 失败时不再复制原 PDF 充当结果文件
- 新增回归：
- `pdf_remove_wm_single_file_output`
- `pdf_remove_wm_single_file_overwrite`
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
- `python smoke_test.py` 12 项通过，`failed: []`
- `python full_debug_test.py` 41 项通过，`failed: []`
- 改动边界：
- 未改动批量压缩与添加水印业务逻辑
- 去水印仍优先走加载层补丁，不直接重写 `fengxi_runtime.bin`

## 2026-04-25 OCR 单文件与拖拽路径回归
- 用户反馈：
- 批量水印已经能正确找到单文件位置
- 但 `PDF 工具 -> OCR 搜索版 PDF` 在单文件输入时仍报 `[WinError 3]`，路径被拼成 `文件.pdf\\【处理完成】结果文件夹`
- 根因定位：
- `_run_pdf_ocr_task(...)` 仍直接 `os.path.join(input_folder, RESULT_FOLDER_NAME)`
- 这在文件夹输入时正常，但在单文件输入时会把文件当文件夹
- 本轮修复：
- OCR 输出目录改为基于 `input_root` 计算，单文件时取父目录
- OCR 文件收集改为先规范化输入，再走统一 `collect_input_files(...)`
- 新增回归：
- `single_file_input_pdf_ocr`
- `drag_drop_single_file_pdf_ocr`
- 验证结果：
- `python -m py_compile Fengxi_Toolbox.py full_debug_test.py smoke_test.py` 通过
- OCR 专项探针：单文件拖拽后可生成 `probe.pdf` 的 OCR 输出且文本可检索
- `python smoke_test.py` 12 项通过，`failed: []`
- `python full_debug_test.py` 43 项通过，`failed: []`
- 当前结论：
- 源码层自定义工作流里，已知会误把单文件当文件夹拼输出路径的问题，`remove_wm` 与 `pdf OCR` 都已修复
## 2026-04-25 OCR 打包版 onnxruntime 修复回归
- 问题现象：
  - 打包版 `PDF 工具 -> OCR 搜索版 PDF` 在实际执行时失败。
  - 典型报错：`DLL load failed while importing onnxruntime_pybind11_state: 动态链接库(DLL)初始化例程失败。`
- 根因定位：
  - PyInstaller 打包产物中，`onnxruntime` 的二进制位于 `_internal\onnxruntime\capi`。
  - 仅有 `_internal` 被纳入默认运行时环境并不足以让 `onnxruntime_pybind11_state.pyd` 完成初始化。
  - 该问题会导致 UI 状态面板误判“rapidocr 可用”，但真正 OCR 时才失败。
- 本轮修复：
  - `tools/fx_pdf_ocr.py` 新增 Windows 运行时 DLL 目录准备逻辑，显式注册 `onnxruntime\capi`。
  - 后端状态改为真实导入探测，失败时会直接显示导入失败原因。
  - `full_debug_test.py` 新增 `pdf_ocr_backend_runtime_probe`。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_pdf_ocr.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：12/12 通过。
  - `python full_debug_test.py`：44/44 通过。
  - 模拟冻结环境探针：
    - 对 `dist_release_ascii\fx_toolbox\_internal\onnxruntime\capi\onnxruntime_pybind11_state.pyd` 导入成功。
  - 已重打包：
    - `dist_release_ascii\fx_toolbox\fx_toolbox.exe`

## 2026-04-25 OCR 页面卡顿与后端误判回归
- 用户反馈：
  - 打开程序后 OCR 相关操作仍提示“当前环境没有可用的 OCR 后端”。
  - 程序整体偏卡，尤其是 OCR 页。
- 本轮定位：
  - OCR 页初始化时会立即执行 `build_backend_status_text()`，从而触发真实导入探测，带来额外卡顿。
  - `auto` 选后端也依赖 `discover_backend_status()` 预判；一旦打包环境里的轻量判断失真，就会把后端提前判死，根本不进入真正导入尝试。
- 本轮修复：
  - OCR 页初始文案改为按需检测，不再在页面初始化时自动做重探测。
  - `刷新状态` 改为手动触发详细检测。
  - `_resolve_backend_key()` 改成真正执行时逐个后端实试，并在失败时汇总每个后端的真实错误原因。
- 验证结果：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_pdf_ocr.py full_debug_test.py smoke_test.py` 通过。
  - `python smoke_test.py`：12/12 通过。
  - `python full_debug_test.py`：44/44 通过。
  - 已重打包新版：
    - `dist_release_ascii\fx_toolbox\fx_toolbox.exe`
## 2026-04-25 打包版 OCR 运行库冲突回归
- 正式打包版 `dist_release_ascii\fx_toolbox\fx_toolbox.exe` 已重新验证：
  - `run_packaged_ocr_diagnostics(...)` 成功写出 `tmp_ocr_diag\packaged_ocr_diag_fixed.json`
  - `module_checks.onnxruntime.import_ok == true`
  - `backend_resolution.rapidocr == rapidocr`
  - `backend_resolution.auto == rapidocr`
  - `rapidocr_backend_init.ok == true`
- 本次关键验证点：
  - 打包目录 `_internal` 中已不再保留会和 `onnxruntime` 冲突的本地 MSVC/UCRT DLL。
  - 诊断中 `available_providers` 已返回 `AzureExecutionProvider`、`CPUExecutionProvider`，说明冻结环境里的 ORT 初始化完成。
- 源码侧回归：
  - `python -m py_compile Fengxi_Toolbox.py tools\fx_pdf_ocr.py full_debug_test.py smoke_test.py` 通过
  - `python smoke_test.py` 12/12 通过
  - `python full_debug_test.py` 44/44 通过
- 当前结论：
  - “找不到库”问题已从打包版复现状态转为已修复状态。
  - 若后续再次复发，优先比对新包 `_internal` 中是否重新出现 `msvcp140*.dll`、`vcruntime140*.dll`、`ucrtbase.dll`、`api-ms-win-crt-*.dll`。
