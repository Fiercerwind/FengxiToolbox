@echo off
chcp 65001 >nul
title 风兮工具箱 - 最终组装程序 (尊重原文件版)
color 0A

echo =======================================================
echo        正在启动最终组装流程...
echo        (EXE + 字体 + 素材 + 源码 + 说明书)
echo =======================================================
echo.

:: --- 0. 强制关闭旧软件 ---
echo [0/7] 正在检查并关闭旧进程...
taskkill /F /IM "风兮文件批量处理工具箱2.0.exe" >nul 2>&1
if %errorlevel% equ 0 (
    echo    - ⚠️ 已强制关闭正在运行的软件。
) else (
    echo    - 软件未运行，准备就绪。
)
timeout /t 1 >nul

:: --- 1. 素材预检 ---
if not exist "assets\background.png" (
    color 0C
    echo [警告] ❌ 没找到 assets\background.png
    echo 请确认 assets 文件夹就在脚本旁边！
    pause
    exit
)
echo [1/7] ✅ 素材文件检查通过...

:: --- 2. 清理旧文件 ---
echo [2/7] 正在清理旧文件...
if exist "dist" (
    rmdir /s /q "dist"
    if exist "dist" (
        color 0C
        echo [错误] ❌ 无法删除旧的 dist 文件夹！
        echo 请手动删除 dist 文件夹后再试。
        pause
        exit
    )
)
if exist "build" rmdir /s /q "build"
del /q *.spec 2>nul


:: --- 3. 生成 EXE ---
echo [3/7] 正在编译 EXE 主程序...
python -m PyInstaller -F -w ^
 --hidden-import=pdf2docx ^
 --hidden-import=pkg_resources.py2_warn ^
 --hidden-import=PIL ^
 --hidden-import=imageio ^
 --hidden-import=imageio_ffmpeg ^
 -n "风兮文件批量处理工具箱2.0" Fengxi_Toolbox.py




if %errorlevel% neq 0 (
    color 0C
    echo [错误] 编译失败！
    pause
    exit
)

:: --- 4. 部署字体 ---
echo [4/7] 正在部署字体库...
if not exist "dist\fonts" mkdir "dist\fonts"
if exist "SmileySans-Oblique.ttf" (
    copy "SmileySans-Oblique.ttf" "dist\fonts\" >nul
) else (
    echo    - [提示] 没找到字体文件，跳过。
)

:: --- 5. 部署素材 ---
echo [5/7] 正在搬运 assets 素材包...
if exist "assets" (
    mkdir "dist\assets" 2>nul
    xcopy "assets" "dist\assets" /E /I /Y >nul
)

:: --- 6. 备份源码 ---
echo [6/7] 正在备份源码...
copy "Fengxi_Toolbox.py" "dist\" >nul
copy "%~nx0" "dist\" >nul

:: --- 7. 复制说明书 (修正逻辑) ---
echo [7/7] 正在处理说明书...

:: 优先复制你自己的 README.txt
if exist "README.txt" (
    copy "README.txt" "dist\" >nul
    echo    - ✅ 检测到原版 README.txt，已完美复制！
) else (
    :: 只有当你没有 README 时，才生成默认的，防止空缺
    echo    - [提示] 未找到原版 README.txt，生成默认说明书...
    (
    echo ========================================================
    echo               风兮水印格式工具箱 2.0 PRO
    echo ========================================================
    echo.
    echo [重要提示]
    echo 请勿删除本文件夹内的 assets 文件夹，否则软件背景和赞助码将无法显示。
    ) > "dist\README.txt"
)

echo.
echo =======================================================
echo               ✅ 全部大功告成！
echo =======================================================
echo.
echo 请打开 dist 文件夹查看最终成品。
echo.
pause