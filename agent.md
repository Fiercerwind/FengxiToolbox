# 风兮工具箱 Agent 约定

## 开工前必做
- 先读 [memory.md](memory.md)。
- 再读 [memory/load-order.md](memory/load-order.md)。
- 然后按任务类别渐进式加载对应记忆文件，优先读蒸馏记忆和最近变更，避免整仓库全量重扫。
- 可以先运行 `python tools/fx_workspace_tools.py snapshot` 获取推荐加载顺序。

## 修改前备份
- 修改任何已有文件前，先运行 `python tools/fx_workspace_tools.py backup <files...>`。
- 备份目录位于 `.session_backups/`，脚本会自动保留最近会话并清理旧备份，避免垃圾文件无限增长。
- 新建文件不需要备份，但如果后续继续修改它，也应纳入备份。

## 修改后记忆
- 重要改动完成后，必须同步更新相关记忆文件。
- 至少要做两件事：
  1. 更新对应类别的 `.md` 记忆文件。
  2. 运行 `python tools/fx_workspace_tools.py log-change --category <category> --summary "<summary>" --files <files...> --details "<details>"`。
- `recent-changes.md` 保存未蒸馏变更，累计达到 30 条后自动蒸馏进 `distilled-memory.md`。

## 项目关键事实
- 主入口是 `Fengxi_Toolbox.py`，但它本质上是加载器。
- 绝大多数业务逻辑封装在 `fengxi_runtime.bin`，运行时通过 `marshal.loads(...)` 加载并注入全局。
- UI 与任务调度核心类是 `FengxiToolboxApp`。
- 文件管家去重现在分成两层：`tools/fx_file_manager_task.py` 负责任务适配，`tools/fx_file_manager_core.py` 负责去重核心；以后改 `file + dedup` 优先看这两层，不要直接回退到原 runtime 分支。
- 音频任务现在由 `tools/fx_audio_task.py` 承接任务编排、输出路径、单文件处理和并行执行；`Fengxi_Toolbox.py` 只应保留薄包装和路由，不要把旧音频实现重新写回主文件。
- 优先使用加载器层补丁或外围修补，不要轻易重构/反编译运行时主体。
- 仓库当前是 Git 仓库，远端为 GitHub；发布与回退优先走 `git status`、`git diff`、标签与 Release 流程。

## 稳定核心修改规则
- `批量压缩` 和 `添加水印` 不再是绝对禁区；用户已明确允许在必要时修改渲染核心和压缩核心。
- 修改这些核心时，最高目标是保证处理逻辑和功能稳定，不允许为了重构、风格或推测优化随意改变既有行为。
- 每次触碰核心前必须先确认影响面，优先用最小补丁解决明确问题；如确实需要重构，必须保持对外参数、输出规则、命名规则、跳过规则和结果模型兼容。
- 每次触碰核心后必须补或更新回归测试，至少运行 `python smoke_test.py`；涉及真实工作流、输出路径、Word/PDF/ZIP 语义时还要运行 `python full_debug_test.py` 或对应专项验证。
- 修改完成后必须在记忆中记录原因、影响范围、验证结果和是否改变用户可见行为。
- OCR 及后续新增功能优先以“风兮工具箱自有工作流”对外呈现。
- 可以复用合规的开源底座，但不要在产品 UI、日志、配置项中直接暴露第三方产品名或要求用户依赖第三方整套软件安装目录。
- OCR 不要锁死单一技术路线，优先维护多后端可切换架构，至少保留默认后端与备用后端思路。
- `build*`、`dist*`、`tmp_*` 主要是产物或测试残留，默认不当作源码区。
- 当前正式发布基线：`4.0.0` / `v4.0.0`。

## 推荐验证顺序
- 快速回归：`python smoke_test.py`
- 全功能增强自检：`python full_debug_test.py`
- 如果只动了某个类别，再补跑对应工作流，并把结果写入记忆。
## 最高优先级约束
- 未经用户明确授权，以后不得删除任何项目外文件。
- 即使为清理缓存、临时文件、旧版本、打包产物或第三方目录，也只能处理本项目目录内文件。
- 如需删除项目外任何文件，必须先停下并取得用户明确同意。

## Default Packaging Behavior
- After completing implementation or bug fixes, default to running the release package flow and opening `dist_release_ascii\fx_toolbox\fx_toolbox.exe` for the user.
- Skip automatic packaging/opening only when the user explicitly says not to package, not to open, or asks for analysis only.
- Before packaging, stop only the existing project-packaged `fx_toolbox.exe` process from this repository's `dist_release_ascii\fx_toolbox` path so the build output is not locked.

## Watermark Type-Skip Rule
- Batch watermark now supports a second skip dimension by file type: `PDF`, `Word`, and `PPT`.
- These type-skip options are loader/task-runner behavior, not a rendering-core rule change.
- If none of the type checkboxes are selected, batch watermark behavior must remain exactly as before.
- If one or more type checkboxes are selected, matching files must be skipped from watermark processing, counted in `skipped_count`, and logged as `按文件类型跳过`.
- If `跳过文件复制到输出文件夹` is enabled, type-skipped files must also be copied into the output/result folder just like filename-rule skipped files and other unprocessed skipped files.
- The selected type-skip options must participate in last-settings memory so the next session restores them.
