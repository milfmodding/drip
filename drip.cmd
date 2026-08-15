@echo off
REM DRIP content author's tool. Double-click for the interactive menu, or run from a
REM terminal:
REM
REM   drip check                 check every content pack for mistakes
REM   drip new                   make a new item, asking you what you need
REM   drip id slick              find a vanilla item's ID from its name
REM
REM See docs/AUTHORING.md.

where python >nul 2>&1
if errorlevel 1 (
  echo.
  echo   Python isn't installed, or isn't on your PATH.
  echo   Get it from https://www.python.org/downloads/ and tick
  echo   "Add Python to PATH" during setup.
  echo.
  pause
  exit /b 1
)

if "%~1"=="" (
  rem The menu loops on its own, so no pause is needed on the way out.
  python "%~dp0tools\drip.py" menu
  exit /b 0
)

python "%~dp0tools\drip.py" %*
