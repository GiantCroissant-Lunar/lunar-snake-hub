# Installs pre-commit hooks and injects references from lunar-snake-hub.
# Uses hash comparison to skip injection when files are identical (dogfooding case).
param(
    [string]$HooksSource = "precommit/hooks",
    [string]$HooksTarget = ".git/hooks",
    [string]$BackupDir = ".git/hooks.backup.hub",
    [string]$PackageRoot = "",
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

# Get relative path from consumer root to hub package
function Get-HubRelativePath {
    if ($PackageRoot) {
        return [System.IO.Path]::GetRelativePath((Get-Location), $PackageRoot).Replace('\', '/')
    }
    return "node_modules/@giantcroissant-lunar/lunar-snake-hub"
}

# Load hub configuration
function Get-HubConfig {
    $configPath = if ($PackageRoot) {
        Join-Path $PackageRoot "hub.config.json"
    } else {
        "hub.config.json"
    }

    if (-not (Test-Path $configPath)) {
        Write-Warn "No hub.config.json found at $configPath"
        return $null
    }

    return Get-Content $configPath -Raw | ConvertFrom-Json
}

# Load template content with placeholder substitution
function Get-TemplateContent {
    param(
        [string]$TemplateName,
        [string]$HubPath
    )

    $templatePath = if ($PackageRoot) {
        Join-Path $PackageRoot "templates" $TemplateName
    } else {
        Join-Path "templates" $TemplateName
    }

    if (-not (Test-Path $templatePath)) {
        Write-Warn "Template not found: $templatePath"
        return $null
    }

    $content = Get-Content $templatePath -Raw
    # Substitute {hubPath} placeholder
    $content = $content.Replace("{hubPath}", $HubPath)
    return $content
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

# Remove existing markers from content
function Remove-MarkerContent {
    param(
        [string]$Content,
        [string]$MarkerStart,
        [string]$MarkerEnd
    )

    $escapedStart = [regex]::Escape($MarkerStart)
    $escapedEnd = [regex]::Escape($MarkerEnd)
    $pattern = "(?s)$escapedStart.*?$escapedEnd\r?\n?"

    return $Content -replace $pattern, ''
}

# Inject content into a file
function Add-InjectedContent {
    param(
        [string]$TargetPath,
        [string]$InjectContent,
        [string]$Position
    )

    $existingContent = ""
    if (Test-Path $TargetPath) {
        $existingContent = Get-Content $TargetPath -Raw
        if ($null -eq $existingContent) { $existingContent = "" }
    }

    # Determine marker type based on file extension
    $ext = [System.IO.Path]::GetExtension($TargetPath)
    if ($ext -eq ".md") {
        $markerStart = $script:HubMarkerStartMd
        $markerEnd = $script:HubMarkerEndMd
    } else {
        $markerStart = $script:HubMarkerStartBash
        $markerEnd = $script:HubMarkerEndBash
    }

    # Remove any existing markers first (force replace)
    $existingContent = Remove-MarkerContent $existingContent $markerStart $markerEnd

    switch -Wildcard ($Position) {
        "prepend" {
            $newContent = $InjectContent + "`n" + $existingContent.TrimStart()
        }
        "append" {
            $newContent = $existingContent.TrimEnd() + "`n" + $InjectContent
        }
        "after:*" {
            $afterPattern = $Position.Substring(6)
            if ($existingContent -match "(?m)^$afterPattern\s*$") {
                $newContent = $existingContent -replace "(?m)^($afterPattern)\s*$", "`$1`n$InjectContent"
            } else {
                Write-Warn "Pattern '$afterPattern' not found in $TargetPath, prepending instead"
                $newContent = $InjectContent + "`n" + $existingContent
            }
        }
        default {
            $newContent = $InjectContent + "`n" + $existingContent
        }
    }

    # Ensure parent directory exists
    $parentDir = Split-Path $TargetPath -Parent
    if ($parentDir -and -not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Force -Path $parentDir | Out-Null
    }

    Set-Content $TargetPath -Value $newContent -NoNewline
    return $true
}

# Process injection entries from config
function Install-Injections {
    param([PSCustomObject]$Config, [string]$HubPath)

    $managed = @()

    foreach ($entry in $Config.inject) {
        $targetPath = $entry.target
        $comparePath = if ($PackageRoot) {
            Join-Path $PackageRoot $entry.compare
        } else {
            $entry.compare
        }

        Write-Info "Processing: $targetPath"

        # Hash comparison: skip if files are identical
        $targetHash = Get-FileHashValue $targetPath
        $hubHash = Get-FileHashValue $comparePath

        if ($targetHash -and $hubHash -and ($targetHash -eq $hubHash)) {
            Write-Info "  Skipped (identical content - hash match)"
            continue
        }

        # Load and inject template
        $templateContent = Get-TemplateContent -TemplateName $entry.template -HubPath $HubPath
        if (-not $templateContent) {
            Write-Warn "  Skipped (template not found: $($entry.template))"
            continue
        }

        $injected = Add-InjectedContent -TargetPath $targetPath -InjectContent $templateContent.Trim() -Position $entry.position

        if ($injected) {
            $action = if ($targetHash) { "inject" } else { "create" }
            Write-Info "  $($action): $targetPath"

            $managed += @{
                file = $targetPath
                action = $action
                contentHash = Get-StringHash $templateContent.Trim()
                position = $entry.position
            }
        }
    }

    return $managed
}

# Process hook installations
function Install-Hooks {
    param([PSCustomObject]$Config, [string]$HubPath)

    $managed = @()

    $hooksSourceDir = if ($PackageRoot) {
        Join-Path $PackageRoot $Config.hooks.source
    } else {
        $Config.hooks.source
    }

    if (-not (Test-Path $hooksSourceDir)) {
        Write-Warn "Hooks source directory not found: $hooksSourceDir"
        return $managed
    }

    # Ensure hooks target directory exists
    if (-not (Test-Path $HooksTarget)) {
        Write-Info "Creating $HooksTarget"
        New-Item -ItemType Directory -Force -Path $HooksTarget | Out-Null
    }

    # Ensure backup directory exists
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
    }

    foreach ($hookName in $Config.hooks.files) {
        $sourcePath = Join-Path $hooksSourceDir $hookName
        $targetPath = Join-Path $HooksTarget $hookName

        if (-not (Test-Path $sourcePath)) {
            Write-Warn "Hook source not found: $sourcePath"
            continue
        }

        Write-Info "Processing hook: $hookName"

        # Hash comparison: skip if identical
        $sourceHash = Get-FileHashValue $sourcePath
        $targetHash = Get-FileHashValue $targetPath

        if ($sourceHash -and $targetHash -and ($sourceHash -eq $targetHash)) {
            Write-Info "  Skipped (identical content - hash match)"
            continue
        }

        # Backup existing hook if different
        if (Test-Path $targetPath) {
            Write-Info "  Backing up existing hook"
            Copy-Item -Path $targetPath -Destination (Join-Path $BackupDir $hookName) -Force
        }

        # Copy hook (marker is already in source file)
        Copy-Item -Path $sourcePath -Destination $targetPath -Force

        # Make executable (git index)
        try { git update-index --chmod=+x -- "$targetPath" 2>$null } catch { }

        $action = if ($targetHash) { "replace" } else { "create" }
        Write-Info "  $($action): $hookName"

        # Get hash of the installed hook (with marker)
        $installedHash = Get-FileHashValue $targetPath

        $managed += @{
            file = $targetPath
            action = $action
            contentHash = $installedHash
        }
    }

    return $managed
}

# Save installation manifest
function Save-Manifest {
    param(
        [array]$ManagedInjections,
        [array]$ManagedHooks,
        [string]$HubPath
    )

    $manifest = @{
        version = "2.0.0"
        installedAt = (Get-Date -Format "o")
        hubPath = $HubPath
        injections = $ManagedInjections
        hooks = $ManagedHooks
    }

    $manifest | ConvertTo-Json -Depth 4 | Set-Content ".hub-installed.json"
    Write-Info "Created .hub-installed.json manifest"
}

# === Main Execution ===

if (!(Test-Path ".git")) {
    Write-Warn "Not a git repository, skipping installation"
    exit 0
}

$hubPath = Get-HubRelativePath
Write-Info "Hub path: $hubPath"

$config = Get-HubConfig
if (-not $config) {
    Write-Warn "No configuration found, skipping installation"
    exit 0
}

# Process injections
$managedInjections = @()
if ($config.inject) {
    $managedInjections = Install-Injections -Config $config -HubPath $hubPath
}

# Process hooks
$managedHooks = @()
if ($config.hooks) {
    $managedHooks = Install-Hooks -Config $config -HubPath $hubPath

    # Set git hooks path
    Write-Info "Setting core.hooksPath to '$HooksTarget'"
    git config --local core.hooksPath "$HooksTarget"
}

# Save manifest only if we managed something
$injectionCount = if ($managedInjections) { @($managedInjections).Count } else { 0 }
$hookCount = if ($managedHooks) { @($managedHooks).Count } else { 0 }

if ($injectionCount -gt 0 -or $hookCount -gt 0) {
    Save-Manifest -ManagedInjections $managedInjections -ManagedHooks $managedHooks -HubPath $hubPath
} else {
    Write-Info "No changes made (all files identical or skipped)"
}

Write-Info "Done."
