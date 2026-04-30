@echo off
setlocal
chcp 65001 >nul
title Fengxi Toolbox Packager
color 0A

set "APP_NAME=fx_toolbox"
set "DIST_DIR=dist_release_ascii"
set "BUILD_DIR=build_release_ascii"
set "APP_ROOT=%DIST_DIR%\%APP_NAME%"

echo =======================================================
echo               Fengxi Toolbox Packager
echo          Build onedir release with bundled assets
echo =======================================================
echo.

echo [1/6] Checking required files...
if not exist "Fengxi_Toolbox.py" (
    color 0C
    echo [ERROR] Missing Fengxi_Toolbox.py
    if not defined FX_NO_PAUSE pause
    exit /b 1
)
if not exist "fx_toolbox.spec" (
    color 0C
    echo [ERROR] Missing fx_toolbox.spec
    if not defined FX_NO_PAUSE pause
    exit /b 1
)
if not exist "assets\background.png" (
    color 0C
    echo [ERROR] Missing assets\background.png
    if not defined FX_NO_PAUSE pause
    exit /b 1
)
if not exist "assets\donate_qr.png" (
    color 0C
    echo [ERROR] Missing assets\donate_qr.png
    if not defined FX_NO_PAUSE pause
    exit /b 1
)

echo [2/6] Cleaning previous build folders...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"

echo [3/6] Running PyInstaller...
python -m PyInstaller --clean --noconfirm ^
 --distpath "%DIST_DIR%" ^
 --workpath "%BUILD_DIR%" ^
 fx_toolbox.spec

if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] PyInstaller build failed.
    if not defined FX_NO_PAUSE pause
    exit /b 1
)

echo [4/6] Copying runtime assets...
if not exist "%APP_ROOT%\fonts" mkdir "%APP_ROOT%\fonts"
if not exist "%APP_ROOT%\assets" mkdir "%APP_ROOT%\assets"
if exist "SmileySans-Oblique.ttf" copy /y "SmileySans-Oblique.ttf" "%APP_ROOT%\fonts\" >nul
if exist "assets" xcopy "assets\*" "%APP_ROOT%\assets\" /E /I /Y >nul

echo [5/6] Copying docs...
if exist "README.txt" (
    copy /y "README.txt" "%APP_ROOT%\README.txt" >nul
) else (
    (
        echo Fengxi Toolbox
        echo.
        echo Keep the assets and fonts folders beside the EXE.
    ) > "%APP_ROOT%\README.txt"
)

echo [6/6] Cleaning temporary leftovers...
del /q "%APP_ROOT%\*.tmp" 2>nul
if exist "%APP_ROOT%\_internal" (
    for %%F in (
        msvcp140.dll
        MSVCP140_1.dll
        ucrtbase.dll
        vcruntime140.dll
        vcruntime140_1.dll
    ) do (
        if exist "%APP_ROOT%\_internal\%%~F" del /q "%APP_ROOT%\_internal\%%~F"
    )
    for %%F in ("%APP_ROOT%\_internal\api-ms-win-crt-*.dll") do (
        if exist "%%~fF" del /q "%%~fF"
    )
)

echo.
echo =======================================================
echo Build completed.
echo EXE: %APP_ROOT%\%APP_NAME%.exe
echo =======================================================
echo.
if not defined FX_NO_PAUSE pause
