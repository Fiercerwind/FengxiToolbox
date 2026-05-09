# 渐进式加载策略

## Level 0：所有任务都读
- [agent.md](../agent.md)
- [memory.md](../memory.md)
- [memory/distilled-memory.md](distilled-memory.md)
- [memory/recent-changes.md](recent-changes.md)

## Level 1：按类别读
- 改入口、任务调度、依赖注入、打包行为：读 [memory/architecture.md](architecture.md)
- 改水印或去水印：读 [memory/categories/watermark-and-remove.md](categories/watermark-and-remove.md)
- 改文档转换、音频、图片：读 [memory/categories/convert-audio-image.md](categories/convert-audio-image.md)
- 改 PDF、文件重命名、去重、元数据、压缩：读 [memory/categories/pdf-file-meta-zip.md](categories/pdf-file-meta-zip.md)
- 改 GitHub 同步、版本发布、自动化打包：读 [memory/categories/repo-sync-release.md](categories/repo-sync-release.md)

## Level 2：风险控制时再补读
- 任何有副作用的任务，先读 [memory/constraints.md](constraints.md)
- 需要确认现状或回归结论时，再读 [memory/debug-status.md](debug-status.md)

## 工作原则
- 先读蒸馏记忆，再读最近变更，最后才读类别细节。
- 不默认扫描 `build*`、`dist*`、`tmp_*`。
- 修改前先备份，修改后先写记忆，再结束会话。
