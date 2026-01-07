from __future__ import annotations

import subprocess
from pathlib import Path

from app.config import Settings
from app.errors import WhisperFailedError


def run_whisper_txt(*, input_path: Path, output_dir: Path, settings: Settings) -> None:
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

    if settings.whisper_language is not None:
        cmd += ["--language", settings.whisper_language]

    if settings.threads is not None:
        cmd += ["--threads", str(settings.threads)]

    if settings.whisper_device == "cpu":
        cmd += ["--fp16", "False"]

    if settings.verbose:
        proc = subprocess.run(cmd, check=False)
        if proc.returncode != 0:
            raise WhisperFailedError(f"whisper failed for {input_path} (exit={proc.returncode})")
        return

    proc = subprocess.run(
        cmd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if proc.returncode != 0:
        output = (proc.stdout or "").strip()
        tail = "\n".join(output.splitlines()[-50:]) if output else ""
        detail = f"\n{tail}" if tail else ""
        raise WhisperFailedError(f"whisper failed for {input_path} (exit={proc.returncode}){detail}")
