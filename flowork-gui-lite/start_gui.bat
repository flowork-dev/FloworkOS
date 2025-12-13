REM#######################################################################
REM WEBSITE https://flowork.cloud
REM File NAME : C:\ORGINAL\flowork-gui-lite\start_gui.bat total lines 42 
REM#######################################################################

@echo off
TITLE FLOWORK GUI - Launcher

REM #######################################################################
REM # Skrip ini adalah launcher untuk GUI.
REM # Karena berada di dalam folder flowork-gui, ia otomatis portabel.
REM #######################################################################

echo [INFO] Starting FLOWORK GUI...

REM ## Otomatis mendeteksi lokasi folder GUI (tempat .bat ini berada)
set "GUI_ROOT_PATH=%~dp0"

REM ## Tentukan path ke Python portabel dan skrip pre-launcher
set "PYTHON_EXE=%GUI_ROOT_PATH%python\pythonw.exe"
set "PRE_LAUNCHER_SCRIPT=%GUI_ROOT_PATH%template\default\pre_launcher.py"

REM ## Validasi path
if not exist "%PYTHON_EXE%" (
    echo [FATAL] Bundled pythonw.exe not found at: %PYTHON_EXE%
    pause
    exit /b 1
)
if not exist "%PRE_LAUNCHER_SCRIPT%" (
    echo [FATAL] Pre-launcher script not found at: %PRE_LAUNCHER_SCRIPT%
    pause
    exit /b 1
)

echo [INFO] Launching the preloader...

REM ## Jalankan pre-launcher.
REM ## Menggunakan "" di path untuk menangani spasi jika ada.
"%PYTHON_EXE%" "%PRE_LAUNCHER_SCRIPT%"

echo [INFO] Application process has been started.
