from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Download an openai-whisper model into a directory.")
    parser.add_argument("--model", default="turbo", help="e.g. turbo, large-v3-turbo, small, base, ...")
    parser.add_argument("--model-dir", default="/models", help="directory to place the .pt file")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    import whisper  # type: ignore

    whisper.load_model(args.model, download_root=str(model_dir))

    models = getattr(whisper, "_MODELS", {})
    url = models.get(args.model)
    if isinstance(url, str) and url:
        expected = url.split("/")[-1]
        expected_path = model_dir / expected
        if expected_path.exists():
            print(f"downloaded: {expected_path}")
        else:
            print("downloaded, but expected file not found at:", expected_path)
    else:
        print("downloaded model:", args.model)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
