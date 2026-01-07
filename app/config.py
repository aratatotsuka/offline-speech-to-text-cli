from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from app.errors import ConfigError


def _getenv(env: Mapping[str, str], key: str, default: str) -> str:
    value = env.get(key, "").strip()
    return value if value else default


def _getenv_bool(env: Mapping[str, str], key: str, default: bool) -> bool:
    raw = env.get(key, "").strip()
    if raw == "":
        return default
    if raw.lower() in {"1", "true", "yes", "y", "on"}:
        return True
    if raw.lower() in {"0", "false", "no", "n", "off"}:
        return False
    raise ConfigError(f"invalid {key}={raw!r} (expected 0/1 or true/false)")


def _getenv_int(env: Mapping[str, str], key: str, default: int | None) -> int | None:
    raw = env.get(key, "").strip()
    if raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"invalid {key}={raw!r} (expected integer)") from exc
    return value


@dataclass(frozen=True)
class Settings:
    input_dir: Path
    output_dir: Path
    output_format: str
    whisper_model: str
    whisper_language: str | None
    whisper_device: str
    whisper_task: str
    model_dir: Path
    require_models_present: bool
    diarization: bool
    threads: int | None
    verbose: bool
    overwrite: bool
    keep_intermediate: bool

    @staticmethod
    def from_env(env: Mapping[str, str] | None = None) -> "Settings":
        import os

        env = env or os.environ

        input_dir = Path(_getenv(env, "INPUT_DIR", "/data/input"))
        output_dir = Path(_getenv(env, "OUTPUT_DIR", "/data/output"))

        output_format = _getenv(env, "OUTPUT_FORMAT", "txt").lower()
        if output_format not in {"txt", "docx"}:
            raise ConfigError("OUTPUT_FORMAT must be txt or docx")

        whisper_model = _getenv(env, "WHISPER_MODEL", "turbo")
        whisper_language_raw = _getenv(env, "WHISPER_LANGUAGE", "auto")
        whisper_language = None if whisper_language_raw.lower() in {"auto", "none", ""} else whisper_language_raw

        whisper_device = _getenv(env, "WHISPER_DEVICE", "cpu").lower()
        if whisper_device not in {"cpu", "cuda"}:
            raise ConfigError("WHISPER_DEVICE must be cpu or cuda")

        whisper_task = _getenv(env, "WHISPER_TASK", "transcribe").lower()
        if whisper_task not in {"transcribe", "translate"}:
            raise ConfigError("WHISPER_TASK must be transcribe or translate")

        model_dir = Path(_getenv(env, "MODEL_DIR", "/models"))

        require_models_present = _getenv_bool(env, "REQUIRE_MODELS_PRESENT", True)
        diarization = _getenv_bool(env, "DIARIZATION", False)
        threads = _getenv_int(env, "THREADS", None)
        if threads is not None and threads <= 0:
            raise ConfigError("THREADS must be a positive integer")
        verbose = _getenv_bool(env, "VERBOSE", False)
        overwrite = _getenv_bool(env, "OVERWRITE", False)
        keep_intermediate = _getenv_bool(env, "KEEP_INTERMEDIATE", False)

        return Settings(
            input_dir=input_dir,
            output_dir=output_dir,
            output_format=output_format,
            whisper_model=whisper_model,
            whisper_language=whisper_language,
            whisper_device=whisper_device,
            whisper_task=whisper_task,
            model_dir=model_dir,
            require_models_present=require_models_present,
            diarization=diarization,
            threads=threads,
            verbose=verbose,
            overwrite=overwrite,
            keep_intermediate=keep_intermediate,
        )
