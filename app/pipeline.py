from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.diarization import run_diarization_pipeline
from app.docx_writer import txt_to_docx
from app.errors import ConfigError, DocxConversionError, ModelNotFoundError, NoInputFilesError, WhisperFailedError
from app.file_scan import scan_media_files
from app.log import log_info
from app.model_check import ensure_model_present
from app.whisper_runner import run_whisper_txt


def _ensure_dirs(settings: Settings) -> None:
    if not settings.input_dir.exists() or not settings.input_dir.is_dir():
        raise ConfigError(f"INPUT_DIR not found or not a directory: {settings.input_dir}")

    settings.output_dir.mkdir(parents=True, exist_ok=True)

    if settings.require_models_present:
        if not settings.model_dir.exists() or not settings.model_dir.is_dir():
            raise ModelNotFoundError(
                f"MODEL_DIR not found or not a directory: {settings.model_dir} (set REQUIRE_MODELS_PRESENT=0 to allow downloads)"
            )


def run_pipeline(settings: Settings) -> None:
    _ensure_dirs(settings)

    if settings.diarization:
        run_diarization_pipeline()
        return

    ensure_model_present(
        model=settings.whisper_model,
        model_dir=settings.model_dir,
        require=settings.require_models_present,
    )

    media_files = scan_media_files(settings.input_dir)
    if not media_files:
        raise NoInputFilesError(f"no input media files found under {settings.input_dir}")

    whisper_failures: list[str] = []
    docx_failures: list[str] = []

    for src in media_files:
        rel = src.relative_to(settings.input_dir)
        out_dir = settings.output_dir / rel.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        txt_path = out_dir / f"{src.stem}.txt"
        docx_path = out_dir / f"{src.stem}.docx"
        final_path = docx_path if settings.output_format == "docx" else txt_path

        if final_path.exists() and not settings.overwrite:
            log_info("skip", f"exists: {final_path}")
            continue

        log_info("file", str(rel))

        try:
            run_whisper_txt(
                input_path=src,
                output_dir=out_dir,
                settings=settings,
            )
        except WhisperFailedError as exc:
            whisper_failures.append(f"{rel}: {exc}")
            continue

        if settings.output_format == "docx":
            try:
                txt_to_docx(txt_path=txt_path, docx_path=docx_path, title=src.name)
                if not settings.keep_intermediate:
                    try:
                        txt_path.unlink(missing_ok=True)
                    except Exception as exc:
                        raise DocxConversionError(f"failed to remove intermediate txt: {txt_path} ({exc})")
            except DocxConversionError as exc:
                docx_failures.append(f"{rel}: {exc}")
                continue
            except Exception as exc:
                docx_failures.append(f"{rel}: docx conversion failed: {exc}")
                continue

    if whisper_failures:
        message = "some files failed (whisper):\n" + "\n".join(whisper_failures)
        if docx_failures:
            message += "\n\nsome files also failed (docx):\n" + "\n".join(docx_failures)
        raise WhisperFailedError(message)

    if docx_failures:
        raise DocxConversionError("some files failed (docx):\n" + "\n".join(docx_failures))
