@echo off
setlocal
cd /d "%~dp0"
if errorlevel 1 goto folder_error

if exist ".venv\Scripts\python.exe" goto check_python
where py >nul 2>&1
if errorlevel 1 goto use_python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"
if errorlevel 1 goto python_error
echo Preparing the ZEZ environment ^(first launch only^)...
py -3 -m venv ".venv"
if errorlevel 1 goto venv_error
goto check_python

:use_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
if errorlevel 1 goto python_error
echo Preparing the ZEZ environment ^(first launch only^)...
python -m venv ".venv"
if errorlevel 1 goto venv_error

:check_python
".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)"
if errorlevel 1 goto python_error
".venv\Scripts\python.exe" -c "import importlib.metadata as m; import pygame; assert m.version('pygame-ce') == '2.5.6'" >nul 2>&1
if not errorlevel 1 goto run_game
echo Installing game dependencies ^(internet required on first launch^)...
".venv\Scripts\python.exe" -m pip --disable-pip-version-check install -r "requirements.txt"
if errorlevel 1 goto install_error

:run_game
set PYGAME_HIDE_SUPPORT_PROMPT=1
".venv\Scripts\python.exe" "main.py" %*
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" echo ZEZ stopped with error code %RESULT%. See the message above.
exit /b %RESULT%

:folder_error
echo ZEZ could not start: cannot open the game folder.
exit /b 1

:python_error
echo ZEZ requires Python 3.9 or newer. Install it from https://www.python.org/downloads/.
echo Enable the Python launcher during installation. If .venv is outdated, remove it and retry.
exit /b 1

:venv_error
echo ZEZ could not create .venv. Check Python installation and folder permissions.
exit /b 1

:install_error
echo ZEZ dependency installation failed. Check your internet connection and run play.bat again.
exit /b 1
