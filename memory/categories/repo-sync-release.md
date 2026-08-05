# GitHub 同步与发布

## 2026-05-02 当前基线
- 当前远端仓库：`origin -> https://github.com/Fiercerwind/FengxiToolbox.git`
- 当前默认分支：`main`
- 当前发布版本基线：
  - 展示版本：`4.0`
  - 标签版本：`v4.0.0`
  - 版本文件：`VERSION`
  - 发布说明：`CHANGELOG.md`
- 历史标签 `v3.0.0` 已存在并指向早期发布自动化基线，后续不要重用或覆盖该标签，正式版本从 `v4.0.0` 继续递增。

## 定时同步
- 本机自动同步脚本：`tools/fx_git_sync.ps1`
- 该脚本会：
  - 自动检测当前分支
  - 自动提交所有未忽略改动
  - 在远端领先时先 `pull --rebase`
  - 最后执行 `git push`
- 默认自动提交信息前缀：`chore(sync): auto backup`
- 计划任务注册脚本：`tools/register_github_sync_task.ps1`
- 计划任务移除脚本：`tools/unregister_github_sync_task.ps1`
- 2026-05-02 曾注册每日 `21:30` 计划任务 `FengxiToolbox Auto Sync to GitHub`；该任务已于 2026-07-22 移除，不再作为默认同步方式。

## 2026-07-22 按打包次数同步 GitHub
- 用户明确要求：从本次 GitHub 同步完成后开始，后续每成功打包 `5` 次才自动提交并推送一次 GitHub。
- `package.bat` 在构建完全成功后调用 `tools/fx_package_sync.ps1`；构建失败不计数。
- 计数文件位于本机 `%LOCALAPPDATA%\FengxiToolbox\package-sync-state.json`，不写入仓库、不随 Git 提交；本次同步后基线从 `0/5` 开始。
- 第 5 次成功打包会调用 `tools/fx_git_sync.ps1` 执行提交、拉取变基和推送；同步成功后计数重置为 `0/5`。
- 若 GitHub 同步失败，计数保留，下一次成功打包会继续重试，避免遗漏已完成的 5 次打包。
- 原每日计划任务 `FengxiToolbox Auto Sync to GitHub` 已移除，避免定时任务绕开此规则。
- `package.bat` 调用计数脚本时必须使用 `-RepoRoot "%~dp0."`，不能直接传尾部为反斜杠的 `"%~dp0"`；后者在 Windows 参数解析中会让路径混入引号并导致 `Resolve-Path` 报非法字符。2026-07-22 已在首次实际打包时修复并确认计数为 `1/5`。

## 版本发布
- 版本标签发布脚本：`tools/fx_release_version.ps1`
- 该脚本要求：
  - 工作区必须干净
  - 版本号必须是 `X.Y.Z`
  - 本地与远端都不存在同名标签
- 成功后会创建并推送 `vX.Y.Z` 注释标签
- 2026-05-09 补充约束：
  - 如果仓库已公开，发布前要检查 README、LICENSE、NOTICE 和记忆文件中是否还带有本机用户名、绝对路径或其他不应公开的信息。
  - 如果正式标签刚创建后才发现公开信息问题，可以先修正 `main`，再把同名正式标签重指向修正版提交，保证 GitHub Release 的源码快照同步干净。
  - 如果 GitHub Release 页面只有源码快照，没有 Windows 发布包，需要补传 `dist_release_ascii/fengxi-toolbox-<version>-windows.zip` 这类 onedir 打包资产，不能只留 source code。

## GitHub Actions
- 手动打包工作流：`.github/workflows/build-windows-exe.yml`
  - 用于手动构建 Windows 目录版 EXE
- 正式发布工作流：`.github/workflows/publish-release.yml`
  - 触发方式：推送 `v*` 标签
  - 流程：安装依赖 -> 复用 `package.bat` 打包 -> 压缩产物 -> 调用 GitHub Release API 创建或更新正式版本 -> 上传 zip 资产
  - 发布说明来源：`CHANGELOG.md` 中对应版本段落

## 稳健性约束
- 这套 GitHub 同步/发布方案只应作用于仓库协作层，不应顺带改动稳定业务区。
- 脚本默认根目录解析不能依赖参数默认值阶段的 `$PSScriptRoot`。
- 已确认需要在脚本正文中解析默认 `RepoRoot` 的脚本：
  - `tools/fx_git_sync.ps1`
  - `tools/register_github_sync_task.ps1`
  - `tools/fx_release_version.ps1`

## 推荐操作顺序
1. 本地完成功能修改并验证。
2. 使用手动同步脚本或等待定时同步，把改动推到 GitHub。
3. 更新 `VERSION` 与 `CHANGELOG.md`。
4. 执行 `powershell -ExecutionPolicy Bypass -File tools\fx_release_version.ps1 -Version X.Y.Z`。
5. 等待 `Publish Release` 工作流构建并生成 GitHub Release。

## 2026-06-09 License model update
- User explicitly changed the project license strategy from proprietary/source-available to AGPL-3.0-only open source.
- Commercial use is allowed under AGPL-3.0 as long as AGPL obligations and third-party license obligations are followed.
- Brand/trademark/release identity remains reserved separately in NOTICE: forks and redistributed builds must not present themselves as official Fengxi Toolbox releases and should use a different product name.
- Do not reintroduce proprietary no-redistribution/no-modification restrictions into LICENSE/README because they conflict with AGPL.
- Before this license-only edit, local code was restored from origin/main at commit faba1fc.
