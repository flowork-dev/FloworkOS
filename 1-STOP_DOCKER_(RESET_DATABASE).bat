REM#######################################################################
REM WEBSITE https://flowork.cloud
REM File NAME : C:\FLOWORK\1-STOP_DOCKER_(RESET_DATABASE).bat total lines 28 
REM#######################################################################

@echo off
TITLE FLOWORK - Docker Stopper v1.3 (TOTAL WIPE)

cls
echo =================================================================
echo        FLOWORK DOCKER STACK STOPPER (TOTAL WIPE)
echo =================================================================
echo.
echo --- [STEP 1/2] Stopping and removing all Flowork services ---
echo (This will remove containers, networks, and data volumes...)
docker-compose down -v --remove-orphans

echo.
echo --- [STEP 2/2] Hunting and cleaning up all leftover (ghost) containers ---
docker container prune -f

echo.
echo -----------------------------------------------------------------
echo [SUCCESS] Total Wipe complete! All services and leftover containers have been cleaned.
echo -----------------------------------------------------------------
echo.
pause
