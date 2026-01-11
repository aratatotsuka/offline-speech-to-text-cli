#!/usr/bin/env bash
set -euo pipefail

_err() {
  echo "error: $*" >&2
}

# Default: run the local-transcription app (configured via env vars).
if [[ $# -eq 0 ]]; then
  exec python -m app
fi

# If the first arg doesn't look like an option for this container, treat args as a command
# (so `docker run ... python -c ...` works).
case "$1" in
  -h|--help|--device|--device=*|-*)
    ;;
  *)
    exec "$@"
    ;;
esac

device_override=""
declare -a passthrough=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --device)
      if [[ $# -lt 2 ]]; then
        _err "--device requires a value (cpu|cuda)"
        exit 2
      fi
      device_override="$2"
      shift 2
      ;;
    --device=*)
      device_override="${1#--device=}"
      shift
      ;;
    -h|--help)
      passthrough+=("$1")
      shift
      ;;
    *)
      passthrough+=("$1")
      shift
      ;;
  esac
done

if [[ -n "$device_override" ]]; then
  case "${device_override,,}" in
    cpu|cuda)
      export WHISPER_DEVICE="${device_override,,}"
      ;;
    *)
      _err "invalid --device value: ${device_override} (expected cpu|cuda)"
      exit 2
      ;;
  esac
fi

exec python -m app "${passthrough[@]}"
