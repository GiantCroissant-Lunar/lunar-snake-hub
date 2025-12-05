# Ensures pre-commit hooks from this repo are installed into the current git repo.
param(
    [string]$HooksSource = "precommit/hooks",
    [string]$HooksTarget = ".git/hooks",
    [string]$BackupDir = ".git/hooks.backup.hub",
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[hub-precommit] $msg" }

if (!(Test-Path ".git")) { throw "Not a git repository: $(Get-Location)" }

if (!(Test-Path $HooksTarget)) {
    Write-Info "Creating $HooksTarget"
    New-Item -ItemType Directory -Force -Path $HooksTarget | Out-Null
}

# Prepare backup directory for existing hooks
if (!(Test-Path $BackupDir)) {
    Write-Info "Creating backup dir $BackupDir"
    New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
}

if (!(Test-Path $HooksSource)) { throw "Hooks source not found: $HooksSource" }

$files = Get-ChildItem -Path $HooksSource -File
foreach ($f in $files) {
    $dest = Join-Path $HooksTarget $f.Name
    if (Test-Path $dest) {
        if (-not $Force) {
            Write-Info "Backing up existing hook: $($f.Name)"
            Copy-Item -Path $dest -Destination (Join-Path $BackupDir $f.Name) -Force
        }
    }
    Copy-Item -Path $f.FullName -Destination $dest -Force
    # Ensure executable on UNIX-like; on Windows git ignores executable bit but keep consistency
    try { git update-index --chmod=+x -- "$dest" | Out-Null } catch { }
    # Mark file as managed by hub for safe cleanup later
    Add-Content -Path $dest -Value "`n# managed-by: lunar-snake-hub"
    Write-Info "Installed hook: $($f.Name) (managed-by: lunar-snake-hub)"
}

Write-Info "Setting core.hooksPath to '$HooksTarget' (local)"
git config --local core.hooksPath "$HooksTarget"

Write-Info "Done. Test with: git commit --allow-empty -m 'hook test'"
