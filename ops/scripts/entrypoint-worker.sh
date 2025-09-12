# ops/scripts/entrypoint-worker.sh
#!/usr/bin/env bash
set -Eeuo pipefail

export PYTHONUNBUFFERED=1

# Display & addon settings (override via env if needed)
: "${ADDON_MODULE:=BlendArMocap}"
: "${BLENDER_ADDON_SCRIPT:=/opt/addons/BlendArMocap/addon_script.py}"
: "${DISPLAY_W:=1920}"
: "${DISPLAY_H:=1080}"
: "${DISPLAY_D:=24}"

# IO paths
: "${UPLOAD_DIR:=/shared/in}"
: "${OUTPUT_DIR:=/shared/out}"
mkdir -p "$UPLOAD_DIR" "$OUTPUT_DIR"

# Helper to run blender under a virtual display so GUI-only context exists
run_blender() {
  xvfb-run -s "-screen 0 ${DISPLAY_W}x${DISPLAY_H}x${DISPLAY_D}" \
    blender --factory-startup \
            --addons "$ADDON_MODULE" \
            --python "$BLENDER_ADDON_SCRIPT" -- "$@"
}

# Modes:
# 1) Explicit single job: entrypoint-worker.sh run <args passed to addon_script.py>
# 2) Batch over files in $UPLOAD_DIR (default): calls addon once per file, then exits
case "${1:-}" in
  run)
    shift
    echo "[worker] running single job via $BLENDER_ADDON_SCRIPT -- $*"
    exec run_blender "$@"
    ;;
  *)
    echo "[worker] batch mode: scanning $UPLOAD_DIR"
    shopt -s nullglob
    for f in "$UPLOAD_DIR"/*; do
      echo "[worker] processing $(basename "$f")"
      run_blender "$(basename "$f")" "$f"
    done
    echo "[worker] done."
    ;;
esac
