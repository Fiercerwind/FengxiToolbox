# 项目架构

## 2026-05-20 任务队列 / 历史记录 / 失败重试
- 本轮新增“任务队列 + 历史记录 + 失败重试”，实现仍限定在 `Fengxi_Toolbox.py` 加载器层，不修改 `fengxi_runtime.bin`。
- UI 入口：
  - 底部操作区新增 `加入队列` 与 `队列历史` 两个按钮。
  - `加入队列` 会把当前输入路径、当前功能类型、以及已初始化页面上的参数变量/输入框内容保存为任务快照。
  - `队列历史` 打开独立窗口，左侧显示等待执行队列，右侧显示历史记录与失败重试。
- 调度策略：
  - 队列只做顺序执行，不做并发，避免 Office COM、OCR、PDF 去水印等重任务互相污染。
  - 每个队列任务执行前会恢复保存的参数快照，再调用现有 `run_process(input, task_type)`。
  - 这样用户可以先配置多个不同功能任务入队，再统一执行。
- 历史与重试：
  - 历史记录保存到用户配置目录 `FengxiToolbox/queue_history.json`，不写入项目源码目录。
  - 历史最多保留 `QUEUE_HISTORY_LIMIT = 80` 条。
  - 失败判断目前基于异常捕获、用户停止状态、以及任务日志中的错误关键词。
  - 失败重试会把失败历史的原始快照重新加入等待队列，避免只重试路径却丢失当时配置。
- 测试隔离：
  - `full_debug_test.py` 会临时替换 `_get_user_pref_root()` 到本轮 `tmp_full_debug_*/user_prefs`，避免队列回归污染真实用户历史。
- 维护边界：
  - 后续若增强队列，不要改稳定业务区的 `批量压缩` / `添加水印` 核心逻辑。
  - 若要支持并发队列，必须先重新评估 Office COM、OCR、去水印、文件覆盖等副作用风险。
  - 若要提高失败判断准确度，优先让各自工作流返回结构化结果，而不是继续扩大日志关键词列表。

## 2026-05-20 自检与快关测试架构稳健化
- 本轮未改 `批量压缩` 与 `添加水印` 的业务实现，只在加载器外围、测试脚本和发布链路做工程可靠性优化。
- `Fengxi_Toolbox.py` 的 `_request_fast_close(app)` 保持真实应用快速关闭逻辑不变：先 `withdraw()` 隐藏窗口，再异步 `quit()/destroy()`，必要时强制退出。
- 为避免自动化测试中的快关探针触发真实 `os._exit(0)` 导致测试进程提前结束，新增实例级开关 `_fx_disable_fast_close_force_exit`：
  - 默认不存在或为 `False`，真实应用行为不变。
  - `full_debug_test.py` 会在测试 app 和 close probe 上设置为 `True`，只关闭“兜底强退定时器”，不关闭快关本身。
- `smoke_test.py` 与 `full_debug_test.py` 现在统一使用项目根目录内的 `tmp_*` 临时目录，并在全部通过后自动删除本轮新建目录。
- 测试输出现在对每条 JSON 记录使用 `flush=True`，避免长测试或异常退出时丢失关键进度。
- 边界：历史遗留 `tmp_*` 目录没有在本轮批量删除；后续如要清理，应作为单独维护任务处理，并只限项目目录内。

## 2026-05-20 Release 大文件上传稳健化
- `.github/workflows/publish-release.yml` 仍保留原有 Release 创建/更新 API 流程。
- 最后的 zip 资产上传步骤已从 PowerShell `Invoke-WebRequest -InFile` 改为 `curl.exe --data-binary`。
- 原因：之前补传正式 Windows zip 资产时，手动验证 `curl.exe --data-binary` 上传更稳定；`Invoke-WebRequest` 在大文件上传时有卡住/超时风险。
- 新上传步骤会：
  - 使用 `GITHUB_TOKEN`、GitHub API headers 和 `application/zip`。
  - 将响应写入同目录临时 response json。
  - 检查 `curl.exe` 退出码。
  - 只接受 HTTP `200` 或 `201`，否则输出响应体并失败。
- 后续维护 Release 工作流时，优先保留这条 `curl.exe --data-binary` 路线，不要轻易回退到 `Invoke-WebRequest -InFile` 上传大 zip。

## 2026-05-09 使用教程改为应用内滚动页
- `使用教程` 不再通过 `show_readme()` 调用系统打开 `README.txt / README.md`，而是被加载器层重定向为应用内页面。
- 实现仍限定在 `Fengxi_Toolbox.py`，不修改 `fengxi_runtime.bin`。
- 当前方案：
  - 新增 `HELP_TAB_TITLE = "使用教程"` 与 `INLINE_HELP_SECTIONS`，将帮助内容直接内置为结构化章节。
  - 通过 `_ensure_inline_help_tab()` 在 `main_panel` 上懒创建帮助页 tab。
  - 帮助内容使用 `CTkScrollableFrame` 承载，页面显示不下时可直接纵向滚动。
  - 左侧 `btn_help_proxy` 的命令已改为 `_show_inline_help(...)`，不再走外部文档打开链路。
  - `show_readme()` 也被补丁层接管，任何旧入口最终都会切到应用内帮助页。
- 交互约束：
  - 进入帮助页时会高亮 `使用教程` 按钮。
  - 帮助页显示期间，底部开始按钮会禁用，避免 `current_task="help"` 误进入业务处理分支。
  - 切回任意功能页后，帮助按钮高亮取消，开始按钮恢复正常状态。
