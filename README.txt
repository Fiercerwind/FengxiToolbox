风兮文件批量处理工具箱 4.0
==========================

简介
----
风兮文件批量处理工具箱是一款面向日常办公与资料整理场景的本地批处理工具，提供水印、格式转换、音视频处理、PDF/OCR、图片处理、压缩、属性修改、文件重命名等常用功能。

当前正式版本为 4.0.0，对应 Git 标签版本为 `v4.0.0`。

核心能力
--------
- 批量添加水印
- 去除部分固定样式水印
- Word / PDF / PPT 转换
- PDF 压缩、拆分、加密
- OCR 搜索版 PDF
- 图片转 PDF、多图合并 PDF
- 图片格式转换与压缩
- 音频提取与音频格式转换
- 批量压缩
- 文件时间、作者等元数据修改
- 批量重命名与文件整理

运行方式
--------
1. 运行打包版：双击 `dist_release_ascii\fx_toolbox\fx_toolbox.exe`
2. 运行源码版：在项目目录执行 `python Fengxi_Toolbox.py`

源码运行常见依赖：
- `customtkinter`
- `pypdf`
- `pdf2docx`
- `Pillow`
- `reportlab`
- `pywin32`
- `windnd`
- `imageio`
- `imageio_ffmpeg`
- `moviepy`
- `pywinstyles`
- `rapidocr`
- `onnxruntime`

打包方式
--------
项目默认使用目录式发布，不走单文件模式。

执行：
`set FX_NO_PAUSE=1`
`package.bat`

默认输出目录：
`dist_release_ascii\fx_toolbox\`

获取与发布
----------
- 源码仓库：
  `https://github.com/Fiercerwind/FengxiToolbox`
- 正式发布页：
  `https://github.com/Fiercerwind/FengxiToolbox/releases`
- 正式发布应包含 Windows 打包产物，而不只是源码快照

授权说明
--------
本仓库不是开源仓库。源码、品牌名称、图标和发行包受权利保留约束。

详细条款见：
- `LICENSE`
- `NOTICE`

简要原则：
- 允许按许可条款使用官方未修改发布版
- 不允许未授权复制、修改、再分发、售卖、套壳或去署名
- `风兮`、`Fengxi Toolbox` 与相关图标素材保留全部品牌权利

免责声明
--------
本软件按“现状”提供。执行批量改名、去水印、覆盖原文件或删除源文件前，请先用测试样本验证结果是否符合预期。
