# Chatterbox TTS Worker for RunPod Serverless
# Text-to-Speech with voice cloning and emotion control
#
# Based on: https://github.com/geronimi73/runpod_chatterbox

FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    python3.11-dev \
    git \
    wget \
    curl \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default and ensure pip uses it
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    python3.11 -m pip install --upgrade pip

WORKDIR /app

# Install PyTorch with CUDA (using python3.11 -m pip to ensure correct Python)
RUN python3.11 -m pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install Chatterbox TTS and verify installation in same layer (cache bust v2)
RUN python3.11 -m pip install --no-cache-dir chatterbox-tts && \
    python3.11 -c "import chatterbox; print('Chatterbox installed:', chatterbox.__file__)"

# Install RunPod SDK and utilities
RUN python3.11 -m pip install --no-cache-dir runpod requests soundfile numpy scipy

# Copy handler
COPY handler.py /app/handler.py

# Pre-download model during build (required for fast startup)
RUN python3.11 -c "from chatterbox.tts import ChatterboxTTS; print('Downloading Chatterbox model...'); model = ChatterboxTTS.from_pretrained(); print('Model downloaded successfully')"

# Start handler
CMD ["python3.11", "-u", "/app/handler.py"]