- 维护要求：
  - 后续功能有新增或行为变化时，需要同步更新 `INLINE_HELP_SECTIONS` 文案。
  - 如果继续扩展帮助页，优先沿用“应用内 tab + scrollable 内容”的路线，不要退回外部 README 打开方式。

## 2026-05-09 侧栏与标题图标清晰度重绘
- 用户反馈：左侧功能区图标线条发糊、细节乱，想按新的视觉参考图把图标做得更清晰、更规整。
- 当前修复仍限定在 `Fengxi_Toolbox.py` 加载器层，不改 `fengxi_runtime.bin`，不触碰稳定区 `批量压缩` / `添加水印` 的业务处理逻辑。
- 当前方案：
  - `_draw_sidebar_icon(...)` 不再沿用旧的低分辨率直接描线方案，而是统一改成更规整的几何线稿。
  - `_build_sidebar_icon_image(...)` 改为先按高分辨率画布超采样绘制，再用 `LANCZOS` 缩回实际显示尺寸，提升边缘清晰度。
  - 由于页面内标题图标复用同一套自绘逻辑，侧栏图标与功能页标题图标会同步变清晰，不需要分别维护两套素材。
  - `水印内容` 小标题图标已按参考图切换为文档语义，和页面布局更一致。
- 后续边界：
  - 若继续调整图标观感，优先改 `_draw_sidebar_icon(...)` 的几何路径与 `_build_sidebar_icon_image(...)` 的渲染策略，不要回退到 22px 画布直接硬描边。
  - 若引入新的图标种类，默认继续走“统一线稿 + 超采样缩放”路线，保持侧栏与页面标题风格一致。
  - 2026-05-09 起，侧栏头部原来的 `FX` 文本占位也已改为直接显示 `assets/fengxi_app_icon.png` 品牌图标；如果后续再调品牌头部，优先复用 `_get_sidebar_brand_image(...)`，不要重新塞回字母占位。

## 2026-05-09 页面内标题图标统一
- 用户反馈：左侧功能区图标与点击进入后的页面标题图标不一致，且部分页面标题/小标题使用 emoji 或符号时会出现乱码或观感不统一。
- 当前修复仍限定在 `Fengxi_Toolbox.py` 加载器层，不改 `fengxi_runtime.bin`，也不触碰稳定区 `批量压缩` / `添加水印` 业务处理逻辑。
- 当前方案：
  - 侧栏继续使用 PIL 自绘图标缓存 `_draw_sidebar_icon(...)` / `_get_sidebar_icon_images(...)`。
  - 新增页面内标题图标映射 `INLINE_TITLE_ICON_SPECS`，统一为主功能标题与关键小标题分配与侧栏同风格的自绘图标。
  - 通过 `_apply_inline_title_icons(...)` 递归扫描当前页 `CTkLabel`，把运行时自带的 emoji/符号标题改写为“纯文本标题 + 自绘 CTkImage”。
  - 该逻辑接入 `_tighten_single_tab_layout(...)` 与 `_refresh_visible_tab_layout(...)`，保证默认页和懒加载后的页签都会应用一致化图标。
  - `zip` 页残留的单字符闪电标签也已纳入同一映射，改为仅显示自绘图标，避免不同机器下出现符号观感差异。
- 当前边界：
  - 后续如继续调整功能页标题视觉，优先修改 `INLINE_TITLE_ICON_SPECS` 与 `_draw_sidebar_icon(...)`，不要回退到把 emoji 直接写进标题文本。
  - 页面内标题若要做到“只显示图标不显示旧字符”，应复用 `display_text` 机制，而不是保留原符号字符。

## 2026-04-26 侧栏构建快路径
- 继续沿加载器层优化启动性能，不改 `fengxi_runtime.bin`，也不碰稳定区 `批量压缩` / `添加水印` 业务逻辑。
- `Fengxi_Toolbox.py` 新增 `FAST_SIDEBAR_BUILD_FONT`、`_run_with_fast_sidebar_button_construction(...)` 与 `_patch_sidebar_build_performance()`。
- 当前策略是：只在 `setup_sidebar()` 的“构建阶段”临时把侧栏直系 `CTkButton` 做成轻量占位版本：
  - `text=""`
  - `font=("Microsoft YaHei UI", 12)`
- 真正展示给用户之前，仍然由 `_tighten_layout(...) -> _apply_shell_layout_tightening(...)` 统一恢复正式文案、图标和字体，所以最终可见 UI 不变。
- 这一层优化的核心边界：
  - 只影响 `setup_sidebar()` 运行时的按钮创建开销
  - 不改变按钮命令绑定
  - 不改变后续图标、对齐和视觉样式
  - 不能绕开 `_tighten_layout(...)`，否则窗口若被外部直接显示，侧栏可能还停留在占位态
- 本轮复测中，`setup_sidebar` 的累计耗时从约 `1.505s` 降到约 `0.183s`；同轮新进程里整体启动约 `3.78s -> 3.07s`。

## 2026-05-05 快速关闭补丁
- 用户反馈打包版点击关闭后窗口很久才消失。
- 排查发现默认水印页的文件名规则补丁中，`CTkOptionMenu` 误用了 `CTkComboBox` 支持的 `border_width` / `border_color` 参数。
- 这会导致下拉控件半初始化，窗口销毁时抛出 `_variable` 缺失异常，并拖慢关闭。
- 当前修复：
  - 新增 `_get_option_menu_style(...)`，只把 `CTkOptionMenu` 支持的样式参数传入水印规则下拉框。
  - 新增 `_install_fast_close_protocol(...)` 与 `_request_fast_close(...)`。
  - 点击窗口关闭时先设置 `stop_event=True` 并 `withdraw()` 隐藏窗口，再异步 `quit()` / `destroy()`。
