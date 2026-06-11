@echo off
setlocal EnableExtensions
rem Unified packaging: use repo .venv and build PyInstaller onefile on Windows.
rem Usage from repo root: tools\pack.bat [src]
rem Products: dist\jinja-build.exe and dist\jinja-build-<version>-windows.zip.
rem The script creates or reuses .venv, force-reinstalls the project and PyInstaller.
rem Spec: jinja-build-cli.spec builds the jinja-build.exe binary.
cd /d "%~dp0\.."

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=src"

if not exist ".venv\Scripts\python.exe" (
    echo 未找到 .venv，正在创建...
    py -3 -m venv .venv 2>nul || python -m venv .venv
    if errorlevel 1 (
        echo 错误: 无法创建 .venv，请确认已安装 Python。
        exit /b 1
    )
)

set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" (
    echo 错误: 未找到 %PY%
    exit /b 1
)

echo ==^> 使用虚拟环境: %PY%
"%PY%" -V

"%PY%" -m pip install -q -U pip setuptools wheel
if errorlevel 1 exit /b 1
"%PY%" -m pip install -q --upgrade --force-reinstall -e .
if errorlevel 1 exit /b 1
"%PY%" -m pip install -q --upgrade --force-reinstall "pyinstaller>=6.0"
if errorlevel 1 exit /b 1

if /I not "%TARGET%"=="src" (
    echo Usage: tools\pack.bat [src] >&2
    exit /b 1
)

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

set "SPEC=%CD%\jinja-build-cli.spec"
if not exist "%SPEC%" (
    echo 错误: 未找到 %SPEC% >&2
    exit /b 1
)

echo ==^> PyInstaller: %SPEC%
"%PY%" -m PyInstaller --clean --noconfirm "%SPEC%"
if errorlevel 1 exit /b 1

if exist "%CD%\dist\jinja-build.exe" (
    echo 完成: %CD%\dist\jinja-build.exe (Windows, no staticx)
) else (
    echo 错误: 未在 dist 找到 jinja-build.exe。>&2
    exit /b 1
)

echo ==^> Assemble release archive
"%PY%" tools\bundle_release.py
if errorlevel 1 exit /b 1

echo PyInstaller output directory: %CD%\dist
exit /b 0
