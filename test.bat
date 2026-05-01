@echo off
cls
cd /d %~dp0

call .venv\Scripts\activate.bat
python tests