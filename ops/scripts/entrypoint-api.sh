# ops/scripts/entrypoint-api.sh
#!/usr/bin/env bash
set -Eeuo pipefail

export PYTHONUNBUFFERED=1

# Ensure shared IO paths exist (and respect env overrides)
: "${UPLOAD_DIR:=/shared/in}"
: "${OUTPUT_DIR:=/shared/out}"
mkdir -p "$UPLOAD_DIR" "$OUTPUT_DIR"

echo "[api] starting uvicorn at 0.0.0.0:8000"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
