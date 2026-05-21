# 最近变更

## 2026-05-21 19:51:45 | runtime
- 摘要：subwindow app icon and history failure filter
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Applied the Fengxi app icon to child windows including the unified file/folder picker, task history detail dialog, and queue/history window so subpages no longer fall back to generic icons. Continued the unfinished next step by wiring failure-category filtering into task history with a new failure filter option menu, matching filter state, and search support for classified failure reasons. Added regression checks for path-missing failure filtering through both direct helper filtering and app-bound filter state. Validation: py_compile passed, smoke_test 14/14, full_debug_test 83/83.

## 2026-05-21 19:08:52 | runtime
- 摘要：history failure classification preview
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Added a lightweight failure classification layer for task history entries so failed rows can surface path-missing, permission, timeout, dependency, partial-failure, and generic failure hints. The history search blob now includes failure kind and reason, and the list view can display the failure label alongside the existing detail lines. Added regression checks for path-missing classification and search-blob inclusion. Validation: py_compile passed, smoke_test 14/14, full_debug_test 81/81.

## 2026-05-21 18:39:59 | runtime
- 摘要：history detail failure grouping and highlighting
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Extended the task history detail dialog with explicit failure sections: failure overview, failure reason, failed items, and key failure logs. Added text-tag highlighting for failed headers, failure text, failed-item lines, and error logs inside the history detail textbox. Added regression checks for grouped failure text and textbox tag ranges. Validation: py_compile passed, smoke_test 14/14, full_debug_test 79/79.

## 2026-05-21 18:20:07 | runtime
- 摘要：history detail open output location
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Added an 打开位置 action to the task history detail dialog. It opens the current entry's best available target on Windows, preferring output_root, then the first output file's parent, then the input's parent directory. Added regression checks for opening output_root, falling back from an output file to its parent directory, and rejecting empty targets.

## 2026-05-21 17:02:05 | runtime
- 摘要：history detail log export
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Added a 导出日志 action to the task history detail dialog. It exports a plain text snapshot of the current entry's title, task, status, input, timestamps, and log lines, using a safe default filename and a clean empty-log fallback. Added regression checks for filename safety, successful log export, and empty-log handling.

## 2026-05-21 16:52:47 | runtime
- 摘要：history detail export
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：Added a 导出结果 action to the task history detail dialog, exporting the current entry's structured task_result JSON with a safe default filename. Added regression checks for filename safety, export success, and empty-entry rejection. Also made the full debug test tolerate a PowerPoint COM Close() hiccup during teardown so the suite finishes cleanly.

## 2026-05-21 16:13:39 | runtime
- 摘要：任务历史增加详情查看入口
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：历史列表新增详情按钮，可查看结构化结果、失败项、输出目录、日志片段与原始 JSON；补充 detail_text 回归。

## 2026-05-21 16:06:12 | runtime
- 摘要：失败重试支持失败项子集回放
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：历史重试优先解析 failed_items，成功生成时可仅重放失败子集；无法解析时回退整任务重试，并清理临时 staging。

## 2026-05-21 15:57:19 | runtime
- 摘要：任务历史增加筛选与回放入口
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：任务队列历史窗口新增状态/功能/关键词筛选，历史条目支持成功回放入队，失败项保留重试；补充历史摘要和回归测试。

## 2026-05-21 15:22:08 | runtime
- 摘要：统一任务结果模型并接入队列历史
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：新增统一 task_result 结构并挂载到 app._fx_last_task_result；run_process 最外层补丁在任务开始时创建结果对象，在结束时统一补齐 status、outputs、output_root、duration_seconds、error 等字段；pdf OCR、pdf 压缩、图片转 PDF、去水印、单文件 zip 已接入结果写入；队列 worker 与历史记录优先消费结构化结果；新增 task_queue_structured_result 与 single_file_input_pdf_compress_result_model 回归；验证 smoke_test 14/14、full_debug_test 61/61。

## 2026-05-20 18:28:52 | watermark
- 摘要：批量水印文件名跳过规则提示与本地记忆修复
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/debug-status.md, memory/recent-changes.md
- 说明：文件名规则控件改为两行布局，完整显示留空默认提示；新增 watermark.filename_skip_rule 用户偏好，持久化开关、开头/结尾和 marker；新增 save/load/hint layout 三条回归；验证 py_compile、smoke_test 14/14、full_debug_test 59/59。

## 2026-05-20 17:15:54 | runtime
- 摘要：新增任务队列、历史记录与失败重试
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：底部新增加入队列和队列历史入口；队列任务保存输入路径、任务类型与参数快照，顺序调用现有 run_process 执行；历史持久化到用户配置目录 queue_history.json，失败历史可重新入队重试；新增 task_queue_snapshot、task_queue_success_history、task_queue_retry_failed 回归；验证 smoke_test 14/14、full_debug_test 56/56、package.bat 打包通过并打开 EXE。

## 2026-05-20 16:17:35 | release
- 摘要：全量自检输出与 Release 上传链路稳健化
- 文件：Fengxi_Toolbox.py, full_debug_test.py, smoke_test.py, .github/workflows/publish-release.yml, memory/architecture.md, memory/debug-status.md, memory/recent-changes.md
- 说明：修复快关探针导致全量测试提前退出并丢失最终 JSON 的问题；smoke/full_debug 改为项目内临时目录并在成功后自动清理；Release 资产上传改用 curl.exe --data-binary 并校验 HTTP 状态码；验证 smoke_test 14/14、full_debug_test 53/53、package.bat 通过。

## 2026-05-10 00:05:23 | release
- 摘要：公开仓库已清理隐私信息，并为 v4.0.0 Release 补传 Windows 打包资产
- 文件：README.md, README.txt, agent.md, memory.md, memory/load-order.md, memory/constraints.md, LICENSE, NOTICE, memory/categories/repo-sync-release.md, dist_release_ascii/fengxi-toolbox-4.0.0-windows.zip
- 说明：清理 README 与记忆入口中的绝对路径/用户名暴露，将 LICENSE/NOTICE 改为不显示个人标识；main 已推送修正版提交，v4.0.0 标签已强制重指向修正版提交；使用 Git 凭据通过 GitHub API 成功上传 dist_release_ascii/fengxi-toolbox-4.0.0-windows.zip，当前 Release 资产数为 1。

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
