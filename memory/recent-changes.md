# 最近变更

## 2026-05-22 20:09:57 | ui
- 摘要：remove parallel status hint and restore queue actions
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/architecture.md, memory/debug-status.md
- 说明：Removed the visible bottom-row 并行状态 hint label so it no longer consumes space beside 加入队列 / 队列历史. Kept the 批量并行（部分生效） switch label and underlying parallel capability; _refresh_parallel_mode_hint now clears the hint variable and destroys stale labels. Added regression parallel_hint_removed_queue_actions_kept. Validation: py_compile passed, smoke_test 14/14, full_debug_test 110/110.
