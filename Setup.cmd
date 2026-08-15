@echo off
setlocal
title DRIP setup

REM Sets up everything DRIP's authoring tools need, and tells you what it found.
REM Double-click it. Safe to run again at any time - it changes nothing that is already right.
REM
REM This part has to be a .cmd rather than Python, because the first thing it checks for
REM is Python.

echo.
echo   DRIP setup
echo   ----------
echo.

REM `where python` is not enough on Windows. A stub called python.exe ships in WindowsApps and
REM exists purely to open the Microsoft Store - it answers `where` and then does nothing. Ask
REM for a version number instead, so only a real interpreter passes.
set "PYOK="
for /f "delims=" %%v in ('python -c "import sys;print(sys.version_info[0]*100+sys.version_info[1])" 2^>nul') do set "PYOK=%%v"

if not defined PYOK (
  echo   [ MISSING ]  Python
  echo.
  echo   DRIP's authoring tools are Python scripts, so they need it installed.
  echo   Nothing else is needed - no extra packages, no toolchain.
  echo.
  where winget >nul 2>&1
  if errorlevel 1 goto :manual
  echo   I can install it for you with Windows' own package manager.
  echo.
  set /p "ANS=  Install Python now? (y/n): "
  if /i not "%ANS%"=="y" goto :manual
  echo.
  echo   Installing. Windows may ask you to approve this.
  echo.
  winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
  echo.
  echo   Installed. Windows needs a new window to see it on the PATH.
  echo   ^>^> Close this window, then run Setup.cmd again. ^<^<
  echo.
  pause
  exit /b 0
)

if %PYOK% LSS 309 (
  echo   [ TOO OLD ]  Python
  echo.
  echo   Found Python, but the tools need 3.9 or newer.
  goto :manual
)

python "%~dp0tools\bootstrap.py" %*
echo.
pause
exit /b 0

:manual
echo.
echo   Get it from   https://www.python.org/downloads/
echo.
echo   During setup, tick "Add python.exe to PATH". That box is the whole
echo   difference between this working and not - it is easy to miss.
echo.
echo   Then run Setup.cmd again.
echo.
pause
exit /b 1