- 目标是让用户点击关闭后窗口立即消失，即使后台 Tk 控件树清理仍需要一点时间。
- 当前回归：`full_debug_test.py` 的 `app_fast_close_hides_first`，验证关闭请求约毫秒级隐藏并进入销毁流程。

## 2026-05-05 水印页可视高度优化
- 用户截图反馈默认水印页中间出现一条明显黑色横带，挤压下方功能框，导致右侧参数区底部控件显示不全。
- 当前判断为外壳布局与水印页固定请求高度共同造成：
  - `main_panel` 与 `bottom_bar` 之间原有外壳背景间隙会露出黑色横带。
  - 默认水印页左右两列卡片原始请求高度约 `692px`，在常见 1360x768 视窗下可视高度不足。
  - 底部进度/按钮/日志区请求高度偏大，继续压缩主功能区。
- 当前修复仍只在加载器层做 UI 布局补丁，不改水印业务处理：
  - 将 `watermark -> tab_wm` 加入 `TAB_LAYOUT_ATTRS`，让默认水印页也走 `_tighten_single_tab_layout(...)`。
  - `_apply_shell_layout_tightening(...)` 收紧顶部栏、主区域和底部栏外距，移除主区域与底部栏之间的黑色间隙。
  - `_tighten_watermark_tab_layout(...)` 直接收紧 `tab_wm` 左右两列，压缩文本框、参数行、字体下拉框和三组滑块的垂直占位。
  - 在 1360x768 窗口模拟测量中，水印页可视高度从约 `577px` 提升到约 `664px`，右侧三组滑块完整显示。

## 2026-04-25 懒加载布局收敛
- 这轮启动/切页性能优化继续坚持“优先改 `Fengxi_Toolbox.py` 加载器层，不碰 `fengxi_runtime.bin`，不动稳定的添加水印/批量压缩业务”。
- `_tighten_layout(...)` 已拆成三层：
  - `_get_sidebar_button_font(...)`：缓存侧栏字体，避免重复创建
  - `_apply_shell_layout_tightening(...)`：只负责侧栏、顶部、底部这些一次性外框样式
  - `_tighten_single_tab_layout(...)`：只对刚初始化的目标页做局部收紧
- `_ensure_lazy_tab_initialized(...)` 不再在每个懒加载页初始化后重跑整套侧栏重排；现在是“初始化目标页 -> 针对该页做局部布局收紧 -> 再刷新 idle tasks”。
- 同口径冷启动基准里，整体启动时间基本持平（约 `4.41s -> 4.41s`），说明当前启动主热点仍然在 `setup_sidebar` 和默认 `watermark` 页构建，而不再是懒加载页切换后的重复布局。
- 同口径首次切页基准里，局部收益明确：
  - `remove_wm`: `0.6425s -> 0.5288s`
  - `convert`: `0.3632s -> 0.3380s`
  - `zip`: `0.4306s -> 0.4258s`
  - `pdf`: `0.7645s -> 0.7504s`
  - `meta`: `0.3068s -> 0.2573s`
  - `file`: `0.5073s -> 0.2685s`
- 后续如果还要继续压启动速度，优先研究 `setup_sidebar` 的按钮构建/绘制成本；默认不要为了提速去动 `watermark` 业务页本体，因为该功能属于用户明确要求的稳定区。

## 2026-04-25 统一进度条修复架构
- 进度条修复继续坚持“优先改加载器层，不改 `fengxi_runtime.bin`”。
- `Fengxi_Toolbox.py` 新增 `_patch_runtime_progress_reporting()`：
  - 先沿补丁链剥离出嵌入式原始 `run_process()`
  - 再用 `_build_runtime_progress_site_map(...)` 分析字节码中的进度调用点，区分三类：
    - `before_process_single`：处理前预写进度，改为等 `process_single_file()` 返回后再累计
    - `direct_pre`：直接循环分支，改为在下一轮开始或任务收尾时补记上一项完成
    - `pass_through`：原本就是完成后进度，保持直通
- 运行期通过实例级 `_FxRunProgressTracker` 临时接管：
  - `progress_bar.set`
  - `process_single_file`
  - `reset_ui`
- 这样可以统一修复大多数封装在运行时里的“提前跳进度”问题，同时不去反编译或重写运行时主体。

## 2026-04-25 OCR 页级进度接回 UI
- `tools/fx_pdf_ocr.py` 的 `FengxiPdfOcrEngine.ocr_pdf_to_searchable_pdf(...)` 原本已经支持 `progress_callback(page_done, total_pages)`。
- 当前 `Fengxi_Toolbox.py` 中的 `_run_pdf_ocr_task()` 已正式接入这个回调，并把页进度映射到整体批处理进度。
- 后续如果继续改 OCR 工作流，优先复用这个回调，不要再退回到“按文件开始就直接 +1”的粗粒度进度写法。

## 总体形态
- 仓库表面上是单文件应用，但真实结构是“加载器 + 封装运行时 + 测试脚本 + 打包产物”。
- `Fengxi_Toolbox.py` 不是完整业务源码，它负责：
  1. 载入 `fengxi_runtime.bin`
  2. 将运行时对象注入全局
  3. 用 ffmpeg 版音频转换函数覆盖原音频转换入口
  4. 在加载器层补 UI、OCR、启动性能等外围补丁
  5. 对部分调用做 debug 包装
  6. 在 `__main__` 中创建 `FengxiToolboxApp`

