REM#######################################################################
REM WEBSITE https://flowork.cloud
REM File NAME : C:\FLOWORK\3-RUN_DOCKER.bat total lines 85 
REM#######################################################################

@echo off
TITLE FLOWORK - Docker Launcher v1.9 (Smart Cache)
cd /d "%~dp0"

cls
echo =================================================================
echo           FLOWORK DOCKER STACK LAUNCHER
echo =================================================================
echo.
echo --- [STEP 1/4] Ensuring Docker Desktop is running ---
docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop is not running. Please start it and run this script again.
    pause
    exit /b 1
)
echo [SUCCESS] Docker Desktop is active.
echo.
echo --- [STEP 2/4] Stopping any old running containers (Safe Mode) ---
docker-compose down
echo [SUCCESS] Old containers stopped.
echo.
echo --- [STEP 3/4] Starting services (Smart Mode: Code Updates Only) ---
echo (Skipping library reinstall. Using cached environment for speed.)
REM [FIX] Hapus --build agar tidak force install ulang library
REM Perubahan kode Python akan tetap terdeteksi otomatis via Volume Mapping
docker-compose up -d

if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose failed to start containers.
    pause
    exit /b 1
)
echo.
echo --- [STEP 4/4] Displaying the status of running containers ---
echo.
docker-compose ps
echo.
echo -----------------------------------------------------------
echo [INFO] Main GUI is accessible at https://flowork.cloud
echo ------------------------------------------------------------
echo.
echo [IMPORTANT!] If the Core Engine still fails to authenticate after a few minutes,
echo             please check the logs using 'docker-compose logs core'.
echo.
echo --- [AUTO-LOG] Displaying Cloudflare Tunnel status (last 50 lines)... ---
echo.
docker-compose logs --tail="50" flowork_cloudflared
echo.
echo -----------------------------------------------------------------
echo.
echo --- [ AUTO-LOG (IMPORTANT) ] FINDING YOUR PRIVATE KEY... ---
echo.
echo    Your Login Private Key should appear below (inside the warning box):
echo    (If empty/not found, you MUST run '1-STOP_DOCKER_(RESET_DATABASE).bat' ONCE)
echo.
set "KEY_FILE_PATH=%~dp0\data\DO_NOT_DELETE_private_key.txt"
if exist "%KEY_FILE_PATH%" (
    echo [INFO] Reading key from saved file: %KEY_FILE_PATH%
    echo.
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo !!! YOUR LOGIN PRIVATE KEY IS:
    echo.
    TYPE "%KEY_FILE_PATH%"
    echo.
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo.
) else (
    echo [ERROR] Key file not found at %KEY_FILE_PATH%
    echo [ERROR] This can happen on first run if the container is still starting.
    echo [ERROR] Trying to find it in the logs as a fallback...
    echo.
    docker compose logs gateway | findstr /C:"!!! Generated NEW Private Key:" /C:"0x"
)
echo.
echo -----------------------------------------------------------------
echo [INFO] Copy the Private Key line above (it already includes '0x') and use it to log in.
echo.
pause
