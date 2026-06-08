#!/usr/bin/env python3
"""Tell a strands-robots Device Connect device to execute an instruction (move it).

Calls the device's ``execute(instruction, policy_provider, duration, robot_name)``
RPC over Device Connect.

Connect to the tenant first by pointing MESSAGING_CREDENTIALS_FILE at a tenant
credential bundle (the device bundle works for a quick test; for real ops mint a
separate operator credential from the portal).

Examples:
    # mock = canned motion (motors move, ignores the instruction) — first test
    MESSAGING_CREDENTIALS_FILE=./beta-kavya-lekiwi.creds.json \\
        python move.py --instruction "drive forward" --policy-provider mock --duration 5

    # instruction-following needs a trained policy
    python move.py --instruction "drive to the door" --policy-provider lerobot_local --duration 10
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def _default_target() -> str | None:
    """Default the target to the device_id in the creds bundle, if present."""
    cf = os.environ.get("MESSAGING_CREDENTIALS_FILE")
    if cf and os.path.exists(cf):
        try:
            with open(cf) as f:
                return json.load(f).get("device_id")
        except Exception:
            return None
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", default=_default_target(),
                    help="device id to command (default: the creds bundle's device_id)")
    ap.add_argument("--instruction", default="drive forward")
    ap.add_argument("--policy-provider", default="mock", choices=["mock", "lerobot_local", "groot"])
    ap.add_argument("--duration", type=float, default=5.0)
    ap.add_argument("--robot-name", default="", help="robot within the device (empty = first/only)")
    a = ap.parse_args()

    if not a.target:
        print("error: no --target and no device_id in MESSAGING_CREDENTIALS_FILE", file=sys.stderr)
        return 2

    from device_connect_agent_tools import connect, invoke_device

    connect()
    print(f"-> {a.target}: {a.instruction}  (policy={a.policy_provider}, duration={a.duration}s)")
    result = invoke_device(a.target, "execute", {
        "instruction": a.instruction,
        "policy_provider": a.policy_provider,
        "duration": a.duration,
        "robot_name": a.robot_name,
    })
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
