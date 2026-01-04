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
    git \
    wget \
    curl \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

WORKDIR /app

# Install PyTorch with CUDA
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install Chatterbox TTS
RUN pip install --no-cache-dir chatterbox-tts

# Install RunPod SDK and utilities
RUN pip install --no-cache-dir runpod requests soundfile numpy scipy

# Copy handler
COPY handler.py /app/handler.py

# Pre-download model on build (optional - can also download on first run)
RUN python -c "from chatterbox.tts import ChatterboxTTS; ChatterboxTTS.from_pretrained()" || true

# Start handler
CMD ["python", "-u", "/app/handler.py"]
