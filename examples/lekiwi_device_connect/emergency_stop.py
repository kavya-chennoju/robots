#!/usr/bin/env python3
"""Emergency-stop every Device Connect device on the tenant.

Point MESSAGING_CREDENTIALS_FILE at a tenant credential bundle first.

    MESSAGING_CREDENTIALS_FILE=./beta-kavya-lekiwi.creds.json python emergency_stop.py
"""
from __future__ import annotations

import sys


def main() -> int:
    from device_connect_agent_tools import connect, get_connection

    connect()
    conn = get_connection()
    devices = conn.list_devices()
    stopped = 0
    for d in devices:
        try:
            conn.invoke(d["device_id"], "stop", timeout=3.0)
            stopped += 1
        except Exception as exc:  # noqa: BLE001 — best-effort fan-out
            print(f"  {d.get('device_id', '?')}: {exc}", file=sys.stderr)
    print(f"E-STOP: {stopped}/{len(devices)} devices stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
