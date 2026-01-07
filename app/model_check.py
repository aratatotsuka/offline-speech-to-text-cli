from __future__ import annotations

from pathlib import Path

from app.errors import ModelNotFoundError


def _is_probable_path(value: str) -> bool:
    return value.endswith(".pt") or value.startswith("/") or value.startswith("./") or value.startswith("../")


def ensure_model_present(*, model: str, model_dir: Path, require: bool) -> None:
    if not require:
        return

    # 1) Direct path (absolute/relative) support (whisper.load_model accepts file path)
    model_path = Path(model)
    if model_path.is_file():
        return

    # 2) Model file directly under MODEL_DIR (e.g., large-v3-turbo.pt)
    if _is_probable_path(model):
        candidate = model_dir / model
        if candidate.is_file():
            return

    # 3) Use openai-whisper's mapping to get the expected checkpoint filename.
    expected_filenames: list[str] = []
    try:
        import whisper  # type: ignore

        models = getattr(whisper, "_MODELS", {})
        url = models.get(model)
        if isinstance(url, str) and url:
            expected = url.split("/")[-1]
            expected_filenames.append(expected)
            if (model_dir / expected).is_file():
                return
            for p in model_dir.rglob(expected):
                if p.is_file():
                    return
    except Exception:
        pass

    # 4) Fallback: common convention {model}.pt
    fallback = f"{model}.pt"
    expected_filenames.append(fallback)
    if (model_dir / fallback).is_file():
        return
    for p in model_dir.rglob(fallback):
        if p.is_file():
            return

    uniq = sorted(set(expected_filenames))
    hint = ", ".join(uniq)
    raise ModelNotFoundError(
        f"required model not found in {model_dir} for WHISPER_MODEL={model!r}. "
        f"Place the checkpoint file (e.g. {hint}) under MODEL_DIR, or set REQUIRE_MODELS_PRESENT=0."
    )
