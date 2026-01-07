from __future__ import annotations

import sys

from app.config import Settings
from app.errors import AppError
from app.log import log_error, log_info


def _print_help() -> None:
    print(
        "\n".join(
            [
                "local-transcription (container entrypoint)",
                "",
                "This container is configured via environment variables.",
                "See README.md for full usage and docker run examples (offline: --network none).",
                "",
                "Key env vars:",
                "  INPUT_DIR=/data/input",
                "  OUTPUT_DIR=/data/output",
                "  OUTPUT_FORMAT=txt|docx",
                "  WHISPER_MODEL=turbo",
                "  MODEL_DIR=/models",
                "  REQUIRE_MODELS_PRESENT=1",
                "  DIARIZATION=0",
            ]
        )
    )


def main(argv: list[str]) -> int:
    if any(arg in ("-h", "--help") for arg in argv):
        _print_help()
        return 0

    try:
        settings = Settings.from_env()
        from app.pipeline import run_pipeline

        log_info(
            "start",
            f"input_dir={settings.input_dir}",
            f"output_dir={settings.output_dir}",
            f"output_format={settings.output_format}",
            f"model={settings.whisper_model}",
            f"device={settings.whisper_device}",
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
