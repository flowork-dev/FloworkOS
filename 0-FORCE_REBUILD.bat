REM#######################################################################
REM WEBSITE https://flowork.cloud
REM File NAME : C:\FLOWORK\0-FORCE_REBUILD.bat total lines 113 
REM#######################################################################

@echo off
TITLE FLOWORK - FULL RESET AND FORCE REBUILD
cd /d "%~dp0"

cls
echo =================================================================
echo     FLOWORK DOCKER - FULL RESET AND FORCE REBUILD
echo =================================================================
echo.
echo --- [STEP 0/6] Destroying remaining old containers AND VOLUMES ---
echo [INFO] Running 'docker-compose down --volumes' to shut down containers...
echo [INFO] This is a FIX for the 'wrong key' and 'DB failed to delete' bugs.
docker-compose down -v --remove-orphans
echo [SUCCESS] All containers stopped and old volumes are clean.
echo.
echo --- [STEP 1/6] Destroying old database folder (Total Wipe)... ---
echo [INFO] Deleting C:\FLOWORK\data (including DBs and docker-engine.conf)...
rmdir /S /Q "%~dp0\\data"
echo [SUCCESS] Old database folder is clean.
echo.
echo [INFO] Main data folders (modules, plugins) are SAFE.
echo.
echo --- [STEP 2/6] Re-creating .env file and all data folders (if not exists) ---
echo [INFO] Ensuring python:3.11-slim image is available...
docker pull python:3.11-slim > nul
if %errorlevel% neq 0 (
    echo [ERROR] Failed to pull 'python:3.11-slim' image. Make sure Docker is connected to the internet.
    pause
    exit /b 1
)
echo [INFO] Using Docker container to generate credentials and new folders...
docker run --rm -v "%~dp0:/app" -w /app python:3.11-slim python generate_env.py --force
if %errorlevel% neq 0 (
    echo [ERROR] Failed to run generate_env.py.
    pause
    exit /b 1
)

echo [SUCCESS] .env file and
echo all data folders have been generated/verified.
echo.
echo --- [STEP 3/6] Ensuring Docker Desktop is running ---
docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop is not running. Please start it and run this script again.
    pause
    exit /b 1
)
echo [SUCCESS] Docker Desktop is active.
echo.
echo --- [STEP 4/6] Ensuring all containers are stopped (Safety Check) ---
docker-compose down --remove-orphans
echo [INFO] Hunting and cleaning up all leftover (ghost) containers...
docker container prune -f
echo [SUCCESS] All old leftovers and ghost containers are clean.
echo.
echo --- [STEP 5/6] Rebuilding ALL services without cache ---
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo [ERROR] Build process for services failed. Check the errors above.
    pause
    exit /b 1
)
echo [SUCCESS] All images are ready from scratch.
echo.
echo --- [STEP 6/6] Starting all new services ---
docker-compose up -d
echo.
docker-compose ps
echo.
echo -----------------------------------------------------------
echo [INFO] Main GUI is accessible at https://flowork.cloud
echo ------------------------------------------------------------
echo.
echo --- [AUTO-LOG] Displaying Cloudflare Tunnel status (last 50 lines)... ---
echo.
docker-compose logs --tail="50" flowork_cloudflared
echo.
echo -----------------------------------------------------------------
echo.
echo --- [ AUTO-LOG (IMPORTANT) ] FINDING YOUR NEW PRIVATE KEY... ---
echo.
echo     Generated NEW Private Key will appear below:
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
    echo [ERROR] This should not happen. Trying to find it in logs as a fallback...
    echo.
    docker compose logs gateway | findstr /C:"!!! Generated NEW Private Key:" /C:"0x"
)
echo.
echo -----------------------------------------------------------------
echo [INFO] Copy the Private Key line above (it already includes '0x') and use it to log in.
echo.
pause
