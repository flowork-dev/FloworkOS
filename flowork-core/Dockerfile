#######################################################################
# WEBSITE https://flowork.cloud
# File NAME : flowork-core/Dockerfile
# AUTHOR : flowork dev
# VERSION : 5.1 (ETERNAL SKELETON - Isolated App Path)
# REFACTORED BY GEMINI - RULE 2: Decoupled Heavy AI for App-Centric Architecture
#######################################################################

# --- Stage 1: The Builder (Keeping Compilers for Dynamic App Installs) ---
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# 1. Install Python 3.11 & System Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    git \
    build-essential \
    cmake \
    ffmpeg \
    portaudio19-dev \
    libportaudio2 \
    pkg-config \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libavfilter-dev \
    libavdevice-dev \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 2. Setup Python Environment
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 4. Install Skeleton Requirements (The lightweight core libs)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade packaging ninja && \
    pip install --no-cache-dir --no-build-isolation -r requirements.txt

# --- Stage 2: The Runner (Optimized for Skeleton Execution) ---
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install Runtime Deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    build-essential \
    git \
    ffmpeg \
    libportaudio2 \
    libgomp1 \
    libgl1 \
    libcurl4-openssl-dev \
    curl \
    # --- ADDED: Essential Libraries for Apps (OpenCV, etc) ---
    libsm6 \
    libxext6 \
    libxrender-dev \
    ca-certificates \
    # ---------------------------------------------------------
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    # --- ADDED: Pip in Runner for Dynamic App Installs ---
    python3-pip \
    # -----------------------------------------------------
    && rm -rf /var/lib/apt/lists/*

# --- ADDED: Install Node.js (Required by yt-dlp for JS Runtime) ---
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*
# ------------------------------------------------------------------

# Copy Virtual Env from Builder
COPY --from=builder /opt/venv /opt/venv

# [English Note] Global path management prioritizing our sanitized venv
ENV PATH="/opt/venv/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"

# [CACHE BUSTER]
ENV FORCE_CODE_UPDATE=v5.1_ETERNAL_CORE_ISOLATION

# [English Note] Creating persistent volumes for Apps and Data
# RUN mkdir -p /app/app /app/data /app/logs # [ZOMBIE] Old path leads to volume collision
# [FIXED] Isolated User Apps path to prevent system amnesia and quarantine crashes
RUN mkdir -p /app/app /app/flowork_apps /app/data /app/logs

# [English Note] Only install essential conduits for Skeleton operation
RUN /opt/venv/bin/pip install --no-cache-dir numpy

COPY . .

# Environment Variables for GPU acceleration support in Apps
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# [ADDED] Default path for apps to sync with NodeManager and AppManager fixes
ENV FLOWORK_APPS_DIR=/app/flowork_apps

# Flowork Core API and Local Dashboard Ports
EXPOSE 8989
EXPOSE 5001

# [English Note] Skeleton Core Conductor Entry point
CMD ["python", "run_server.py"]