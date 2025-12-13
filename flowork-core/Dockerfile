#######################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-core\Dockerfile
# [REBUILT BY FLOWORK DEV] - "THE LEGEND EDITION V3.4" (Build Isolation Fix + GGUF Anti-Hang)
#######################################################################

# --- Stage 1: The Builder (NVIDIA CUDA 12.4) ---
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
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3. Install AI Engine (Prioritas - Llama CPP)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    llama-cpp-python \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu124

# 4. Install Sisa Requirements (DENGAN FIX BUILD ISOLATION)
# [FIX] Kita install packaging & ninja dulu, lalu install sisanya dengan --no-build-isolation
# Ini mencegah pip membuat environment terisolasi yang gagal mendeteksi CUDA/Torch saat compile Unsloth
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade packaging ninja && \
    pip install --no-cache-dir --no-build-isolation -r requirements.txt

# --- Stage 2: The Runner (Final Image) ---
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install Runtime Deps
# [FLOWORK FIX] Menambahkan libgl1 agar MediaPipe/OpenCV berjalan mulus
# [FLOWORK FIX V3.3] Menambahkan build-essential & python-dev agar Unsloth bisa compile kernel saat runtime
# [GGUF FIX] Menambahkan libcurl4-openssl-dev agar GGUF conversion gak macet install packages
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
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python

# [CACHE BUSTER] - Ubah angka ini setiap kali kamu update code tapi Docker nggak mau baca
# Ini memaksa Docker untuk menjalankan ulang perintah COPY di bawahnya
ENV FORCE_CODE_UPDATE=v3.4_BUILD_ISOLATION_FIX_PLUS_GGUF

# [FLOWORK FIX] Install Golden Moment Dependencies langsung di Image agar tidak perlu install manual
# Kita install numpy<2.0.0 secara eksplisit untuk menghindari ABI conflict dengan MediaPipe
RUN pip install --no-cache-dir \
    "numpy<2.0.0" \
    opencv-python-headless \
    mediapipe \
    faster-whisper \
    "protobuf==3.20.3"

COPY . .

# Environment Variables
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

EXPOSE 8989
EXPOSE 5001

CMD ["python", "run_server.py"]