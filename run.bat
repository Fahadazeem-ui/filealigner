@echo off
cd /d "%~dp0"
python file_sorter.py
if errorlevel 1 pause
