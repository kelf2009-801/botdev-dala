@echo off
chcp 65001 >nul
title Landing Editor

echo ==================================================
echo   Landing Editor starting...
echo   URL: http://localhost:8095
echo ==================================================
echo.

set "PYTHON_EXE="

if exist "C:\Users\kelf2\AppData\Local\Programs\Python\Python313\python.exe" (
    set "PYTHON_EXE=C:\Users\kelf2\AppData\Local\Programs\Python\Python313\python.exe"
    goto found
)

where python >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_EXE=python"
    goto found
)

where py >nul 2>&1
if %errorlevel%==0 (
    set "PYTHON_EXE=py"
    goto found
)

echo ERROR: Python not found!
echo Install from https://python.org
pause
exit /b 1

:found
echo Python: %PYTHON_EXE%
echo.
%PYTHON_EXE% "D:\Hermes_Projects\Landing-Pages\landing-editor.py" --port 8095

pause
