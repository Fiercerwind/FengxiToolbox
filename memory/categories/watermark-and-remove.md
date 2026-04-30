# 水印与去水印

## 批量水印
- 任务类型：`watermark`
- 关键参数：
  - 水印文本
  - 字体
  - 字号
  - 透明度
  - 旋转角度
  - 页范围：`all` / `first`
  - 防重模式：`smart` / `force`
  - 是否跳过文件名以 `-` 结尾的文件
  - 是否先转 PDF 再加水印
  - 是否删除源文件
- 关键函数：
  - `create_watermark_packet`
  - `add_watermark_to_pdf`
  - `add_watermark_to_word`

## 去水印
- 任务类型：`remove_wm`
- Word 去水印通过扫描页眉中的艺术字/图片水印处理。
- PDF 去水印走“PDF -> Word -> 去水印 -> PDF”的重构链路。
- 关键开关：`保留我的水印 (XMU_DONE)`。
- 2026-04-22 补充：
  - `remove_wm` 必须稳定走单线程 Word COM 专用分支；如果误落到 `process_single_file()` 的普通路径，PDF/Word 只会被复制并写“跳过”日志，不会真正去水印。
  - `remove_watermark_from_word()` 原始实现会清理页眉 `Shapes`，但会漏掉 `页眉 Range.InlineShapes` 类型的图片水印。
  - 当前已在 `Fengxi_Toolbox.py` 加载器层补了后处理：原函数成功后，再次打开输出文档并清理页眉 `InlineShapes`，覆盖图片型页眉水印漏删问题。
  - 新增回归：`word_remove_wm_header_inline_image`，用于锁定“返回 SUCCESS 但图片水印未实际删除”的历史问题。

## 稳定性标记
- 这块是用户明确标记的稳定区。
- 非必要不改水印逻辑本体，只能做外围修补、兼容性补丁或测试增强。
## 2026-04-22 去水印误删修复
- 已确认旧版 `remove_watermark_from_word()` 过于激进：
- 会直接删除页眉里的全部 `Shapes`。
- `is_pdf_source=True` 时还会继续删除文档级 `Shapes` 与页眉 `InlineShapes`。
- 这会误伤正常页眉 logo、小标题形状，以及部分 PDF 转 Word 后被表示为 shape 的正常内容。
- 当前加载层策略已改为“保守水印判定”：
- 优先删除明确带 `XMU_DONE` 标记的风兮自有水印。
- 对非风兮对象，仅在命中水印关键词，或满足“大尺寸 + 居中/越界 + 斜向/半透明”特征时才删除。
- 页眉 `InlineShapes` 不再全删，只处理明显的大幅图片水印或带水印标记/关键词的对象。
- 这次修复的原则是“宁可少删，也不要误删正常内容”。
- 新增回归：
- `word_remove_wm_header_inline_image`
- `word_remove_wm_preserve_header_assets`
## 2026-04-22 PDF 去水印稳定兜底
- 已确认 `PDF 去水印` 与 `Word 去水印` 是两类不同问题。
- Word 侧的风险是“误删正常图文”，所以当前走保守判定删除。
- PDF 侧的风险是运行时链路不稳定，失败时会直接保留原 PDF，表现为“去水印没生效”。
- 当前加载层已新增 PDF 专用兜底：
- 仅在 `remove_wm` 任务里发现 PDF 输入时接管处理。
- 流程为 `PDF -> ASCII 临时 DOCX -> 安全版 remove_watermark_from_word(..., is_pdf_source=True) -> Word 转回 PDF`。
- 临时 DOCX 放在 ASCII 路径的系统临时目录中，避免中文结果目录或运行时内部临时路径导致的 COM/转换不稳定。
- 这样既保留 Word 去水印的保守删除策略，也让 PDF 去水印不再因为运行时回退而残留水印。

## 2026-04-24 PDF 去水印 COM 稳定性补强
- 已确认 PDF 去水印在批量/连续处理时，还会遇到 `Word.Application` 会话被前一个文件污染的问题。
- 现象：
- `remove_watermark_from_word(..., is_pdf_source=True)` 偶发报 `Open.Sections` 或 `RPC 服务器不可用`。
- 一旦同一个 Word 进程被拖坏，后续 PDF 会一起回退成保留原文件。
- 当前修复：
- PDF 去水印链路中的 Word 会话改为“每个 PDF 独立实例”。
- `_create_hidden_word_app()` 现在使用 `DispatchEx("Word.Application")` 创建隔离的隐藏 Word 进程。
- `remove_watermark_from_word(...)` 与 `convert_doc_to_pdf(...)` 分别使用独立 Word 会话，避免前一步异常污染后一步。
- 结果：
- 连续两份带水印 PDF 专项验证通过。
- `full_debug_test.py` 重新通过 `pdf_remove_wm_workflow`，整轮恢复为 39 项通过。

## 2026-04-24 去水印单文件输出规则
- 用户当前期望已固定：
- 文件夹输入：输出 `【处理完成】结果文件夹`
- 单文件输入：默认在原文件同目录生成新的去水印文件
- 单文件输入：允许可选直接覆盖原文件
- 当前实现：
- UI 新增 `rm_wm_overwrite_original`
- 默认关闭时，单文件结果命名为 `原文件名_去水印.ext`
- 开启后，仅在处理成功时覆盖原文件；失败则原文件保持不变
- 这条规则适用于 PDF / Word / PPT 等 `remove_wm` 单文件场景，不只限于 PDF

## 2026-04-24 PDF 去水印失败防伪成功
- 本轮确认了一个关键历史风险：
- PDF round-trip 中，如果 `remove_watermark_from_word(...)` 失败，旧逻辑仍可能继续把未清理的中间文档转回 PDF
- 同时失败分支还会复制原 PDF 到结果目录，造成“有结果文件但水印还在”的伪成功现象
- 当前约束：
- `remove_watermark_from_word(...)` 不是 `SUCCESS`，或 `cleaned.docx` 未生成，必须直接判定失败
- 失败时不再复制原 PDF 作为结果文件
- 单文件失败时只记日志并保持原文件不变
- 文件夹失败时继续写失败清单报告
