REM#######################################################################
REM WEBSITE https://flowork.cloud
REM File NAME : C:\FLOWORK\scan_flowork.bat total lines 59 
REM#######################################################################

@echo off
cls
color 0B
echo ========================================================
echo    FLOWORK DEEP SCAN - GENERATING FULL FILE MAP
echo ========================================================
echo.
echo Sedang memindai C:\FLOWORK... Mohon tunggu...
echo.

REM Reset file log
echo MAP GENERATED ON %DATE% %TIME% > "C:\FLOWORK_MAP_LENGKAP.txt"
echo -------------------------------------------------------- >> "C:\FLOWORK_MAP_LENGKAP.txt"

REM 1. SCAN AI MODELS (RECURSIVE)
echo [SCANNING] C:\FLOWORK\ai_models (Deep Scan)...
echo. >> "C:\FLOWORK_MAP_LENGKAP.txt"
echo [SECTION: AI MODELS] >> "C:\FLOWORK_MAP_LENGKAP.txt"
if exist "C:\FLOWORK\ai_models" (
    dir "C:\FLOWORK\ai_models" /s /b >> "C:\FLOWORK_MAP_LENGKAP.txt"
) else (
    echo [X] FOLDER TIDAK DITEMUKAN: C:\FLOWORK\ai_models >> "C:\FLOWORK_MAP_LENGKAP.txt"
)

REM 2. SCAN AI PROVIDERS (RECURSIVE)
echo [SCANNING] C:\FLOWORK\ai_providers (Deep Scan)...
echo. >> "C:\FLOWORK_MAP_LENGKAP.txt"
echo [SECTION: AI PROVIDERS] >> "C:\FLOWORK_MAP_LENGKAP.txt"
if exist "C:\FLOWORK\ai_providers" (
    dir "C:\FLOWORK\ai_providers" /s /b >> "C:\FLOWORK_MAP_LENGKAP.txt"
) else (
    echo [X] FOLDER TIDAK DITEMUKAN: C:\FLOWORK\ai_providers >> "C:\FLOWORK_MAP_LENGKAP.txt"
)

REM 3. SCAN CORE SERVICES (PENTING BUAT DEBUG IMPORT)
echo [SCANNING] C:\FLOWORK\flowork-core\flowork_kernel\services (Deep Scan)...
echo. >> "C:\FLOWORK_MAP_LENGKAP.txt"
echo [SECTION: KERNEL SERVICES] >> "C:\FLOWORK_MAP_LENGKAP.txt"
if exist "C:\FLOWORK\flowork-core\flowork_kernel\services" (
    dir "C:\FLOWORK\flowork-core\flowork_kernel\services" /s /b >> "C:\FLOWORK_MAP_LENGKAP.txt"
)

echo.
echo ========================================================
echo    SELESAI!
echo ========================================================
echo.
echo File peta lengkap telah dibuat di:
echo [ C:\FLOWORK_MAP_LENGKAP.txt ]
echo.
echo Buka file tersebut, COPY SEMUA ISINYA, dan kirim ke Chat!
echo.
pause
