REM#######################################################################
REM WEBSITE https://flowork.cloud
REM File NAME : C:\FLOWORK\0-FORCE_REBUILD.bat total lines 178 
REM#######################################################################

@echo off
rem (PERBAIKAN) Karakter '&' diganti dengan 'dan' untuk menghindari error batch
TITLE FLOWORK - FULL RESET AND FORCE REBUILD
cd /d "%~dp0"

cls
echo =================================================================
echo     FLOWORK DOCKER - JURUS SAPU JAGAT DAN BANGUN ULANG PAKSA
echo =================================================================
echo.

rem --- (PERBAIKAN OLEH GEMINI - BUG FIX URUTAN PERINTAH) ---
rem (English Hardcode) STEP 0/6: Stop all containers AND clear volumes FIRST.
rem (English Hardcode) This releases file locks on the database (gateway.db)
rem (English Hardcode) BEFORE we try to delete it in the next step.
echo --- [LANGKAH 0/6] Menghancurkan sisa container DAN VOLUME lama ---
echo [INFO] Menjalankan 'docker-compose down --volumes' untuk mematikan container...
echo [INFO] Ini adalah FIX untuk bug "salah key" dan "DB gagal hapus".
docker-compose down -v --remove-orphans
echo [SUCCESS] Semua container mati dan volume lama bersih.
echo.

rem (English Hardcode) STEP 1/6: Nuke ONLY the database/config directory.
rem (English Hardcode) We MUST NOT delete the root /modules, /plugins, etc.
echo --- [LANGKAH 1/6] Menghancurkan folder database lama (Sapu Jagat)... ---
echo [INFO] Menghapus C:\FLOWORK\data (termasuk DBs dan docker-engine.conf)...
rmdir /S /Q "%~dp0\\data"
echo [SUCCESS] Folder database lama bersih.
echo.

rem (English Hardcode) The rmdir commands below are COMMENTED OUT
rem (English Hardcode) to prevent deleting permanent user data (modules, plugins, etc.)
rem (English Hardcode) This is correct behavior.
rem echo [INFO] Menghapus C:\FLOWORK\ai_models...
rem rmdir /S /Q "%~dp0\\ai_models"
rem echo [INFO] Menghapus C:\FLOWORK\ai_providers...
rem rmdir /S /Q "%~dp0\\ai_providers"
rem echo [INFO] Menghapus C:\FLOWORK\assets...
rem rmdir /S /Q "%~dp0\\assets"
rem echo [INFO] Menghapus C:\FLOWORK\formatters...
rem rmdir /S /Q "%~dp0\\formatters"
rem echo [INFO] Menghapus C:\FLOWORK\modules...
rem rmdir /S /Q "%~dp0\\modules"
rem echo [INFO] Menghapus C:\FLOWORK\plugins...
rem rmdir /S /Q "%~dp0\\plugins"
rem echo [INFO] Menghapus C:\FLOWORK\scanners...
rem rmdir /S /Q "%~dp0\\scanners"
rem echo [INFO] Menghapus C:\FLOWORK\tools...
rem rmdir /S /Q "%~dp0\\tools"
rem echo [INFO] Menghapus C:\FLOWORK\triggers...
rem rmdir /S /Q "%~dp0\\triggers"
echo [INFO] Folder data utama (modules, plugins) AMAN.
echo.
rem --- (AKHIR PERBAIKAN) ---


rem --- (MODIFIKASI KODE) Nama langkah diubah jadi 2/6 ---
echo --- [LANGKAH 2/6] Membuat ulang file .env dan semua folder data (jika belum ada) ---
echo [INFO] Memastikan image python:3.11-slim tersedia...
docker pull python:3.11-slim > nul
if %errorlevel% neq 0 (
    echo [ERROR] Gagal menarik image 'python:3.11-slim'. Pastikan Docker terhubung ke internet.
    pause
    exit /b 1
)
echo [INFO] Menggunakan container Docker untuk men-generate kredensial dan folder baru...

