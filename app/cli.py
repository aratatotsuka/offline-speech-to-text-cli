from __future__ import annotations

import sys

from app.config import Settings
from app.errors import AppError, ConfigError
from app.log import log_error, log_info


def _print_help() -> None:
    print(
        "\n".join(
            [
                "local-transcription (container entrypoint)",
                "",
                "This container is configured via environment variables.",
                "You can also override the device via a startup argument: --device cpu|cuda",
                "Priority: --device > WHISPER_DEVICE > default cpu",
                "See README.md for full usage and docker run examples (offline: --network none).",
                "",
                "Key env vars:",
                "  INPUT_DIR=/data/input",
                "  OUTPUT_DIR=/data/output",
                "  OUTPUT_FORMAT=txt|docx",
                "  WHISPER_MODEL=turbo",
                "  MODEL_DIR=/models",
                "  REQUIRE_MODELS_PRESENT=1",
                "  WHISPER_FP16=auto|0|1",
                "  DIARIZATION=0",
            ]
        )
    )


def _ensure_cuda_available() -> None:
    try:
        import torch  # type: ignore
    except Exception as exc:
        raise ConfigError(
            "WHISPER_DEVICE=cuda was requested, but PyTorch could not be imported. "
            f"Make sure the image includes a CUDA-enabled PyTorch build. (detail: {exc})"
        ) from exc

    try:
        available = bool(torch.cuda.is_available())
    except Exception as exc:
        raise ConfigError(
            "WHISPER_DEVICE=cuda was requested, but torch.cuda.is_available() failed.\n"
            f"detail: {exc}\n"
            "Hints: run with `--gpus all`, and ensure the host has NVIDIA Container Toolkit and a compatible NVIDIA driver."
        ) from exc

    if available:
        return

    version_cuda = getattr(getattr(torch, "version", None), "cuda", None)
    detail_parts: list[str] = []
    detail_parts.append(f"torch.version.cuda={version_cuda!s}")
    try:
        detail_parts.append(f"torch.cuda.device_count={torch.cuda.device_count()!s}")
    except Exception as exc:
        detail_parts.append(f"torch.cuda.device_count error={exc!s}")
    detail = ", ".join(detail_parts)

    raise ConfigError(
        "WHISPER_DEVICE=cuda was requested, but CUDA is not available.\n"
        f"({detail})\n"
        "GPU execution requires passing GPUs to the container (e.g., `docker run --gpus all ...`) "
        "and having NVIDIA Container Toolkit + a compatible NVIDIA driver installed on the host.\n"
        "If you intended to run on CPU, use `--device cpu` (or set WHISPER_DEVICE=cpu)."
    )


def main(argv: list[str]) -> int:
    if any(arg in ("-h", "--help") for arg in argv):
        _print_help()
        return 0

    try:
        settings = Settings.from_env()
        from app.pipeline import run_pipeline

        if settings.whisper_device == "cuda":
            _ensure_cuda_available()

        log_info(
            "start",
            f"input_dir={settings.input_dir}",
            f"output_dir={settings.output_dir}",
            f"output_format={settings.output_format}",
            f"model={settings.whisper_model}",
            f"device={settings.whisper_device}",
            f"fp16={'auto' if settings.whisper_fp16 is None else settings.whisper_fp16}",
        )
        run_pipeline(settings)
        log_info("done")
        return 0
    except AppError as exc:
        log_error("error", str(exc))
        return exc.exit_code
    except KeyboardInterrupt:
        log_error("error", "interrupted")
        return 130
    except Exception as exc:
        log_error("error", f"unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
