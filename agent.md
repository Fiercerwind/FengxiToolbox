# 风兮工具箱 Agent 约定

## 开工前必做
- 先读 [memory.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory.md)。
- 再读 [memory/load-order.md](/d:/Users/CHEER/Desktop/Tools/FengxiToolbox/memory/load-order.md)。
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
- 优先使用加载器层补丁或外围修补，不要轻易重构/反编译运行时主体。
- 仓库不是 git 仓库，不能依赖 `git diff` / `git restore` 流程。

## 稳定区与禁区
- `批量压缩` 和 `添加水印` 目前被用户明确标记为“很完美”。
- 非必要不要改这两块的业务实现。
- 如果必须修相关问题，优先做最小范围补丁，并在记忆中明确记录原因与影响面。
- OCR 及后续新增功能优先以“风兮工具箱自有工作流”对外呈现。
- 可以复用合规的开源底座，但不要在产品 UI、日志、配置项中直接暴露第三方产品名或要求用户依赖第三方整套软件安装目录。
- OCR 不要锁死单一技术路线，优先维护多后端可切换架构，至少保留默认后端与备用后端思路。
- `build*`、`dist*`、`tmp_*` 主要是产物或测试残留，默认不当作源码区。

## 推荐验证顺序
- 快速回归：`python smoke_test.py`
- 全功能增强自检：`python full_debug_test.py`
- 如果只动了某个类别，再补跑对应工作流，并把结果写入记忆。
## 最高优先级约束
- 未经用户明确授权，以后不得删除任何项目外文件。
- 即使为清理缓存、临时文件、旧版本、打包产物或第三方目录，也只能处理本项目目录内文件。
- 如需删除项目外任何文件，必须先停下并取得用户明确同意。
