# Generate an age key for use with SOPS (Project-scoped)
# Key will be stored in .sops/age.key (project root), not globally

$ErrorActionPreference = "Stop"

# Determine project root (go up from infra/secrets to root)
$projectRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$sopsDir = Join-Path $projectRoot ".sops"
$keyPath = Join-Path $sopsDir "age.key"
$pubPath = Join-Path $sopsDir "age.pub"

# Create .sops directory if it doesn't exist
if (-not (Test-Path $sopsDir)) {
    New-Item -ItemType Directory -Path $sopsDir -Force | Out-Null
    Write-Host "Created SOPS directory: $sopsDir"
}

# Generate the key only if it doesn't already exist
if (-not (Test-Path $keyPath)) {
    Write-Host "Generating new age key..."
    age-keygen -o $keyPath
    Write-Host "✅ Age key generated at: $keyPath"
    Write-Host ""

    # Extract public key to separate file
    $publicKeyLine = Get-Content $keyPath | Select-String "^# public key:"
    $publicKeyLine | Out-File -Encoding ascii $pubPath
    $publicKey = $publicKeyLine.ToString() -replace "^# public key: ", ""

    Write-Host "📋 Your public key (saved to $pubPath):"
    Write-Host $publicKey
    Write-Host ""

    Write-Host "📁 Project structure:"
    Write-Host "  .sops/age.key  ❌ NEVER commit (private key, in .gitignore)"
    Write-Host "  .sops/age.pub  ✅ CAN commit (public key, for reference)"
    Write-Host ""

    Write-Host "⚠️  IMPORTANT: Add the PRIVATE key as a GitHub secret:"
    Write-Host "1. Copy the ENTIRE contents of $keyPath"
    Write-Host "2. Go to: https://github.com/GiantCroissant-Lunar/lunar-snake-hub/settings/secrets/actions"
    Write-Host "3. Create a new secret named: SOPS_AGE_KEY"
    Write-Host "4. Paste the entire key file contents"
    Write-Host ""
} else {
    Write-Host "✅ Age key already exists at: $keyPath"

    # Display public key
    $publicKeyLine = Get-Content $keyPath | Select-String "^# public key:"
    $publicKey = $publicKeyLine.ToString() -replace "^# public key: ", ""
    Write-Host "📋 Your public key:"
    Write-Host $publicKey
    Write-Host ""
}

# No need to set environment variable - .sops.yaml references the key file directly
Write-Host "✅ Project uses .sops.yaml key_file directive (no env var needed)"
Write-Host ""
Write-Host "💡 .sops.yaml automatically uses: .sops/age.key"
