# Robonine bench setup

The setup script installs the serial dependency, checks the bundled published v9
image, backs up the connected servo and flashes it. The default setup uses the
published image for FEETECH GD32F130 STS TTL hardware with model bytes 9, 3.

From the repository root on Windows, with Python installed:

```powershell
.\bench\setup.ps1 -Port COM6 -Id 1 -Flash
```

Omit `-Flash` to prepare and check the image without opening the port. Close other
serial apps first. Use stable servo power, isolate the intended motor, and
release torque before flashing. The setup does not initiate a motion test.
The backup and flash report are saved in `bench-local/`.

On macOS or Linux, with Python 3 installed, run `bash bench/setup.sh /dev/ttyUSB0 1`
with your actual device path and ID. Run `bash bench/setup.sh` without arguments
to prepare and check the image offline. See the
[upstream flashing instructions](../tools/flash/README.md) for recovery.

- [Controller configs and test plans](config/) include the original Q8 PID tune
  and the bench gravity model. Port, joint limits, load and encoder calibration
  must match the real setup before running a motion plan.
- [Printable weight-test arm](results/STS3215-weight-test-arm.stl).

- [Bench scripts](scripts/) preserve the experimental analysis and hardware
  harnesses. Some retain the original workspace paths and require adapting those
  paths before rerunning. Use the upstream CLI and configs for portable operation.
- [Firmware images](images/) include the v9 build and the
  experimental adaptive build. The setup script selects only published v9.
  Use the backup from the same physical servo when restoring factory settings.

For tuning and replay, install Node.js 20+ and run `npm ci` in the repository root.
Start with `npm run tune -- inspect bench/config/loaded-replay-250.json` to inspect
the plan offline. The checked-in gravity coefficients describe this bench only.
See the [upstream gravity model guide](../host/arm-control/models/README.md).

## Bench PID and two-joint controller

The validated PID profile is [two-count-profile.json](config/two-count-profile.json).
Its Q8 gains are P 1280, I 768, D 128, with integral effort capped at 28.

The separate [two-joint gravity configuration](config/so101-two-joint-controller.json)
uses zero PID gains for hand-guided testing. The [fixed-tip model](config/so101-two-joint-fixed-tip.json)
assumes a straight rigid tip and needs physical alignment and load validation
before use on a different mechanism. The live harness is
[scripts/two-joint-gravity-live.cjs](scripts/two-joint-gravity-live.cjs).

## Single-motor ring trial

Robonine v9.0 on ID 2 moved 2,909 → 2,961 → 2,909 at 45 counts/s with
the same PID settings. The load was a half-pound ring attached to the
original printed test arm. Each column shows one run.

| Metric (encoder counts) | Gravity comp off | Gravity comp on |
|---|---:|---:|
| Lift tracking RMS error | 9.33 | 7.05 |
| Lift settled error | 9 | 3 |
| Return tracking RMS error | 6.51 | 8.84 |
| Return settled error | 4 | 4 |

The [provisional ring model](config/gravity-half-pound-ring-model.json)
uses a 2,904-count horizontal reference and approximately 29 PWM effort
units from three paired measurements near one angle. Recalibrate after
changing the load or mounting. The [trial script](scripts/ring-directional-ab.cjs)
commands motion and assumes the tested COM6 fixture, motor ID and clear travel.
