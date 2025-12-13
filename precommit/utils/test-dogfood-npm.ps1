param(
    [string]$RepoRoot = (Get-Location),
    [switch]$Verbose
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Info($m) { Write-Host "[hub-npm-dogfood] $m" }
function Run($cmd) { if ($Verbose) { Info $cmd } ; iex $cmd }

Push-Location $RepoRoot
try {
    if (!(Test-Path ".git")) { throw "Not a git repo: $RepoRoot" }

    Info "Packing npm tarball"
    Run "npm pack"

    $pack = Get-ChildItem -Filter "*.tgz" | Sort-Object LastWriteTime | Select-Object -Last 1
    if (-not $pack) {
        throw "No .tgz pack found after 'npm pack'"
    }
    Info "Using pack: $($pack.Name)"

    $consumerRoot = Join-Path $RepoRoot ".hub-cache/npm-dogfood-consumer"
    if (Test-Path $consumerRoot) {
        Info "Removing existing consumer repo at $consumerRoot"
        Remove-Item -Recurse -Force $consumerRoot
    }
    Info "Creating consumer repo at $consumerRoot"
    New-Item -ItemType Directory -Path $consumerRoot | Out-Null

    Push-Location $consumerRoot
    try {
        Info "Initializing git repo"
        Run "git init ."
        Run "git config user.email 'hub-dogfood@example.com'"
        Run "git config user.name 'Hub Dogfood'"

        Info "Initializing package.json"
        Run "npm init -y"

        Info "Installing hub pack via npm (this runs postinstall hooks)"
        Run "npm install '$($pack.FullName)'"

        Info "Verifying hooks installed and core.hooksPath set"
        $hooksPath = try { git config --local --get core.hooksPath } catch { '' }
        if (-not $hooksPath) {
            throw "core.hooksPath not set locally after npm install"
        }

        $managed = Get-ChildItem ".git/hooks" -File | Where-Object {
            try { Select-String -Path $_.FullName -Pattern 'managed-by: lunar-snake-hub' -Quiet } catch { $false }
        }
        if (-not $managed) {
            throw "No managed hooks detected after npm install"
        }

        Info "Triggering an empty commit to exercise hooks"
        Run "git commit --allow-empty -m 'hub npm dogfood test'"

        Info "Uninstalling hub npm package"
        Run "npm uninstall @giantcroissant-lunar/lunar-snake-hub"

        Info "Verifying hooks and core.hooksPath cleaned up"
        $postHooksPath = try { git config --local --get core.hooksPath } catch { '' }
        if ($postHooksPath) {
            throw "core.hooksPath still set after npm uninstall"
        }

        $postManaged = Get-ChildItem ".git/hooks" -File | Where-Object {
            try { Select-String -Path $_.FullName -Pattern 'managed-by: lunar-snake-hub' -Quiet } catch { $false }
        }
        if ($postManaged) {
            throw "Managed hooks still present after npm uninstall"
        }

        Info "npm dogfood test passed"
    }
    finally {
        Pop-Location
    }
}
finally {
    Pop-Location
}
