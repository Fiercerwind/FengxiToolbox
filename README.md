# 风兮工具箱 FengxiToolbox

![风兮工具箱图标](assets/fengxi_app_icon.png)

风兮工具箱是一个面向 Windows 桌面环境的本地批处理工具箱，聚焦办公资料整理、文档处理、音视频转换与文件管理。项目当前以中文桌面 GUI 为主，优先服务“本地批量处理、结果可回看、操作可恢复”的日常工作流。

当前发布版本：`3.0.0`

## 当前能力

- 批量添加水印
- 去除部分固定样式水印
- Word / PDF / PPT 格式转换
- 音频提取与音频格式转换
- 批量压缩
- PDF 加密、拆分、多图合并 PDF
- 图片格式转换与压缩
- 文件时间与作者等元数据修改
- 批量重命名与文件整理
- OCR 搜索版 PDF

## 项目特点

- 本地优先：绝大多数处理流程在本机完成，不主动上传用户文件
- 文件与文件夹双入口：支持拖拽或选择单个文件，也支持选择整个目录
- 多后端 OCR：当前架构保留多后端切换能力，避免锁死单一路线
- 打包友好：仓库已包含 PyInstaller 配置与 Windows 打包脚本
- 记忆驱动维护：项目内置 `agent.md`、`memory.md` 与蒸馏记忆机制，方便后续会话快速恢复上下文
- GitHub 回退友好：仓库支持定时同步、手动打包和标签发布

## 运行环境

- 操作系统：Windows
- Python：3.11.x
- Office 相关功能依赖本机可用的 Microsoft Office / COM 环境

## 源码运行

```powershell
python -m pip install -r requirements.txt
python Fengxi_Toolbox.py
```

## 打包 EXE

项目默认使用目录式发布，不走单文件模式。

```powershell
set FX_NO_PAUSE=1
package.bat
```

打包产物默认输出到：

```text
dist_release_ascii\fx_toolbox\
```

主程序路径：

```text
dist_release_ascii\fx_toolbox\fx_toolbox.exe
```

## GitHub 定期同步

### 手动同步

```powershell
powershell -ExecutionPolicy Bypass -File tools\fx_git_sync.ps1
```

这个脚本会：

- 自动检测当前分支
- 自动提交所有未忽略的本地改动
- 在需要时先 `pull --rebase`
- 再推送到 GitHub 对应分支

默认自动提交信息格式为：

```text
chore(sync): auto backup 2026-05-02 21:30:00 +08:00
```

### 注册定时任务

默认推荐每天 `21:30` 自动同步一次：

```powershell
powershell -ExecutionPolicy Bypass -File tools\register_github_sync_task.ps1 -DailyAt 21:30
```

如果要删除这个计划任务：

```powershell
powershell -ExecutionPolicy Bypass -File tools\unregister_github_sync_task.ps1
```

## GitHub Actions

### 手动打包

仓库已提供 Windows 手动打包工作流：

- 入口：`Actions -> Build Windows EXE`
- 方式：手动触发
- 产物：上传 `dist_release_ascii/fx_toolbox` 目录为 artifact

### 标签发布

仓库已提供基于 Git 标签的自动发布工作流：

- 触发方式：推送 `v*` 标签
- 发布内容：自动构建 Windows 目录包、压缩为 zip、创建或更新 GitHub Release
- 发布说明来源：[CHANGELOG.md](CHANGELOG.md)

创建新版本标签的推荐方式：

```powershell
powershell -ExecutionPolicy Bypass -File tools\fx_release_version.ps1 -Version 3.0.0
```

## 版本与发布

- 当前版本文件：[VERSION](VERSION)
- 版本变更记录：[CHANGELOG.md](CHANGELOG.md)
- 当前正式版本目标：`v3.0.0`

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

- 很多功能不能只测 helper，必须测真实 `FengxiToolboxApp.run_process()` 工作流
- Office、拖拽、窗口样式、OCR 等能力会受本机环境影响

## 项目结构

```text
Fengxi_Toolbox.py                   # 加载器层、补丁层、UI 与调度增强
fengxi_runtime.bin                  # 封装后的主体运行时逻辑
tools/fx_pdf_ocr.py                 # OCR 搜索版 PDF 引擎与后端探测
tools/fx_workspace_tools.py         # 备份、记忆、蒸馏与日志工具
tools/fx_git_sync.ps1               # 本机 GitHub 自动同步脚本
tools/register_github_sync_task.ps1 # 注册计划任务
tools/fx_release_version.ps1        # 创建并推送版本标签
assets/                             # 背景图、赞助码、应用图标等资源
memory/                             # 架构、约束、近期改动、分类记忆与研究记录
.github/workflows/                  # 打包与发布工作流
package.bat                         # Windows 打包入口
fx_toolbox.spec                     # PyInstaller 发布配置
smoke_test.py                       # 快速回归
full_debug_test.py                  # 全功能增强自检
```

## 维护约束

- `批量压缩` 与 `添加水印` 当前属于稳定区，非必要不应改动其业务实现
- 优先修改 `Fengxi_Toolbox.py` 的加载器/补丁层，不轻易重写 `fengxi_runtime.bin` 对应逻辑
- 修改任何已有文件前，先使用 `python tools/fx_workspace_tools.py backup <files...>` 做可恢复备份
- 重要改动后，必须同步更新记忆文件并记录变更

## 依赖说明

依赖清单见 [requirements.txt](requirements.txt)。

项目当前已验证的核心依赖包括：

- `customtkinter`
- `pypdf`
- `pdf2docx`
- `Pillow`
- `reportlab`
- `pywin32`
- `windnd`
- `imageio`
- `imageio-ffmpeg`
- `moviepy`
- `pywinstyles`
- `rapidocr`
- `onnxruntime`
- `PyInstaller`

## 免责声明

本软件按“现状”提供。执行批量改名、去水印、覆盖原文件、删除源文件等操作前，请先用测试样本验证结果是否符合预期。
