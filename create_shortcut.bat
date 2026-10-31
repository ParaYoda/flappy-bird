@echo off
rem Double click this file once. It creates a "Flappy Bird" shortcut with the bird
rem picture as its icon, in this folder and on your Desktop.
rem (If you move this folder later, just run this file again.)

cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=(Get-Location).Path; $ws=New-Object -ComObject WScript.Shell; foreach($p in @($d,[Environment]::GetFolderPath('Desktop'))){ $s=$ws.CreateShortcut((Join-Path $p 'Flappy Bird.lnk')); $s.TargetPath=(Join-Path $d 'play.bat'); $s.WorkingDirectory=$d; $s.IconLocation=(Join-Path $d 'icon.ico'); $s.Description='Flappy Bird'; $s.Save() }"
if errorlevel 1 goto fail

echo Done. A "Flappy Bird" shortcut was created in this folder and on your Desktop.
pause
goto end

:fail
echo Something went wrong while creating the shortcut.
pause

:end
