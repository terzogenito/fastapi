@echo off

cd /d "%~dp0"
uvicorn main:app --reload --port 8001
pause
exit