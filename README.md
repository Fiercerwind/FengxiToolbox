# 风兮工具箱 FengxiToolbox

![风兮工具箱图标](assets/fengxi_app_icon.png)

风兮工具箱是一个面向 Windows 的本地批处理桌面工具箱，覆盖文档处理、PDF/OCR、图片、音频、压缩、文件整理与元数据修改等常见办公场景。项目以中文 GUI 为主，强调本地处理、可回看结果、可恢复修改和批量工作流效率。

当前正式版本：`4.0.0`
当前正式标签：`v4.0.0`

## 功能概览

### 文档与 PDF

- 批量添加水印
- 去除部分固定样式水印
- Word / PDF / PPT 相互转换
- PDF 压缩、拆分、加密
- OCR 搜索版 PDF
- 图片转 PDF、多图合并 PDF

### 图片与音频

- 图片格式转换
- 图片压缩
- 音频提取
- 音频格式转换

### 文件与批处理

- 批量压缩
- 文件时间与作者等元数据修改
- 批量重命名
- 文件整理与去重

## 项目特点

- 本地优先：绝大多数处理流程在本机完成，不主动上传用户文件。
- 文件与文件夹双入口：支持拖拽或选择单个文件，也支持处理整个目录。
- 多后端 OCR：当前架构保留多后端切换能力，避免锁死单一路线。
- 打包友好：仓库内已包含 PyInstaller 配置、打包脚本和 GitHub Actions 工作流。
- 记忆驱动维护：仓库内置 `agent.md`、`memory.md`、分类记忆和蒸馏机制，便于后续会话快速恢复上下文。
- 可发布可回退：支持本机定时同步、标签发布和 GitHub Release 自动构建。

## 运行环境

- 操作系统：Windows 10/11
- Python：3.11.x
- Office 相关功能依赖本机可用的 Microsoft Office / COM 环境

## 源码运行

```powershell
python -m pip install -r requirements.txt
python Fengxi_Toolbox.py
```

## 打包 EXE

项目默认使用 `onedir` 目录式发布，不走单文件模式。

```powershell
set FX_NO_PAUSE=1
package.bat
```

默认产物目录：

```text
dist_release_ascii\fx_toolbox\
```

主程序：

```text
dist_release_ascii\fx_toolbox\fx_toolbox.exe
```

## 获取与发布

- 源码仓库：`https://github.com/Fiercerwind/FengxiToolbox`
- 正式发布页：`https://github.com/Fiercerwind/FengxiToolbox/releases`
- 发布版包含 Windows 打包产物，不仅是源码快照。

如需从源码自行构建，可直接运行 `package.bat`。

## 版本文件

- 当前版本文件：[VERSION](VERSION)
- 变更记录：[CHANGELOG.md](CHANGELOG.md)
- 当前正式版本基线：`4.0.0` / `v4.0.0`

## 测试与回归

快速回归：

```powershell
python smoke_test.py
```

增强自检：

```powershell
python full_debug_test.py
```

说明：

- 很多功能不能只测 helper，必须测真实 `FengxiToolboxApp.run_process()` 工作流。
- Office、拖拽、窗口样式、OCR 等能力会受本机环境影响。

## 主要文件

```text
Fengxi_Toolbox.py                   # 加载器层、补丁层、UI 与调度增强
fengxi_runtime.bin                  # 封装后的主体运行时逻辑
tools/fx_pdf_ocr.py                 # OCR 搜索版 PDF 引擎与后端探测
tools/fx_workspace_tools.py         # 备份、记忆、蒸馏与日志工具
assets/                             # 图标、赞助码与其他 UI 资源
memory/                             # 架构、约束、近期改动、分类记忆与研究记录
.github/workflows/                  # 打包与发布工作流
package.bat                         # Windows 打包入口
fx_toolbox.spec                     # PyInstaller 发布配置
smoke_test.py                       # 快速回归
full_debug_test.py                  # 全功能增强自检
```

## 授权与权利声明

本仓库不是开源仓库，默认不授予任何源码复用、再分发或商业化权利。详细条款见：

- [LICENSE](LICENSE)
- [NOTICE](NOTICE)

简要说明：

- 允许下载官方发布版并按许可条款在合法范围内使用未修改的官方构建产物。
- 不允许未授权复制、修改、再分发、二次发布、商用售卖、套壳、去署名或使用本项目品牌素材。
- `风兮`、`Fengxi Toolbox`、项目图标及相关品牌视觉均保留权利。

如果需要商业授权、定制授权或合作，请联系权利人并取得书面许可。

## 免责声明

本软件按“现状”提供。执行批量改名、去水印、覆盖原文件、删除源文件等操作前，请先用测试样本验证结果是否符合预期。