## 运行时装载
- `fengxi_runtime.bin` 通过 `marshal.loads(...)` 反序列化。
- 运行时命名空间中的类、函数被拷贝进 `globals()`。
- 当前可见核心对象：
  - `FengxiToolboxApp`
  - `create_watermark_packet`
  - `add_watermark_to_pdf`
  - `add_watermark_to_word`
  - `remove_watermark_from_word`
  - `convert_doc_to_pdf`
  - `convert_pdf_to_word`
  - `convert_ppt_to_pdf`
  - `merge_images_to_pdf`
  - `modify_file_timestamp`
  - `modify_office_meta`

## UI 与任务调度
- 主类：`FengxiToolboxApp`
- 主要方法：
  - `collect_input_files`
  - `resolve_task_config`
  - `process_single_file`
  - `run_process`
  - `on_start_click`
- Tab/页面：
  - 批量水印
  - 去除水印
  - 格式转换
  - 音频工具
  - 批量压缩
  - PDF 工具
  - 图片工厂
  - 属性隐私
  - 文件管家
- 2026-04-21 起，启动流程改为“默认页即时初始化，其余页首次访问时再初始化”：
  - 默认首屏是 `watermark`
  - `switch_tab()` 已被加载器层补丁接管，会在切页前补建目标页面
  - `__getattr__` 也做了延迟补建兼容，因此像 `pdf_mode_var`、`file_mode_var` 这类变量即使在未手动切页前被访问，也会自动触发所属页面初始化
- 启动窗口现在先 `withdraw()`，等布局收束后再 `deiconify()`，用于减少打开时连续闪过多个半成品界面的问题

## 入口与依赖
- GUI：`customtkinter`
- PDF：`pypdf`, `reportlab`, `pdf2docx`
- 图像：`Pillow`
- Office COM：`pythoncom`, `win32com.client`
- 拖拽/窗体样式：`windnd`, `pywinstyles`
- 音视频：优先使用 `imageio_ffmpeg` 提供的 ffmpeg 二进制

## 当前源码层补丁
- 由于运行时内部把 `PDF 合并` 和 `文件去重` 的专用分支放在单线程路径，而原配置分流未强制切换，源码层在加载器中增加了任务路由补丁：
  - `pdf_mode == "merge"` 时强制单线程
  - `file_mode == "dedup"` 时强制单线程
- 2026-04-22 起，`remove_wm` 也在加载器层显式强制单线程：
  - 真正的 Word/PDF 去水印逻辑只存在于 `run_process()` 的单线程 COM 工作流里
  - 一旦误落到 `process_single_file()` 普通路径，去水印只会复制原文件并写“跳过”日志
- 2026-04-22 起，输入入口支持“单文件或文件夹”双模式：
  - `_patch_single_input_support()` 接管了 `select_folder` / `collect_input_files` / `on_start_click` / `run_process`
  - 普通任务的单文件模式做法是：把 `run_process()` 根路径切到目标文件父目录，再通过 `_fx_single_input_target` 只放行这一份文件
  - 为避免 `process_single_file()` 在工作线程里写 UI 日志时触发 `main thread is not in main loop`，单文件输入会自动临时关闭多线程，强制走单线程稳定模式
  - `zip` 是例外：单文件压缩不改稳定压缩主体，而是先把文件复制到临时隔离目录，调用原始 `run_process('zip')` 后再把生成的 zip 移回原目录
- 这样无需改动稳定业务实现，只修正调度入口。
- OCR 搜索版 PDF、左侧导航布局、PDF OCR 双栏布局、启动性能优化都优先通过 `Fengxi_Toolbox.py` 的加载器层补丁完成，不直接改 `fengxi_runtime.bin`。
- 2026-04-22 起，左侧导航不再依赖“emoji 直接拼进按钮文字”的方案：
  - 改为加载器层动态生成固定尺寸的图标图片 + 独立文本标签
  - 当前实现使用 PIL 画线稿风格的小图标，不依赖系统 emoji 字体，避免缺字或宽度不一致
  - 目标是让所有导航项、教程按钮、赞助按钮的起始线和内部间距保持统一，同时保留真正的图形图标
  - 后续如果继续调左侧视觉，优先改这套 icon image + `border_spacing` 的样式，不要回退到 emoji 文本前缀或字母缩写占位符
- 2026-04-22 起，左侧底部辅助入口也有单独约束：
  - `使用教程` 与 `赞助作者` 统一通过 `_style_sidebar_aux_button(...)` 收口样式
  - 两者必须保持同一高度、同一圆角、同一边框宽度、同一图标槽与文字对齐节奏
  - `赞助作者` 只允许通过暖色填充/边框做轻强调，不要再回退到另一套控件观感
- 2026-04-22 起，Word 去水印还有一个加载器层稳健性补丁：
  - `_patch_remove_watermark_robustness()` 会在原始 `remove_watermark_from_word()` 成功后，对输出 doc/docx 再做一轮 `页眉 Range.InlineShapes` 清理
  - 这是为了解决原始实现只删 `header.Shapes`、却漏删 `页眉图片水印` 的问题
  - 该补丁属于外围兜底，不重写原始去水印主体逻辑

## 品牌图标资产
- 2026-04-22 起，应用图标由项目内脚本 `tools/generate_fengxi_icon.py` 生成：
  - `assets/fengxi_app_icon.png`
  - `assets/fengxi_app_icon.ico`
- 当前品牌图标语义：
  - 主体是“流风回旋”形态
  - 配合暖金印章感点缀，表达“风兮”品牌感
- 接入位置：
  - 运行时窗口图标由 `Fengxi_Toolbox.py` 中的 `_apply_app_icon(app)` 负责加载
  - 发布版窗口标题由 `Fengxi_Toolbox.py` 中的 `_apply_release_identity(app)` 在启动时统一设置，当前展示口径为 `风兮文件批量处理工具箱 4.0`
  - 打包 exe 图标由 `fx_toolbox.spec` 的 `icon='assets\\fengxi_app_icon.ico'` 负责接入
