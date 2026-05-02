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
  - 是否按文件名规则跳过文件
  - 是否先转 PDF 再加水印
  - 是否删除源文件
- 关键函数：
  - `create_watermark_packet`
  - `add_watermark_to_pdf`
  - `add_watermark_to_word`

## 2026-05-02 批量水印文件名跳过规则补丁
- 历史逻辑只支持一个固定规则：
  - 启用开关后，跳过“文件名去掉扩展名后以 `-` 结尾”的文件
- 用户新要求是：
  - 仍然保留“智能跳过”思路
  - 但允许在 UI 里选择“开头”或“结尾”
  - 并允许输入自定义字符或字符串
- 当前实现策略：
  - 不修改 `fengxi_runtime.bin`
  - 只在 `Fengxi_Toolbox.py` 加载器层做最小补丁
  - 保留原有 `wm_skip_hyphen_var` 开关作为是否启用规则的总开关
  - 新增两个 UI 变量：
    - `wm_skip_name_position_var`
    - `wm_skip_name_text_var`
  - 默认值保持旧行为兼容：
    - 位置：`结尾`
    - 字符：`-`
- 运行时补丁策略：
  - 在 `collect_input_files()` 包装层按“开头/结尾 + 自定义字符”过滤文件
  - 在 `run_process()` 包装层临时关闭运行时内建的固定 `-` 结尾判断
  - 这样既保留原水印主体逻辑，又把跳过规则改为用户可配置
- 这一补丁只应影响 `watermark` 任务，不得影响其他任务类型

## 去水印
- 任务类型：`remove_wm`
- Word 去水印通过扫描页眉中的艺术字 / 图片水印处理
- PDF 去水印走“PDF -> Word -> 去水印 -> PDF”的重构链路
- 关键开关：`保留我的水印 (XMU_DONE)`

## 2026-04-22 去水印单线程约束
- `remove_wm` 必须稳定走单线程 Word COM 专用分支
- 如果误落到 `process_single_file()` 普通路径，PDF/Word 只会被复制并写“跳过”日志，不会真正去水印

## 2026-04-22 去水印误删修复
- `remove_watermark_from_word()` 旧实现过于激进
- 当前原则是“宁可少删，也不要误删正常内容”
- 重点修复：
  - 页眉 `InlineShapes` 图片型水印漏删
  - 正常页眉 logo / 标题图形被误删
- 当前回归重点：
  - `word_remove_wm_header_inline_image`
  - `word_remove_wm_preserve_header_assets`

## 2026-04-22 到 2026-04-24 PDF 去水印稳健性补丁
- PDF 去水印与 Word 去水印是两类不同问题
- PDF 链路当前由加载器层兜底为：
  - `PDF -> ASCII 临时 DOCX -> 安全版 remove_watermark_from_word(..., is_pdf_source=True) -> Word 转回 PDF`
- 为避免批量处理中的 COM 污染：
  - `_create_hidden_word_app()` 使用 `DispatchEx("Word.Application")`
  - 去水印和转回 PDF 分别使用独立 Word 会话
- 单文件去水印当前规则：
  - 默认在同目录输出新文件
  - 可选“成功时覆盖原文件”
  - 失败时原文件保持不变

## 稳定性标记
- 这一块是用户明确标记的稳定区
- 非必要不改水印主体逻辑
- 如必须修改，优先做加载器层外围补丁、兼容性补丁或测试增强
