#######################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gateway\Dockerfile
# TOTAL LINES: 44
# (MODIFIED BY GEMINI - FIX #6 - FINAL BOOTSTRAP FIX)
#######################################################################

# (Roadmap 1.F) Use slim image, pin version
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# --- (PENAMBAHAN KODE) ---
# Install 'dos2unix' utility to fix Windows CRLF line ending issues.
# Clean up apt cache afterward.
RUN apt-get update && \
    apt-get install -y dos2unix && \
    rm -rf /var/lib/apt/lists/*
# --- (AKHIR PENAMBAHAN KODE) ---

# Install dependencies
# (Roadmap 1.F) Use --no-cache-dir
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# (Roadmap 2.1, 2.3, 2.4, 3.1) Install extra libs
# ... (all other libs) ...
# hrw (Hashing/Cluster) <--- (INI DIA FIX-NYA YANG SEBENERNYA)
RUN pip install --no-cache-dir \
    msgpack \
    PyJWT \
    flask-jwt-extended \
    Flask-Cors \
    Flask-Migrate \
    Flask-Script \
    alembic \
    cryptography \
    prometheus-flask-exporter \
    requests \
    urllib3 \
    mmh3 \
    hrw \
    gunicorn

# Copy the rest of the app files
COPY . .

# (Roadmap 1.A) Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# --- (PENAMBAHAN KODE / MODIFIKASI) ---
# (FIX for Windows CRLF line endings)
# Use the dos2unix utility we just installed.
# RUN ["sed", "-i", "s/\\r$//", "/app/entrypoint.sh"] # (DI-KOMEN - Faulty sed command)
RUN dos2unix /app/entrypoint.sh
# --- (AKHIR PENAMBAHAN KODE) ---

# --- (PENAMBAHAN KODE OLEH GEMINI - SESUAI ROADMAP 5.3) ---
# (English Hardcode) Copy migration scripts and SQL files
# (English Hardcode) NOTE: Paths are Linux-style inside the container
COPY scripts/migrate.py /app/scripts/migrate.py
COPY migrations /app/migrations
# --- (AKHIR PENAMBAHAN KODE) ---

# --- (PENAMBAHAN KODE OLEH GEMINI - FIX #6) ---
# (English Hardcode) Explicitly copy the scripts needed by entrypoint.sh.
# (English Hardcode) This fixes "[Errno 2] No such file or directory".
COPY create_admin.py /app/create_admin.py
COPY seed_dev_engine.py /app/seed_dev_engine.py
# --- (AKHIR PENAMBAHAN KODE) ---

# (Roadmap 1.A / 1.C)
# --- (MODIFIKASI KODE OLEH GEMINI - FIX #6) ---
# (English Hardcode) Original entrypoint is commented out as per Rule #2
# ENTRYPOINT ["/app/entrypoint.sh"]

# (English Hardcode) The CMD below is a "zombie" from a previous fix (Rule #2).
# (English Hardcode) It conflicts with the logic now inside entrypoint.sh.
# CMD ["bash","-c","python /app/scripts/migrate.py && /app/entrypoint.sh"]

# (English Hardcode) This is the correct final command.
# (English Hardcode) It runs entrypoint.sh, which handles *all* boot logic:
# (English Hardcode) 1. flask db upgrade, 2. create_admin, 3. seed_engine, 4. gunicorn
ENTRYPOINT ["/app/entrypoint.sh"]
# --- (AKHIR MODIFIKASI KODE) ---

# Expose the port
EXPOSE 8000