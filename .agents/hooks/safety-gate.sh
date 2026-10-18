#!/bin/sh
# Antigravity PreToolUse Safety Gate for bundium
set -e

# Read stdin JSON payload via embedded python3
eval $(python3 -c '
import sys, json, shlex

try:
    data = json.load(sys.stdin)
    tool_call = data.get("toolCall", {})
    name = tool_call.get("name", "")
    cmd = tool_call.get("args", {}).get("CommandLine", "")
    print(f"TOOL_NAME={shlex.quote(name)}")
    print(f"COMMAND_LINE={shlex.quote(cmd)}")
except Exception:
    print("TOOL_NAME=\"\"")
    print("COMMAND_LINE=\"\"")
')

if [ "$TOOL_NAME" = "run_command" ]; then
  case "$COMMAND_LINE" in
    *git\ push*--force*|*git\ push*-f*|*git\ reset\ --hard*|*git\ clean*-fd*|*rm\ -rf\ /*|*rm\ -rf\ ~*|*rm\ -rf\ \.\.*)
      printf '{"decision":"ask","reason":"⚠️ High-risk command detected: %s. Please confirm execution."}\n' "$COMMAND_LINE"
      exit 0
      ;;
  esac
fi

# Allow safe commands automatically
printf '{"decision":"allow"}\n'
exit 0
