FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    INPUT_DIR=/data/input \
    OUTPUT_DIR=/data/output \
    OUTPUT_FORMAT=txt \
    WHISPER_MODEL=turbo \
    WHISPER_LANGUAGE=auto \
    WHISPER_DEVICE=cpu \
    WHISPER_FP16=auto \
    WHISPER_TASK=transcribe \
    MODEL_DIR=/models \
    REQUIRE_MODELS_PRESENT=1 \
    DIARIZATION=0 \
    VERBOSE=0 \
    OVERWRITE=0 \
    KEEP_INTERMEDIATE=0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        ffmpeg \
        python3 \
        python-is-python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY requirements.txt /app/requirements.txt

# Install CUDA-enabled PyTorch (cu121) following the official PyTorch wheel index.
RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 --extra-index-url https://pypi.org/simple torch \
    && python3 -m pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY scripts /app/scripts

RUN sed -i 's/\r$//' /app/scripts/entrypoint.sh \
    && chmod +x /app/scripts/entrypoint.sh \
    && mkdir -p /models /data/input /data/output \
    && chown -R appuser:appuser /app /models /data

USER appuser

ENTRYPOINT ["/app/scripts/entrypoint.sh"]

