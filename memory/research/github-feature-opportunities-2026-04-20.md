# GitHub 功能机会调研 2026-04-20

## 调研目标
- 参考 GitHub 上与 PDF、扫描件、媒体整理、批处理工具接近的项目。
- 找出风兮工具箱当前还没有、但和现有定位高度匹配的功能。
- 明确哪些适合优先做，哪些先放在中后期。

## 当前项目基线
- 已有：水印、去水印、文档转换、音频转换、批量压缩、PDF 拆分/加密/多图转 PDF、图片转码/压缩、时间/作者元数据、批量重命名、MD5 去重。
- 用户明确稳定区：批量压缩、添加水印。
- 因此新增功能应优先放在 PDF 深加工、智能去重、扫描件增强、媒体整理和隐私处理上。

## 高优先级建议

### 1. OCR 搜索版 PDF
- 价值：
  - 把“扫描版 PDF / 图片 PDF”变成可搜索、可复制文本的 PDF。
  - 非常贴近日常办公场景，和现有 PDF 工具天然同类。
- GitHub 参考：
  - OCRmyPDF: https://github.com/ocrmypdf/OCRmyPDF
  - Stirling PDF: https://github.com/Stirling-Tools/stirling-pdf
- 可吸收点：
  - 多语言 OCR
  - 自动旋转错页
  - 倾斜校正
  - 生成 PDF/A
  - 保留原分辨率并尽量优化体积
- 对风兮的落地建议：
  - 先做“PDF OCR”和“图片 OCR 转 PDF”两个按钮即可。
  - Windows 端建议优先走 `ocrmypdf + tesseract` 外部依赖方案。
  - UI 要显示语言选择、是否 deskew、是否输出 PDF/A。

### 2. PDF 页面整理器
- 价值：
  - 现在只有拆分/加密/合并，多数用户还会需要旋转、裁边、删页、重排。
  - 这是和现有 PDF 模块最接近、最容易被感知到的增强。
- GitHub 参考：
  - pdfarranger: https://github.com/pdfarranger/pdfarranger
  - Stirling PDF: https://github.com/Stirling-Tools/stirling-pdf
- 可吸收点：
  - 页面拖拽排序
  - 旋转 90 度
  - 删除/复制/插空白页
  - 裁白边、裁边距、隐藏边距
  - booklet、小册子拼版
  - 单张合页、2-up / 多页拼一张
- 对风兮的落地建议：
  - 第一阶段先做无需复杂可视化的版本：
    - 页面旋转
    - 删除指定页
    - 提取指定页范围
    - 按页码重排
    - 自动裁白边
  - 第二阶段再考虑缩略图拖拽式页面编排。

### 3. 相似图片 / 相似视频去重
- 价值：
  - 你现在只有 MD5 精确去重。
  - 用户真实场景常常是“同一内容但尺寸不同、压缩过、加过水印、转码过”。
- GitHub 参考：
  - Czkawka: https://github.com/qarmin/czkawka
  - VideoHash: https://github.com/akamhy/videohash
- 可吸收点：
  - 相似图片检测
  - 相似视频检测
  - 对分辨率变化、水印、转码、裁切有一定鲁棒性
  - 缓存以提高二次扫描速度
- 对风兮的落地建议：
  - 先从“相似图片去重”开始，技术门槛最低。
  - 再做“相似视频检测”，可考虑 `videohash` 或 pHash 路线。
  - UI 上必须让用户自己确认删除对象，不要默认自动删。

### 4. 媒体按时间智能重命名
- 价值：
  - 当前文件管家偏通用字符串处理，缺少“照片/视频归档”能力。
  - 这会明显扩展工具箱在素材整理上的实用性。
- GitHub 参考：
  - Date Renamer Toolkit: https://github.com/Ch4r0ne/date-renamer
- 可吸收点：
  - 按最佳拍摄时间命名
  - 多来源时间优先级
  - 预览旧名/新名
  - 冲突自动避让
  - 会话内撤销
  - 支持 sidecar、Google Takeout、文件名模式回退
