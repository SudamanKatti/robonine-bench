[CmdletBinding()]
param(
    [string]$Port = 'COM6',
    [ValidateRange(0,253)][int]$Id = 1,
    [switch]$Flash
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $venv = '.bench-venv'
    $python = Join-Path $venv 'Scripts/python.exe'
    if (!(Test-Path $python)) {
        if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 -m venv $venv }
        else { & python -m venv $venv }
        if ($LASTEXITCODE) { throw 'Could not create the Python environment.' }
    }
    & $python -c 'import serial' 2>$null
    if ($LASTEXITCODE) {
        & $python -m pip install -r tools/flash/requirements.txt
        if ($LASTEXITCODE) { throw 'Could not install the serial dependency.' }
    }
    $manifest = 'bench/images/custom-v9-e44c0e6/release.json'
    & $python tools/flash/flash.py inspect --manifest $manifest
    if ($LASTEXITCODE) { throw 'Firmware image validation failed.' }
    if (!$Flash) {
        Write-Output 'Ready. Specify -Flash -Port COMx -Id 1 to back up and install Robonine v9.'
        return
    }
    $dir = 'bench-local'
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmssfff'
    $backup = Join-Path $dir "servo-$Id-$stamp.json"
    & $python tools/flash/settings.py backup --port $Port --id $Id --file $backup --output (Join-Path $dir "backup-$stamp")
    if ($LASTEXITCODE) { throw 'Could not back up the connected servo.' }
    & $python tools/flash/flash.py flash --manifest $manifest --port $Port --id $Id --output (Join-Path $dir "flash-$stamp") --yes
    if ($LASTEXITCODE) { throw 'Flash failed. Keep the backup and check the flash report before retrying.' }
    Write-Output "Robonine v9 installed and application checks passed. Settings backup: $backup"
} finally {
    Pop-Location
}
