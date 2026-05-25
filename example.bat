@echo off
cd /d "%~dp0"
if "%~1"=="" (
  echo 用法: example.bat ^<示范目录名^>
  echo 例如: example.bat 01-jinja-basics
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" call update.bat
.venv\Scripts\python.exe src\__main__.py -t "examples\%~1" -i "examples\%~1\config.yaml" -o "examples\%~1\generated" %2 %3 %4 %5 %6 %7 %8 %9