- 2026-05-09：
  - 用户已直接替换 `assets/fengxi_app_icon.png` 为新的品牌图。
  - `assets/fengxi_app_icon.ico` 也必须同步由该 `png` 重生成，否则侧栏品牌头、窗口图标与打包 exe 图标会不一致。
  - 当前这版品牌图已清理四角黑底，根资产与打包产物都应保持“透明圆角”状态；若后续再次替换源图，需同时验证 PNG/ICO 左上角 alpha 为 0，避免黑角回归。
- 若后续继续改品牌图标，优先改生成脚本并重新生成 PNG/ICO，不要只手工替换其中一个产物，避免源码态与打包态图标不一致

## 打包策略
- 2026-04-21 起，发布包优先采用 `onedir` 目录式输出，而不是 `onefile`。
- 原因：
  - `onefile` 每次启动都需要额外解包，桌面工具首启和重复启动都会更慢。
  - 当前项目本身还要加载 `fengxi_runtime.bin`、OCR 依赖和 GUI 资源，`onefile` 叠加后启动感知会更差。
- 当前推荐发布入口：
  - `dist_release_ascii\fx_toolbox\fx_toolbox.exe`
- `package.bat` 与 `fx_toolbox.spec` 都应围绕目录式输出维护，不要再改回单文件思路，除非用户明确接受启动变慢。
## 2026-04-22 去水印安全补丁
- `Fengxi_Toolbox.py` 不再通过“先调用原始 `remove_watermark_from_word()` 再补删 header inline shapes”的方式处理 Word 去水印。
- 当前改为直接在加载层接管 `remove_watermark_from_word()`，使用 `_remove_watermark_from_word_safely(...)`。
- 安全版流程会先读取页面尺寸，再对 header `Shapes`、header `InlineShapes`、以及 `is_pdf_source=True` 时的文档级 `Shapes` 做逐项判定。
- 只有命中 `XMU_DONE` / watermark 关键词，或满足“大尺寸 + 居中/越界 + 斜向/半透明”特征时才删除。
- 这样做的目标是保留正常页眉图文和 PDF 转 Word 后的正常 shape 内容，避免历史上的“去水印成功但内容一起被删掉”。
## 2026-04-22 PDF 去水印兜底补丁
- `Fengxi_Toolbox.py` 新增 `_patch_remove_wm_pdf_fallback()`，在 `run_process()` 层拦截 `task_type == "remove_wm"` 且输入中包含 PDF 的情况。
- 拦截后不再完全依赖运行时原始 PDF 去水印链路，而是交给 `_run_remove_wm_task(...)`。
- 其中 PDF 文件走 `_run_remove_wm_pdf_roundtrip(...)`：
- 使用 ASCII 临时目录生成 `from_pdf.docx` / `cleaned.docx`。
- 先 `convert_pdf_to_word()`，再调用加载层安全版 `remove_watermark_from_word(..., is_pdf_source=True)`，最后 `convert_doc_to_pdf()` 输出到正式结果目录。
- 非 PDF 文件仍保留原有去水印路径；混合输入时会把非 PDF 放进临时 staging 目录交给原始 `run_process()` 处理，再把结果并回真实输出目录。
- 结果目录必须统一复用 `RESULT_FOLDER_NAME`，不要手写字符串，避免编码或目录名漂移导致测试/运行找不到结果文件。

## 2026-04-24 PDF 去水印 Word 会话隔离
- `Fengxi_Toolbox.py` 中的 `_create_hidden_word_app()` 现已改为 `DispatchEx("Word.Application")`，不再复用共享 Word 进程。
- `_run_remove_wm_pdf_roundtrip(...)` 里，每个 PDF 会：
- 先用独立 Word 实例执行 `remove_watermark_from_word(..., is_pdf_source=True)`。
- 再用另一个独立 Word 实例执行 `convert_doc_to_pdf(...)`。
- 这样即使去水印阶段出现 COM 异常，也不会把同一批次后续 PDF 或后续导出阶段一起拖坏。
## 2026-04-22 统一输入选择器
- `Fengxi_Toolbox.py` 的浏览入口不再使用 `askyesnocancel` 先问“文件还是文件夹”。
- 当前改为 `_UnifiedInputPathPicker` 自定义统一路径选择器：
- 同一窗口内直接列出文件和文件夹。
- 双击文件可直接确认。
- 双击文件夹可进入。
- 也可以选中文件夹后点“确定”或“选择当前文件夹”。
- 这一改动只发生在加载层浏览入口，不改动后续单文件/文件夹调度逻辑。
## 2026-04-24 浏览入口回退到系统原生选择器
- 用户明确不接受自定义的大型 `CTkToplevel` 路径选择器观感。
- 当前默认浏览入口已改为 Windows Shell 原生选择器 `_choose_input_path_via_shell_dialog(...)`。
- 技术路径：
- 使用 `SHBrowseForFolder` + `BIF_BROWSEINCLUDEFILES`
- 允许在同一个系统窗口里直接点文件或文件夹
- 通过回调在打开时定位到当前输入目录
- 设计边界：
- 只替换“浏览入口 UI”，不改动后续 `_patch_single_input_support()` 的单文件/文件夹调度逻辑。
- 拖拽输入、单文件处理、文件夹处理、压缩/加水印稳定区都不应受这次改动影响。
- 后续若继续优化输入入口，优先保持“系统原生窗口 + 文件/文件夹同选”方向，不要再把自定义大窗口重新设为默认入口。

