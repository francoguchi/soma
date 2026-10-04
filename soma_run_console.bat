@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" goto missing
"%~dp0.venv\Scripts\python.exe" -I "%~dp0tools\source_launcher.py" console
set "soma_exit=%errorlevel%"
if not "%soma_exit%"=="0" pause
exit /b %soma_exit%
:missing
echo Run soma_setup.bat to prepare the source environment. 1>&2
pause
exit /b 10
