@echo off
cd /d "%~dp0"
if "%~3"=="" (
  echo 用法: run.bat ^<template^> ^<input^> ^<output^> [额外参数...]
  echo 例如: run.bat examples\01-jinja-basics examples\01-jinja-basics\config.yaml examples\01-jinja-basics\generated
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" call update.bat
.venv\Scripts\python.exe src\__main__.py -t "%~1" -i "%~2" -o "%~3" %4 %5 %6 %7 %8 %9
