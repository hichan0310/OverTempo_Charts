@echo off
cd /d "%~dp0"
python server.py
if errorlevel 1 py -3 server.py
pause
