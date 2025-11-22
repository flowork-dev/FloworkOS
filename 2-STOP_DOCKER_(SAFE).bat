REM#######################################################################
REM WEBSITE https://flowork.cloud
REM File NAME : C:\FLOWORK\2-STOP_DOCKER_(SAFE).bat total lines 25 
REM#######################################################################

@echo off
TITLE FLOWORK - Docker Stopper v1.4 (Safe Mode)
cls
echo =================================================================
echo        FLOWORK DOCKER STACK STOPPER (SAFE MODE)
echo =================================================================
echo.
echo --- [STEP 1/2] Stopping and removing all Flowork containers ---
docker-compose down --remove-orphans
echo.
echo --- [STEP 2/2] Cleaning up leftover (ghost) containers ---
docker container prune -f
echo.
echo -----------------------------------------------------------------
echo [SUCCESS] All Flowork services have been stopped.
echo Your data is safe.
echo -----------------------------------------------------------------
echo.
pause
