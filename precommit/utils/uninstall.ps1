# Uninstalls lunar-snake-hub hooks and removes injected references.
# Uses hash comparison to safely remove only unmodified content.
param(
    [string]$HooksTarget = ".git/hooks",
    [string]$BackupDir = ".git/hooks.backup.hub",
    [switch]$Restore,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Markers for identifying hub-managed content
$script:HubMarkerStartBash = "# === lunar-snake-hub:start ==="
$script:HubMarkerEndBash = "# === lunar-snake-hub:end ==="
$script:HubMarkerStartMd = "<!-- lunar-snake-hub:start -->"
$script:HubMarkerEndMd = "<!-- lunar-snake-hub:end -->"

function Write-Info($msg) { Write-Host "[hub] $msg" }
function Write-Warn($msg) { Write-Host "[hub] WARNING: $msg" -ForegroundColor Yellow }

# Get SHA256 hash of a string
function Get-StringHash {
    param([string]$Content)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Content)
    $hash = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    return [BitConverter]::ToString($hash).Replace("-", "").ToLower()
}

# Get SHA256 hash of a file
function Get-FileHashValue {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    $content = Get-Content $Path -Raw -ErrorAction SilentlyContinue
    if ($null -eq $content) { return $null }
    return Get-StringHash $content
}

# Extract marker content from a file
function Get-MarkerContent {
    param(
        [string]$FilePath,
        [string]$MarkerStart,
        [string]$MarkerEnd
    )

    if (-not (Test-Path $FilePath)) { return $null }

    $content = Get-Content $FilePath -Raw
    $escapedStart = [regex]::Escape($MarkerStart)
    $escapedEnd = [regex]::Escape($MarkerEnd)
    $pattern = "(?s)$escapedStart.*?$escapedEnd"

    if ($content -match $pattern) {
        return $Matches[0]
    }
    return $null
}

# Remove marker content from a file
function Remove-MarkerFromFile {
    param(
        [string]$FilePath,
        [string]$MarkerStart,
        [string]$MarkerEnd
    )

    if (-not (Test-Path $FilePath)) { return $false }

    $content = Get-Content $FilePath -Raw
    $escapedStart = [regex]::Escape($MarkerStart)
    $escapedEnd = [regex]::Escape($MarkerEnd)
    $pattern = "(?s)$escapedStart.*?$escapedEnd\r?\n?"

    if ($content -match $escapedStart) {
        $cleaned = $content -replace $pattern, ''
        Set-Content $FilePath -Value $cleaned.Trim() -NoNewline
        return $true
    }
    return $false
}

# Load installation manifest
function Get-Manifest {
    $manifestPath = ".hub-installed.json"
    if (-not (Test-Path $manifestPath)) {
        return $null
    }
    return Get-Content $manifestPath -Raw | ConvertFrom-Json
}

# Remove injected content from files
function Uninstall-Injections {
    param([PSCustomObject]$Manifest)

    if (-not $Manifest.injections) { return }

    foreach ($entry in $Manifest.injections) {
        $filePath = $entry.file
        Write-Info "Processing: $filePath"

        if (-not (Test-Path $filePath)) {
            Write-Info "  Skipped (file not found)"
            continue
        }

        # Determine marker type based on file extension
        $ext = [System.IO.Path]::GetExtension($filePath)
        if ($ext -eq ".md") {
            $markerStart = $script:HubMarkerStartMd
            $markerEnd = $script:HubMarkerEndMd
        } else {
            $markerStart = $script:HubMarkerStartBash
            $markerEnd = $script:HubMarkerEndBash
        }

        # Extract current marker content
        $currentMarkerContent = Get-MarkerContent -FilePath $filePath -MarkerStart $markerStart -MarkerEnd $markerEnd

        if (-not $currentMarkerContent) {
            Write-Info "  Skipped (no markers found)"
            continue
        }

        # Hash comparison
        $currentHash = Get-StringHash $currentMarkerContent
        $storedHash = $entry.contentHash

        if ($currentHash -ne $storedHash -and -not $Force) {
            Write-Warn "  Skipped (content modified by user, use -Force to override)"
            Write-Info "    Stored hash:  $storedHash"
            Write-Info "    Current hash: $currentHash"
            continue
        }

        # Remove markers
        $removed = Remove-MarkerFromFile -FilePath $filePath -MarkerStart $markerStart -MarkerEnd $markerEnd

        if ($removed) {
            Write-Info "  Removed injection from $filePath"
        }
    }
}

