REM#######################################################################
REM WEBSITE https://flowork.cloud
REM File NAME : C:\Users\User\Music\OPEN SOURCE MODE\FLOWORK\3-START_FAST.bat total lines 54 
REM#######################################################################

@echo off
TITLE FLOWORK - FAST LAUNCHER (NO REBUILD)
cd /d "%~dp0"

cls
echo =================================================================
echo           FLOWORK FAST LAUNCHER (NO INSTALL)
echo =================================================================
echo.
echo --- [STEP 1/3] Ensuring Docker Desktop is running ---
docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop is not running.
    pause
    exit /b 1
)
echo [SUCCESS] Docker Desktop is active.
echo.

echo --- [STEP 2/3] Starting existing containers... ---
echo [INFO] Skipping build process. Waking up containers...
REM [FIX] Hapus flag --build agar tidak install ulang
docker-compose up -d

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start containers.
    echo [TIP] If this is your FIRST RUN, please use '3-RUN_DOCKER.bat' instead.
    pause
    exit /b 1
)
echo.

echo --- [STEP 3/3] Displaying status ---
echo.
docker-compose ps
echo.
echo -----------------------------------------------------------
echo [INFO] GUI is ready at https://flowork.cloud
echo -----------------------------------------------------------
echo.
echo --- [AUTO-LOG] Cloudflare Tunnel Status ---
docker-compose logs --tail="20" flowork_cloudflared
echo.

echo -----------------------------------------------------------------
echo [INFO] Done. Happy Flowing!
echo.
pause
