# 最近变更

## 2026-11-21 20:20:03 | watermark
- 摘要：Use Word Text Recovery Converter on legacy DOC retries
- 文件：Fengxi_Toolbox.py, tools/fx_watermark_core.py, full_debug_test.py, memory/categories/watermark-and-remove.md
- 说明：Repeated DOC PDF retries previously repeated the same OpenAndRepair strategy. Added read-only RECOVR32.CNV (OpenFormat 30) fallback after standard repair opens fail; after a failed/timed-out first DOC conversion, the next retry and direct Word fallback use recovery-only mode. Text recovery is fallback-only because it may simplify formatting. Regression validates converter arguments and full batch retry mode transition auto->text. py_compile passed, smoke 17/17, full_debug 300/300; real Word text-recovery-to-PDF probe passed.

## 2026-11-21 19:20:28 | watermark
- 摘要：Stabilize legacy DOC watermarking and release Word instances
- 文件：Fengxi_Toolbox.py, tools/fx_watermark_core.py, tools/fx_watermark_finish.py, full_debug_test.py, memory/categories/watermark-and-remove.md
- 说明：Legacy .doc uses correctly-positioned OpenAndRepair in read-only mode, saves a separate output copy, and uses repair-based PDF export. Batch behavior is an explicit parameter. Batch Word/PDF conversion workers close their dedicated Word PID after success or failure and force-stop only if it remains after Quit; timeout cleanup uses the same owned PID. Real legacy DOC watermark+edit-password+source-reopen probe passed; smoke 17/17. Full debug was interrupted by full C: and Office COM activation failure after DOCX/DOC password cases passed.

## 2026-11-05 23:10:21 | watermark
- 摘要：Use fresh timestamps for copied skipped and failed watermark files
- 文件：Fengxi_Toolbox.py, full_debug_test.py, memory/categories/watermark-and-remove.md, memory/recent-changes.md
- 说明：Changed watermark skip/failure source-copy paths from copy2 to copyfile so copied outputs receive current filesystem times without extra scans or timestamp writes. Added regression with a 2000 source mtime. full_debug_test.py: 292/292 passed.

## 2026-11-02 23:59:47 | watermark
- 摘要：Fix clipped watermark size slider by locating rows through controls
- 文件：Fengxi_Toolbox.py, memory/categories/watermark-and-remove.md
- 说明：Replaced positional slider-row layout with named-control parent lookup. All three rendered sliders now measure 24px high within 54px rows. Visual and value checks passed; smoke 17/17 passed.

## 2026-11-02 23:15:15 | watermark
- 摘要：Combine watermark finishing before encryption and align parameter controls
- 文件：Fengxi_Toolbox.py, tools/fx_watermark_core.py, tools/fx_watermark_finish.py, tools/fx_edit_password.py, tools/fx_watermark_finish_regression.py, tools/fx_edit_password_regression.py, full_debug_test.py, memory/categories/watermark-and-remove.md
- 说明：Protection runs after content and page insertion; normal PDF saves once and Word opens/saves once. Verify staging before atomic output replacement; preserve old outputs and copy failed sources without clobbering. Plaintext password and aligned parameter rows. Smoke 17/17 and full regression 292/292 passed.

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
