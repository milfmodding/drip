@echo off
setlocal
title DRIP - Review Prices

REM Double-click this. It makes a spreadsheet of every price, and when you've
REM edited it and run this again, it puts your changes back safely.
REM See docs/REVIEWING-PRICES.md.

cd /d "%~dp0"
set SHEET=Prices to review.xlsx

where python >nul 2>&1
if errorlevel 1 (
  echo.
  echo   Python isn't installed on this computer, and this tool needs it.
  echo.
  echo   Get it from  https://www.python.org/downloads/
  echo   During setup, tick "Add Python to PATH".
  echo.
  pause
  exit /b 1
)

if not exist "%SHEET%" goto :make

echo.
echo   Found "%SHEET%".
echo.
echo     1  Put my changes into the mod
echo     2  Start again with a fresh spreadsheet ^(loses any edits^)
echo     3  Do nothing
echo.
set /p CHOICE=  Type 1, 2 or 3 and press Enter:

if "%CHOICE%"=="1" goto :apply
if "%CHOICE%"=="2" goto :remake
goto :done

:remake
del "%SHEET%"
:make
echo.
echo   Making the spreadsheet...
python "tools\price_review.py" export
if errorlevel 1 goto :failed
if exist "%SHEET%" (
  echo   Opening it now.
  start "" "%SHEET%"
  echo.
  echo   Edit the yellow NEW PRICE column, save, close Excel,
  echo   then run this again to apply your changes.
)
goto :done

:apply
echo.
python "tools\price_review.py" apply
if errorlevel 1 goto :failed
goto :done

:failed
echo.
echo   Something went wrong - nothing has been changed.
echo   Show the message above to whoever set this up.

:done
echo.
pause
