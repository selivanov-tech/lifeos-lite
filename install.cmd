@echo off
chcp 65001 >nul
rem Prefer the cross-platform installer; fall back to PowerShell when Python is missing.
where py >nul 2>nul && (py -3 "%~dp0install.py" %* & goto done)
where python >nul 2>nul && (python "%~dp0install.py" %* & goto done)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
:done
pause
