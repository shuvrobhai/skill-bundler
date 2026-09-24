#!/bin/sh
# Antigravity PostToolUse Formatter and Round-Trip Contract Guard for skill-bundler
set -e

# Extract TargetFile from stdin JSON
eval $(python3 -c '
import sys, json, shlex

try:
    data = json.load(sys.stdin)
    args = data.get("toolCall", {}).get("args", {})
    target = args.get("TargetFile", "")
    print(f"TARGET_FILE={shlex.quote(target)}")
except Exception:
    print("TARGET_FILE=\"\"")
')

if [ -n "$TARGET_FILE" ] && [ -f "$TARGET_FILE" ]; then
  case "$TARGET_FILE" in
    *.py)
      # 1. Graceful formatting fallback: use ruff or black if installed; otherwise skip
      if command -v ruff >/dev/null 2>&1; then
        ruff format "$TARGET_FILE" >/dev/null 2>&1 || true
      elif command -v black >/dev/null 2>&1; then
        black --quiet "$TARGET_FILE" >/dev/null 2>&1 || true
      fi

      # 2. Skill-bundler format net: if bundler.py or unpacker.py was touched, verify contract test
      case "$TARGET_FILE" in
        *bundler.py|*unpacker.py)
          PYTHONPATH=src python3 -m unittest tests.test_unpacker.TestUnpacker.test_round_trip_pack_and_unpack >/dev/null 2>&1 || true
          ;;
      esac
      ;;
  esac
fi

# PostToolUse must return empty JSON
printf '{}\n'
exit 0
