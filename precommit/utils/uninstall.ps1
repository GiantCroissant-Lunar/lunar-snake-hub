param(
    [string]$HooksTarget = ".git/hooks",
    [string]$BackupDir = ".git/hooks.backup.hub",
    [switch]$Restore
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[hub-precommit] $msg" }

if (!(Test-Path ".git")) { throw "Not a git repository: $(Get-Location)" }

if (Test-Path $HooksTarget) {
    $managed = Get-ChildItem -Path $HooksTarget -File | Where-Object {
        try { Select-String -Path $_.FullName -Pattern "managed-by: lunar-snake-hub" -Quiet } catch { $false }
    }
    foreach ($m in $managed) {
        Write-Info "Removing managed hook: $($m.Name)"
        Remove-Item -Path $m.FullName -Force -ErrorAction SilentlyContinue
    }
}

if ($Restore -and (Test-Path $BackupDir)) {
    Write-Info "Restoring backup hooks from $BackupDir"
    Get-ChildItem -Path $BackupDir -File | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination (Join-Path $HooksTarget $_.Name) -Force
    }
}

# Reset hooksPath if empty and we had set it previously
try {
    $hooksPath = git config --local --get core.hooksPath
    if ($hooksPath) {
        Write-Info "Unsetting core.hooksPath (local)"
        git config --local --unset core.hooksPath
    }
} catch { }

Write-Info "Uninstall complete."
