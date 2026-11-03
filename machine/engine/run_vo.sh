#!/bin/bash
# One time-boxed, resumable voice chunk. usage: run_vo.sh <episode_dir> [budget_secs]
# exit 0 = all lines done, 3 = run again, 4 = another heavy job holds the lock.
set -u; HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(cd "$HERE/../.." && pwd)"
CACHE="${WIS_CACHE:-$HOME/.wisdrop}"; mkdir -p "$CACHE"
export HF_HOME="${HF_HOME:-$CACHE/hf}" HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}" PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false MALLOC_ARENA_MAX=2
PY="${WIS_VOICE_PY:-$CACHE/venv_cb/bin/python}"
exec 9>"$CACHE/.heavy.lock"; flock -n 9 2>/dev/null || { command -v flock >/dev/null && { echo "another heavy job is running"; exit 4; }; }
"$PY" "$HERE/vo_runner.py" "$1" --budget "${2:-1080}" >> "$1/vo_run.log" 2>&1
rc=$?; echo "chunk exit $rc"; tail -20 "$1/vo_run.log"; exit $rc
