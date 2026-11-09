@echo off
cd /d "%~dp0"
set "BRADESCARD_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%BRADESCARD_PYTHON%" set "BRADESCARD_PYTHON=python"
"%BRADESCARD_PYTHON%" actualizar.py
if errorlevel 1 (
  echo No se actualizo el tablero. Revisa los archivos y config.local.json.
  pause
  exit /b 1
)
start "" "%~dp0site\index.html"
pause