- 对风兮的落地建议：
  - 先做简化版：
    - EXIF / QuickTime 时间重命名
    - 预览
    - 冲突自动加序号
    - 撤销上一次
  - 后续再加 sidecar / Takeout JSON 支持。

## 中优先级建议

### 5. 扫描件增强
- 价值：
  - 和 PDF OCR 组合后体验会更完整。
  - 对拍照扫描、老旧纸质资料数字化很有帮助。
- GitHub 参考：
  - ScanTailor Advanced: https://github.com/4lex4/scantailor-advanced
  - deskew: https://github.com/galfar/deskew
- 可吸收点：
  - page split
  - deskew
  - 去黑边 / 加边距
  - 内容区域选择
  - 自适应二值化
  - dewarp
- 对风兮的落地建议：
  - 先做轻量版：
    - 批量 deskew
    - 去黑边
    - 自适应黑白化
    - 双页扫描拆分
  - dewarp 可以放后面，因为实现和体验都更重。

### 6. 批量隐私清理
- 价值：
  - 你已有“改作者/改时间”，但还没有“一键去元数据”。
  - 对图片、视频、PDF 的分享前清理非常实用。
- GitHub 参考：
  - ExifCleaner: https://github.com/szTheory/exifcleaner
  - Czkawka: https://github.com/qarmin/czkawka
- 可吸收点：
  - 图片/视频/PDF 批量清空元数据
  - 保留时间戳
  - 另存副本
  - 前后差异查看
- 对风兮的落地建议：
  - 新增“隐私清理”页签或挂在“属性隐私”下。
  - 先支持：图片、PDF、视频。
  - 提供“覆盖原文件 / 另存副本 / 保留文件时间”。

### 7. PDF 敏感信息打码 / 涂黑
- 价值：
  - 办公场景里需求很真实，尤其是病历、表格、合同、截图类资料。
  - 和 OCR、PDF 整理一起会形成完整文档处理链。
- GitHub 参考：
  - Stirling PDF: https://github.com/Stirling-Tools/stirling-pdf
- 可吸收点：
  - 手动区域涂黑
  - 文本关键词打码
  - 自动打码
- 对风兮的落地建议：
  - 第一阶段不做复杂可视化编辑器。
  - 先做“按关键词打码”与“按正则替换为黑块/空白”更现实。

## 低优先级但有吸引力的建议

### 8. 视频联系表 / 缩略图总览
- 价值：
  - 对整理课程视频、素材库、监控片段很方便。
  - 很适合和现有音视频模块形成轻量增强。
- GitHub 参考：
  - vcsi: https://github.com/amietn/vcsi
- 可吸收点：
  - 视频网格缩略图
  - 时间戳标注
  - 媒体信息头部
- 对风兮的落地建议：
  - 适合作为“音频工具”旁边的小功能，不必优先。

## 不建议马上做的方向
- 在线服务型协同、账号体系、云端 API：
  - 和当前本地单机定位不一致。
- 全量 PDF 富编辑器：
  - 复杂度过高，会明显拖慢整体节奏。
- AI 内容理解类功能：
  - 依赖模型、成本、部署复杂度都明显更高，暂时不划算。

## 推荐开发顺序
1. OCR 搜索版 PDF
2. PDF 页面整理基础版
3. 相似图片去重
4. 媒体按时间智能重命名
5. 批量隐私清理
6. 扫描件增强
7. PDF 关键词打码
8. 相似视频去重
9. 视频联系表

## 关键来源
- OCRmyPDF: https://github.com/ocrmypdf/OCRmyPDF
- Stirling PDF: https://github.com/Stirling-Tools/stirling-pdf
- pdfarranger: https://github.com/pdfarranger/pdfarranger
- Czkawka: https://github.com/qarmin/czkawka
- VideoHash: https://github.com/akamhy/videohash
- Date Renamer Toolkit: https://github.com/Ch4r0ne/date-renamer
- ExifCleaner: https://github.com/szTheory/exifcleaner
- ScanTailor Advanced: https://github.com/4lex4/scantailor-advanced
- deskew: https://github.com/galfar/deskew
- vcsi: https://github.com/amietn/vcsi
