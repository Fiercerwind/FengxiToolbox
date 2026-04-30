# PDF、文件、元数据、压缩

## PDF 工具
- 任务类型：`pdf`
- 模式：
  - `merge`
  - `split`
  - `encrypt`
  - `ocr`
- 现状：
  - `split`、`encrypt` 可走单文件处理路径。
  - `merge` 必须走 `run_process()` 内的专用单线程分支。
  - 已在加载器层补丁中强制 `merge` 进入单线程。
  - `ocr` 由加载器层补丁接管 `run_process()`，不走运行时原生分支。
  - `ocr` 当前由风兮自有 OCR 工作流实现，底层使用通用开源 OCR 引擎，不再依赖第三方整套软件目录。
  - `ocr` 默认模型目录优先使用 `assets/ocr_models/rapidocr`，否则退回 `%LOCALAPPDATA%\FengxiToolbox\ocr_models\rapidocr`，也支持环境变量 `FX_OCR_MODEL_ROOT` 覆盖。
  - `ocr` 当前生成的是双层可搜索 PDF，保留原页面画面并叠加透明文字层。
  - `ocr` 当前为多后端架构，支持：
    - `auto`
    - `rapidocr`
    - `paddleocr`
    - `easyocr`
    - `tesseract_cli`
  - `ocr` 自动选择顺序：
    - `rapidocr -> paddleocr -> easyocr -> tesseract_cli`
  - `ocr` 已提供参数：
    - OCR 模型目录
    - OCR 后端
    - OCR 识别配置
    - 提取模式：`mixed` / `fullPage` / `imageOnly`
    - 方向纠正
    - PDF 密码输入框兼容 OCR 解密文档
  - `ocr` UI 当前会显示后端状态面板，并支持手动刷新当前环境探测结果。
  - `ocr` 支持勾选“生成后端对比报告（首页）”，会额外输出 Markdown 报告到结果目录 `_ocr_compare_reports/`。
  - `ocr` UI 当前采用双栏布局：
    - 左侧显示 PDF 基础模式、删除源文件、密码输入与 OCR 模式入口
    - 右侧显示紧凑版 OCR 配置卡片
    - 右侧状态展示当前采用紧凑摘要，避免多行状态文本把底部开关挤出可见区
  - PDF 页面的 OCR 配置区优先通过 `Fengxi_Toolbox.py` 的加载器层布局补丁调整，不改 OCR 业务执行链路。

## OCR 实现说明
- OCR 引擎模块：`tools/fx_pdf_ocr.py`
- 实现策略：
  - 不侵入 `fengxi_runtime.bin`
  - 在 `Fengxi_Toolbox.py` 加载器层补丁 UI 和任务调度
  - 使用统一 PDF 工作流 + 多后端识别器
  - 当前已接入：
    - `RapidOCR + onnxruntime`
    - `PaddleOCR`（可选依赖）
    - `EasyOCR`（可选依赖）
    - `Tesseract CLI`（外部程序）
  - PDF 层处理统一使用 `PyMuPDF`
  - UI、日志、环境变量与模块命名统一使用风兮自有表述，避免产品层面依赖第三方品牌
  - 当前默认推荐后端仍为 `RapidOCR`，但不是唯一实现路径

## 维护注意
- OCR 模式下默认单线程，避免多文档同时拉起 OCR 子进程导致资源争用。
- OCR 界面如果出现“看不全”或纵向溢出，优先检查 `patched_init_pdf_ui()` 中的双栏容器与面板内边距，不要回退到整块纵向堆叠。
- 当前已验证：`CTkScrollableFrame` 方案在该页面上容易出现内容空白，优先使用普通 `CTkFrame` + 紧凑排版。
- UI 下拉值为了避开编码链路问题，模式值采用 ASCII 前缀：
  - `mixed | ...`
  - `fullPage | ...`
  - `imageOnly | ...`
- OCR 后端切换优先修改 `tools/fx_pdf_ocr.py` 的后端注册与适配层，不要复制整套 PDF 叠字逻辑。
- 可选后端未必默认安装；如果用户指定某后端不可用，应优雅报错或退回 `auto`。
- 后端状态展示基于 `discover_backend_status()` 与 `build_backend_status_text()`，后续如果新增后端，要同步更新状态汇总逻辑。
- 对比报告当前基于首页整页渲染采样，目标是让不同后端在同一输入条件下可比较。
- 对比报告逻辑集中在 `compare_pdf_ocr_backends()` 与 `write_pdf_ocr_comparison_report()`。
- 如果未来要支持“图片 OCR 转 PDF”，优先复用 `tools/fx_pdf_ocr.py`，不要重复造 OCR 调度逻辑。

