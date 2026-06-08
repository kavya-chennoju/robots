#!/usr/bin/env bash
# Run a LeKiwi (or any strands-robots robot) as a Device Connect device.
#
#   • If a creds bundle is found (MESSAGING_CREDENTIALS_FILE, or the first
#     *.creds.json in this directory), the device connects to your REMOTE
#     Device Connect tenant over mTLS. The peer_id (device id) and tenant are
#     taken straight from the bundle — nothing is written to disk.
#   • With no creds bundle, it falls back to LOCAL D2D mode (Zenoh multicast)
#     so you can test on a laptop without infrastructure.
#
# Env knobs:
#   ROBOT=lekiwi     robot model from the registry
#   MODE=real        'real' drives the hardware; 'sim' runs MuJoCo (safe)
#   PEER_ID=...      override the device id (defaults to the bundle's device_id)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

ROBOT="${ROBOT:-lekiwi}"
MODE="${MODE:-real}"

CREDS="${MESSAGING_CREDENTIALS_FILE:-}"
if [ -z "$CREDS" ]; then
  CREDS="$(ls "$HERE"/*.creds.json 2>/dev/null | head -1 || true)"
fi

if [ -n "$CREDS" ] && [ -f "$CREDS" ]; then
  export MESSAGING_CREDENTIALS_FILE="$CREDS"
  export DEVICE_CONNECT_ALLOW_INSECURE=false       # enforce mTLS
  export MESSAGING_BACKEND=zenoh
  PEER_ID="${PEER_ID:-$(python3 -c "import json;print(json.load(open('$CREDS'))['device_id'])")}"
  echo "[run_device] REMOTE mTLS via $(basename "$CREDS")  (device_id=$PEER_ID, robot=$ROBOT, mode=$MODE)"
else
  PEER_ID="${PEER_ID:-$ROBOT-$(python3 -c "import os;print(os.urandom(3).hex())")}"
  echo "[run_device] no creds bundle found -> LOCAL D2D mode  (peer_id=$PEER_ID, robot=$ROBOT, mode=$MODE)"
  echo "             drop your *.creds.json in $HERE to connect to the remote tenant."
fi

exec python3 -u -c "
from strands_robots import Robot
r = Robot('$ROBOT', mode='$MODE', peer_id='$PEER_ID')
r.run()
"
