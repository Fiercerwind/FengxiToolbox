# 最近变更

## 2026-11-02 22:36:23 | watermark
- 摘要：Add optional editing passwords to batch watermark outputs
- 文件：Fengxi_Toolbox.py, tools/fx_edit_password.py, tools/fx_edit_password_regression.py, full_debug_test.py, memory/categories/watermark-and-remove.md
- 说明：Added password row beneath filename skip controls; PDF owner-password encryption with password-free viewing; Word read-only protection; skip preservation and password-aware output reuse. Smoke 17/17 and full debug 286/286 passed.

## 2026-10-29 15:21:08 | watermark
- 摘要：Rename watermark copy option to include failed files
- 文件：Fengxi_Toolbox.py, memory/categories/watermark-and-remove.md
- 说明：Changed the checkbox label to 跳过/失败文件复制到输出文件夹; smoke test passed.

## 2026-10-29 15:04:48 | watermark
- 摘要：Copy failed watermark sources when the copy-skipped option is enabled
- 文件：Fengxi_Toolbox.py, memory/categories/watermark-and-remove.md
- 说明：Applied the existing output-copy policy to failed watermark items in serial and parallel PDF paths; smoke test passed and full_debug_test.py passed 272/272.