## 2026-04-24 输入路径字节解码修复
- Windows Shell 选择器在某些环境下返回的路径可能是 `bytes`，而不是普通 `str`。
- 旧版 `_normalize_input_path_value()` 直接做 `str(value)`，会把字节路径污染成：
- `b'...'`
- `\x..` 转义片段
- 甚至被 `os.path.abspath(...)` 错误拼成 `项目目录\\b'真实路径'`
- 这会进一步导致：
- 输入框显示脏路径
- `os.path.isfile()` / `os.path.isdir()` 误判
- `remove_wm` 等任务拿着错误路径执行，表现成卡住、无法停止或日志乱码
- 当前修复：
- 新增 `_decode_input_path_bytes(...)` 与 `_coerce_input_path_text(...)`
- `_normalize_input_path_value()` 统一先做字节解码，再做路径归一化
- 同时兼容三类脏输入：
- 原始 `bytes`
- 形如 `b'...'` 的字节字面量字符串
- 已被错误拼到当前工作目录前缀里的 `...\\b'真实路径'`
- 后续凡是浏览、拖拽、日志回填、单文件调度涉及路径规范化，都应继续复用 `_normalize_input_path_value()`，不要绕开这层直接 `str(...)`

## 2026-04-24 拖拽单文件与去水印单文件输出根目录修复
- 运行时原始 `accept_drag_drop()` 会把拖入的单文件自动改写成其父目录。
- 这会导致：
- UI 看起来像“拖入成功了”，但实际只锁定到文件夹
- 桌面单个 PDF 拖入后会退化成处理整个桌面目录
- 单文件任务无法做到精准选中目标文件
- 当前加载层已新增 `_patch_drag_drop_input_support()`：
- 拖入单个文件时保留文件本体路径
- 拖入文件夹时保持文件夹路径
- 同步更新 `_fx_input_pick_mode` 与 `_fx_last_input_dir`
- 多项目拖拽时暂时只取第 1 个，并在日志里明确提示
- 同时，`remove_wm` 的加载层专用链路 `_run_remove_wm_task(...)` 现已区分：
- `normalized_input`：用户真实输入，可能是文件也可能是文件夹
- `input_root`：用于输出目录和相对路径计算的根目录；若输入是文件，则取其父目录
- 这样可避免把结果目录错误拼成 `某文件.pdf\\【处理完成】结果文件夹`
- 后续凡是新增“单文件专用工作流”，都要警惕：
- 输出目录不能直接 `os.path.join(输入文件路径, RESULT_FOLDER_NAME)`
- `relpath()` 的基准目录也不能直接拿“文件路径”来算

## 2026-04-24 启动性能懒加载
- `Fengxi_Toolbox.py` 的 `_load_runtime_namespace()` 现在会在执行 `fengxi_runtime.bin` 前，临时安装运行时懒加载代理。
- 当前仅对启动期开销大的可选依赖做懒加载：
- `pdf2docx`
- `moviepy`
- `moviepy.editor`
- 代理入口由 `_install_runtime_lazy_imports()`、`_LazyImportModule`、`_LazyImportSymbol`、`_resolve_lazy_runtime_module()` 组成。
- 设计边界：
- 只延后“首次真正调用”时再导入重依赖，不改动运行时业务函数签名。
- 执行完 `fengxi_runtime.bin` 后会通过 `_restore_runtime_lazy_imports()` 清理 `sys.modules` 中仍是代理的占位项，避免污染常规导入环境。
- 2026-05-09 起需兼容 `moviepy==2.2.x` 已不再提供 `moviepy.editor` 实体模块这一事实：
  - 加载器层仍保留 `moviepy.editor` 代理名，避免嵌入运行时里的旧导入路径失效。
  - 但其真实符号解析已回退到 `moviepy` 根模块上的 `AudioFileClip` / `VideoFileClip`。
  - `fx_toolbox.spec` 不再无条件写死 `moviepy.editor` hidden import，而是仅在当前环境存在该模块时才加入；同时显式补入新版可用的 `moviepy.audio.io.AudioFileClip` 与 `moviepy.video.io.VideoFileClip`。
- 后续如果还要继续优化启动速度，优先沿着“可选重依赖懒加载”思路做；不要轻易动 `customtkinter`、首屏 `watermark` UI、批量压缩、添加水印的稳定业务逻辑。

## 2026-04-24 去水印单文件输出与失败防伪成功
- `去除水印` 页现已由加载层补入 `rm_wm_overwrite_original` 开关，文案为“单文件时直接覆盖原文件（谨慎）”。
- 当前去水印输出规则固定为：
- 文件夹输入：继续输出到 `RESULT_FOLDER_NAME`
- 单文件输入：默认在同目录输出 `原文件名_去水印.ext`
- 单文件输入且开启覆盖：仅在处理成功后替换原文件
- `_run_remove_wm_task(...)` 现已允许单文件先写入临时结果目录，再通过 `_finalize_single_remove_wm_output(...)` 落到最终位置，避免在单文件模式下误生成 `【处理完成】结果文件夹`。
- `_run_remove_wm_pdf_roundtrip(...)` 现已严格要求 `remove_watermark_from_word(...) == "SUCCESS"` 且 `cleaned.docx` 真实存在，否则直接按失败处理。
- 后续凡是继续改 `remove_wm`，都必须保持这个边界：失败时宁可不产出结果，也不能把原文件重新导出后冒充“去水印成功”。

