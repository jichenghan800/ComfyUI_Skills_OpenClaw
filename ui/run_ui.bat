@echo off
cd /d "%~dp0"
echo Ensuring port 8189 is free...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8189') do taskkill /f /pid %%a >nul 2>&1

echo Starting ComfyUI OpenClaw Skill UI...
python app.py
pause
