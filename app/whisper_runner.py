from __future__ import annotations

import subprocess
from pathlib import Path

from app.config import Settings
from app.errors import WhisperFailedError
from app.log import log_info


_CUDA_FP16_FORCE_FP32 = False


def run_whisper_txt(*, input_path: Path, output_dir: Path, settings: Settings) -> None:
    expected_txt_path = output_dir / f"{input_path.stem}.txt"

    def _build_cmd(*, fp16: bool | None) -> list[str]:
        cmd: list[str] = [
        "whisper",
        str(input_path),
        "--model",
        settings.whisper_model,
        "--model_dir",
        str(settings.model_dir),
        "--output_dir",
        str(output_dir),
        "--output_format",
        "txt",
        "--task",
        settings.whisper_task,
        "--device",
        settings.whisper_device,
        "--verbose",
        "True" if settings.verbose else "False",
        ]

        resolved_fp16 = fp16
        if settings.whisper_device == "cpu":
            resolved_fp16 = False
        if resolved_fp16 is not None:
            cmd += ["--fp16", "True" if resolved_fp16 else "False"]

        if settings.whisper_language is not None:
            cmd += ["--language", settings.whisper_language]

        if settings.threads is not None:
            cmd += ["--threads", str(settings.threads)]

        return cmd

    def _run_once(*, fp16: bool | None) -> tuple[int, str]:
        cmd = _build_cmd(fp16=fp16)
        if settings.verbose:
            proc = subprocess.run(cmd, check=False)
            return proc.returncode, ""

        proc = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return proc.returncode, (proc.stdout or "")

    def _raise_failed(*, exit_code: int, output: str) -> None:
        out = output.strip()
        tail = "\n".join(out.splitlines()[-50:]) if out else ""
        detail = f"\n{tail}" if tail else ""
        hint = ""
        if settings.whisper_device == "cuda":
            hint = "\nHint: try setting WHISPER_FP16=0 (some GPUs/drivers produce NaNs with fp16)."
        raise WhisperFailedError(f"whisper failed for {input_path} (exit={exit_code}){detail}{hint}")

    def _raise_no_output(*, output: str) -> None:
        out = output.strip()
        tail = "\n".join(out.splitlines()[-50:]) if out else ""
        detail = f"\n{tail}" if tail else ""
        hint = ""
        if settings.whisper_device == "cuda":
            hint = "\nHint: try setting WHISPER_FP16=0 (some GPUs/drivers produce NaNs with fp16)."
        raise WhisperFailedError(
            f"whisper produced no output for {input_path} (expected: {expected_txt_path}){detail}{hint}"
        )

    global _CUDA_FP16_FORCE_FP32

    if settings.whisper_device == "cuda" and settings.whisper_fp16 is None and _CUDA_FP16_FORCE_FP32:
        initial_fp16 = False
    else:
        initial_fp16 = settings.whisper_fp16 if settings.whisper_device == "cuda" else False

    exit_code, output = _run_once(fp16=initial_fp16)
    if exit_code != 0:
        _raise_failed(exit_code=exit_code, output=output)

    if expected_txt_path.exists():
        return

    if settings.whisper_device == "cuda" and settings.whisper_fp16 is None:
        log_info("retry", f"fp16=0 for {input_path.name} (fallback: no output produced on cuda)")
        exit_code2, output2 = _run_once(fp16=False)
        if exit_code2 != 0:
            _raise_failed(exit_code=exit_code2, output=output2)
        if expected_txt_path.exists():
            _CUDA_FP16_FORCE_FP32 = True
            return
        _raise_no_output(output=output2)

    _raise_no_output(output=output)