## 文件管家
- 任务类型：`file`
- 模式：
  - `rename`
  - `dedup`
- `rename` 子模式：
  - `add`
  - `replace`
  - `cut`
- `dedup` 依赖全目录 MD5 去重逻辑，必须走 `run_process()` 的专用单线程分支。
- 已在加载器层补丁中强制 `dedup` 进入单线程。

## 属性隐私
- 任务类型：`meta`
- 模式：
  - `author`
  - `time`
- PDF 作者修改直接通过 `pypdf` 写元数据。
- Office 作者修改依赖 COM。
- 时间修改是通用文件操作。

## 批量压缩
- 任务类型：`zip`
- 模式：
  - `total`
  - `recursive`
  - `smart_recursive`
- 这块被用户标记为稳定区，默认不动业务代码。

## 2026-04-25 OCR 单文件/拖拽输入补丁
- OCR 搜索版 PDF 属于 PDF 工具页中的加载层自定义工作流，不完全依赖运行时原始 `run_process()` 分支。
- 因此它不能假设 `input_folder` 一定是目录。
- 当前规则：
- 文件夹输入：输出到 `输入文件夹\\RESULT_FOLDER_NAME`
- 单文件输入：输出到 `单文件父目录\\RESULT_FOLDER_NAME`
- 拖拽单文件 PDF 到窗口后，`app.input_path` 必须保持精确文件路径，`_fx_input_pick_mode == 'file'`
- 随后直接运行 `pdf_mode == "ocr"` 也必须成功生成 OCR 结果
- 当前新增回归：
- `pdf_ocr_searchable`
- `pdf_ocr_compare_report`
- `single_file_input_pdf_ocr`
- `drag_drop_single_file_pdf_ocr`
- 当前整轮验证已恢复为 43 项通过。
## 2026-04-25 OCR 打包版 DLL 初始化修复
- OCR 后端状态面板现在不仅检查模块是否存在，还会做真实导入探测。
- `rapidocr` 路线当前固定先调用 `tools/fx_pdf_ocr.py` 中的 `_prepare_windows_ocr_runtime_dirs()`。
- 该补丁的核心不是改 OCR 识别逻辑，而是修复打包版 `onnxruntime` 的运行时装载条件。
- 当前已验证：
  - 源码侧 OCR 搜索版 PDF 正常。
  - 单文件输入与拖拽单文件 OCR 正常。
  - 打包产物里的 `onnxruntime_pybind11_state.pyd` 在显式注册 `onnxruntime\capi` 后可成功导入。
- 维护注意：
  - 后续如果继续改 OCR 打包链路，优先保留“只注册 `onnxruntime\capi`”这一策略。
  - 不要把整层 `_internal` 当作 OCR DLL 搜索路径的唯一兜底方案。

## 2026-04-25 OCR 探测改为按需重检
- OCR 页面初始状态文本当前是轻量提示，不会在打开页面时立即触发真实导入探测。
- `build_backend_status_text(detailed=True)` 才会做详细导入检测；默认调用走轻量展示。
- `auto` 选后端当前不再依赖状态面板结果，而是在真正处理时逐个尝试真实导入。
- 如果全部失败，错误信息会带上每个后端的失败原因，便于继续定位打包问题。
## 2026-04-25 OCR 打包版库冲突结论
- OCR 搜索版 PDF 的源码工作流一直是通的，这次失败点确认只在打包版 EXE。
- 真正根因不是 “RapidOCR 包没打进去”，而是 `_internal` 根目录里随包带出的本地 MSVC/UCRT 运行库和 `onnxruntime` 冲突。
- 当前确认要从正式产物中排除的 DLL：
  - `msvcp140.dll`
  - `MSVCP140_1.dll`
  - `vcruntime140.dll`
  - `vcruntime140_1.dll`
  - `ucrtbase.dll`
  - `api-ms-win-crt-*.dll`
- 当前稳定做法：
  - 保留 `onnxruntime\capi` 下的 ORT 二进制。
  - 让打包版优先使用系统提供的运行库，而不是 `_internal` 中的本地 CRT 副本。
  - `fx_toolbox.spec` 过滤冲突 DLL，`package.bat` 再做一次兜底清理。
- 以后如果用户反馈“OCR 找不到库 / 没有可用后端 / DLL 初始化失败”，排查顺序应为：
  - 先看 `tmp_ocr_diag\*.json`
  - 再看 `dist_release_ascii\fx_toolbox\_internal` 是否重新带入上述 DLL
  - 最后才回头怀疑 `tools/fx_pdf_ocr.py` 的后端选择逻辑
