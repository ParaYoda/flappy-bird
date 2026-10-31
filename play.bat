@echo off
rem Double click this file to play. It does the same as typing: python main.py
rem (the first time it also installs pygame-ce, it needs internet for that)

cd /d "%~dp0"

set PY=python
where py >nul 2>nul
if not errorlevel 1 set PY=py

%PY% --version >nul 2>nul
if errorlevel 1 goto nopython

%PY% -c "import pygame" >nul 2>nul
if not errorlevel 1 goto run

echo Installing pygame-ce, please wait...
%PY% -m pip install pygame-ce
if errorlevel 1 goto fail

:run
%PY% main.py
if errorlevel 1 goto fail
goto end

:nopython
echo Python was not found. Install it from https://www.python.org/downloads/
echo and tick "Add python.exe to PATH" in the installer, then double click this file again.
pause
goto end

:fail
echo.
echo Something went wrong, see the messages above.
pause

:end
