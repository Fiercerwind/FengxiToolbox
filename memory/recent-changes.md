# 最近变更

## 2026-05-09 23:28:57 | release
- 摘要：公开仓库隐私清理，并准备为 v4.0.0 Release 补传 Windows 打包资产
- 文件：README.md, README.txt, agent.md, memory.md, memory/load-order.md, memory/constraints.md, LICENSE, NOTICE, dist_release_ascii/fengxi-toolbox-4.0.0-windows.zip
- 说明：README 改为公开产品说明，不再展示内部维护细节；记忆入口与约束文件移除本机绝对路径和用户名暴露；LICENSE/NOTICE 去掉个人标识；已生成 dist_release_ascii/fengxi-toolbox-4.0.0-windows.zip，接下来将同步 main、重指向 v4.0.0 标签并上传 Release 资产。

## 2026-05-09 23:00:08 | release
- 摘要：发布基线提升到 4.0.0，并补齐 README、LICENSE、NOTICE 与 GitHub Release 口径
- 文件：VERSION, README.md, README.txt, CHANGELOG.md, LICENSE, NOTICE, Fengxi_Toolbox.py, .github/workflows/publish-release.yml, agent.md, memory.md, memory/architecture.md, memory/categories/repo-sync-release.md
- 说明：将 VERSION、README.md、README.txt、CHANGELOG.md、agent.md、memory.md、repo-sync-release 记忆与启动窗口标题统一提升到 4.0.0 / v4.0.0；新增自定义专有 LICENSE 和 NOTICE；GitHub Release 工作流名称改为 ASCII 的 Fengxi Toolbox <version>；保留 v3.0.0 为历史标签，不再复用。

## 2026-05-09 20:53:00 | ui
- 摘要：清理品牌图标四角黑底，改为透明圆角，并同步重生 PNG/ICO
- 文件：assets/fengxi_app_icon.png, assets/fengxi_app_icon.ico, dist_release_ascii/fx_toolbox/assets/fengxi_app_icon.png, dist_release_ascii/fx_toolbox/assets/fengxi_app_icon.ico
- 说明：仅修改 assets/fengxi_app_icon.png 与 assets/fengxi_app_icon.ico；通过边界连通黑底清除生成透明角，重新打包后已验证 dist_release_ascii/fx_toolbox/assets 中 PNG/ICO 哈希一致且左上角 alpha=0。

## 2026-05-09 20:42:01 | ui
- 摘要：同步发布目录图标资源：将 dist_release_ascii\\fx_toolbox\\assets 下的 fengxi_app_icon.png/ico 更新为用户新放入的品牌图，避免源码资源与已打包目录不一致。
- 文件：-
- 说明：-

## 2026-05-09 19:42:23 | ui
- 摘要：侧栏品牌头部将 FX 文本占位替换为风兮图标，直接复用现有 app icon 资源；仅改品牌区 UI。
- 文件：-
- 说明：-

## 2026-05-09 19:24:01 | watermark
- 摘要：批量水印文本框新增本地记忆与自动回填；保存时机覆盖输入防抖、失焦、开始执行前和关闭前，未改加水印业务逻辑。
- 文件：-
- 说明：-

## 2026-05-09 19:10:52 | ui
- 摘要：使用教程改为应用内滚动帮助页，侧栏按钮与show_readme统一重定向到内置页面；帮助页期间禁用开始按钮，避免误执行。
- 文件：-
- 说明：-

## 2026-05-09 16:46:33 | zip
- 摘要：更新批量压缩页智能混合模式说明文案，仅改加载器/UI补丁层，不动ZIP业务逻辑；说明与当前smart_recursive实际行为对齐。
- 文件：-
- 说明：-
