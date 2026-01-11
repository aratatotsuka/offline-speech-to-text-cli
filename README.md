# local-transcription (Whisper / Offline-ready)

Dockerコンテナ内で `openai-whisper` のCLI `whisper` をローカル実行し、マウントした音声・動画ファイルを一括で文字起こしして出力します。  
実行時は外部ネットワークへ接続しない前提のため、READMEの実行例はすべて `--network none` を使用します。

## Features

- 入力ディレクトリ配下を再帰的に走査して一括処理
- 音声/動画を対象（`ffmpeg` 同梱。`ffmpeg` が読める形式なら処理対象）
- 出力形式: `txt` / `docx`（デフォルト `txt`）
- オフライン運用前提: `MODEL_DIR` を常に `whisper --model_dir` に指定
- モデル未配置時に **ダウンロードを試みず即エラー**（`REQUIRE_MODELS_PRESENT=1` がデフォルト）

## Quickstart

### 1) Build

```bash
docker build -t whisper-local:latest .
```

### 2) Prepare models (one-time)

実行時は `--network none` 前提のため、Whisperモデルは事前に `/models` 相当へ配置してください。

#### Option A: ホスト側で事前に用意（推奨）

- Whisperの `.pt` を `WHISPER_MODEL` に対応するファイル名で `models/` に配置して、実行時にマウントします。

#### Option B: コンテナでダウンロードしてホストへ保存（ネットワークが使える環境のみ）

```bash
mkdir -p ./models
docker run --rm \
  -v "$(pwd)/models:/models" \
  whisper-local:latest \
  python /app/scripts/download_model.py --model turbo --model-dir /models
```

ダウンロード後、オフライン実行では `-v /host/models:/models:ro` のようにマウントします。

### 3) Run (offline, network disabled)

#### txtで実行（必須例: `--network none`）

```bash
docker run --rm --network none \
  -v /host/media:/data/input:ro \
  -v /host/out:/data/output \
  -v /host/models:/models:ro \
  -e OUTPUT_FORMAT=txt \
  -e DIARIZATION=0 \
  whisper-local:latest
```

#### docxで実行

```bash
docker run --rm --network none \
  -v /host/media:/data/input:ro \
  -v /host/out:/data/output \
  -v /host/models:/models:ro \
  -e OUTPUT_FORMAT=docx \
  -e DIARIZATION=0 \
  whisper-local:latest
```

#### CPUで明示的に実行（`--device cpu`）

```bash
docker run --rm --network none \
  -v /host/media:/data/input:ro \
  -v /host/out:/data/output \
  -v /host/models:/models:ro \
  whisper-local:latest --device cpu
```

#### GPUで実行（`--device cuda` + `--gpus all`）

```bash
docker run --rm --network none --gpus all \
  -v /host/media:/data/input:ro \
  -v /host/out:/data/output \
  -v /host/models:/models:ro \
  whisper-local:latest --device cuda
```

`--device` の優先順位:

1. 起動引数 `--device`
2. 環境変数 `WHISPER_DEVICE`
3. デフォルト `cpu`

※ `--device cuda`（または `WHISPER_DEVICE=cuda`）を指定したのにGPUが見えない場合、**CPUへ黙ってフォールバックせずエラーで終了**します。  
GPU実行には `--gpus all` の指定と、ホスト側の NVIDIA driver / NVIDIA Container Toolkit が必要です。

## docker-compose example (offline)

`docker-compose.yml` は `network_mode: "none"` を指定しています。

```bash
docker compose build
docker compose run --rm whisper
```

## docker-compose example (GPU, offline)

`docker-compose.gpu.yml` はGPU予約（`deploy.resources.reservations.devices`）と `--device cuda` を指定しています。

```bash
docker compose -f docker-compose.gpu.yml build
docker compose -f docker-compose.gpu.yml run --rm whisper
```

※ `deploy` セクションは Compose の実装/バージョン差で無視される場合があります（特に非Swarm運用）。  
GPUが認識されない場合は `docker run --gpus all ...` の例で実行してください。

