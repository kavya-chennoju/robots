# LeKiwi × Device Connect — run & drive over a remote tenant

Run a LeKiwi (or any strands-robots robot) as a **Device Connect** device that
registers with a **remote** Device Connect deployment over **mTLS**, then send it
movement commands from anywhere on the same tenant.

Validated against tenant `beta` at `137.184.86.16` (registry `:8080`, Zenoh
router `zenoh+tls://137.184.86.16:7447`).

```
operator (move.py) ──invoke execute()──► Zenoh router (mTLS) ──► LeKiwi device (run_device.sh)
                                          137.184.86.16:7447         registers as <device_id> on tenant `beta`
```

## 0. Prerequisites

- **Python 3.12+** (strands-robots requires it; Raspberry Pi OS ships 3.11 — install 3.12 via [`uv`](https://docs.astral.sh/uv/) or pyenv if needed).
- Your **device credential bundle**, e.g. `beta-kavya-lekiwi.creds.json` — a self-contained mTLS cert/key + CA + tenant + device_id. **It holds a private key. Keep it secret; it is gitignored here. Never commit it.**

## 1. Install (on the LeKiwi)

```bash
git clone --branch lekiwi-device-connect-example https://github.com/kavya-chennoju/robots.git
cd robots
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e .            # strands-robots + device-connect-edge + device-connect-agent-tools
```
> If `device-connect-edge` / `device-connect-agent-tools` aren't on your PyPI, install from the
> `arm/device-connect` source instead:
> ```bash
> pip install -e /path/to/device-connect/packages/device-connect-edge
> pip install -e '/path/to/device-connect/packages/device-connect-agent-tools[strands]'
> ```
> For **real hardware**, also install LeRobot's LeKiwi stack (motors/base/cameras) per the LeRobot LeKiwi docs.

## 2. Drop in your credentials

```bash
cp ~/beta-kavya-lekiwi.creds.json examples/lekiwi_device_connect/   # gitignored
# …or point at it from anywhere:
export MESSAGING_CREDENTIALS_FILE=/abs/path/to/your.creds.json
```

## 3. Run the device (on the LeKiwi)

```bash
cd examples/lekiwi_device_connect
MODE=real ./run_device.sh          # drives the hardware;  MODE=sim runs MuJoCo (safe)
```
Expect:
```
Connected to ZENOH broker: ['zenoh+tls://137.184.86.16:7447']
Device registered: registration_id=...
```
`device_id` and `tenant` come from the bundle automatically; `peer_id` matches the cert.

## 4. Make it move (from any machine on the tenant)

```bash
export MESSAGING_CREDENTIALS_FILE=/abs/path/to/a-tenant-credential.creds.json
# mock = canned motion (motors move, ignores the instruction) — best first test:
python move.py --instruction "drive forward" --policy-provider mock --duration 5
# real instruction-following needs a trained policy:
python move.py --instruction "drive to the door" --policy-provider lerobot_local --duration 10
```
`--target` defaults to the `device_id` in your bundle; pass it explicitly to address another device.

| `policy_provider` | Behavior |
|---|---|
| `mock` | Canned sinusoidal actions — motors **move**, but the instruction is ignored. Quickest "does it drive?" check. |
| `lerobot_local` | Trained LeRobot policy on the Pi (needs a checkpoint + torch/lerobot) — follows the instruction. |
| `groot` | NVIDIA GR00T (ZMQ policy server or local GPU) — follows the instruction. |

## 5. Emergency stop

```bash
python emergency_stop.py           # stops every device on the tenant
```

## ⚠️ Safety
Real motion — clear the area, keep the base away from table edges, and keep
`emergency_stop.py` ready before you send a command.

## How it works
`run_device.sh` exports `MESSAGING_CREDENTIALS_FILE` and runs
`Robot("lekiwi", mode="real", peer_id=<device_id>).run()`. The `device-connect-edge`
runtime reads the broker URL, mTLS cert/key/CA, tenant and device id **straight from
the self-contained bundle** (base64 into the Zenoh config — nothing touches disk),
connects to the remote router and registers. `move.py` calls the device's
`execute(instruction, policy_provider, duration, robot_name)` RPC.
