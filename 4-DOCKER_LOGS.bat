REM#######################################################################
REM WEBSITE https://flowork.cloud
REM File NAME : C:\Users\User\Music\OPEN SOURCE MODE\FLOWORK\4-DOCKER_LOGS.bat total lines 42 
REM#######################################################################

@echo off
TITLE FLOWORK - Docker Log Viewer v1.2 (Open Core MVP)
cls
echo =================================================================
echo                 FLOWORK - DOCKER LOG VIEWER
echo =================================================================
echo.
echo [INFO] This script will display the last 100 log lines from
echo        the Gateway, Core Engine, and Cloudflare Tunnel services
echo        to help debug the Open Core MVP setup.
echo.
echo -----------------------------------------------------------------
echo.
echo --- [1/3] Displaying Logs for: flowork_gateway ---
echo.
docker-compose logs --tail="100" flowork_gateway
echo.
echo -----------------------------------------------------------------
echo.
echo --- [2/3] Displaying Logs for: flowork_core ---
echo.
docker-compose logs --tail="100" flowork_core
echo.
echo -----------------------------------------------------------------
echo.
rem (ADDITION) Displaying cloudflared logs, important for WSS connection
echo --- [3/3] Displaying Logs for: flowork_cloudflared ---
echo.
docker-compose logs --tail="100" flowork_cloudflared
echo.
echo -----------------------------------------------------------------
echo [SUCCESS] Logs have been displayed.
echo Press any key to close.
echo -----------------------------------------------------------------
echo.
pause
