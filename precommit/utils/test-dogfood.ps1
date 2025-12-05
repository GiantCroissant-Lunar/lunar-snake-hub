param(
    [string]$RepoRoot = (Get-Location),
    [switch]$Verbose
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Info($m) { Write-Host "[hub-dogfood] $m" }
function Run($cmd) { if ($Verbose) { Info $cmd } ; iex $cmd }

Push-Location $RepoRoot
try {
    if (!(Test-Path ".git")) { throw "Not a git repo: $RepoRoot" }

    # Ensure clean state
    Info "Ensuring clean working tree"
    Run 'git add -A'
    Run 'git diff --quiet --cached' # no output if clean
    Run 'git diff --quiet' # no output if clean

    # Record pre state
    $preHooksPath = try { git config --local --get core.hooksPath } catch { '' }
    $preHooks = Get-ChildItem .git/hooks -File -ErrorAction SilentlyContinue
    $preBackupExists = Test-Path .git/hooks.backup.hub

    # Install
    Info "Installing hooks via installer"
    pwsh -File precommit/utils/install.ps1 | Out-Null

    # Verify managed markers and hooksPath
    $managed = Get-ChildItem .git/hooks -File | Where-Object {
        try { Select-String -Path $_.FullName -Pattern "managed-by: lunar-snake-hub" -Quiet } catch { $false }
    }
    if (-not $managed) { throw "No managed hooks detected after install" }

    $hooksPath = git config --local --get core.hooksPath
    if (-not $hooksPath) { throw "core.hooksPath not set locally after install" }

    # Trigger hooks
    Info "Triggering an empty commit"
    Run 'git commit --allow-empty -m "hub dogfood test"'

    # Uninstall and restore
    Info "Uninstalling and restoring hooks"
    pwsh -File precommit/utils/uninstall.ps1 -Restore | Out-Null

    # Post state checks
    $postHooksPath = try { git config --local --get core.hooksPath } catch { '' }
    if ($postHooksPath) { throw "core.hooksPath still set after uninstall" }

    $postManaged = Get-ChildItem .git/hooks -File | Where-Object {
        try { Select-String -Path $_.FullName -Pattern "managed-by: lunar-snake-hub" -Quiet } catch { $false }
    }
    if ($postManaged) { throw "Managed hooks still present after uninstall" }

    Info "Dogfood test passed"
} finally {
    Pop-Location
}
