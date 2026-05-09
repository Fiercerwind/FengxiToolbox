# 最近变更

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
