from __future__ import annotations

from app.errors import DiarizationNotSupportedError


def run_diarization_pipeline() -> None:
    raise DiarizationNotSupportedError(
        "DIARIZATION=1 is not supported in this image. Set DIARIZATION=0."
    )