rem (COMMENT) Call the centralized Python script
docker run --rm -v "%~dp0:/app" -w /app python:3.11-slim python generate_env.py --force
if %errorlevel% neq 0 (
    echo [ERROR] Gagal menjalankan generate_env.py.
    pause
    exit /b 1
)

echo [SUCCESS] File .env dan semua folder data telah di-generate/diverifikasi.
echo.

rem --- (MODIFIKASI KODE) Nama langkah diubah jadi 3/6 ---
echo --- [LANGKAH 3/6] Memastikan Docker Desktop berjalan ---
docker info > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop tidak berjalan. Nyalakan dulu dan jalankan lagi skrip ini.
    pause
    exit /b 1
)
echo [SUCCESS] Docker Desktop aktif.
echo.

rem --- (MODIFIKASI KODE) Nama langkah diubah jadi 4/6 ---
echo --- [LANGKAH 4/6] Memastikan semua container mati (Safety Check) ---
rem (COMMENT) Perintah 'down -v' sudah dijalankan di LANGKAH 0/6.
rem (COMMENT) Perintah 'rmdir' sudah dijalankan di LANGKAH 1/6.
rem (COMMENT) Perintah di bawah ini hanya untuk safety-check.
docker-compose down --remove-orphans

rem --- (PENAMBAHAN KODE OLEH GEMINI - GABUNG LOGIC) ---
rem (English Hardcode) Adding 'prune' from 1-STOP_DOCKER_(RESET_DATABASE).bat
echo [INFO] Memburu dan membersihkan semua container sisa (hantu)...
docker container prune -f
rem --- (AKHIR PENAMBAHAN KODE) ---

echo [SUCCESS] Semua sisa-sisa lama dan container hantu sudah bersih.
echo.

rem --- (MODIFIKASI KODE) Nama langkah diubah jadi 5/6 ---
echo --- [LANGKAH 5/6] Membangun ulang SEMUA service tanpa cache ---
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo [ERROR] Proses build untuk service gagal. Periksa error di atas.
    pause
    exit /b 1
)
echo [SUCCESS] Semua image sudah siap dari nol.
echo.

rem --- (MODIFIKASI KODE) Nama langkah diubah jadi 6/6 ---
echo --- [LANGKAH 6/6] Menyalakan semua service yang sudah baru ---
docker-compose up -d
echo.
docker-compose ps
echo.
echo -----------------------------------------------------------
echo [INFO] Main GUI is accessible at https://flowork.cloud
echo ------------------------------------------------------------
echo.

rem (PERBAIKAN KUNCI) Bagian ini diubah agar tidak "follow" dan menambahkan pencarian key
echo --- [AUTO-LOG] Displaying Cloudflare Tunnel status (last 50 lines)... ---
echo.
rem (COMMENT) Nama service log sudah benar 'flowork_cloudflared'.
docker-compose logs --tail="50" flowork_cloudflared
echo.
echo -----------------------------------------------------------------
echo.

rem --- (PENAMBAHAN KODE OLEH GEMINI - MEMPERBAIKI LOG KEY YANG HILANG) ---
rem (English Hardcode) This is the fix for the missing key log.
rem (English Hardcode) This logic reads the key from the file generated/overwritten by 'create_admin.py'.
echo --- [ AUTO-LOG (PENTING) ] MENCARI PRIVATE KEY BARU ANDA... ---
echo.
echo     Generated NEW Private Key akan muncul di bawah:
echo.

rem (English Hardcode) This is the correct path where create_admin.py saves the final key.
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
    rem (COMMENT) Fallback to logs, though the file is the source of truth
    docker compose logs gateway | findstr /C:"!!! Generated NEW Private Key:" /C:"0x"
)
rem --- (AKHIR PENAMBAHAN KODE) ---

echo.
echo -----------------------------------------------------------------
rem (English Hardcode) Added 'echo' to fix '[INFO] is not recognized' error
echo [INFO] Copy the Private Key line above (it already includes '0x') and use it to log in.
echo.
pause
