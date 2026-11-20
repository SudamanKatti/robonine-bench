#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
if (( $# != 0 && $# != 2 )); then
    echo 'Usage: bash bench/setup.sh [PORT ID]' >&2
    exit 2
fi
[[ -x .bench-venv/bin/python ]] || python3 -m venv .bench-venv
py=.bench-venv/bin/python
if ! "$py" -c 'import serial' 2>/dev/null; then
    "$py" -m pip install -r tools/flash/requirements.txt
fi
manifest=bench/images/custom-v9-e44c0e6/release.json
"$py" tools/flash/flash.py inspect --manifest "$manifest"
if (( $# == 0 )); then
    echo 'Ready. Pass the serial port and servo ID to back up and flash.'
    exit 0
fi
mkdir -p bench-local
dir=$(mktemp -d bench-local/setup.XXXXXXXX)
"$py" tools/flash/settings.py backup --port "$1" --id "$2" --file "$dir/servo-settings.json" --output "$dir/backup"
"$py" tools/flash/flash.py flash --manifest "$manifest" --port "$1" --id "$2" --output "$dir/flash" --yes
printf 'Robonine v9 installed. Settings backup: %s/servo-settings.json\n' "$dir"