## Configuration (Environment Variables)

| Name | Default | Description |
|---|---:|---|
| `INPUT_DIR` | `/data/input` | 入力ディレクトリ（再帰走査） |
| `OUTPUT_DIR` | `/data/output` | 出力ディレクトリ |
| `OUTPUT_FORMAT` | `txt` | `txt` or `docx` |
| `WHISPER_MODEL` | `turbo` | 例: `turbo`, `large-v3-turbo`, `small`, `base`, ... |
| `WHISPER_LANGUAGE` | `auto` | `auto` の場合は `--language` を指定しない（自動判定） |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` |
| `WHISPER_FP16` | `auto` | `auto`（デフォルト）/ `0`でfp16無効（GPUのNaN回避） |
| `WHISPER_TASK` | `transcribe` | `transcribe` or `translate` |
| `MODEL_DIR` | `/models` | Whisperモデル格納先（常に `whisper --model_dir` に指定） |
| `REQUIRE_MODELS_PRESENT` | `1` | `1` の場合、モデル未配置ならダウンロードせず即エラー |
| `DIARIZATION` | `0` | `0`のみサポート（`1`は後述） |
| `THREADS` | (empty) | `whisper --threads` に渡す（CPU推奨。未指定ならWhisper側のデフォルト） |
| `VERBOSE` | `0` | `1`で `whisper` の標準出力をそのまま表示 |
| `OVERWRITE` | `0` | `1`で既存の出力を上書き |
| `KEEP_INTERMEDIATE` | `0` | `OUTPUT_FORMAT=docx` のとき `1`で中間 `.txt` を残す |

## Output spec

- `DIARIZATION=0`
  - `txt`: Whisperの文字起こし本文のみ（`.txt`）
  - `docx`: 見出しにファイル名、本文に全文（1ファイル=1docx）

## Bundling models into the image (optional)

`/models` は **マウント運用** を推奨しますが、イメージへ同梱することもできます。

1. `models/` に `.pt` を配置（例: `models/large-v3-turbo.pt`）
2. `.dockerignore` から `models/` を除外しないよう調整
3. `Dockerfile` に `COPY models /models` を追加

## DIARIZATION=1 (strategy / current behavior)

このリポジトリは **デフォルトでは `DIARIZATION=1` を未サポート** とし、指定された場合は分かりやすいエラーで終了します。

実装戦略（将来拡張）:

- バックエンド候補: `whisperx` + `pyannote.audio` によるspeaker diarization
- 運用方針: diarization用モデルを `MODEL_DIR` 配下へ事前配置し、実行時はネットワーク無しで完結
- モデル/依存が不足している場合: ダウンロードを試みず、**明示エラーで停止**（オフラインで“取りに行って落ちる”を防止）

## Troubleshooting

- `MODEL_DIR` にモデルが無い: `REQUIRE_MODELS_PRESENT=1`（デフォルト）では即エラーになります。モデルを配置してから再実行してください。
- `--device cuda` / `WHISPER_DEVICE=cuda` なのにGPUが使えない: `docker run --gpus all ...` を指定し、ホスト側の NVIDIA driver / NVIDIA Container Toolkit を確認してください（CPUで良ければ `--device cpu` / `WHISPER_DEVICE=cpu`）。
- GPUで `tensor([[nan, ...` / `Expected parameter logits ...` などが出て出力されない: `WHISPER_FP16=0` を指定してfp16を無効化してください
- `Permission denied` で `OUTPUT_DIR` に書けない: ホスト側のディレクトリ権限を確認し、必要なら `docker run --user` を指定してください。

## Exit codes

- `0`: success
- `2`: invalid configuration (`INPUT_DIR` など, `--device cuda` なのにGPUが使えない等)
- `3`: no input files found
- `4`: model not found in `MODEL_DIR` (`REQUIRE_MODELS_PRESENT=1`)
- `5`: whisper execution failed (some files failed)
- `6`: docx conversion failed (some files failed)
- `10`: diarization requested but not supported