# Remove hooks
function Uninstall-Hooks {
    param([PSCustomObject]$Manifest)

    if (-not $Manifest.hooks) { return }

    foreach ($entry in $Manifest.hooks) {
        $hookPath = $entry.file
        $hookName = Split-Path $hookPath -Leaf

        Write-Info "Processing hook: $hookName"

        if (-not (Test-Path $hookPath)) {
            Write-Info "  Skipped (not found)"
            continue
        }

        # Hash comparison
        $currentHash = Get-FileHashValue $hookPath
        $storedHash = $entry.contentHash

        if ($currentHash -ne $storedHash -and -not $Force) {
            Write-Warn "  Skipped (hook modified, use -Force to override)"
            continue
        }

        # Remove hook
        Remove-Item -Path $hookPath -Force -ErrorAction SilentlyContinue
        Write-Info "  Removed $hookName"

        # Restore backup if exists and requested
        if ($Restore) {
            $backupPath = Join-Path $BackupDir $hookName
            if (Test-Path $backupPath) {
                Copy-Item -Path $backupPath -Destination $hookPath -Force
                Write-Info "  Restored from backup"
            }
        }
    }
}

# Fallback: Remove any hub markers even without manifest
function Remove-StaleMarkers {
    Write-Info "Checking for stale hub markers..."

    # Check common locations
    $filesToCheck = @(
        ".agent/rules/00-index.md",
        ".pre-commit-config.yaml"
    )

    foreach ($file in $filesToCheck) {
        if (-not (Test-Path $file)) { continue }

        $ext = [System.IO.Path]::GetExtension($file)
        if ($ext -eq ".md") {
            $markerStart = $script:HubMarkerStartMd
            $markerEnd = $script:HubMarkerEndMd
        } else {
            $markerStart = $script:HubMarkerStartBash
            $markerEnd = $script:HubMarkerEndBash
        }

        $removed = Remove-MarkerFromFile -FilePath $file -MarkerStart $markerStart -MarkerEnd $markerEnd
        if ($removed) {
            Write-Info "  Removed stale markers from $file"
        }
    }

    # Check for managed hooks
    if (Test-Path $HooksTarget) {
        Get-ChildItem -Path $HooksTarget -File -ErrorAction SilentlyContinue | ForEach-Object {
            $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
            if ($content -match "managed-by: lunar-snake-hub") {
                Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
                Write-Info "  Removed managed hook: $($_.Name)"

                # Restore backup if exists
                if ($Restore) {
                    $backupPath = Join-Path $BackupDir $_.Name
                    if (Test-Path $backupPath) {
                        Copy-Item -Path $backupPath -Destination $_.FullName -Force
                        Write-Info "    Restored from backup"
                    }
                }
            }
        }
    }
}

# Remove manifest file
function Remove-Manifest {
    $manifestPath = ".hub-installed.json"
    if (Test-Path $manifestPath) {
        Remove-Item -Path $manifestPath -Force
        Write-Info "Removed $manifestPath"
    }
}

# === Main Execution ===

if (!(Test-Path ".git")) {
    Write-Warn "Not a git repository"
    exit 0
}

$manifest = Get-Manifest

if ($manifest) {
    Write-Info "Found manifest (version $($manifest.version))"

    # Uninstall based on manifest
    Uninstall-Injections -Manifest $manifest
    Uninstall-Hooks -Manifest $manifest
} else {
    Write-Info "No manifest found, checking for stale markers..."
    Remove-StaleMarkers
}

# Always try to clean up manifest
Remove-Manifest

# Reset hooksPath if set
try {
    $hooksPath = git config --local --get core.hooksPath 2>$null
    if ($hooksPath) {
        Write-Info "Unsetting core.hooksPath"
        git config --local --unset core.hooksPath
    }
} catch { }

Write-Info "Uninstall complete."
