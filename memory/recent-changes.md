# 最近变更

## 2026-05-01 00:00:54 | repo
- 摘要：补齐 GitHub 首页说明、依赖清单与 Windows 自动打包工作流
- 文件：README.md, requirements.txt, .github/workflows/build-windows-exe.yml, memory/architecture.md
- 说明：新增 README.md 作为 GitHub 首页主说明；新增 requirements.txt，固定当前已验证依赖版本；新增 GitHub Actions 手动工作流 build-windows-exe.yml，在 windows-latest + Python 3.11 上复用 package.bat 构建并上传 dist_release_ascii/fx_toolbox artifact。原 README.txt 继续保留给打包产物分发。

## 2026-04-30 23:36:18 | repo
- 摘要：接入 GitHub 远端并完成首次推送
- 文件：memory/architecture.md
- 说明：远端仓库确认为 Fiercerwind/FengxiToolbox。已验证 SSH 不可作为当前默认链路：22 端口连接关闭，443 端口可达但公钥未获接受。随后切换 origin 为 HTTPS，并成功执行 git push -u origin main；本地首个提交 2a48666 已进入 GitHub 私有仓库，main 已建立跟踪关系。

## 2026-04-30 23:23:23 | repo
- 摘要：初始化本地 Git 仓库并建立首个 .gitignore 上传基线
- 文件：.gitignore, memory/architecture.md
- 说明：执行 git init -b main；新增仓库级 .gitignore，忽略 .session_backups、__pycache__、build*、dist*、tmp_* 及 Fengxi_Toolbox_corrupted_backup.py。当前项目已具备本地提交条件，但 gh CLI 不可用，真正推送前仍需确认 GitHub 远端地址与可用认证路径。

## 2026-04-26 00:11:42 | runtime
- 摘要：为setup_sidebar增加创建阶段快路径，继续优化启动速度
- 文件：Fengxi_Toolbox.py, memory/recent-changes.md, memory/architecture.md, memory/debug-status.md
- 说明：新增侧栏按钮轻量占位构建补丁，仅在setup_sidebar创建阶段把按钮临时设为空文本+轻量字体，窗口显示前由_tighten_layout恢复正式图标与文案。实测启动约3.78s降到3.07s，setup_sidebar cProfile约1.505s降到0.183s；侧栏最终文本/图标校验正常，smoke_test 12/12、full_debug_test 47/47通过。

## 2026-04-25 23:59:24 | runtime
- 摘要：收敛懒加载布局刷新范围，降低首次切页开销
- 文件：Fengxi_Toolbox.py, memory/recent-changes.md, memory/architecture.md, memory/debug-status.md
- 说明：拆分_tighten_layout为一次性外框样式与目标页局部布局收紧；_ensure_lazy_tab_initialized只刷新当前懒加载页。基准显示冷启动约4.41s基本持平，首次切页remove_wm/meta/file等更快；py_compile、smoke_test 12/12、full_debug_test 47/47通过。

## 2026-04-25 23:32:44 | progress
- 摘要：统一修复运行时进度条并接入OCR页级进度
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/recent-changes.md, memory/architecture.md, memory/debug-status.md
- 说明：新增加载器层运行时进度跟踪补丁，修正run_process多分支提前跳进度；OCR改为页级总进度；PDF去水印改为完成后推进；新增3条进度回归并验证 smoke_test 12/12、full_debug_test 47/47。
