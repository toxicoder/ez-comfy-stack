# Operator laptop bootstrap on Windows. Supported path is WSL2 Ubuntu.
# Native PowerShell does not run manage.sh; this script only installs WSL
# or writes a reminder. Never starts the Spark stack.
#
# Usage:
#   powershell -File scripts/utilities/setup-client.ps1
#   powershell -File scripts/utilities/setup-client.ps1 -HostName 10.0.0.5 -User spark

[CmdletBinding()]
param(
    [string] $HostName = "127.0.0.1",
    [string] $User = "spark",
    [int] $Port = 8188
)

$ErrorActionPreference = "Stop"

function Write-Status([string] $Message) {
    [Console]::Error.WriteLine("setup-client: $Message")
}

$wsl = Get-Command wsl -ErrorAction SilentlyContinue
if ($null -ne $wsl) {
    Write-Status "WSL found - running setup-client.sh inside the default distro"
    $repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    wsl -e bash -lc "cd '$repo' && ./scripts/utilities/setup-client.sh --host $HostName --user $User --port $Port"
    exit $LASTEXITCODE
}

Write-Status "WSL2 is the supported Windows path (bash manage.sh, doctor, setup)."
Write-Status "Install: wsl --install -d Ubuntu   then re-run this script."
Write-Status "Without WSL you still need Git for Windows + OpenSSH, then:"
Write-Status "  ssh -L ${Port}:127.0.0.1:${Port} ${User}@${HostName}"
Write-Status "Never auto-starts Comfy. On the Spark: ./scripts/manage.sh start  # type yes"
exit 1