## 2026-04-25 OCR 单文件路径规则补齐
- `_run_pdf_ocr_task(...)` 现已改为复用统一的结果根目录解析：
- 若输入是文件夹，则输出到 `输入文件夹\\RESULT_FOLDER_NAME`
- 若输入是单个文件，则输出到 `该文件父目录\\RESULT_FOLDER_NAME`
- 这样可避免旧逻辑把结果目录错误拼成 `某个.pdf\\【处理完成】结果文件夹`
- OCR 现在与单文件支持补丁 `_patch_single_input_support()`、拖拽补丁 `_patch_drag_drop_input_support()` 的路径语义保持一致。
- 后续凡是新增“加载层自定义工作流”时，都不要直接 `os.path.join(input_folder, RESULT_FOLDER_NAME)`，必须先判断 `input_folder` 是文件还是文件夹。
## 2026-04-25 OCR 打包运行时补丁
- 打包版 OCR 的 RapidOCR/onnxruntime 不能只依赖 PyInstaller 默认注入的 `_internal` 路径。
- `onnxruntime_pybind11_state.pyd` 在冻结环境里真正需要显式注册 `onnxruntime\capi` 目录，否则会报：
  - `DLL load failed while importing onnxruntime_pybind11_state: 动态链接库(DLL)初始化例程失败。`
- 当前修复落在 `tools/fx_pdf_ocr.py`：
  - 新增 `_prepare_windows_ocr_runtime_dirs()`，仅注册 `onnxruntime\capi`，不把整层 `_internal` 当作 OCR DLL 兜底路径塞进去，避免额外 DLL 冲突。
  - `discover_backend_status()` 不再只做 `find_spec` 级别判断，而是对 `rapidocr` / `onnxruntime` 做真实导入探测。
  - `RapidOcrBackend.__init__()` 在导入 `rapidocr` 前先执行运行时 DLL 路径准备。
- 调试结论：
  - `_internal` 单独在 PATH 中时，导入 dist 里的 `onnxruntime_pybind11_state.pyd` 仍会失败。
  - 显式加入 `_internal\onnxruntime\capi` 后，dist 里的扩展模块可成功导入。

## 2026-04-25 OCR 状态探测与自动选后端解耦
- OCR 页面状态栏不能作为真正执行时的唯一准入门槛。
- 当前策略改为：
  - UI 初始状态不再自动做重导入探测，避免一打开 PDF/OCR 页就卡顿。
  - `刷新状态` 按钮才触发详细后端检测。
  - 真正执行 OCR 时，`auto` 会按 `rapidocr -> paddleocr -> easyocr -> tesseract_cli` 逐个做真实导入/可用性尝试，而不是先被 `discover_backend_status()` 的预判拦死。
- 这样即使冻结环境里 `find_spec()`/状态面板判断有偏差，也不会提前把本可运行的后端误判成不可用。
## 2026-04-25 OCR 打包运行库冲突修复
- 这次真正的根因不在 `tools/fx_pdf_ocr.py` 的识别逻辑，而在打包产物 `_internal` 目录里随包带出的 MSVC/UCRT 运行库。
- 已确认会和 `onnxruntime` 冲突的 DLL 组：
  - `msvcp140.dll`
  - `MSVCP140_1.dll`
  - `vcruntime140.dll`
  - `vcruntime140_1.dll`
  - `ucrtbase.dll`
  - `api-ms-win-crt-*.dll`
- 现行发布策略：
  - `fx_toolbox.spec` 会在 `Analysis(...)` 后过滤上述冲突 DLL，避免被收进最终产物。
  - `package.bat` 在收尾阶段还会再次清理 `%APP_ROOT%\\_internal` 中的同名 DLL，防止历史构建残留。
- 诊断结论：
  - 保留这些本地运行库时，冻结环境里 `onnxruntime_pybind11_state.pyd` 会报 `DLL 初始化例程失败`。
  - 去掉这组 DLL 后，同一份 `onnxruntime` 二进制即可在打包版 EXE 中成功导入，`RapidOCR` 初始化也恢复正常。
- 后续如果 OCR 只在打包版失败，优先检查：
  - `fx_toolbox.spec`
  - `package.bat`
  - `tmp_ocr_diag/*.json`
  - `_internal` 下是否重新混入了上述运行库
## 2026-05-01 GitHub 仓库协作层补强
- 仓库根目录现已新增 `README.md`，作为 GitHub 首页主说明文档；原有 `README.txt` 继续保留给打包产物随包分发使用。
- `README.md` 当前覆盖的重点包括：
  - 功能总览
  - 源码运行方式
  - Windows 打包方式
  - 测试入口
  - 项目结构
  - 维护约束
- 仓库根目录现已新增 `requirements.txt`，使用当前本机已验证可导入/可打包的一组固定版本依赖，供源码运行与 CI 构建复用。
- 仓库现已新增 `.github/workflows/build-windows-exe.yml`：
  - 触发方式为 `workflow_dispatch`
  - 运行环境为 `windows-latest`
  - Python 版本固定为 `3.11`
  - `actions/setup-python` 已启用 `pip` 缓存并绑定 `requirements.txt`
  - 直接复用现有 `package.bat`
  - 构建成功后通过 `actions/upload-artifact@v7` 上传 `dist_release_ascii/fx_toolbox` 为 artifact
- 后续若继续维护 GitHub 发布能力，默认顺序应为：
  1. 先更新 `requirements.txt`
  2. 再确认 `package.bat` / `fx_toolbox.spec`
  3. 最后再调整 Actions 工作流
- 这层改动只属于仓库协作与发布层，不涉及业务代码回归；默认无需触碰稳定区 `批量压缩` / `添加水印`。

## 2026-04-30 Git 仓库初始化与上传准备
- 项目根目录现已执行 `git init -b main`，后续工作可以基于本地 Git 历史推进。
- 新增仓库级 `.gitignore`，当前明确忽略：
  - `.session_backups/`
  - `__pycache__/`
  - `build*`
  - `dist*`
  - `tmp_*`
  - `Fengxi_Toolbox_corrupted_backup.py`
