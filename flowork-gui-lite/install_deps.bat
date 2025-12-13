REM#######################################################################
REM WEBSITE https://flowork.cloud
REM File NAME : C:\ORGINAL\flowork-gui-lite\install_deps.bat total lines 47 
REM#######################################################################

@echo off
TITLE FLOWORK GUI - Dependency Installer

REM #######################################################################
REM # Skrip ini HANYA untuk menginstal library untuk FLOWORK-GUI
REM # dari file requirements.txt di folder ini.
REM #######################################################################

echo [INFO] Starting FLOWORK GUI dependency installation...
echo.

REM ## Otomatis mendeteksi lokasi folder GUI (tempat .bat ini berada)
set "GUI_ROOT_PATH=%~dp0"

REM ## Tentukan path ke Python & requirements.txt di dalam folder ini
set "PYTHON_EXE=%GUI_ROOT_PATH%python\python.exe"
set "REQUIREMENTS_FILE=%GUI_ROOT_PATH%requirements.txt"

REM ## Validasi path
if not exist "%PYTHON_EXE%" (
    echo [FATAL] Bundled Python not found at: %PYTHON_EXE%
    pause
    exit /b 1
)
if not exist "%REQUIREMENTS_FILE%" (
    echo [FATAL] requirements.txt not found at: %REQUIREMENTS_FILE%
    pause
    exit /b 1
)

echo [INFO] Python and requirements.txt found.
echo [INFO] Installing libraries for the GUI... please wait.
echo ----------------------------------------------------------------------

REM ## Jalankan pip install
"%PYTHON_EXE%" -m pip install -r "%REQUIREMENTS_FILE%"

echo ----------------------------------------------------------------------
echo [SUCCESS] GUI dependencies installed successfully.
echo.
pause
