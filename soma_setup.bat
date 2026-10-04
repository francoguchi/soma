@echo off
setlocal
py -3.14 -I -c "import sys" >nul 2>&1
if not errorlevel 1 goto python314
py -3.13 -I -c "import sys" >nul 2>&1
if not errorlevel 1 goto python313
echo Source setup requires Windows Python 3.13 or 3.14. 1>&2
exit /b 10
:python314
py -3.14 -I "%~dp0tools\source_launcher.py" setup
exit /b %errorlevel%
:python313
py -3.13 -I "%~dp0tools\source_launcher.py" setup
exit /b %errorlevel%