- 现阶段可以安全执行 `git add` / `git commit`，不会把打包产物、临时调试目录和会话备份一并纳入版本库。
- 本机当前已确认：
  - `git` 可用
  - `gh` CLI 不可用
  - SSH 到 GitHub 当前不可用：22 端口连接被关闭，443 端口可连通但目标账号未接受本机公钥
  - HTTPS 远端可用，已成功配置 `origin -> https://github.com/Fiercerwind/FengxiToolbox.git`
- 本地首个提交 `2a48666` 已成功推送到 GitHub 私有仓库 `Fiercerwind/FengxiToolbox`，`main` 分支已建立跟踪关系。
- 后续继续发布时，默认基线路径就是当前 `origin/main`，无需再次初始化仓库；优先直接 `git status` -> `git add/commit` -> `git push`。

## 2026-05-05 水印页黑色横条与底部占位修复
- 用户反馈默认水印页中部有一条黑色横条，导致下方功能框显示不全。
- 根因确认仍属于外壳布局问题，不是添加水印业务逻辑：主窗口背景为 `#000000`，`top_bar` / `main_panel` / `bottom_bar` 间距露出时形成黑线；同时底部栏在高 DPI 下实际占位过高，压缩了水印页主区域。
- 当前修复仍只在 `Fengxi_Toolbox.py` 加载器层处理：
  - `_apply_shell_layout_tightening()` 将窗口和 `main_panel` 背景统一为 `COLOR_CARD_ALT`，避免布局缝隙露黑。
  - 取消 `bottom_bar.grid_propagate(False)` 的硬固定高度，改为自然紧凑高度。
  - 收紧顶部栏、进度条、操作按钮区和日志框的高度/外边距。
- 复测 1360x768 窗口：底部栏实际高度约从 `246px` 降到 `149px`，水印主面板可视高度约从 `746px` 提升到 `871px`，右侧水印参数控件完整显示并有余量。
- 稳定区提醒：本次没有改 `watermark` 任务处理逻辑、智能水印规则执行逻辑或批量压缩业务逻辑。

## 2026-05-05 底部栏高度恢复
- 用户确认上一轮压缩后底部操作/日志区过小，需要恢复原来的底部高度。
- 当前处理：保留“窗口/主面板背景统一为 `COLOR_CARD_ALT` 以消除黑色横条”的修复，只恢复底部栏高度策略。
- `_apply_shell_layout_tightening()` 中 `bottom_bar` 恢复 `height=164` + `grid_propagate(False)`，进度条/按钮/日志框恢复到原先较舒展的尺寸。
- 1360x768 复测：`bottom_bar` 实际高度恢复到约 `246px`；`tab_wm` 可视高度约 `690px`，仍高于水印页右侧控件请求高度约 `671px`，控件应完整显示。
- 稳定区提醒：本次仍只改 UI 外壳布局，不改添加水印业务逻辑。

## 2026-05-05 底部运行信息框双倍高度
- 用户要求将底部运行信息/日志框高度增加一倍。
- 当前处理仍只在 `Fengxi_Toolbox.py` 加载器层做 UI 布局调整：
  - `_apply_shell_layout_tightening()` 中 `bottom_bar.height` 从 `164` 增至 `228`。
  - `bottom_bar` 第 2 行 `minsize` 从 `64` 增至 `128`。
  - `log_box.configure(height=64)` 改为 `height=128`。
- 高 DPI 下复测：日志框实际高度从约 `96px` 增至约 `192px`，符合“双倍高度”。
- 为避免 1360x768 窗口下默认水印页右侧参数被裁切，同步微调 `_tighten_watermark_tab_layout()` 的右侧控件垂直间距和滑块组高度；只改 UI 排版，不改添加水印业务逻辑。
- 复测：`right_panel` 请求高度约 `589px`，可视高度约 `594px`，右侧控件可完整显示。

## 2026-05-08 属性页与 PDF 页显示裁切修复
- 用户反馈：属性隐私页底部输入区域被裁切，PDF 功能页左侧按钮列与共享控件显示不全。
- 根因：2026-05-05 将 `bottom_bar` 日志区加高到双倍后，主内容区可视高度降到约 `676px`；`meta` 页原始请求高度约 `754px`，`pdf` 页虽然整体请求高度不高，但左侧功能列内部仍保留较大的按钮高度与间距，导致下半部分被裁切。
- 当前修复仍只在 `Fengxi_Toolbox.py` 加载器层做 UI 调整：
  - 新增 `_tighten_meta_tab_layout()`：隐藏属性页中无子控件的 300px 空白占位 frame，并压紧单选区与两个输入区的高度。
  - 新增/修正 `_tighten_pdf_tab_layout()`：压紧 PDF 页卡片边距、左侧功能按钮高度与共享开关/密码框高度；修正了 PDF 页真实内容嵌套在额外一层 frame 中的层级判断。
  - 新增 `_refresh_visible_tab_layout()`，并在 `patched_switch_tab()` 中于原始切页后执行，确保 `meta/pdf` 的紧凑布局是在页签真正显示后应用，而不是在不可见阶段提前失效。
- 1360x768 复测：
  - `meta` 页请求高度约从 `754px` 降到 `424px`，作者/时间两个输入区完整可见。
  - `pdf` 页请求高度约从 `466px` 降到 `398px`；左侧 5 个模式按钮、`OCR` 按钮及共享控件完整显示。
- 本次未改 PDF/OCR/属性处理业务逻辑，仅调整布局与切页后的可见态刷新。
