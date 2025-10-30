# Generate an age key for use with SOPS
# Adapted from giantcroissant-lunar-ai project

$ageDir = Join-Path $env:USERPROFILE ".config\sops\age"
if (-not (Test-Path $ageDir)) {
    New-Item -ItemType Directory -Path $ageDir -Force | Out-Null
    Write-Host "Created age key directory: $ageDir"
}

$keyPath = Join-Path $ageDir "keys.txt"

# Generate the key only if it doesn't already exist
if (-not (Test-Path $keyPath)) {
    Write-Host "Generating new age key..."
    age-keygen | Out-File -Encoding ascii $keyPath
    Write-Host "✅ Age key generated at: $keyPath"
    Write-Host ""

    # Extract and display public key
    $publicKey = (Get-Content $keyPath | Select-String "^# public key:").ToString() -replace "^# public key: ", ""
    Write-Host "📋 Your public key (for .sops.yaml):"
    Write-Host $publicKey
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
    $publicKey = (Get-Content $keyPath | Select-String "^# public key:").ToString() -replace "^# public key: ", ""
    Write-Host "📋 Your public key:"
    Write-Host $publicKey
    Write-Host ""
}

# Set environment variable
$env:SOPS_AGE_KEY_FILE = $keyPath
Write-Host "✅ Environment variable set: SOPS_AGE_KEY_FILE=$keyPath"
Write-Host ""
Write-Host "💡 To make this permanent, add to your PowerShell profile:"
Write-Host "`$env:SOPS_AGE_KEY_FILE = '$keyPath'"
