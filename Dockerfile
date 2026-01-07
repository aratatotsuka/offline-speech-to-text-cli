FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    INPUT_DIR=/data/input \
    OUTPUT_DIR=/data/output \
    OUTPUT_FORMAT=txt \
    WHISPER_MODEL=turbo \
    WHISPER_LANGUAGE=auto \
    WHISPER_DEVICE=cpu \
    WHISPER_TASK=transcribe \
    MODEL_DIR=/models \
    REQUIRE_MODELS_PRESENT=1 \
    DIARIZATION=0 \
    VERBOSE=0 \
    OVERWRITE=0 \
    KEEP_INTERMEDIATE=0

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY scripts /app/scripts

RUN mkdir -p /models /data/input /data/output \
    && chown -R appuser:appuser /app /models /data

USER appuser

ENTRYPOINT ["python", "-m", "app"]

